#!/usr/bin/python
from mp3md import *

runchecks([
  # document recommended order - version checks to make sure everything's OK, check presence + apply sets before bulk dir operations
  # percentage of nice-to-haves: e.g. TDRL
  # Strip id3v1, or check it's consistent?
  # are there fields which should be stripped?
  TagVersionCheck(fix=UpdateTag()),
  FramePresentCheck(['APIC', 'TALB', 'TOWN', 'TRCK', 'TDRC']),
  # FramePresentCheck(['RVA2',]),
  FramePresentCheck(['TPE2'], fix=ApplyCommonValue(source='TPE1', target='TPE2', outliers=0.15)),
  MutualPresenceCheck(['TOAL', 'TOPE', 'TDOR']),
  TrackNumberContinuityCheck(),
  # FrameAbsentCheck(['COMM'], fix=StripFrame(['COMM'])),
  FrameWhitelistCheck('TOWN', ['emusic', 'rip', 'hmm', 'nic', 'nate']),
  FrameWhitelistCheck('TCON', ['Rock', 'Children\'s', 'Lullaby', 'Audiobook', 'Alternative', 'Poetry', 'Soundtrack']),
  FrameBlacklistCheck('TIT2', [r'[\(\[].*with', r'[\(\[].*live', r'[\(\[].*remix', r'[\(\[].*cover'], regex=True),
  FrameBlacklistCheck('TPE1', [r'[Vv]arious', r' and ', r' with ', r' feat(uring|\.)? '], regex=True),
  FrameBlacklistCheck('TPE2', ['Various', 'Assorted'], regex=False, fix=ApplyValue('TPE2', 'Various Artists')),
  #FrameWhitelistCheck('TPE3', ['xxx']), # conductor
  #FrameWhitelistCheck('TCOM', ['xxx']), # composer
  DependentValueCheck('TCMP', '1', 'TPE2', 'Various Artists', fix=ApplyValue('TCMP', '1')),
  FrameConsistencyCheck(['TALB', 'TPE2', 'TOWN', 'TDRL', 'TCMP']),
])
