import logging
import os
from itertools import product
from tempfile import mkdtemp

from PIL import Image

from nose2.tools.decorators import with_setup
from nose2.tools.such import helper
from nose2.tools import params
import unittest

import zxing

test_barcode_dir = os.path.join(os.path.dirname(__file__), 'barcodes')

test_barcodes = [
    ('QR_CODE-easy.png', 'QR_CODE', 'This should be QR_CODE'),
    ('CODE_128-easy.jpg', 'CODE_128', 'This should be CODE_128'),
    ('PDF_417-easy.bmp', 'PDF_417', 'This should be PDF_417'),
    ('AZTEC-easy.jpg', 'AZTEC', 'This should be AZTEC'),
    ('AZTEC-utf8.png', 'AZTEC', 'L’état, c’est moi'),
    ('QR CODE (¡filenáme törture test! 😉).png', 'QR_CODE', 'This should be QR_CODE'),
    ('QR_CODE-png-but-wrong-extension.bmp', 'QR_CODE', 'This should be QR_CODE'),
    ('QR_CODE-fun-with-whitespace.png', 'QR_CODE', '\n\r\t\r\r\r\n '),
    ('QR_CODE-screen_scraping_torture_test.png', 'QR_CODE', '\n\\n¡Atención ☹! UTF-8 characters,\n\r embedded newlines,\r &&am&p;& trailing whitespace\t \r '),
]

test_non_barcodes = [
    ('empty.png', None, None),
]

test_valid_images = test_barcodes + test_non_barcodes

test_reader = None


def setup_reader():
    global test_reader
    if test_reader is None:
        test_reader = zxing.BarCodeReader()


@with_setup(setup_reader)
def test_version():
    global test_reader
    assert test_reader.zxing_version is not None
    assert '.'.join(map(str, test_reader.zxing_version_info)) == test_reader.zxing_version


@with_setup(setup_reader)
def _check_decoding(filename, expected_format, expected_raw, extra={}, as_Image=False):
    global test_reader
    if (3, 5, 0) <= test_reader.zxing_version_info < (3, 5, 3) and expected_format == 'PDF_417':
        # See https://github.com/zxing/zxing/issues/1682 and https://github.com/zxing/zxing/issues/1683
        raise unittest.SkipTest("ZXing v{} CommandLineRunner is broken for combination of {} barcode format and --raw option".format(
            test_reader.zxing_version, expected_format))
    path = os.path.join(test_barcode_dir, filename)
    what = Image.open(path) if as_Image else path
    logging.debug('Trying to parse {}, expecting {!r}.'.format(path, expected_raw))
    dec = test_reader.decode(what, pure_barcode=True, **extra)
    if expected_raw is None:
        assert dec.raw is None, (
            'Expected failure, but got result in {} format'.format(dec.format))
    else:
        assert dec.raw == expected_raw, (
            'Expected {!r} but got {!r}'.format(expected_raw, dec.raw))
        assert dec.format == expected_format, (
            'Expected {!r} but got {!r}'.format(expected_format, dec.format))
        if as_Image:
            assert not os.path.exists(dec.path), (
                'Expected temporary file {!r} to be deleted, but it still exists'.format(dec.path))


def test_decoding():
    global test_reader
    yield from ((_check_decoding, filename, expected_format, expected_raw) for filename, expected_format, expected_raw in test_valid_images)


def test_decoding_from_Image():
    global test_reader
    yield from ((_check_decoding, filename, expected_format, expected_raw, {}, True) for filename, expected_format, expected_raw in test_valid_images)


def test_possible_formats():
    yield from ((_check_decoding, filename, expected_format, expected_raw, dict(possible_formats=('CODE_93', expected_format, 'DATA_MATRIX')))
                for filename, expected_format, expected_raw in test_barcodes)


@with_setup(setup_reader)
def test_decoding_multiple():
    global test_reader
    # See https://github.com/zxing/zxing/issues/1682 and https://github.com/zxing/zxing/issues/1683
    _tvi = [x for x in test_valid_images if not ((3, 5, 0) <= test_reader.zxing_version_info < (3, 5, 3) and x[1] == 'PDF_417')]
    filenames = [os.path.join(test_barcode_dir, filename) for filename, expected_format, expected_raw in _tvi]
    for dec, (filename, expected_format, expected_raw) in zip(test_reader.decode(filenames, pure_barcode=True), _tvi):
        assert dec.raw == expected_raw, (
            '{}: Expected {!r} but got {!r}'.format(filename, expected_raw, dec.parsed))
        assert dec.format == expected_format, (
            '{}: Expected {!r} but got {!r}'.format(filename, expected_format, dec.format))


@params(*product((False, True), repeat=2))
def test_parsing(with_raw_bits, with_netloc):
    stdout = ("""
file://""") + ("NETWORK_SHARE" if with_netloc else "") + ("""/tmp/default%20file.png (format: FAKE_DATA, type: TEXT):
Raw result:
Élan|\tthe barcode is taking off
Parsed result:
Élan
\tthe barcode is taking off""") + ("""
Raw bits:
  f00f00cafe""" if with_raw_bits else "") + ("""
Found 4 result points:
  Point 0: (24.0,18.0)
  Point 1: (21.0,196.0)
  Point 2: (201.0,198.0)
  Point 3: (205.23952,21.0)
""")
    dec = zxing.BarCode.parse(stdout.encode())
    assert dec.uri == 'file://' + ("NETWORK_SHARE" if with_netloc else "") + '/tmp/default%20file.png'
    assert dec.path == (None if with_netloc else '/tmp/default file.png')
    assert dec.format == 'FAKE_DATA'
    assert dec.type == 'TEXT'
    assert dec.raw == 'Élan|\tthe barcode is taking off'
    assert dec.raw_bits == (bytes.fromhex('f00f00cafe') if with_raw_bits else b'')
    assert dec.parsed == 'Élan\n\tthe barcode is taking off'
    assert dec.points == [(24.0, 18.0), (21.0, 196.0), (201.0, 198.0), (205.23952, 21.0)]
    r = repr(dec)
    assert r.startswith('BarCode(') and r.endswith(')')


def test_parsing_not_found():
    stdout = "file:///tmp/some%5ffile%5fwithout%5fbarcode.png: No barcode found\n"
    dec = zxing.BarCode.parse(stdout.encode())
    assert dec.uri == 'file:///tmp/some%5ffile%5fwithout%5fbarcode.png'
    assert dec.path == '/tmp/some_file_without_barcode.png'
    assert dec.format is None
    assert dec.type is None
    assert dec.raw is None
    assert dec.raw_bits is None
    assert dec.parsed is None
    assert dec.points is None
    assert bool(dec) is False
    r = repr(dec)
    assert r.startswith('BarCode(') and r.endswith(')')


def test_wrong_formats():
    all_test_formats = {fmt for fn, fmt, raw in test_barcodes}
    yield from ((_check_decoding, filename, expected_format, None, dict(possible_formats=all_test_formats - {expected_format}))
                for filename, expected_format, expected_raw in test_barcodes)


def test_bad_java():
    test_reader = zxing.BarCodeReader(java=os.devnull)
    with helper.assertRaises(zxing.BarCodeReaderException):
        test_reader.decode(test_barcodes[0][0])


def test_bad_classpath():
    with helper.assertRaises(zxing.BarCodeReaderException):
        test_reader = zxing.BarCodeReader(classpath=mkdtemp())


def test_wrong_JAVA_HOME():
    saved_JAVA_HOME = os.environ.get('JAVA_HOME')
    try:
        os.environ['JAVA_HOME'] = '/non-existent/path/to/java/stuff'
        test_reader = zxing.BarCodeReader()
        with helper.assertRaises(zxing.BarCodeReaderException):
            test_reader.decode(test_barcodes[0][0])
    finally:
        if saved_JAVA_HOME is not None:
            os.environ['JAVA_HOME'] = saved_JAVA_HOME


@with_setup(setup_reader)
def test_nonexistent_file_error():
    global test_reader
    with helper.assertRaises(zxing.BarCodeReaderException):
        test_reader.decode(os.path.join(test_barcode_dir, 'nonexistent.png'))


@with_setup(setup_reader)
def test_bad_file_format_error():
    global test_reader
    with helper.assertRaises(zxing.BarCodeReaderException):
        test_reader.decode(os.path.join(test_barcode_dir, 'bad_format.png'))


def test_data_uris():
    def _check_data_uri(uri, contents, suffix):
        fobj = zxing.data_uri_to_fobj(uri)
        assert fobj.getvalue() == contents
        assert fobj.name.endswith(suffix)

    yield from ((_check_data_uri, uri, contents, suffix) for (uri, contents, suffix) in (
        ('data:image/png,ABCD', b'ABCD', '.png'),
        ('data:image/jpeg;base64,3q2+7w==', bytes.fromhex('deadbeef'), '.jpeg'),
        ('data:application/binary,%f1%f2%f3', bytes.fromhex('f1f2f3'), '.binary'),
    ))
