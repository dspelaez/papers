#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 Daniel Santiago <dpelaez@cicese.edu.mx>
#
# Distributed under terms of the GNU/GPL license.

from setuptools import setup

setup(
    name='papers',
    version='0.1',
    py_modules=['papers'],
    install_requires=[
        'bibtexparser',
        'requests',
        'Click',
        'PyPDF2',
        'pyyaml',
        'inquirer',
        'colorama',
    ],
    entry_points='''
        [console_scripts]
        papers=papers.cli:cli
    ''',
)
