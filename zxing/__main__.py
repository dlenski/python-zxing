from __future__ import print_function
import argparse

from . import BarCodeReader, BarCode

p = argparse.ArgumentParser()
p.add_argument('-P','--classpath')
p.add_argument('--try-harder', action='store_true')
p.add_argument('image', nargs='+')
args = p.parse_args()

bcr = BarCodeReader(args.classpath)

for fn in args.image:
    print("%s\n%s" % (fn, '='*len(fn)))
    bc = bcr.decode(fn, try_harder=args.try_harder)
    if bc is None:
        print("  ERROR: Failed to decode barcode.")
    else:
        print("  Decoded %s barcode in %s format." % (bc.type, bc.format))
        print("  Raw text:    %r" % bc.raw)
        print("  Parsed text: %r\n" % bc.parsed)
