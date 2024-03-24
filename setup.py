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
    files = {'java/javase.jar': 'https://repo1.maven.org/maven2/com/google/zxing/javase/3.5.3/javase-3.5.3.jar',
             'java/core.jar': 'https://repo1.maven.org/maven2/com/google/zxing/core/3.5.3/core-3.5.3.jar',
             'java/jcommander.jar': 'https://repo1.maven.org/maven2/com/beust/jcommander/1.82/jcommander-1.82.jar'}

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
    description="Wrapper for decoding/reading barcodes with ZXing (Zebra Crossing) library",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/dlenski/python-zxing",
    author='Daniel Lenski',
    author_email='dlenski@gmail.com',
    packages=['zxing'],
    package_data={'zxing': download_java_files()},
    entry_points={'console_scripts': ['zxing=zxing.__main__:main']},
    extras_require={
        "Image": [
            "pillow>=3.0,<6.0; python_version < '3.5'",
            "pillow>=3.0,<8.0; python_version >= '3.5' and python_version < '3.6'",
            "pillow>=8.0; python_version >= '3.6'",
        ]
    },
    install_requires=open('requirements.txt').readlines(),
    python_requires=">=3",
    tests_require=open('requirements-test.txt').readlines(),
    test_suite='nose2.collector.collector',
    license='LGPL v3 or later',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Topic :: Multimedia :: Graphics :: Capture',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Software Development :: Libraries :: Java Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
