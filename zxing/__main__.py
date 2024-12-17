import argparse
import csv
from sys import stdout, stdin

from . import ZxingBarCodeReader, RxingBarCodeReader, BarCodeReaderException, data_uri_to_fobj
from .version import __version__


class ErrorDeferredArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        self._errors = []
        super().__init__(*args, **kwargs)

    def error(self, message):
        self._errors.append(message)

    def handle_errors(self):
        for e in self._errors:
            super().error(e)


def main():
    p = ErrorDeferredArgumentParser()
    p.add_argument('-c', '--csv', action='store_true')
    p.add_argument('--try-harder', action='store_true')
    p.add_argument('--pure-barcode', action='store_true')
    p.add_argument('image', nargs='+', help='File path or data: URI of an image containing a barcode')
    p.add_argument('-Z', '--zxing', action='store_true', help='Use ZXing instead of RXing')
    p.add_argument('-P', '--classpath', help=argparse.SUPPRESS)
    p.add_argument('-J', '--java', help=argparse.SUPPRESS)
    p.add_argument('-V', '--version', action='store_true')
    args = p.parse_args()
    if p._errors and not args.version:
        p.handle_errors()

    bcr = ZxingBarCodeReader(args.classpath, args.java) if args.zxing else RxingBarCodeReader()
    if isinstance(bcr, RxingBarCodeReader):
        libver = 'Rust RXing library version v%s' % bcr.rxing_version
    else:
        libver = 'Java ZXing library version v%s' % bcr.zxing_version

    if args.version:
        p.exit(0, '%s v%s\nusing %s\n' % (p.prog, __version__, libver))

    if args.csv:
        wr = csv.writer(stdout)
        wr.writerow(('Filename', 'Format', 'Type', 'Raw', 'Parsed'))

    for fn in args.image:
        if fn == '-':
            ff = stdin.buffer
            fn = ff.name
        elif ':' in fn:
            try:
                ff = data_uri_to_fobj(fn)
                fn = ff.name
            except ValueError as exc:
                p.error(exc.args[0])
        else:
            ff = fn

        bc = None
        try:
            bc = bcr.decode(ff, try_harder=args.try_harder, pure_barcode=args.pure_barcode)
        except BarCodeReaderException as e:
            p.error(e.message + ((': ' + e.filename) if e.filename else '') + (('\n\tCaused by: ' + repr(e.__cause__) if e.__cause__ else '')))

        if args.csv:
            wr.writerow((fn, bc.format, bc.type, bc.raw, bc.parsed) if bc else (fn, 'ERROR', None, None, None))
        else:
            print("%s\n%s" % (fn, '=' * len(fn)))
            if not bc:
                print("  ERROR: Failed to decode barcode (using %s)." % libver)
            else:
                print("  Decoded %s barcode in %s format." % (bc.type, bc.format))
                print("  Raw text:    %r" % bc.raw)
                print("  Parsed text: %r" % bc.parsed)
                if bc.raw_bits:
                    print("  Raw bits:    %r\n" % bc.raw_bits.hex())


if __name__=='__main__':
    main()
