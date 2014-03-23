================
Flask Hypertable
================


.. image:: https://travis-ci.org/coderfi/flask_hypertable.png?branch=master
    :target: https://travis-ci.org/coderfi/flask_hypertable

.. image:: https://badge.fury.io/py/flask_hypertable.png
    :target: http://badge.fury.io/py/flask_hypertable

.. image:: https://coveralls.io/repos/coderfi/flask_hypertable/badge.png?branch=master
    :target: https://coveralls.io/r/coderfi/flask_hypertable?branch=master

.. image:: https://pypip.in/d/flask_hypertable/badge.png
        :target: https://crate.io/packages/flask_hypertable?version=latest

``flask_hypertable`` - A Flask extension which provides connectivity to 
`Hypertable <http://hypertable.org/>`_ over `Thrift <https://thrift.apache.org/>`_.


Features
--------

* ``FlaskHypertable`` ``hypertable.thrift.ThriftClient`` Flask extension.


Installation
------------

.. code-block:: bash

    pip install Flask-Hypertable

Or if you *must* use easy_install:

.. code-block:: bash

    alias easy_install="pip install $1"
    easy_install flask-redis


Configuration
-------------

Your configuration should be declared within your Flask config.

.. code-block:: python

    HYPERTABLE_HOST = "localhost"
    HYPERTABLE_PORT = 38080

To create the Hypertable instance within your application

.. code-block:: python

    from flask import Flask
    from flask_hypertable import FlaskHypertable

    app = Flask(__name__)
    ht = FlaskHypertable(app) 

or

.. code-block:: python

    from flask import Flask
    from flask_hypertable import FlaskHypertable

    ht = FlaskHypertable()

    def create_app():
        app = Flask(__name__)
        ht.init_app(app)
        return app


==============  ==========================================================
Hypertable      http://hypertable.com/documentation/reference_manual/thrift_api
Thrift          https://thrift.apache.org/docs/
Python support  Python 2.7, >= 3.3
Source          https://github.com/coderfi/flask_hypertable
Docs            http://flask_hypertable.rtfd.org
Changelog       http://flask_hypertable.readthedocs.org/en/latest/history.html
API             http://flask_hypertable.readthedocs.org/en/latest/api.html
Issues          https://github.com/coderfi/flask_hypertable/issues
Travis          http://travis-ci.org/coderfi/flask_hypertable
Test coverage   https://coveralls.io/r/coderfi/flask_hypertable
pypi            https://pypi.python.org/pypi/flask_hypertable
Ohloh           https://www.ohloh.net/p/flask_hypertable
License         `BSD`_.
git repo        .. code-block:: bash

                    $ git clone https://github.com/coderfi/flask_hypertable.git
install dev     .. code-block:: bash

                    $ git clone https://github.com/coderfi/flask_hypertable.git flask_hypertable
                    $ cd ./flask_hypertable
                    $ virtualenv .env
                    $ source .env/bin/activate
                    $ pip install -e .
tests           .. code-block:: bash

                    $ python setup.py test
==============  ==========================================================

About This Project
------------------

Project started with `cookiecutter-pypackage <https://github.com/tony/cookiecutter-pypackage>`_.

.. _BSD: http://opensource.org/licenses/BSD-3-Clause
.. _Documentation: http://flask_hypertable.readthedocs.org/en/latest/
.. _API: http://flask_hypertable.readthedocs.org/en/latest/api.html
