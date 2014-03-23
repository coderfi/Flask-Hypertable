#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import os
import sys
import re

_package_file = os.path.join(os.path.dirname(__file__),
                            "flask_hypertable/__init__.py")


class Package_Metadata(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    attributes = [
        'title', 'package_name', 'author', 'description', 'email',
        'version', 'license', 'copyright'
    ]

    @staticmethod
    def get_attribute(attr, file_content,):
        regex_expression = r"^__{0}__ = ['\"]([^'\"]*)['\"]".format(attr)
        mo = re.search(regex_expression, file_content, re.M)
        if mo:
            return mo.group(1)
        else:
            raise RuntimeError("Unable to find __%s__ string in %s."
                               % (attr, _package_file,))

    def refresh(self, attributes):
        f = open(self.package_file, "rt")
        try:
            file_content = f.read()
        finally:
            f.close()

        for k in attributes:
            attr_val = self.get_attribute(k, file_content)
            if attr_val:
                self[k] = attr_val

    def __init__(self, package_file, attributes=None):
        if attributes:
            self.attributes = attributes

        self.package_file = package_file

        self.refresh(self.attributes)

p = Package_Metadata(_package_file)


def print_metadata():
    for k, v in p.items():
        print('%s: %s' % (k, v))

if __name__ == '__main__':
    print_metadata()
    sys.exit()
