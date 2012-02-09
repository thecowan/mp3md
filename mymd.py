from mp3md import *

runchecks([
  # percentage of nice-to-haves: TDRL
  # TCMP if 'Various' set
  TagVersionCheck(fix=UpdateTag()),
  FramePresentCheck(['APIC', 'TALB', 'TOWN', 'TRCK']),
  # FramePresentCheck(['TDRC', 'RVA2',]),
  FramePresentCheck(['TPE2'], fix=ApplyCommonValue(source='TPE1', target='TPE2', outliers=0.15)),
  MutualPresenceCheck(['TOAL', 'TOPE', 'TDOR']),
  TrackNumberContinuityCheck(),
  FrameConsistencyCheck(['TALB', 'TPE2', 'TOWN', 'TDRL', 'TCMP']),
  # FrameAbsentCheck(['COMM'], fix=StripFrame(['COMM'])),
  FrameWhitelistCheck('TOWN', ['emusic', 'rip', 'hmm', 'nic', 'nate']),
  FrameWhitelistCheck('TCON', ['Rock', 'Children\'s', 'Lullaby', 'Audiobook', 'Alternative', 'Poetry', 'Soundtrack']),
  FrameBlacklistCheck('TIT2', [r'[\(\[].*with', r'[\(\[].*live', r'[\(\[].*remix', r'[\(\[].*cover'], regex=True),
  FrameBlacklistCheck('TPE1', [r'[Vv]arious', r' and ', r' with ', r' feat(uring|\.)? '], regex=True),
  FrameBlacklistCheck('TPE2', ['Various', 'Assorted'], regex=False, fix=ApplyValue('TPE2', 'Various Artists')),
  #FrameWhitelistCheck('TPE3', ['xxx']), # conductor
  #FrameWhitelistCheck('TCOM', ['xxx']), # composer
])
