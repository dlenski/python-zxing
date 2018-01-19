# python-zxing

[![PyPI](https://img.shields.io/pypi/v/zxing.svg)](https://pypi.python.org/pypi/zxing)
[![Build Status](https://api.travis-ci.org/dlenski/python-zxing.png)](https://travis-ci.org/dlenski/python-zxing)

This is a wrapper for the [ZXing barcode library](https://github.com/zxing/zxing). (It's a "slightly less quick-and-dirty" fork of [oostendo/python-zxing](https://github.com/oostendo/python-zxing).)
It will allow you to read and decode barcode images from Python.

## Dependencies and installation

You'll neeed to have a recent `java` binary somewhere in your path. (Tested with OpenJDK.)

Use the Python 3 version of pip (usually invoked via `pip3`) to install: `pip3 install zxing`

## Usage

The `BarCodeReader` class is used to decode images:

```python
>>> import zxing
>>> reader = zxing.BarCodeReader()
>>> barcode = reader.decode("test/barcodes/QR_CODE-easy.png")
```

The attributes of the decoded `BarCode` object are `raw`, `parsed`, `format`, `type`, and `points`. The list of formats which ZXing can decode is
[here](https://zxing.github.io/zxing/apidocs/com/google/zxing/BarcodeFormat.html).

The `decode()` method accepts an image path and takes optional parameters `try_harder` (boolean) and `possible_formats` (list of formats to consider).
If no barcode is found, it returns `None`.

## Command-line interface

The command-line interface can decode images into barcodes and output in either a human-readable or CSV format:

```
usage: zxing [-h] [-c] [--try-harder] image [image ...]
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
