#!/usr/bin/env python3

from setuptools import setup
from urllib.request import urlretrieve
from urllib.error import URLError
from os import access, path, R_OK

def download_java_files():
    files = {'java/javase.jar': 'https://repo1.maven.org/maven2/com/google/zxing/javase/3.3.0/javase-3.3.0.jar',
             'java/core.jar': 'https://repo1.maven.org/maven2/com/google/zxing/core/3.3.0/core-3.3.0.jar',
             'java/jcommander.jar': 'https://repo1.maven.org/maven2/com/beust/jcommander/1.7/jcommander-1.7.jar'}

    for fn, url in files.items():
        p = path.join(path.dirname(__file__), 'zxing', fn)
        if access(p, R_OK):
            print("Already have %s." % p)
        else:
            print("Downloading %s from %s ..." % (p, url))
            try:
                urlretrieve(url, p)
            except URLError as e:
                raise SystemExit(*e.args)
    return list(files.keys())

setup(
    name='zxing',
    version='0.4',
    description="wrapper for zebra crossing (zxing) barcode library",
    author='Dan Lenski',
    author_email='dlenski@gmail.com',
    packages=['zxing'],
    package_data = {'zxing': download_java_files()},
    entry_points = {'console_scripts': ['zxing=zxing.__main__:main']},
)
