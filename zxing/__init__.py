########################################################################
#
#  zxing.py -- a quick and dirty wrapper for zxing for python
#
#  this allows you to send images and get back data from the ZXing
#  library:  http://code.google.com/p/zxing/
#

import glob
import os
import pathlib
import re
import subprocess as sp
import sys
import urllib.parse
import zipfile
from abc import abstractmethod, ABC
from base64 import b64decode
from enum import Enum
from functools import update_wrapper
from io import BytesIO, IOBase
from itertools import chain


try:
    from PIL.Image import Image
    from tempfile import NamedTemporaryFile
    have_pil = True
except ImportError:
    have_pil = None

from .version import __version__  # noqa: F401


def file_uri_to_path(s):
    uri = urllib.parse.urlparse(s)
    if (uri.scheme, uri.netloc, uri.query, uri.fragment) != ('file', '', '', ''):
        raise ValueError(uri)
    return urllib.parse.unquote_plus(uri.path)


def data_uri_to_fobj(s):
    r = urllib.parse.urlparse(s)
    if r.scheme == 'data' and not r.netloc:
        mime, *rest = r.path.split(',', 1)
        if rest:
            if mime.endswith(';base64') and rest:
                mime = mime[:-7]
                data = b64decode(rest[0])
            else:
                data = urllib.parse.unquote_to_bytes(rest[0])
            ff = BytesIO(data)
            ff.name = f'data_uri_{len(data)}_bytes.{mime.split("/")[-1]}'
            return ff
    raise ValueError("Cannot handle URIs other than data:MIMETYPE[;base64],DATA")


class BarCodeReaderException(Exception):
    def __init__(self, message, filename=None):
        self.message, self.filename = message, filename
        super().__init__(message, filename)


class _BarCodeReader(ABC):
    @abstractmethod
    def decode(self, filenames, possible_formats=None):
        pass

    def decode(self, filenames, possible_formats=None, **kwargs):
        possible_formats = (possible_formats,) if isinstance(possible_formats, str) else possible_formats

        if isinstance(filenames, (str, IOBase, Image) if have_pil else (str, IOBase)):
            one_file = True
            filenames = filenames,
        else:
            one_file = False

        fns = []
        temp_files = []
        try:
            for fn_or_im in filenames:
                if have_pil and isinstance(fn_or_im, Image):
                    tf = NamedTemporaryFile(prefix='PIL_image_', suffix='.png')
                    temp_files.append(tf)
                    fn_or_im.save(tf, compresslevel=0)
                    tf.flush()
                    fn = tf.name
                elif isinstance(fn_or_im, IOBase):
                    tf = NamedTemporaryFile(prefix='temp_', suffix=os.path.splitext(getattr(fn_or_im, 'name', ''))[1])
                    temp_files.append(tf)
                    tf.write(fn_or_im.read())
                    tf.flush()
                    fn = tf.name
                else:
                    fn = fn_or_im
                fns.append(fn)

            results = self._decode(fns, possible_formats=possible_formats, **kwargs)
        finally:
            for tf in temp_files:
                tf.close()

        if one_file:
            return results[0]
        else:
            return results

    @abstractmethod
    def _decode(self, filenames, possible_formats=None):
        pass

class RxingBarCodeReader(_BarCodeReader):
    def __init__(self, rxing_cli=None):
        self.rxing_cli = rxing_cli or 'rxing-cli'
        output = sp.check_output([self.rxing_cli, '--version'], stderr=sp.STDOUT, universal_newlines=True)
        self.rxing_version = output.split()[-1].strip()
        self.rxing_version_info = tuple(int(n) for n in self.rxing_version.split('.'))

    def _decode(self, filenames, try_harder=False, possible_formats=None, pure_barcode=False):
        options = []
        if try_harder:
            options.append('--try-harder')
        if pure_barcode:
            options += ['--pure-barcode', 'true']
        if possible_formats:
            for pf in possible_formats:
                options += ['-b', pf]

        try:
            return [BarCode.parse_rxing(
                sp.check_output([self.rxing_cli, fn, 'decode', '--detailed-results'] + options, stderr=sp.STDOUT, text=True), fn)
                for fn in filenames]
        except OSError as e:
            raise BarCodeReaderException("Could not execute specified rxing-cli binary", self.rxing_cli) from e

class ZxingBarCodeReader(_BarCodeReader):
    cls = "com.google.zxing.client.j2se.CommandLineRunner"
    classpath_sep = ';' if os.name == 'nt' else ':'  # https://stackoverflow.com/a/60211688

    def __init__(self, classpath=None, java=None):
        self.java = java or 'java'
        self.zxing_version = self.zxing_version_info = None
        if classpath:
            self.classpath = classpath if isinstance(classpath, str) else self.classpath_sep.join(classpath)
        elif "ZXING_CLASSPATH" in os.environ:
            self.classpath = os.environ.get("ZXING_CLASSPATH", "")
        else:
            self.classpath = os.path.join(os.path.dirname(__file__), 'java', '*')

        for fn in chain.from_iterable(glob.glob(cp) for cp in self.classpath.split(self.classpath_sep)):
            if os.path.basename(fn) == 'core.jar':
                self.core_jar = fn
                with zipfile.ZipFile(self.core_jar) as c:
                    for line in c.open('META-INF/MANIFEST.MF'):
                        if line.startswith(b'Bundle-Version: '):
                            self.zxing_version = line.split(b' ', 1)[1].strip().decode()
                            self.zxing_version_info = tuple(int(n) for n in self.zxing_version.split('.'))
                            break
                return
        raise BarCodeReaderException("Java JARs not found in classpath (%s)" % self.classpath, self.classpath)

    def _decode(self, filenames, try_harder=False, possible_formats=None, pure_barcode=False, products_only=False):
        file_uris = [pathlib.Path(fn).absolute().as_uri() for fn in filenames]
        cmd = [self.java, '-Djava.awt.headless=true', '-cp', self.classpath, self.cls] + file_uris
        if self.zxing_version_info and self.zxing_version_info >= (3, 5, 3):
            # The --raw option was added in 3.5.0, but broken for certain barcode types (PDF_417 and maybe others) until 3.5.3
            # See https://github.com/zxing/zxing/issues/1682 and https://github.com/zxing/zxing/issues/1683
            cmd.append('--raw')
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
        except OSError as e:
            raise BarCodeReaderException("Could not execute specified Java binary", self.java) from e
        else:
            stdout, stderr = p.communicate()

        if stdout.startswith((b'Error: Could not find or load main class com.google.zxing.client.j2se.CommandLineRunner',
                              b'Exception in thread "main" java.lang.NoClassDefFoundError:')):
            raise BarCodeReaderException("Java JARs not found in classpath (%s)" % self.classpath, self.classpath)
        elif stdout.startswith((b'''Exception in thread "main" javax.imageio.IIOException: Can't get input stream from URL!''',
                                b'''Exception in thread "main" java.util.concurrent.ExecutionException: javax.imageio.IIOException: Can't get input stream from URL!''')):  # noqa: E501
            # Find the line that looks like: "Caused by: java.io.FileNotFoundException: $FILENAME ({No such file or directory,Permission denied,*)"
            fn, err = next((map(bytes.decode, l[42:].rsplit(b' (', 1)) for l in stdout.splitlines()
                            if l.startswith(b"Caused by: java.io.FileNotFoundException: ")), ('', ''))
            if err == 'No such file or directory)':
                err = FileNotFoundError(fn)
            elif err == 'Permission denied)':
                err = PermissionError(fn)
            else:
                err = OSError(err[:-1])
            raise BarCodeReaderException("Java library could not read image", fn) from err
        elif stdout.startswith(b'''Exception in thread "main" java.io.IOException: Could not load '''):
            # First line ends with file:// URI
            fn = file_uri_to_path(stdout.splitlines()[0][63:].decode())
            raise BarCodeReaderException("Java library could not read image (is it in a supported format?)", fn)
        elif stdout.startswith(b'''Exception '''):
            raise BarCodeReaderException("Unknown Java exception", self.java) from sp.CalledProcessError(0, cmd, stdout)
        elif stdout.startswith(b'''The operation couldn't be completed. Unable to locate a Java Runtime.'''):
            raise BarCodeReaderException("Unable to locate Java runtime (check JAVA_HOME variable and other configuration)", self.java) from sp.CalledProcessError(p.returncode, cmd, stdout)
        elif p.returncode:
            raise BarCodeReaderException("Unexpected Java subprocess return code", self.java) from sp.CalledProcessError(p.returncode, cmd, stdout)

        file_results = []
        for line in stdout.splitlines(True):
            if line.startswith((b'file://', b'Exception')):
                file_results.append(line)
            else:
                file_results[-1] += line
        codes = [BarCode.parse_zxing(result) for result in file_results]

        # zxing (insanely) randomly reorders the output blocks, so we have to put them back in the
        # expected order, based on their URIs
        d = {c.uri: c for c in codes}
        return [d[f] for f in file_uris]


update_wrapper(RxingBarCodeReader.decode, RxingBarCodeReader._decode)
update_wrapper(ZxingBarCodeReader.decode, ZxingBarCodeReader._decode)


class CLROutputBlock(Enum):
    UNKNOWN = 0
    RAW = 1
    PARSED = 2
    POINTS = 3
    RAW_BITS = 4


class BarCode(object):
    RUST_UNICODE_ESCAPE = re.compile(r'\\u\{([a-f0-9]+)\}')
    POINTS = re.compile(r'PointT\s*\{\s*x\:\s*([-\d.]+),\s*y\:\s*([-\d.]+)\s*\}')

    RXING_FORMAT_TO_ZXING = {'QRCODE': 'QR_CODE'}

    @classmethod
    def parse_rxing(cls, rxing_output, fn):
        errp = f"Error while attempting to locate barcode in '{fn}':"
        if rxing_output.startswith(errp):
            err = rxing_output.removeprefix(errp).strip()
            if err == "NotFoundException":
                return BarCode(uri=pathlib.Path(path).absolute().as_uri())
            else:
                raise BarCodeReaderException(err, fn)
        format = None
        raw = ''
        points = []
        for l in rxing_output.splitlines():
            if l.startswith('[Barcode Format] '):
                # rxing's output names of the barcode formats can be mechanically translated to zxing's names, except for QRCODE:
                # https://github.com/rxing-core/rxing/blob/87ff09bb8e0e4175d2681352aaf3b5e08f32c928/src/barcode_format.rs#L113
                format = l.removeprefix('[Barcode Format] ').replace(' ', '_').upper()
                format = cls.RXING_FORMAT_TO_ZXING.get(format, format)
            elif l.startswith('[Data] '):
                # This is a Rust repr of a string, include backslash escapes. Unlike Python, its
                # unicode character escapes are not always 4 digits, and have braces (e.g. '\u{123}')
                # FIXME: This incorrectly handles the case of an escaped '\\' followed by 'u{...}'
                raw = l.removeprefix('[Data] ')
                raw = cls.RUST_UNICODE_ESCAPE.sub(lambda m: r'\u' + m.group(1).rjust(4, '0'), raw).encode().decode('unicode_escape')
            elif l.startswith('[Points] '):
                points = [((float(m[0]), float(m[1]))) for m in cls.POINTS.findall(l.removeprefix('[Points] '))]

        return cls(pathlib.Path(path).absolute().as_uri(),
                   raw=raw, parsed=parsed, points=points, type='TEXT', format=format)


    @classmethod
    def parse_zxing(cls, zxing_output):
        block = CLROutputBlock.UNKNOWN
        uri = format = type = None
        raw = parsed = raw_bits = b''
        points = []

        for l in zxing_output.splitlines(True):
            if block == CLROutputBlock.UNKNOWN:
                if l.strip().endswith(b': No barcode found'):
                    return cls(l.rsplit(b':', 1)[0].decode(), None, None, None, None, None)
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
                if l.startswith(b"Raw bits:"):
                    block = CLROutputBlock.RAW_BITS
                elif re.match(rb"Found\s+\d+\s+result\s+points?", l):
                    block = CLROutputBlock.POINTS
                else:
                    parsed += l
            elif block == CLROutputBlock.RAW_BITS:
                if re.match(rb"Found\s+\d+\s+result\s+points?", l):
                    block = CLROutputBlock.POINTS
                else:
                    raw_bits += l
            elif block == CLROutputBlock.POINTS:
                m = re.match(rb"\s*Point\s*\d+:\s*\(([-\d.]+),([-\d.]+)\)", l)
                if m:
                    points.append((float(m.group(1)), float(m.group(2))))

        parsed = parsed[:-1].decode()
        raw = raw[:-1].decode()
        raw_bits = bytes.fromhex(raw_bits[:-1].decode())
        return cls(uri, format, type, raw, parsed, raw_bits, points)

    def __bool__(self):
        return bool(self.raw)

    def __init__(self, uri, format=None, type=None, raw=None, parsed=None, raw_bits=None, points=None):
        self.raw = raw
        self.parsed = parsed
        self.raw_bits = raw_bits
        self.uri = uri
        self.format = format
        self.type = type
        self.points = points

    @property
    def path(self):
        try:
            return file_uri_to_path(self.uri)
        except ValueError:
            pass

    def __repr__(self):
        return '{}(raw={!r}, parsed={!r}, raw_bits={!r}, {}={!r}, format={!r}, type={!r}, points={!r})'.format(
            self.__class__.__name__, self.raw, self.parsed, self.raw_bits.hex() if self.raw_bits else None,
            'path' if self.path else 'uri', self.path or self.uri,
            self.format, self.type, self.points)
