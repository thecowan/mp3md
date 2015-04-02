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
  FrameBlacklistCheck('TCON', ['Alternative Rock'], regex=False, fix=ApplyValue('TCON', 'Alternative')),
  FrameWhitelistCheck('TOWN', ['allofmp3', 'cdbaby', 'purchasedonline', 'amazon', 'bleep', 'emusic', 'rip', 'hmm', 'nic', 'nate',
                               'free', 'chris', 'google', 'daytrotter', 'humblebundle', 'soundsupply', 'bandcamp']),
  FrameWhitelistCheck('TCON', ['Rock', 'Children\'s', 'Lullaby', 'Audiobook', 'Alternative', 'Poetry', 'Soundtrack', 'Indie',
                               'Christmas', 'Pop', 'Folk', 'Electronic', 'Folk', 'Comedy', 'Dance', 'Country', 'Classical',
                               'Bluegrass', 'Blues', 'World', 'Vocal', 'Swing', 'Punk', 'Hip-Hop', 'Musical', 'Latin', 'Jazz',
                               'Lounge', 'R&B', 'Reggae', 'Mashup', 'Techno', 'Trip Hop', 'A Capella', 'Instrumental', 'Funk',
                               'Chiptune']),
  #FrameBlacklistCheck('TIT2', [r'[\(\[].*with', r'[\(\[].*live', r'[\(\[].*remix', r'[\(\[].*cover'], regex=True),
  FrameBlacklistCheck('TALB', [r'[dD]is[kc] [0-9]+'], regex=True),
  #FrameBlacklistCheck('TPE1', [r'[Vv]arious', r' and ', r' with ', r' feat(uring|\.)? '], regex=True),
  FrameBlacklistCheck('TPE2', ['Various', 'Assorted'], regex=False, fix=ApplyValue('TPE2', 'Various Artists')),
  DependentValueCheck('TCMP', '1', 'TPE2', 'Various Artists', fix=ApplyValue('TCMP', '1')),
  FrameConsistencyCheck(['TALB', 'TPE2', 'TOWN', 'TDRL', 'TCMP']), # TCON?
  FrameAbsentCheck(['PRIV:contentgroup@emusic.com'], fix=StripFrame(['PRIV:contentgroup@emusic.com'])),
  FrameAbsentCheck(['PRIV:Google/UITS'], fix=StripFrame(['PRIV:Google/UITS'])),
  FrameAbsentCheck(['PRIV:Google/StoreId'], fix=StripFrame(['PRIV:Google/StoreId'])),
  FrameAbsentCheck(['COMM:Media Jukebox'], fix=StripFrame(['COMM:Media Jukebox'])),
  FrameAbsentCheck(['USER'], fix=StripFrame(['USER'])),
  FrameAbsentCheck(['PRIV:WM/UniqueFileIdentifier'], fix=StripFrame(['PRIV:WM/UniqueFileIdentifier'])),
  FrameAbsentCheck(['PRIV:WM/MediaClassSecondaryID'], fix=StripFrame(['PRIV:WM/MediaClassSecondaryID'])),
  FrameAbsentCheck(['PRIV:WM/WMCollectionGroupID'], fix=StripFrame(['PRIV:WM/WMCollectionGroupID'])),
  FrameAbsentCheck(['PRIV:WM/Provider'], fix=StripFrame(['PRIV:WM/Provider'])),
  FrameAbsentCheck(['PRIV:WM/MediaClassPrimaryID'], fix=StripFrame(['PRIV:WM/MediaClassPrimaryID'])),
  FrameAbsentCheck(['PRIV:WM/WMContentID'], fix=StripFrame(['PRIV:WM/WMContentID'])),
  FrameAbsentCheck(['PRIV:WM/WMCollectionID'], fix=StripFrame(['PRIV:WM/WMCollectionID'])),
  FrameAbsentCheck(['PRIV:PeakValue'], fix=StripFrame(['PRIV:PeakValue'])),
  FrameAbsentCheck(['PRIV:AverageLevel'], fix=StripFrame(['PRIV:AverageLevel'])),
  # FrameAbsentCheck(['PRIV'], fix=StripFrame(['PRIV'])),
])
