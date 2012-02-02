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
      test.run_check(tocheck)

class FileCheck(object):
  def run_check(self, files):
    for file, tags in files:
      self.check_file(file, tags)

  def check_file(self, file, id3):
    pass

class TagPresentCheck(FileCheck):
  def __init__(self, tag):
    self.tag = tag

  def check_file(self, file, id3):
    try:
      matchframe = [frame for frame in id3.frames if frame.fid == self.tag][0]
      # print "Got it %s" % (matchframe,)
    except IndexError:
      print(file, "No frame: %s" % self.tag)

def runchecks(path):
  tests = [TagPresentCheck('APIC'), TagPresentCheck('TALB')]
  tester = DirectoryCheck(tests)
  tester.check_dir(path)

runchecks(sys.argv[1])
