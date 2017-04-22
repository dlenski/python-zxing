########################################################################
#
#  zxing.py -- a quick and dirty wrapper for zxing for python
#
#  this allows you to send images and get back data from the ZXing
#  library:  http://code.google.com/p/zxing/
#

from __future__ import print_function
from enum import Enum

__version__ = '0.4'
import subprocess as sp, re, os

class BarCodeReader(object):
  cls = "com.google.zxing.client.j2se.CommandLineRunner"

  def __init__(self, classpath=None, java=None):
    self.java = java or 'java'
    if classpath:
      self.classpath = classpath if isinstance(classpath, str) else ':'.join(classpath)
    elif "ZXING_CLASSPATH" in os.environ:
      self.classpath = os.environ.get("ZXING_CLASSPATH","")
    else:
      self.classpath = os.path.join(os.path.dirname(__file__), 'java', '*')

  def decode(self, filenames, try_harder = False, possible_formats = None):
    possible_formats = (possible_formats,) if isinstance(possible_formats, str) else possible_formats

    if isinstance(filenames, str):
      one_file = True
      filenames = [ os.path.abspath(filenames) ]
    else:
      one_file = False
      filenames = [ os.path.abspath(f) for f in filenames ]

    cmd = [self.java, '-cp', self.classpath, self.cls] + filenames
    if try_harder:
      cmd.append('--try_harder')
    if possible_formats:
      for pf in possible_formats:
        cmd += ['--possible_formats', pf ]

    p = sp.Popen(cmd, stdout=sp.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate()

    if p.returncode:
      raise sp.CalledProcessError(p.returncode, p.args, stdout, stderr)
    else:
      file_results = re.split(r'\nfile:', stdout)
      codes = [ BarCode.parse(result) for result in file_results ]

    return (codes[0] if one_file else codes)

class CLROutputBlock(Enum):
  UNKNOWN = 0
  RAW = 1
  PARSED = 2
  POINTS = 3

class BarCode(object):
  @classmethod
  def parse(cls, zxing_output):
    block = CLROutputBlock.UNKNOWN
    format = type = None
    raw = parsed = ''
    points = []

    for l in zxing_output.splitlines(True):
      if block==CLROutputBlock.UNKNOWN:
        if l.endswith(': No barcode found\n'):
          return None
        m = re.search(r"format:\s*([^,]+),\s*type:\s*([^)]+)", l)
        if m:
          format, type = m.groups()
        elif l.startswith("Raw result:"):
          block = CLROutputBlock.RAW
      elif block==CLROutputBlock.RAW:
        if l.startswith("Parsed result:"):
          block = CLROutputBlock.PARSED
        else:
          raw += l
      elif block==CLROutputBlock.PARSED:
        if re.match(r"Found\s+\d+\s+result\s+points?", l):
          block = CLROutputBlock.POINTS
        else:
          parsed += l
      elif block==CLROutputBlock.POINTS:
        m = re.match(r"\s*Point\s*\d+:\s*\(([\d.]+),([\d.]+)\)", l)
        if m:
          points.append((float(m.group(1)), float(m.group(2))))

    return cls(format, type, raw[:-1], parsed[:-1], points)

  def __init__(self, format, type, raw, parsed, points):
    self.raw = raw
    self.parsed = parsed
    self.format = format
    self.type = type
    self.points = points

  def __repr__(self):
    return '{}({!r}, {!r}, {!r}, {!r}, {!r})'.format(self.__class__.__name__, self.raw, self.parsed, self.format, self.type, self.points)
