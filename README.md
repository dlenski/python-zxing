# python-zxing

[![PyPI](https://img.shields.io/pypi/v/zxing.svg)](https://pypi.python.org/pypi/zxing)
[![Build Status](https://github.com/dlenski/python-zxing/workflows/test_and_release/badge.svg)](https://github.com/dlenski/python-zxing/actions/workflows/test_and_release.yml)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

This is a wrapper for the [ZXing barcode library](https://github.com/zxing/zxing).
It will allow you to read and decode barcode images from Python.

It was originally a "slightly less quick-and-dirty" fork of [oostendo/python-zxing](https://github.com/oostendo/python-zxing), but has since
evolved considerably beyond that ancestral package.

## Dependencies and installation

Use the Python 3 version of pip (usually invoked via `pip3`) to install: `pip3 install zxing`

* You'll neeed to have a recent `java` binary somewhere in your path. (Tested with OpenJDK v7, v8, v11.)
* pip will automatically download the relevant [JAR](https://en.wikipedia.org/wiki/JAR_(file_format)) files for the Java ZXing libraries (currently v3.5.3)

## Usage

The `BarCodeReader` class is used to decode images:

```python
>>> import zxing
>>> reader = zxing.BarCodeReader()
>>> print(reader.zxing_version, reader.zxing_version_info)
3.5.1 (3, 5, 1)
>>> barcode = reader.decode("test/barcodes/QR_CODE-easy.png")
>>> print(barcode)
BarCode(raw='This should be QR_CODE', parsed='This should be QR_CODE', path='test/barcodes/QR_CODE-easy.png', format='QR_CODE', type='TEXT', points=[(15.0, 87.0), (15.0, 15.0), (87.0, 15.0), (75.0, 75.0)])
```

The attributes of the decoded `BarCode` object are `raw`, `parsed`, `path`, `format`, `type`, `points`, and `raw_bits`.
The list of formats which ZXing can decode is [here](https://zxing.github.io/zxing/apidocs/com/google/zxing/BarcodeFormat.html).

The `decode()` method accepts an image path or [PIL Image object](https://pillow.readthedocs.io/en/stable/reference/Image.html) (or list thereof)
and takes optional parameters `try_harder` (boolean), `possible_formats` (list of formats to consider), and `pure_barcode` (boolean).
If no barcode is found, it returns a `False`-y `BarCode` object with all fields except `path` set to `None`.
If it encounters any other recognizable error from the Java ZXing library, it raises `BarCodeReaderException`.

## Command-line interface

The command-line interface can decode images into barcodes and output in either a human-readable or CSV format:

```
usage: zxing [-h] [-c] [--try-harder] [--pure-barcode] [-V] image [image ...]
```

Human-readable:

```sh
$ zxing /tmp/barcode.png
/tmp/barcode.png
================
  Decoded TEXT barcode in QR_CODE format.
  Raw text:    'Testing 123'
  Parsed text: 'Testing 123'
```

CSV output (can be opened by LibreOffice or Excel):

```sh
$ zxing /tmp/barcode1.png /tmp/barcode2.png /tmp/barcode3.png
Filename,Format,Type,Raw,Parsed
/tmp/barcode1.png,CODE_128,TEXT,Testing 123,Testing 123
/tmp/barcode2.png,QR_CODE,URI,http://zxing.org,http://zxing.org
/tmp/barcode3.png,QR_CODE,TEXT,"This text, ""Has stuff in it!"" Wow⏎Yes it does!","This text, ""Has stuff in it!"" Wow⏎Yes it does!"
```

## License

LGPLv3
