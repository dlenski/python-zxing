from __future__ import print_function
from sys import stdout
import argparse
import csv

from . import BarCodeReader, BarCode

def main():
    p = argparse.ArgumentParser()
    p.add_argument('-c','--csv', action='store_true')
    p.add_argument('--try-harder', action='store_true')
    p.add_argument('image', nargs='+')
    p.add_argument('-P','--classpath', help=argparse.SUPPRESS)
    p.add_argument('-J','--java', help=argparse.SUPPRESS)
    args = p.parse_args()

    bcr = BarCodeReader(args.classpath, args.java)

    if args.csv:
        wr = csv.writer(stdout)
        wr.writerow(('Filename','Format','Type','Raw','Parsed'))

    for fn in args.image:
        bc = bcr.decode(fn, try_harder=args.try_harder)
        if args.csv:
            wr.writerow((fn, bc.format, bc.type, bc.raw, bc.parsed) if bc else (fn, 'ERROR', None, None, None))
        else:
            print("%s\n%s" % (fn, '='*len(fn)))
            if bc is None:
                print("  ERROR: Failed to decode barcode.")
            else:
                print("  Decoded %s barcode in %s format." % (bc.type, bc.format))
                print("  Raw text:    %r" % bc.raw)
                print("  Parsed text: %r\n" % bc.parsed)
