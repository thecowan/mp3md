from tagger import *

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

class TestRunner(object):
  def __init__(self, tests):
    self.tests = tests

  def test_dir(self, directory):
    tocheck = []
    files = fnmatch.filter(os.listdir(directory), '*.mp3')
    errors = dict()
    for file in files:
      path = os.path.join(directory, file)
      id3 = ID3v2(path)
      if not id3.tag_exists():
        errors.setdefault(path, []).append("Unable to find ID3v2 tag")
      else:
        tocheck.append((path, id3))
    for test in self.tests:
      test.run_check(directory, tocheck, errors)
    if len(errors) > 0:
      for file, errormessages in errors.items():
        print "%s:" % (file)
        for message in errormessages:
          print "  %s" % (message)

class Check(object):
  def run_check(self, directory, files, errors):
    pass

  def get_frame(self, id3, frametype):
    try:
      return [frame for frame in id3.frames if frame.fid == frametype][0]
    except IndexError:
      return None

  def get_value(self, id3, frametype): 
    frame = self.get_frame(id3, frametype)
    if frame:
      return str(frame.strings)
    return None

class FileCheck(Check):
  def run_check(self, directory, files, errors):
    for file, frames in files:
      self.check_file(file, frames, errors)

  def check_file(self, file, id3, errors):
    pass

class FramePresentCheck(FileCheck):
  def __init__(self, frametype):
    self.frametype = frametype

  def check_file(self, file, id3, errors):
    frame = self.get_frame(id3, self.frametype) 
    if not frame:
      errors.setdefault(file, []).append("Required frame %s missing" % self.frametype)

class FrameAbsentCheck(FileCheck):
  def __init__(self, frametype):
    self.frametype = frametype

  def check_file(self, file, id3, errors):
    frame = self.get_frame(id3, self.frametype) 
    if frame:
      errors.setdefault(file, []).append("Banned frame %s present" % self.frametype)


class FrameWhitelistCheck(FileCheck):
  def __init__(self, frametype, whitelist, regex=False):
    self.frametype = frametype
    self.whitelist = set(whitelist)
    self.regex = regex

  def check_file(self, file, id3, errors):
    frame = self.get_frame(id3, self.frametype) 
    if not frame:
      return
    if self.regex:
      valid = [[string for regex in self.whitelist if re.match(regex, string)] for string in frame.strings]
      if valid:
        valid = valid[0]
      invalid = [string for string in frame.strings if string not in valid]
    else:
      invalid = [string for string in frame.strings if string not in self.whitelist]
    if len(invalid) > 0:
      errors.setdefault(file, []).append("Frame %s has values not in whitelist %s" % (self.frametype, invalid))


class FrameBlacklistCheck(FileCheck):
  def __init__(self, frametype, blacklist, regex=False):
    self.frametype = frametype
    self.blacklist = set(blacklist)
    self.regex = regex

  def check_file(self, file, id3, errors):
    frame = self.get_frame(id3, self.frametype) 
    if not frame:
      return
    if (self.regex):
      invalid = [[string for regex in self.blacklist if re.match(regex, string)] for string in frame.strings]
      if invalid:
        invalid = invalid[0]
    else:
      invalid = [string for string in frame.strings if string in self.blacklist]
    if len(invalid) > 0:
      errors.setdefault(file, []).append("Frame %s has values %s matching blacklist %s" % (self.frametype, invalid, self.blacklist))


class FrameConsistencyCheck(Check):
  def __init__(self, frametype):
    self.frametype = frametype

  def run_check(self, directory, files, errors):
    values = set()
    for file, frame in files:
      value = self.get_value(frame, self.frametype)
      values.add(value)
   
    if len(values) > 1:
      errors.setdefault(directory, []).append("Inconsistent values for frame %s: %s" % (self.frametype, values))


def runchecks(path):
  tests = [FramePresentCheck('APIC'), FramePresentCheck('TALB'), FramePresentCheck('TOWN'), FrameConsistencyCheck('TALB'), FrameConsistencyCheck('TPE2'),
    FrameWhitelistCheck('TCON', ['Rock']),
    FrameWhitelistCheck('TOWN', ['emusic']),
    FramePresentCheck('TDOR'),
    FrameAbsentCheck('XXXX'),
    FrameBlacklistCheck('TPE2', ['David Bowie']),
    FrameWhitelistCheck('TPE2', ['^E', '^D'], regex=True),
    FrameBlacklistCheck('TPE2', [r'[\(\[].*with'], regex=True),
    FrameBlacklistCheck('TPE2', [r'[\(\[].*live'], regex=True),
    FrameBlacklistCheck('TPE2', [r'[\(\[].*remix'], regex=True),
  ]
  doctor = Doctor(tests)
  doctor.checkup(path, recursive=True)

runchecks(sys.argv[1])
