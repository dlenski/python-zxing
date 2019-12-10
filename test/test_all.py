import logging
import zxing
from tempfile import mkdtemp
import os

from nose import with_setup
from nose.tools import raises

test_barcode_dir = os.path.join(os.path.dirname(__file__), 'barcodes')

test_barcodes = [
    ( 'QR_CODE-easy.png', 'QR_CODE', 'This should be QR_CODE', ),
    ( 'CODE_128-easy.jpg', 'CODE_128', 'This should be CODE_128', ),
    ( 'PDF_417-easy.bmp', 'PDF_417', 'This should be PDF_417', ),
    ( 'AZTEC-easy.jpg', 'AZTEC', 'This should be AZTEC' ),
    ( 'QR CODE (¡filenáme törture test! 😉).png', 'QR_CODE', 'This should be QR_CODE' ),
    ( 'QR_CODE-png-but-wrong-extension.bmp', 'QR_CODE', 'This should be QR_CODE' ),
    ( 'QR_CODE-fun-with-whitespace.png', 'QR_CODE', '\n\r\t\r\r\r\n ' ),
    ( 'QR_CODE-screen_scraping_torture_test.png', 'QR_CODE',
      '\n\\n¡Atención ☹! UTF-8 characters,\n embedded newline, &amp; trailing whitespace\t ' ),
]

test_reader = None
def setup_reader():
    global test_reader
    if test_reader is None:
        test_reader = zxing.BarCodeReader()

@with_setup(setup_reader)
def test_decoding():
    global test_reader
    for filename, expected_format, expected_raw in test_barcodes:
        path = os.path.join(test_barcode_dir, filename)
        logging.debug('Trying to parse {}, expecting {!r}.'.format(path, expected_raw))
        dec = test_reader.decode(path)
        if dec.raw != expected_raw:
            raise AssertionError('Expected {!r} but got {!r}'.format(expected_raw, dec.raw))
        if dec.format != expected_format:
            raise AssertionError('Expected {!r} but got {!r}'.format(expected_format, dec.format))


def test_parsing():
    dec = zxing.BarCode.parse("""
file:default.png (format: FAKE_DATA, type: TEXT):
Raw result:
Élan|\tthe barcode is taking off
Parsed result:
Élan
\tthe barcode is taking off
Found 4 result points:
  Point 0: (24.0,18.0)
  Point 1: (21.0,196.0)
  Point 2: (201.0,198.0)
  Point 3: (205.23952,21.0)
""".encode())
    assert dec.format == 'FAKE_DATA'
    assert dec.type == 'TEXT'
    assert dec.raw == 'Élan|\tthe barcode is taking off'
    assert dec.parsed == 'Élan\n\tthe barcode is taking off'
    assert dec.points == [(24.0,18.0),(21.0,196.0),(201.0,198.0),(205.23952,21.0)]


@with_setup(setup_reader)
def test_possible_formats():
    global test_reader
    all_test_formats = {fmt for fn,fmt,raw in test_barcodes}
    for filename, expected_format, expected_raw in test_barcodes:
        path = os.path.join(test_barcode_dir, filename)
        incomplete_formats = all_test_formats - {expected_format}
        dec = test_reader.decode(path, possible_formats=incomplete_formats)
        if dec is not None:
            raise AssertionError('Tried to decode {}-format barcode with possible_formats={!r}; expected failure, but got result in {} format'.format(
                expected_format, incomplete_formats, dec.format))


@raises(zxing.BarCodeReaderException)
def test_bad_java():
    test_reader = zxing.BarCodeReader(java=os.devnull)
    test_reader.decode(test_barcodes[0][0])


@raises(zxing.BarCodeReaderException)
def test_bad_classpath():
    test_reader = zxing.BarCodeReader(classpath=mkdtemp())
    test_reader.decode(test_barcodes[0][0])


@raises(zxing.BarCodeReaderException)
@with_setup(setup_reader)
def test_nonexistent_file_error():
    global test_reader
    test_reader.decode(os.path.join(test_barcode_dir, 'nonexistent.png'))


@raises(zxing.BarCodeReaderException)
@with_setup(setup_reader)
def test_bad_file_format_error():
    global test_reader
    test_reader.decode(os.path.join(test_barcode_dir, 'bad_format.png'))
