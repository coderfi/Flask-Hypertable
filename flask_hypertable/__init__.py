#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Flask Hypertable
----------------

A Flask extension for Hypertable over Thrift.

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

__title__ = 'Flask Hypertable'
__package_name__ = 'Flask-Hypertable'
__author__ = 'Fairiz Azizi'
__description__ = 'A Flask extension for Hypertable over Thrift.'
__email__ = 'coderfi@gmail.com'
__version__ = '0.3.0'
__license__ = 'BSD'
__copyright__ = 'Copyright 2014 Fairiz Azizi'

from .flask_hypertable import FlaskHypertable, FlaskPooledHypertable
