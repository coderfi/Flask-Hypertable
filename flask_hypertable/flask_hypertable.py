#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

__all__ = ['FlaskHypertable', 'FlaskPooledHypertable']

import atexit

from Queue import Queue, Empty, Full
from hypertable.thriftclient import ThriftClient
from flask import current_app
from thrift.transport import TTransport

# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

# see http://flask.pocoo.org/docs/extensiondev/
# pool settings inspired
# by sqlalchemy: http://docs.sqlalchemy.org/en/rel_0_9/core/pooling.html


class FlaskHypertable(object):
    """ Flask extension for the Hypertable ThriftClient.

    The following is the expected app configuration and defaults:

    HYPERTABLE_HOST: 'localhost'
    HYPERTABLE_PORT: 38080

    Under the hood, this extension uses the ``ManagedThriftClient``.
    """

    app = None

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

        # register just in case
        atexit.register(self.close_app)

    def init_app(self, app):
        """
        Connects Hypertable to your Flask app.
        """
        app.config.setdefault('HYPERTABLE_HOST', 'localhost')
        app.config.setdefault('HYPERTABLE_PORT', 38080)

        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def __del__(self):
        self.close_app()

    def close_app(self):
        """ shutdowns this instance, releasing the connection pool """
        pass

    def connect(self):
        """ Creates a new Thrift client
        :return: ``ManagedThriftClient``
        """
        return ManagedThriftClient(current_app.config['HYPERTABLE_HOST'],
                                   current_app.config['HYPERTABLE_PORT'])

    def teardown(self, exception):
        """ Puts the connection object back into the pool. """
        ctx = stack.top
        if hasattr(ctx, 'ht_client'):
            ctx.ht_client.close()

    @property
    def connection(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'ht_client'):
                ctx.ht_client = self.connect()
            return ctx.ht_client


class FlaskPooledHypertable(FlaskHypertable):
    """ Extends FlaskHypertable to offer pooled Hypertable ThriftClient
    connections.

    Be sure to call close_app() to properly shutdown the pools
    (if enabled).

    The following additional configuration is supported/required:

    #the size of the pool to maintain, you probably want at least 1
    HYPERTABLE_POOL_SIZE: 5

    #if all connections are busy, create this many extra connections
    #0 disables
    HYPERTABLE_MAX_OVERFLOW: 10
    """

    # the connection pool
    _q = None

    # the overflow pool
    _qo = None

    pool_size = 1
    pool_overflow = 0
    overflow_count = 0

    def init_app(self, app):
        FlaskHypertable.init_app(self, app)

        self._q = self._qo = None

        app.config.setdefault('HYPERTABLE_POOL_SIZE', 5)
        app.config.setdefault('HYPERTABLE_MAX_OVERFLOW', 10)

        self.pool_size = app.config['HYPERTABLE_POOL_SIZE']
        self.pool_overflow = app.config['HYPERTABLE_MAX_OVERFLOW']

        if self.pool_size < 0:
            raise ValueError("Please specify HYPERTABLE_POOL_SIZE >= 0")
        elif self.pool_overflow < 0:
            raise ValueError("Please specify HYPERTABLE_MAX_OVERFLOW >= 0")

        self._q = Queue(maxsize=self.pool_size)
        if self.pool_overflow > 0:
            self._qo = Queue(maxsize=self.pool_overflow)

    def close_app(self):
        """ shutdowns this instance, forcibly closing all opened
        connections """
        err = None
        while True:
            try:
                client = self._q.get_nowait()
                try:
                    client.close()
                except Exception, e:
                    err = e
            except Empty:
                break

        FlaskHypertable.close_app(self)

        if err:
            raise

    def connect(self):
        """ Grabs a ThriftClient from the pool or create a new one
        if the pool is empty.
        """
        try:
            client = self._q.get_nowait()
        except Empty:
            if self.overflow_count >= self.pool_overflow:
                client = self._q.get(block=True)
            else:
                client = FlaskHypertable.connect(self)
                self.overflow_count += 1

        return client

    # blow away the super class's teardown
    def teardown(self, exception):
        """ Puts the connection object back into the pool.

        :param: exception if a org.apache.thrift.transport.TTransportException,
                then the connection object is immediately closed
                and is thrown away
        """
        ctx = stack.top
        if hasattr(ctx, 'ht_client'):
            if isinstance(exception, TTransport.TTransportException):
                # throw it away
                if ctx.ht_client.is_active:
                    self.overflow_count = max(0, self.overflow_count - 1)
                    ctx.ht_client.close()
            else:
                try:
                    self._q.put_nowait(ctx.ht_client)
                except Full:
                    # musta overflowed
                    self.overflow_count = max(0, self.overflow_count - 1)
                    if ctx.ht_client.is_active:
                        ctx.ht_client.close()


class ManagedThriftClient(ThriftClient):
    """ Extends the base ``hypertable.thriftclient.ThriftClient``
    with additional helper methods.

    Provides the convenient ``mns`` member of type ``ManagedNamespaces``.

    >>> client = ManagedThriftClient("localhost", 38080)
    >>> res = client.hql_query(client.mns['test'], "select * from foo")
    >>> client.close() #closes any opened namespaces
    """

    mns = None

    def __init__(self, *args, **kwargs):
        ThriftClient.__init__(self, *args, **kwargs)

        self.mns = ManagedNamespaces(self)

    def close(self):
        if self.mns:
            self.mns.close()
        ThriftClient.close(self)

    def __del__(self):
        self.close()


class ManagedNamespaces(object):
    """ Manages opening and closing namespaces.

    Not thread safe.
    """

    namespaces = None

    def __init__(self, client):
        self.client = client
        self.namespaces = {}

    def __getitem__(self, key):
        return self.open_namespace(key)

    def __delitem__(self, key):
        return self.close_namespace(key)

    def open_namespace(self, name):
        """ Opens the specified namespace.
        If already opened, then return the previous identifier.

        :param: name str: the name of the namespace
        :return: the namespace identifier
        """

        if name in self.namespaces:
            return self.namespaces[name]

        ns = self.namespaces[name] = self.client.open_namespace(name)

        return ns

    def close_namespace(self, name):
        """ Closes the specified namespace.
        Does nothing if already closed or was not previously opened.

        :param: name str: the name of the namespace
        :return: the previous identifier or None if never opened
        """
        ns = self.namespaces.get(name)
        if ns:
            self.namespaces[name] = ns
            self.client.close_namespace(ns)
        return ns

    def close(self):
        """ Closes all previously opened namespaces. """

        while self.namespaces:
            self.close_namespace(self.namespaces.popitem()[1])

    def __del__(self):
        """ Calls close(). """

        self.close()
