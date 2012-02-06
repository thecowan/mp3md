# TODO:
#  - group reports by error-per-dir, or error-global
#  - command-line flags (recursive)
#  - supply checks by file, command line, etc
#  - check track number: none missing, all unique
from mutagen.id3 import *

import sys, os, fnmatch, re

class Doctor(object):
  def __init__(self, tests):
    self.test_runner = TestRunner(tests)

  def checkup(self, directory, recursive=False):
    if recursive:
      for dirpath, _, _ in os.walk(directory):
        self.test_runner.test_dir(dirpath)
    else:
      self.test_runner.test_dir(dirpath)

class Message(object):
  def __init__(self, severity, text):
    self.severity = severity
    self.text = text

  def __str__(self):
    return "%s: %s" % (self.severity, self.text)
    
class Errors(object):
  def __init__(self):
    self.errors = dict()
  
  def record(self, path, severity, error):
    self.errors.setdefault(path, []).append(Message(severity, error))

  def has_errors(self):
    return len(self.errors) > 0

  def error_files(self):
    return self.errors.keys()

  def items(self):
    return self.errors.items()

  def merge(self, other):
    for (path, errors) in other.items():
      for error in errors:
        self.errors.setdefault(path, []).append(error)

  def demote_all(self, severity):
    for (_, errors) in self.errors.items():
      for error in errors:
        error.severity = severity
          
class TestRunner(object):
  def __init__(self, tests):
    self.tests = tests

  def test_dir(self, directory):
    valid_tags = []
    files = fnmatch.filter(os.listdir(directory), '*.mp3')
    errors = Errors()
    for file in files:
      path = os.path.join(directory, file)
      try:
        id3 = ID3(path)
        valid_tags.append((path, id3))
      except:
        errors.record(path, "ERROR", "Unable to find ID3v2 tag")
    for test in self.tests:
      local_errors = Errors()
      test.run_check(directory, valid_tags, "POTENTIAL" if test.fix else "ERROR", local_errors)
      if test.fix and local_errors.has_errors():
        tofix = [(path, id3) for (path, id3) in valid_tags if path in local_errors.error_files()]
        test.fix.try_fix(directory, valid_tags, tofix, local_errors)
        test.run_check(directory, valid_tags, "ERROR", local_errors)
      errors.merge(local_errors)

    if errors.has_errors():
      for file, errormessages in errors.items():
        print "%s:" % (file)
        for message in errormessages:
          print " %s" % (message)

class Check(object):
  def __init__(self, fix=None):
    self.fix = fix
    
  def run_check(self, directory, files, severity, errors):
    pass

  def get_frame(id3, frametype):
    try:
      return id3.getall(frametype)[0]
    except IndexError:
      return None
  get_frame = staticmethod(get_frame)
  
  def get_value(id3, frametype): 
    frame = Check.get_frame(id3, frametype)
    if frame:
      return str(frame.text)
    return None
  get_value = staticmethod(get_value)

class FileCheck(Check):
  def run_check(self, directory, files, severity, errors):
    for file, frames in files:
      self.check_file(file, frames, severity, errors)

  def check_file(self, file, id3, errors):
    pass

class FramePresentCheck(FileCheck):
  def __init__(self, frametypes, fix=None):
    FileCheck.__init__(self, fix)
    self.frametypes = frametypes

  def check_file(self, file, id3, severity, errors):
    for frametype in self.frametypes:
      frame = Check.get_frame(id3, frametype) 
      if not frame:
        errors.record(file, severity, "Required frame %s missing" % frametype)

class FrameAbsentCheck(FileCheck):
  def __init__(self, frametypes, fix=None):
    FileCheck.__init__(self, fix)
    self.frametypes = frametypes

  def check_file(self, file, id3, severity, errors):
    for frametype in self.frametypes:
      frame = Check.get_frame(id3, frametype) 
      if frame:
        errors.record(file, severity, "Banned frame %s present" % frametype)


class FrameWhitelistCheck(FileCheck):
  def __init__(self, frametype, whitelist, regex=False, fix=None):
    FileCheck.__init__(self, fix)
    self.frametype = frametype
    self.whitelist = set(whitelist)
    self.regex = regex

  def check_file(self, file, id3, severity, errors):
    frame = Check.get_frame(id3, self.frametype) 
    if not frame:
      return
    if self.regex:
      valid = [[string for regex in self.whitelist if re.match(regex, string)] for string in frame.text]
      if valid:
        valid = valid[0]
      invalid = [string for string in frame.text if string not in valid]
    else:
      invalid = [string for string in frame.text if string not in self.whitelist]
    if len(invalid) > 0:
      errors.record(file, severity, "Frame %s has values not in whitelist %s" % (self.frametype, invalid))


class FrameBlacklistCheck(FileCheck):
  def __init__(self, frametype, blacklist, regex=False, fix=None):
    FileCheck.__init__(self, fix)
    self.frametype = frametype
    self.blacklist = set(blacklist)
    self.regex = regex

  def check_file(self, file, id3, severity, errors):
    frame = Check.get_frame(id3, self.frametype) 
    if not frame:
      return
    if (self.regex):
      invalid = [[string for regex in self.blacklist if re.match(regex, string)] for string in frame.text]
      if invalid:
        invalid = invalid[0]
    else:
      invalid = [string for string in frame.text if string in self.blacklist]
    if len(invalid) > 0:
      errors.record(file, severity, "Frame %s has values %s matching blacklist %s" % (self.frametype, invalid, self.blacklist))


class FrameConsistencyCheck(Check):
  def __init__(self, frametypes, fix):
    FileCheck.__init__(self, fix)
    self.frametypes = frametypes

  def run_check(self, directory, files, severity, errors):
    for frametype in self.frametypes:
      values = set()
      for file, frame in files:
        value = Check.get_value(frame, frametype)
        values.add(value)
   
      if len(values) > 1:
        errors.record(directory, severity, "Inconsistent values for frame %s: %s" % (frametype, values))


class MutualPresenceCheck(FileCheck):
  def __init__(self, frametypes, fix=None):
    FileCheck.__init__(self, fix)
    self.frametypes = frametypes

  def check_file(self, file, id3, severity, errors):
    present = [frametype for frametype in self.frametypes if Check.get_frame(id3, frametype)]
    absent = [frametype for frametype in self.frametypes if frametype not in present]
    if len(present) == 0:
      return
    if len(absent) == 0:
      return
    errors.record(file, severity, "Mutally required frames missing: has %s but not %s" % (present, absent))

class Fix(object):
  def try_fix(self, directory, valid_files, to_fix, errors):
    pass
  
class StripFrame(Fix):
  def __init__(self, frametypes):
    self.frametypes = frametypes
    
  def try_fix(self, directory, valid_files, to_fix, errors):
    for frametype in self.frametypes:
      for file, frame in to_fix:
        try:
          frame.delall(frametype)
          frame.save()
          errors.record(file, "FIXED", "Frame %s deleted" % (frametype,))
        except:
          errors.record(file, "FIXERROR", "Could not delete frame %s" % (frametype,))
          
   
class ApplyCommonValue(Fix):
  def __init__(self, source, target, outliers):
    self.source = source
    self.target = target
    self.outliers = outliers    
    
  def try_fix(self, directory, valid_files, to_fix, errors):
    for (file, tag) in to_fix:
      errors.record(file, "FIXERROR", "Can't fix! Sorry.")



def runchecks(path):
  tests = [
    # 'real' tests
    # TDRL vs TDRC vs TYER
    # RVA2 vs RVAD
    # Blacklist 'Various' from TPE1?
    # 'and' / '&' / 'feat' in artists
#    FramePresentCheck(['APIC', 'TALB', 'TOWN', 'TDRL', 'RVA2', 'TRCK']),
#    MutualPresenceCheck(['TOAL', 'TOPE', 'TDOR']),
#    FrameConsistencyCheck(['TALB', 'TPE2', 'TOWN', 'TDRL']),
#    FramePresentCheck(['TPE2'], fix=ApplyCommonValue(source='TPE1', target='TPE2', outliers=1)),
    FrameAbsentCheck(['COMM'], fix=StripFrame(['COMM'])),
#    FrameWhitelistCheck('TOWN', ['emusic']),
#    FrameWhitelistCheck('TCON', ['Rock']),
#    FrameBlacklistCheck('TIT2', [r'[\(\[].*with', r'[\(\[].*live', r'[\(\[].*remix', r'[\(\[].*cover'], regex=True),
#    FrameWhitelistCheck('TPE3', ['xxx']), # conductor
#    FrameWhitelistCheck('TCOM', ['xxx']), # composer
    
    # 'demo' tests
#    FrameAbsentCheck(['XXXX','YYYY']),
#    FrameBlacklistCheck('TPE2', ['David Bowie']),
#    FrameWhitelistCheck('TPE2', ['^E', '^D'], regex=True),
  ]
  doctor = Doctor(tests)
  doctor.checkup(path, recursive=True)

if __name__ == "__main__":
  runchecks(sys.argv[1])
