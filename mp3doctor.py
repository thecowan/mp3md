from tagger import *

import sys, os, fnmatch

class DirectoryCheck(object):
  def __init__(self, tests):
    self.tests = tests

  def check_dir(self, directory):
    tocheck = []
    files = fnmatch.filter(os.listdir(directory), '*.mp3')
    for file in files:
      path = os.path.join(directory, file)
      id3 = ID3v2(path)
      if not id3.tag_exists():
        print(path, "Unable to find ID3v2 tag")
      else:
        tocheck.append((path, id3))
    for test in self.tests:
      test.run_check(directory, tocheck)

class Check(object):
  def run_check(self, directory, files):
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
  def run_check(self, directory, files):
    for file, frames in files:
      self.check_file(file, frames)

  def check_file(self, file, id3):
    pass

class TagPresentCheck(FileCheck):
  def __init__(self, frametype):
    self.frametype = frametype

  def check_file(self, file, id3):
    frame = self.get_frame(id3, self.frametype) 
    if not frame:
      print(file, "Required frame %s missing" % self.frametype)

class TagAbsentCheck(FileCheck):
  def __init__(self, frametype):
    self.frametype = frametype

  def check_file(self, file, id3):
    frame = self.get_frame(id3, self.frametype) 
    if frame:
      print(file, "Banned frame %s present" % self.frametype)


class TagWhitelistCheck(FileCheck):
  def __init__(self, frametype, whitelist):
    self.frametype = frametype
    self.whitelist = set(whitelist)

  def check_file(self, file, id3):
    frame = self.get_frame(id3, self.frametype) 
    if not frame:
	   return
    invalid = [string for string in frame.strings if string not in self.whitelist]
    if len(invalid) > 0:
      print(file, "Frame %s has values not in whitelist %s" % (self.frametype, invalid))


class TagConsistencyCheck(Check):
  def __init__(self, frametype):
    self.frametype = frametype

  def run_check(self, directory, files):
    values = set()
    for file, frame in files:
      value = self.get_value(frame, self.frametype)
      values.add(value)
   
    if len(values) > 1:
      print (directory, "Inconsistent values for frame %s: %s" % (self.frametype, values))


def runchecks(path):
  tests = [TagPresentCheck('APIC'), TagPresentCheck('TALB'), TagPresentCheck('TOWN'), TagConsistencyCheck('TALB'), TagConsistencyCheck('TPE2'),
    TagWhitelistCheck('TCON', ['Rock']),
    TagWhitelistCheck('TOWN', ['emusic']),
    TagPresentCheck('TDOR'),
    TagAbsentCheck('XXXX'),
  ]
  tester = DirectoryCheck(tests)
  tester.check_dir(path)

runchecks(sys.argv[1])