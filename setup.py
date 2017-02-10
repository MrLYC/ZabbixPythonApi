#!/usr/bin/env python
# coding=utf-8

import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from zabbixapi import __version__

long_description = ""
if os.path.exists("README"):
    with open("README", "rt") as fp:
        long_description = fp.read()
elif os.path.exists("README.md"):
    with open("README.md", "rt") as fp:
        long_description = fp.read()

setup(
    name='zabbixapi',
    version=__version__,
    description='a tool to communicate to zabbix',
    long_description=long_description,
    author='Liu Yicong',
    author_email='imyikong@gmail.com',
    packages=["zabbixapi"],
    include_package_data=True,
    install_requires=(),
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',

        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
