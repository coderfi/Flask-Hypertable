========
Usage
========

Configuration
-------------

Your configuration should be declared within your Flask config::

    HYPERTABLE_HOST = "localhost"
    HYPERTABLE_PORT = 38080

Flask App Extension
-------------------

To create the Hypertable instance within your application::

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

The base ``hypertable.thriftclient.ThriftClient`` is available as the
``ht.connection`` attribute.

Example Usage
-------------

::

    #...

    client = ht.connection
    ns = client.namespace_open("test")
    #do some stuff...
    #see http://hypertable.com/documentation/code_examples/python
    client.close_namespace(ns)

