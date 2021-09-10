#!/usr/bin/env python3

import sys
from os import R_OK, access, makedirs, path
from urllib.error import URLError
from urllib.request import urlretrieve

from setuptools import setup

if not sys.version_info[0] == 3:
    sys.exit("Python 2.x is not supported; Python 3.x is required.")

########################################

version_py = path.join(path.dirname(__file__), 'zxing', 'version.py')

d = {}
with open(version_py, 'r') as fh:
    exec(fh.read(), d)
    version_pep = d['__version__']

########################################


def download_java_files(force=False):
    files = {'java/javase.jar': 'https://repo1.maven.org/maven2/com/google/zxing/javase/3.4.1/javase-3.4.1.jar',
             'java/core.jar': 'https://repo1.maven.org/maven2/com/google/zxing/core/3.4.1/core-3.4.1.jar',
             'java/jcommander.jar': 'https://repo1.maven.org/maven2/com/beust/jcommander/1.78/jcommander-1.78.jar'}

    for fn, url in files.items():
        p = path.join(path.dirname(__file__), 'zxing', fn)
        d = path.dirname(p)
        if not force and access(p, R_OK):
            print("Already have %s." % p)
        else:
            print("Downloading %s from %s ..." % (p, url))
            try:
                makedirs(d, exist_ok=True)
                urlretrieve(url, p)
            except (OSError, URLError) as e:
                raise
    return list(files.keys())


setup(
    name='zxing',
    version=version_pep,
    description="wrapper for zebra crossing (zxing) barcode library",
    long_description="More information: https://github.com/dlenski/python-zxing",
    url="https://github.com/dlenski/python-zxing",
    author='Daniel Lenski',
    author_email='dlenski@gmail.com',
    packages=['zxing'],
    package_data={'zxing': download_java_files()},
    entry_points={'console_scripts': ['zxing=zxing.__main__:main']},
    install_requires=open('requirements.txt').readlines(),
    tests_require=open('requirements-test.txt').readlines(),
    test_suite='nose.collector',
    license='LGPL v3 or later',
)
