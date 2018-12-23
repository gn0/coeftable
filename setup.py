#!/usr/bin/env python
# coding: utf8

from setuptools import setup

setup(
    name='coeftable',
    version='1.0',
    description=u'',
    author=u'Gabor Nyeki',
    url='http://www.gabornyeki.com/',
    packages=['coeftable'],
    install_requires=['argh'],
    provides=['coeftable (1.0)'],
    entry_points={
        'console_scripts': [
            'coeftable = coeftable.coeftable:main',
            'csv2textemplate = coeftable.csv2textemplate:main'
        ],
    }
    )
