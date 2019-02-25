#!/usr/bin/env python
# coding: utf8

from setuptools import setup

setup(
    name='coeftable',
    version='1.1',
    description=u'three command-line tools to generate arbitrarily formatted tables from JSON data files',
    author=u'Gabor Nyeki',
    url='http://www.gabornyeki.com/',
    packages=['coeftable'],
    install_requires=['argh'],
    provides=['coeftable (1.1)'],
    entry_points={
        'console_scripts': [
            'coeftable = coeftable.coeftable:main',
            'csv2textemplate = coeftable.csv2textemplate:main',
            'makecttemplate = coeftable.makecttemplate:main',
        ],
    }
    )
