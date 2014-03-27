========
Usage
========

This package provides two extension points

* ``FlaskHypertable``

  Provides a basic ``ThriftClient`` connection to ``Hypertable``.
  The connection is opened and closed for every HTTP request.

* ``FlaskPooledHypertable``

  Extends the base ``FlaskHypertable`` class to offer transparent 
  connection pooling.
  The connection is opened only once for the lifetime of this instance.
  The ``ThriftClient`` is reused across HTTP requests.

Configuration
-------------

Your configuration should be declared within your Flask config::

    HYPERTABLE_HOST = "localhost"
    HYPERTABLE_PORT = 38080

    ################
    #if using FlaskPooledHypertable

    #the size of the pool to maintain, you probably want at least 1
    HYPERTABLE_POOL_SIZE = 5

    #if all connections are busy, create this many extra connections
    #0 disables
    HYPERTABLE_MAX_OVERFLOW = 10

Flask App Extension
-------------------

To create the ``FlaskHypertable`` instance within your application::

    from flask import Flask
    from flask_hypertable import FlaskHypertable

    app = Flask(__name__)
    ht = FlaskHypertable(app) 

or::

    from flask import Flask
    from flask_hypertable import FlaskHypertable

    ht = FlaskHypertable()

    def create_app():
        app = Flask(__name__)
        ht.init_app(app)
        return app

Or if you would like to use pooled connections::

    from flask import Flask
    from flask_hypertable import FlaskPooledHypertable

    app = Flask(__name__)
    ht = FlaskPooledHypertable(app) 

or::

    from flask import Flask
    from flask_hypertable import FlaskPooledHypertable

    ht = FlaskPooledHypertable()

    def create_app():
        app = Flask(__name__)
        ht.init_app(app)
        return app

The Flask extension provides the ``flask_hypertable.ManagedThriftClient``
instance as the ``ht.connection`` member attribute.

To properly shutdown the ``FlaskPooledHypertable`` the
`close_app` method is automatically called at exit, or, you
may call it manually.

Basic Usage
-----------

The following demonstrates using the extension at its most basic level.

See `Hypertable Python Code Examples<http://hypertable.com/documentation/code_examples/python>`_ 
for more information.

::

    #...

    client = ht.connection

    #...
    #in some method
    ns = client.namespace_open("test")
    res = client.hql_query(ns, "select * from foo")
    for cell in res.cells: print cell
    client.close_namespace(ns)

    #...
    #in some other method (during the same request)
    ns = client.namespace_open("test")
    res = client.hql_query(ns, "select * from bar")
    for cell in res.cells: print cell
    client.close_namespace(ns)

Managed Namespaces
------------------

The above example suffers by having duplicate boiler plate code
surrounding opening the namespace.

It also suffers from the fact that each method will end up opening and
closing namespaces more than once within a request.

To alleviate this, the ``FlaskHypertable.connection`` can help you manage
your namespaces.
This is available through a helper member attribute
called ``mns``.

This helper provides a method to open or reuse previously
created namespaces.

In this manner, we also prevent unnecessary roundtrips to Hypertable.

The above would shorten to something like this::

    #...

    client = ht.connection

    #in some method
    res = client.hql_query(client.mns['test'], "select * from foo")

    #in some other method (during the same request)
    res = client.hql_query(client.mns['test'], "select * from bar")

In the above example, ``client.ns['test']`` is a shortcut to
``client.mns.open_namespace('test')``.

To close the namespace::

    client.mns.close_namespace('test')

    #or

    client.close()

Troubleshooting
---------------

* ThriftClient.open and close seems to be calling too much

  * Use the ``FlaskPooledHypertable`` instead (new since v0.2.0)

  * Try changing the pool configuration settings.

  Did you remember to call the ``FlaskHypertable.init_app(app)`` method when setting
  up your Flask App? If not, the extension will fall back to creating itself in
  each context.
  See `Flask Extension Development<http://flask.pocoo.org/docs/extensiondev/>`_ for more info.
