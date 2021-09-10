import argparse
import csv
from sys import stdout

from . import BarCodeReader, BarCodeReaderException
from .version import __version__


def main():
    p = argparse.ArgumentParser()
    p.add_argument('-c', '--csv', action='store_true')
    p.add_argument('--try-harder', action='store_true')
    p.add_argument('image', nargs='+')
    p.add_argument('-P', '--classpath', help=argparse.SUPPRESS)
    p.add_argument('-J', '--java', help=argparse.SUPPRESS)
    p.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__)
    args = p.parse_args()

    bcr = BarCodeReader(args.classpath, args.java)

    if args.csv:
        wr = csv.writer(stdout)
        wr.writerow(('Filename', 'Format', 'Type', 'Raw', 'Parsed'))

    for fn in args.image:
        try:
            bc = bcr.decode(fn, try_harder=args.try_harder)
        except BarCodeReaderException as e:
            p.error(e.message + (('\n\t' + e.filename) if e.filename else ''))
        if args.csv:
            wr.writerow((fn, bc.format, bc.type, bc.raw, bc.parsed) if bc else (fn, 'ERROR', None, None, None))
        else:
            print("%s\n%s" % (fn, '=' * len(fn)))
            if bc is None:
                print("  ERROR: Failed to decode barcode.")
            else:
                print("  Decoded %s barcode in %s format." % (bc.type, bc.format))
                print("  Raw text:    %r" % bc.raw)
                print("  Parsed text: %r\n" % bc.parsed)
