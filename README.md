# python-zxing

This is a wrapper for the [ZXing barcode library](https://github.com/zxing/zxing). It's a "slightly less quick-and-dirty" fork of [oostendo/python-zxing](https://github.com/oostendo/python-zxing).

This is a hack subprocess control library that gives you a reasonable Python 3 interface to the ZXing command line.  ZXing will recognize and decode 1D and 2D barcodes in images, and return position information and decoded values.  This will let you read barcodes from any images in Python.

If you need to threshold or filter your image prior to sending to ZXing, I recommend using functions from [SimpleCV](http://simplecv.org).

## Installation

Use the `download-jars.sh` script to download JARs for ZXing core and javase, and jcommander ([required since ZXing 3.2.1](https://github.com/zxing/zxing/issues/518)),
before using `pip3` to install:

```sh
$ cd python-zxing
$ ./download-jars.sh
Downloading zxing-javase, zxing-core, and jcommander JARs into ./zxing/java ...
$ pip3 install .
...
```

## Usage

The library consists of two classes, `BarCodeReader` and `BarCode`. `BarCode` parses
the output from ZXing's `CommandLineRunner` into a `BarCode` object:

```python
>>> import zxing
>>> b = zxing.BarCode.parse("""
file:default.png (format: FAKE_DATA, type: TEXT):
Raw result:
foo-bar|the bar of foo
Parsed result:
foo-bar
the bar of foo
Found 4 result points:
  Point 0: (24.0,18.0)
  Point 1: (21.0,196.0)
  Point 2: (201.0,198.0)
  Point 3: (205.23952,21.0)
""")
>>> print(b.format)
FAKE_DATA
>>> print(b.type)
TEXT
>>> print(b.raw)
foo-bar|the bar of foo
>>> print(b.parsed)
foo-bar
the bar of foo
>>> print(b.points)
[(24.0, 18.0) ... ]
```

Initializing and using the barcode reader:

```python
reader = zxing.BarCodeReader()
barcode = reader.decode("/tmp/image.jpg", try_harder=True, possible_formats=['QR_CODE'])
(barcode1, barcode2) = reader.decode(["/tmp/1.png", "/tmp/2.png"])
```

`decode()` takes an image path (or list of paths) and has optional parameters `try_harder` and `possible_formats`.  If no barcode is found, it returns `None` objects.
