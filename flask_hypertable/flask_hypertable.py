#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

__all__ = ['FlaskHypertable', 'FlaskPooledHypertable']

import atexit

from Queue import Queue, Empty, Full
from hypertable.thriftclient import ThriftClient
from thrift.transport import TTransport

import threading

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
    HYPERTABLE_TIMEOUT_MSECS: 5000

    Under the hood, this extension uses the ``ManagedThriftClient``.
    """

    app = None
    data = None

    def __init__(self, app=None, local=None):
        self.app = app
        if app is not None:
            self.init_app(app, local=local)

        # register just in case
        atexit.register(self.close_app)

    def init_app(self, app, local=None):
        """
        Connects Hypertable to your Flask app.

        :param local - if provided, this should be a callable
               that returns a collection object suitable for local storage.
               Default is ``threading.local``
               This is used by __enter__ and __exit__.
        """
        if local is None:
            self.data = threading.local()
        else:
            self.data = local()

        app.config.setdefault('HYPERTABLE_HOST', 'localhost')
        app.config.setdefault('HYPERTABLE_PORT', 38080)
        app.config.setdefault("HYPERTABLE_TIMEOUT_MSECS", 5000)

        self.host = app.config['HYPERTABLE_HOST']
        self.port = app.config['HYPERTABLE_PORT']
        self.timeout_msecs = app.config['HYPERTABLE_TIMEOUT_MSECS']

        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def __del__(self):
        try:
            self.close_app()
        except:
            pass  # just in case

    def close_app(self):
        """ shutdowns this instance, releasing the connection pool """
        pass

    def connect(self):
        """ Creates a new Thrift client
        :return: ``ManagedThriftClient``
        """
        return ManagedThriftClient(self.host,
                                   self.port,
                                   timeout_ms=self.timeout_msecs)

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

    def __enter__(self):
        """ Calls connect() and puts the Client object
        into the thread local storage.
        """
        client = self.data.ht_client = self.connect()
        return client

    def __exit__(self, t, value, traceback):
        """ Closes the Client that was stored in the thread local storage
        by the __enter__ method.
        """
        ht_client = (hasattr(self.data, 'ht_client')
                     and self.data.ht_client
                     or None)

        if ht_client:
            if ht_client.is_active:
                self.overflow_count = max(0, self.overflow_count - 1)
                ht_client.close()

        self.data.ht_client = None


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

    # a queue like collection
    _q = None

    pool_size = 1
    pool_overflow = 0
    overflow_count = 0

    def init_app(self, app, local=None, qClass=None):
        """
        :param qClass the queue class to use, optional.
               Default is ``Queue.Queue`
        """
        FlaskHypertable.init_app(self, app, local=local)

        self._q = None

        app.config.setdefault('HYPERTABLE_POOL_SIZE', 5)
        app.config.setdefault('HYPERTABLE_MAX_OVERFLOW', 10)

        self.pool_size = app.config['HYPERTABLE_POOL_SIZE']
        self.pool_overflow = app.config['HYPERTABLE_MAX_OVERFLOW']

        if self.pool_size < 0:
            raise ValueError("Please specify HYPERTABLE_POOL_SIZE >= 0")
        elif self.pool_overflow < 0:
            raise ValueError("Please specify HYPERTABLE_MAX_OVERFLOW >= 0")

        qClass = qClass or Queue
        self._q = qClass(maxsize=self.pool_size)

    def close_app(self):
        """ shutdowns this instance, forcibly closing all opened
        connections """
        err = None

        if self._q:
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

    def put_back(self, ht_client):
        """ returns the client to the pool """

        try:
            self._q.put_nowait(ht_client)
        except Full:
            # musta overflowed
            self.overflow_count = max(0, self.overflow_count - 1)
            if ht_client.is_active:
                ht_client.close()

    # completely override based class
    def __exit__(self, t, value, traceback):
        """ Puts the connection object back into the pool.

        :param: value if a org.apache.thrift.transport.TTransportException,
                then the connection object is immediately closed
                and is thrown away
        """
        ht_client = (hasattr(self.data, 'ht_client')
                     and self.data.ht_client
                     or None)

        if ht_client:
            if isinstance(value, TTransport.TTransportException):
                # throw it away
                if ht_client.is_active:
                    self.overflow_count = max(0, self.overflow_count - 1)
                    ht_client.close()
            else:
                self.put_back(ht_client)

        self.data.ht_client = None


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
        try:
            self.close()
        except:
            pass  # just in case


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
        try:
            self.close()
        except:
            pass  # just in case
