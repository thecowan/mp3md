#!/usr/bin/python

from mutagen.id3 import ID3
from mutagen.id3 import Frames
from optparse import OptionParser
from mp3md import Check

import sys, os, fnmatch, re

class Renamer(object):
  def execute(self, directory, pattern, recursive=False, dry_run=False):
    if recursive:
      for dirpath, _, _ in os.walk(directory):
        self.rename_dir(dirpath, pattern, dry_run)
    else:
      self.rename_dir(directory, pattern, dry_run)

  def rename_dir(self, directory, pattern, dry_run):
    valid_tags = self.files_with_valid_tags(directory)
    for (file, id3) in valid_tags:
      values = dict()
      values["TALB"] = Check.get_value(id3, "TALB", "Unknown")
      values["TRCK"] = Renamer.first_part(id3, "TRCK")
      values["TPOS"] = Renamer.first_part(id3, "TPOS")
      values["TIT2"] = Check.get_value(id3, "TIT2", "Unknown")
      values["TPE1"] = Check.get_value(id3, "TPE1", "Unknown")
      name = pattern % values
      name = re.sub('[/:]+', '', name)
      name = os.path.join(directory, name)
      print u"renaming file %r to %r" % (file, name)
      if not dry_run:
        os.rename(file, name)

  def first_part(id3, frame):
    value = Check.get_value(id3, frame, "0")
    return int(value.split("/")[0])
  first_part = staticmethod(first_part)

  def files_with_valid_tags(self, directory, errors=None):
    files = fnmatch.filter(os.listdir(directory), '*.mp3')
    for file in files:
      path = os.path.join(directory, file)
      try:
        id3 = ID3(path)
        yield (path, id3)
      except:
          print "Unable to find ID3v2 tag for %s" % (path,)


def dorename():
  parser = OptionParser()
  parser.add_option("-r", "--recursive", action="store_true", default=False, help="Recurse into directories")
  parser.add_option("-d", "--dry-run", action="store_true", default=False, help="Don't actually rename")
  parser.add_option("-p", "--pattern", default="%(TPOS)02d_%(TRCK)02d_%(TALB)s_%(TIT2)s.mp3", help="Filename pattern to apply")
  (options, args) = parser.parse_args()
  if not args:
    raise SystemExit(parser.print_help() or 1)
  renamer = Renamer()
  renamer.execute(args[0], pattern=options.pattern, recursive=options.recursive, dry_run=options.dry_run)

if __name__ == "__main__":
  dorename()
