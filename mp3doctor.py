from tagger import *

import sys, os, fnmatch

class DirectoryCheck(object):
  def check_dir(self, directory):
    files = fnmatch.filter(os.listdir(directory), '*.mp3')
    self.check_dir_files(directory, files)

  def check_dir_files(self, directory, files):
    pass

class FileCheck(DirectoryCheck):
  def check_dir_files(self, directory, files):
    for file in files:
      path = os.path.join(directory, file)
      id3 = ID3v2(path)
      if not id3.tag_exists():
        print(path, "Unable to find ID3v2 tag")
      else:
        self.check_file(file, id3)

  def check_file(self, file, id3):
    pass

class TagPresentCheck(FileCheck):
  def __init__(self, tag):
    self.tag = tag

  def check_file(self, file, id3):
    try:
      matchframe = [frame for frame in id3.frames if frame.fid == self.tag][0]
      print "Got it %s" % (matchframe,)
    except IndexError:
      print(file, "No frame: %s" % self.tag)

def runchecks(paths):
  tests = [TagPresentCheck('APIC'), TagPresentCheck('TALB')]
  for path in paths:
     for test in tests:
       test.check_dir(path)

runchecks((sys.argv[1],))
