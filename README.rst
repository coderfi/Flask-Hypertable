================
Flask Hypertable
================


.. image:: https://travis-ci.org/coderfi/Flask-Hypertable.png?branch=master
    :target: https://travis-ci.org/coderfi/Flask-Hypertable

.. image:: https://badge.fury.io/gh/coderfi%2FFlask-Hypertable.png
    :target: http://badge.fury.io/gh/coderfi%2FFlask-Hypertable

.. image:: https://coveralls.io/repos/coderfi/Flask-Hypertable/badge.png?branch=master
    :target: https://coveralls.io/r/coderfi/flask-hypertable?branch=master

.. image:: https://pypip.in/d/PYPI_PKG_NAME/badge.png
    :target: https://pypi.python.org/pypi//Flask-Hypertable/
    :alt: Downloads

``Flask-Hypertable`` - A Flask extension which provides connectivity to 
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
    easy_install Flask-Hypertable


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
Hypertable      0.9.5.6 (other versions likely to work) http://hypertable.com/documentation/reference_manual/thrift_api
Thrift          https://thrift.apache.org/docs/
Python support  Python 2.7
Source          https://github.com/coderfi/flask-hypertable
Docs            http://flask-hypertable.rtfd.org
Changelog       http://flask-hypertable.readthedocs.org/en/latest/history.html
API             http://flask-hypertable.readthedocs.org/en/latest/api.html
Issues          https://github.com/coderfi/Flask-Hypertable/issues
Travis          http://travis-ci.org/coderfi/Flask-Hypertable
Test coverage   https://coveralls.io/r/coderfi/Flask-Hypertable
pypi            https://pypi.python.org/pypi/Flask-Hypertable
Ohloh           https://www.ohloh.net/p/Flask-Hypertable
License         `BSD`_.
git repo        .. code-block:: bash

                    $ git clone https://github.com/coderfi/Flask-Hypertable.git
install dev     .. code-block:: bash

                    $ git clone https://github.com/coderfi/Flask-Hypertable.git flask-hypertable
                    $ cd ./flask-hypertable
                    $ virtualenv .env
                    $ source .env/bin/activate
                    $ pip install -e .
tests           .. code-block:: bash

                    $ python setup.py test

                or

                .. code-block:: bash

                    $ tox

                or

                .. code-block:: bash

                    $ python run-tests.py


==============  ==========================================================

About This Project
------------------

Project started with `cookiecutter-pypackage <https://github.com/tony/cookiecutter-pypackage>`_.

.. _BSD: http://opensource.org/licenses/BSD-3-Clause
.. _Documentation: http://flask-hypertable.readthedocs.org/en/latest/
.. _API: http://flask-hypertable.readthedocs.org/en/latest/api.html
