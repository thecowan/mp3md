#!/usr/bin/python
from mp3md import *

class TrailingArtistCheck(FileCheck, Fix):
  def __init__(self):
    FileCheck.__init__(self, self)

  def check_file(self, file, id3, severity, errors):
      artist = Check.get_value(id3, 'TPE1') 
      title = Check.get_value(id3, 'TIT2')
      search_string = " - " + artist
      if title.endswith(search_string):
        errors.record(file, severity, "Title '%s' appears to include artist '%s'" % (title, artist))

  def try_fix(self, directory, valid_files, to_fix, errors):
    for file, tag in to_fix:
      try:
        artist = Check.get_value(tag, 'TPE1') 
        title = Check.get_value(tag, 'TIT2')
        search_string = " - " + artist
        newtitle = title.replace(search_string, "")
        tag.delall('TIT2')
        frame = Frames.get('TIT2')(encoding=3, text=newtitle)
        tag.add(frame)
        tag.save() 
        errors.record(file, "FIXED", "Title set to '%s'" % (newtitle))
      except object, e:
        errors.record(file, "FIXERROR", "Could not set title to '%s': %s" % (newtitle, e))

class MigrateRegex(Fix):
  def __init__(self, from_frame, to_frame, regex, overwrite, match_group=0):
    self.from_frame = from_frame
    self.to_frame = to_frame
    self.regex = regex
    self.overwrite = overwrite
    self.match_group = match_group

  def try_fix(self, directory, valid_files, to_fix, errors):
    for file, tag in to_fix:
      try:
        source = Check.get_value(tag, self.from_frame)
        match = re.search(self.regex, source)
        if not match:
          errors.record(file, "FIXERROR", "Cannot move value from frame %s as does not match regex %s" % (self.from_frame, self.regex))
          break

        replace_value = match.group(self.match_group)
        existing_value = Check.get_value(tag, self.to_frame)
        if existing_value:
          if not self.overwrite:
            errors.record(file, "FIXERROR", "Could not copy value '%s' from frame %s; destination frame %s already has value '%s' and overwrite=False" % (replace_value, self.from_frame, self.to_frame, existing_value))
            break

        tag.delall(self.to_frame)
        tag.delall(self.from_frame)
        replace_from = re.sub(self.regex, "", source)

        frame = Frames.get(self.to_frame)(encoding=3, text=replace_value)
        tag.add(frame)
        frame = Frames.get(self.from_frame)(encoding=3, text=replace_from)
        tag.add(frame)
        tag.save()
        errors.record(file, "FIXED", "Value '%s' moved from frame %s to %s" % (replace_value, self.from_frame, self.to_frame))
      except object, e:
        errors.record(file, "FIXERROR", "Could not move regex %s from frame %s to frame %s: %s" % (self.refex, self.from_frame, self.to_frame, e))


metadata_regex = r'(?i) ?[(\[][^)\]]*((single|album) version|explicit|remaster|clean)[)\]]$'

runchecks([
  # check which fields should be stripped (e.g. J River tags)
  # Should I check TCON is consistent per folder?
  # "conducted by" banned in TPE1 (cf. BBC Philharmonic)
  # "strict" version - check full release date (yyyy-mm-dd)
  #FrameAbsentCheck(['COMM'], fix=StripFrame(['COMM'])),
  #FrameWhitelistCheck('TPE3', ['xxx']), # conductor
  #FrameWhitelistCheck('TCOM', ['xxx']), # composer

  TagVersionCheck(fix=UpdateTag()),
  FramePresentCheck(['TIT2', 'TPE1', 'APIC', 'TALB', 'TOWN', 'TRCK', 'TDRC']), # RVA2, TCON
  TrailingArtistCheck(),
  FramePresentCheck(['TPE2'], fix=ApplyCommonValue(source='TPE1', target='TPE2', outliers=1)),
  MutualPresenceCheck(['TOAL', 'TOPE', 'TDOR']),
  #TrackNumberContinuityCheck(),
  FrameWhitelistCheck('TOWN', ['allofmp3', 'cdbaby', 'purchasedonline', 'amazon', 'bleep', 'emusic', 'rip', 'hmm', 'nic', 'nate', 'free']),
  FrameWhitelistCheck('TCON', ['Rock', 'Children\'s', 'Lullaby', 'Audiobook', 'Alternative', 'Poetry', 'Soundtrack', 'Indie',
                               'Christmas', 'Pop', 'Folk', 'Electronic', 'Folk', 'Comedy', 'Dance', 'Country', 'Classical',
                               'Bluegrass', 'Blues', 'World', 'Vocal', 'Swing', 'Punk', 'Hip-Hop', 'Musical', 'Latin', 'Jazz',
                               'Lounge', 'R&B', 'Reggae', 'Mashup', 'Techno', 'Trip Hop', 'A Capella', 'Instrumental']),
  #FrameBlacklistCheck('TIT2', [r'[\(\[].*with', r'[\(\[].*live', r'[\(\[].*remix', r'[\(\[].*cover'], regex=True),
  FrameBlacklistCheck('TALB', [r'(?i)dis[kc] [0-9]+'], regex=True),
  #FrameBlacklistCheck('TPE1', [r'[Vv]arious', r' and ', r' with ', r' feat(uring|\.)? '], regex=True),
  FrameBlacklistCheck('TPE2', ['Various', 'Assorted'], regex=False, fix=ApplyValue('TPE2', 'Various Artists')),
  DependentValueCheck('TCMP', '1', 'TPE2', 'Various Artists', fix=ApplyValue('TCMP', '1')),
  FrameConsistencyCheck(['TALB', 'TPE2', 'TOWN', 'TDRL', 'TCMP']), # TCON?
  FrameAbsentCheck(['PRIV:contentgroup@emusic.com'], fix=StripFrame(['PRIV:contentgroup@emusic.com'])),
  FrameAbsentCheck(['PRIV:www.amazon.com'], fix=StripFrame(['PRIV:www.amazon.com'])),
  FrameBlacklistCheck('TIT2', [metadata_regex], regex=True, fix=MigrateRegex(regex=metadata_regex, from_frame='TIT2', to_frame='TIT3', overwrite=False, match_group=1)),
])
