#!/usr/bin/env python
 
from setuptools import setup

setup(
    name='zxing',
    version='0.4',
    description="wrapper for zebra crossing (zxing) barcode library",
    author='Dan Lenski',
    author_email='dlenski@gmail.com',
    packages=['zxing'],
    package_data = {'zxing': ['java/core.jar', 'java/javase.jar', 'java/jcommander.jar']}
)
