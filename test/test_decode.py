import logging
import zxing
import os

test_barcode_dir = os.path.join(os.path.dirname(__file__), 'barcodes')

test_barcodes = [
    ( 'QR_CODE-easy.png', 'This should be QR_CODE' ),
    ( 'CODE_128-easy.jpg', 'This should be CODE_128' ),
    ( 'PDF_417-easy.bmp', 'This should be PDF_417' ),
    ( 'AZTEC-easy.jpg', 'This should be AZTEC' ),
    ( 'CODE_128-fun-with-whitespace.png', '\n\r\t\r\r\r\n ' ),
    ( 'QR_CODE-screen_scraping_torture_test.png',
      '\n\\n¡Atención ☹! UTF-8 characters,\n embedded newline, &amp; trailing whitespace\t ' ),
]

def test_decoding():
    reader = zxing.BarCodeReader()
    for filename, expected in test_barcodes:
        path = os.path.join(test_barcode_dir, filename)
        logging.debug('Trying to parse {}, expecting {!r}.'.format(path, expected))
        dec = reader.decode(path)
        if dec.parsed != expected:
            raise AssertionError('Expected {!r} but got {!r}'.format(expected, dec.parsed))

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
