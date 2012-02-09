# TODO:
#  - group reports by error-per-dir, or error-global
#  - supply checks by file, command line, etc
#  - collection-wide thresholds for incremental improvements (error if <50% have tag xxxx)
#  - more detailed specifiers (e.g. COMM by language, or by type) - check .delalls too
#  - apply fixes on a directory level
from mutagen.id3 import ID3
from mutagen.id3 import Frames
from optparse import OptionParser

import sys, os, fnmatch, re

class Doctor(object):
  def __init__(self, tests):
    self.tests = tests

  def checkup(self, directory, recursive=False, fix=False):
    if recursive:
      for dirpath, _, _ in os.walk(directory):
        self.test_dir(dirpath, fix)
    else:
      self.test_dir(directory, fix)

  def test_dir(self, directory, apply_fixes):
    errors = Errors()
    valid_tags = self.files_with_valid_tags(directory, errors=errors)
    for test in self.tests:
      local_errors = Errors()
      test.run_check(directory, valid_tags, "WARNING" if test.fix and apply_fixes else "ERROR", local_errors)
      if apply_fixes and test.fix and local_errors.has_errors():
        tofix = [(path, id3) for (path, id3) in valid_tags if path in local_errors.error_files()]
        test.fix.try_fix(directory, valid_tags, tofix, local_errors)
        
        # Update tags in case we're in an unknown state - fixes failed, etc. Some tests may no longer apply.
        # Don't record ID3 errors though, we've already gotten those above (unless something's gone horribly
        # horribly wrong).
        valid_tags = self.files_with_valid_tags(directory, errors=None)
        test.run_check(directory, valid_tags, "ERROR", local_errors)
      errors.merge(local_errors)

    if errors.has_errors():
      for file, errormessages in errors.items():
        print "%s:" % (file)
        for message in errormessages:
          print " %s" % (message)

  def files_with_valid_tags(self, directory, errors=None):
    valid_tags = []
    files = fnmatch.filter(os.listdir(directory), '*.mp3')
    for file in files:
      path = os.path.join(directory, file)
      try:
        id3 = ID3(path)
        valid_tags.append((path, id3))
      except:
        if errors:
          errors.record(path, "ERROR", "Unable to find ID3v2 tag")
    return valid_tags  

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
      # TODO: deal with multi-valued fields
      return str(frame.text[0])
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
  def __init__(self, frametypes, fix=None):
    Check.__init__(self, fix)
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

class TagVersionCheck(FileCheck):
  def check_file(self, file, id3, severity, errors):
    if (id3.version < (2, 4, 0)):
      errors.record(file, severity, "Frame version too old: %s" % (id3.version,))
      
class TrackNumberContinuityCheck(Check):
  def run_check(self, directory, files, severity, errors):
    # TODO: make aware of disc numbers. Provide option not to care about single-track purchases.
    if len(files) == 0:
      return
    track_values = set()
    maxtrack_values = set()
    for file, frame in files:
      values = Check.get_value(frame, "TRCK").split("/")
      track = int(values[0])
      maxtrack = int(values[1]) if len(values) > 1 else None
      track_values.add(track) 
      maxtrack_values.add(maxtrack)
    if len(maxtrack_values) > 1:
      errors.record(directory, severity, "Tracks don't agree about album track length: %s" % (maxtrack_values,))
      return
    maxtrack = list(maxtrack_values)[0]
    if not maxtrack:
      maxtrack = len(files)
    maxtrack = max(maxtrack, max(track_values))
    sorted_tracks = sorted(track_values)
    missing = [num for num in range(1, maxtrack) if not num in track_values]
    if len(missing) > 0:
      errors.record(directory, severity, "Missing track numbers %s out of %s tracks" % (missing, maxtrack))
      
class DependentValueCheck(FileCheck):
  def __init__(self, required_frame, required_value, dependent_frame, dependent_value, fix=None):
    FileCheck.__init__(self, fix)
    self.required_frame = required_frame
    self.required_value = required_value
    self.dependent_frame = dependent_frame
    self.dependent_value = dependent_value

  def check_file(self, file, id3, severity, errors):
    dependent = Check.get_value(id3, self.dependent_frame)
    required = Check.get_value(id3, self.required_frame)
    
    if dependent == self.dependent_value and required != self.required_value:
      errors.record(file, severity, "Frame %s = '%s' but %s not '%s' (was '%s')" % (self.dependent_frame,
          self.dependent_value, self.required_frame, self.required_value, required))
    
    
class Fix(object):
  def try_fix(self, directory, valid_files, to_fix, errors):
    pass

class ApplyValue(Fix):
  def __init__(self, frametype, value):
    self.frametype = frametype
    self.value = value
    
  def try_fix(self, directory, valid_files, to_fix, errors):
    for file, tag in to_fix:
      try:
        tag.delall(self.frametype)
        frame = Frames.get(self.frametype)(encoding=3, text=self.value)
        tag.add(frame)
        tag.save() 
        errors.record(file, "FIXED", "Frame %s set to '%s'" % (self.frametype, self.value))
      except object, e:
        errors.record(file, "FIXERROR", "Could not set frame %s to '%s': %s" % (self.frametype, self.value, e))
  
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
  # outliers may be an integer (in which case it represents the number of files which are permitted
  # to not have the common value), or a decimal < 1.0, in which case it is a fraction. So if there
  # are 25 files in a directory, a value of 5 or a value of 0.2 will have the same effect (apply
  # a common value to target if 20/25 share the same value in source. If a decimal is supplied, a
  # minimum outlier of 1 is assumed. Ties in cardinality (so with 10 items, outliers = 5, and two
  # source values each used by 5 files) are broken arbitrarily.
  def __init__(self, source, target, outliers):
    self.source = source
    self.target = target
    self.outliers = outliers    
    
  def try_fix(self, directory, valid_files, to_fix, errors):
    values = []
    for (file, tag) in valid_files:
      values.append(Check.get_value(tag, self.source))
    if len(values) == 0:
      for (file, tag) in to_fix:
        errors.record(file, "FIXERROR", "No valid source values for tag %s" % self.source)
      
    counter = {}
    for value in values: counter[value] = counter.get(value, 0) + 1    
    top = sorted([ (freq,word) for word, freq in counter.items() ], reverse=True)[0]
    top_value = top[1]
    top_freq = top[0]
    outliers = len(valid_files) - top_freq
    permitted_outliers = 0 if self.outliers == 0 else self.outliers if self.outliers >= 1 else max(int(self.outliers * len(valid_files)), 1)

    for (file, tag) in to_fix:
      if outliers > permitted_outliers:
        errors.record(file, "FIXERROR", "Too many outliers from %s: %s (max %s)" % (top_value, outliers, permitted_outliers))
      else:
        try:
          frame = Frames.get(self.target)(encoding=3, text=top_value)
          tag.add(frame)
          tag.save() 
          errors.record(file, "FIX", "Fixed: set field %s to \"%s\"" % (self.target, top_value))
        except object, e:
          errors.record(file, "FIXERROR", "Could not save %s" % e)

class UpdateTag(Fix):
  def try_fix(self, directory, valid_files, to_fix, errors):
    for (file, tag) in to_fix:
      tag.save()
      errors.record(file, "FIX", "Updated tag to v2.4")



def runchecks(tests):
  parser = OptionParser()
  parser.add_option("-r", "--recursive", action="store_true", default=False, help="Recurse into directories")
  parser.add_option("-f", "--apply-fixes", action="store_true", default=False, help="Apply any configured fixes")
  (options, args) = parser.parse_args()
  doctor = Doctor(tests)
  doctor.checkup(args[0], recursive=options.recursive, fix=options.apply_fixes)

if __name__ == "__main__":
  tests = [
    #TagVersionCheck(fix=UpdateTag()),
    #FramePresentCheck(['APIC', 'TALB', 'TRCK']),
    #MutualPresenceCheck(['TOAL', 'TOPE', 'TDOR']),
    #FrameConsistencyCheck(['TALB', 'TPE2']),
    #FramePresentCheck(['TPE2'], fix=ApplyCommonValue(source='TPE1', target='TPE2', outliers=2)),
    #TrackNumberContinuityCheck(),
    #FrameAbsentCheck(['COMM'], fix=StripFrame(['COMM'])),
    #FrameWhitelistCheck('TCON', ['Rock', 'Pop', 'Alternative']),
    #FrameBlacklistCheck('TIT2', [r'[\(\[].*with', r'[\(\[].*live', r'[\(\[].*remix', r'[\(\[].*cover'], regex=True),
    FramePresentCheck(['TXXX'], fix=ApplyValue('TXXX', 'test')),
    # DependentValueCheck('TCON', 'Rock', 'TPE1', 'Florence + The Machine', fix=ApplyValue('TCON', 'Rock'))
  ]
  runchecks(tests)
