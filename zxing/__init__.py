########################################################################
#
#  zxing.py -- a quick and dirty wrapper for zxing for python
#
#  this allows you to send images and get back data from the ZXing
#  library:  http://code.google.com/p/zxing/
#

import os
import pathlib
import re
import subprocess as sp
import zipfile
from enum import Enum

from .version import __version__  # noqa: F401


class BarCodeReaderException(Exception):
    def __init__(self, message, filename=None, underlying=None):
        self.message, self.filename, self.underlying = message, filename, underlying
        super().__init__(message, filename, underlying)


class BarCodeReader(object):
    cls = "com.google.zxing.client.j2se.CommandLineRunner"

    def __init__(self, classpath=None, java=None):
        self.java = java or 'java'
        self.zxing_version = self.zxing_version_info = None
        if classpath:
            self.classpath = classpath if isinstance(classpath, str) else ':'.join(classpath)
        elif "ZXING_CLASSPATH" in os.environ:
            self.classpath = os.environ.get("ZXING_CLASSPATH", "")
        else:
            self.classpath = os.path.join(os.path.dirname(__file__), 'java', '*')

        with zipfile.ZipFile(os.path.join(os.path.dirname(__file__), 'java', 'core.jar')) as c:
            for line in c.open('META-INF/MANIFEST.MF'):
                if line.startswith(b'Bundle-Version: '):
                    self.zxing_version = line.split(b' ', 1)[1].strip().decode()
                    self.zxing_version_info = tuple(int(n) for n in self.zxing_version.split('.'))
                    break

    def decode(self, filenames, try_harder=False, possible_formats=None, pure_barcode=False, products_only=False):
        possible_formats = (possible_formats,) if isinstance(possible_formats, str) else possible_formats

        if isinstance(filenames, str):
            one_file = True
            filenames = filenames,
        else:
            one_file = False
        file_uris = [pathlib.Path(f).absolute().as_uri() for f in filenames]

        cmd = [self.java, '-cp', self.classpath, self.cls] + file_uris
        if try_harder:
            cmd.append('--try_harder')
        if pure_barcode:
            cmd.append('--pure_barcode')
        if products_only:
            cmd.append('--products_only')
        if possible_formats:
            for pf in possible_formats:
                cmd += ['--possible_formats', pf]

        try:
            p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, universal_newlines=False)
        except FileNotFoundError as e:
            raise BarCodeReaderException("Java binary specified (%s) does not exist" % self.java, self.java, e)
        except PermissionError as e:
            raise BarCodeReaderException("Java binary specified (%s) is not executable" % self.java, self.java, e)
        stdout, stderr = p.communicate()

        if stdout.startswith((b'Error: Could not find or load main class com.google.zxing.client.j2se.CommandLineRunner',
                              b'Exception in thread "main" java.lang.NoClassDefFoundError:')):
            raise BarCodeReaderException("Java JARs not found in classpath (%s)" % self.classpath, self.classpath)
        elif stdout.startswith((b'''Exception in thread "main" javax.imageio.IIOException: Can't get input stream from URL!''',
                                b'''Exception in thread "main" java.util.concurrent.ExecutionException: javax.imageio.IIOException: Can't get input stream from URL!''')):
            raise BarCodeReaderException("Could not find image path: %s" % filenames, filenames)
        elif stdout.startswith(b'''Exception in thread "main" java.io.IOException: Could not load '''):
            raise BarCodeReaderException("Java library could not read image; is it in a supported format?", filenames)
        elif stdout.startswith(b'''Exception '''):
            raise BarCodeReaderException("Unknown Java exception: %s" % stdout)
        elif p.returncode:
            raise BarCodeReaderException("Unexpected Java subprocess return code %d" % p.returncode, self.java)

        if p.returncode:
            codes = [None for fn in filenames]
        else:
            file_results = []
            for line in stdout.splitlines(True):
                if line.startswith((b'file:///', b'Exception')):
                    file_results.append(line)
                else:
                    file_results[-1] += line
            codes = [BarCode.parse(result) for result in file_results]

        if one_file:
            return codes[0]
        else:
            # zxing (insanely) randomly reorders the output blocks, so we have to put them back in the
            # expected order, based on their URIs
            d = {c.uri: c for c in codes}
            return [d[f] for f in file_uris]


class CLROutputBlock(Enum):
    UNKNOWN = 0
    RAW = 1
    PARSED = 2
    POINTS = 3


class BarCode(object):
    @classmethod
    def parse(cls, zxing_output):
        block = CLROutputBlock.UNKNOWN
        uri = format = type = None
        raw = parsed = b''
        points = []

        for l in zxing_output.splitlines(True):
            if block == CLROutputBlock.UNKNOWN:
                if l.endswith(b': No barcode found\n'):
                    return None
                m = re.match(rb"(\S+) \(format:\s*([^,]+),\s*type:\s*([^)]+)\)", l)
                if m:
                    uri, format, type = m.group(1).decode(), m.group(2).decode(), m.group(3).decode()
                elif l.startswith(b"Raw result:"):
                    block = CLROutputBlock.RAW
            elif block == CLROutputBlock.RAW:
                if l.startswith(b"Parsed result:"):
                    block = CLROutputBlock.PARSED
                else:
                    raw += l
            elif block == CLROutputBlock.PARSED:
                if re.match(rb"Found\s+\d+\s+result\s+points?", l):
                    block = CLROutputBlock.POINTS
                else:
                    parsed += l
            elif block == CLROutputBlock.POINTS:
                m = re.match(rb"\s*Point\s*\d+:\s*\(([\d.]+),([\d.]+)\)", l)
                if m:
                    points.append((float(m.group(1)), float(m.group(2))))

        raw = raw[:-1].decode()
        parsed = parsed[:-1].decode()
        return cls(uri, format, type, raw, parsed, points)

    def __init__(self, uri, format, type, raw, parsed, points):
        self.raw = raw
        self.parsed = parsed
        self.uri = uri
        self.format = format
        self.type = type
        self.points = points

    def __repr__(self):
        return '{}(raw={!r}, parsed={!r}, uri={!r}, format={!r}, type={!r}, points={!r})'.format(
            self.__class__.__name__, self.raw, self.parsed, self.uri, self.format, self.type, self.points)
