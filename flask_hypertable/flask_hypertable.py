#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

from hypertable.thriftclient import ThriftClient

# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

from flask import current_app


class FlaskHypertable(object):
    """ Flask extension for the Hypertable ThriftClient. """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

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

    def connect(self):
        return ThriftClient(current_app.config['HYPERTABLE_HOST'],
                            current_app.config['HYPERTABLE_PORT'])

    def teardown(self, exception):
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
