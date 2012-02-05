from mp3doctor import *

Doctor([
  # 'real' tests
  # TDRL vs TDRC vs TYER
  # RVA2 vs RVAD
  # Blacklist 'Various' from TPE1?
  # 'and' / '&' / 'feat' in artists
  FramePresentCheck(['APIC', 'TALB', 'TOWN', 'TRCK']),
  # FramePresentCheck(['TDRL', 'RVA2',]),
  MutualPresenceCheck(['TOAL', 'TOPE', 'TDOR']),
  FrameConsistencyCheck(['TALB', 'TPE2', 'TOWN', 'TDRL']),
  FrameWhitelistCheck('TOWN', ['emusic', 'rip', 'hmm', 'nic', 'nate']),
  FrameWhitelistCheck('TCON', ['Rock', 'Children\'s', 'Lullaby', 'Audiobook', 'Alternative', 'Poetry', 'Soundtrack']),
  #FrameBlacklistCheck('TIT2', [r'[\(\[].*with', r'[\(\[].*live', r'[\(\[].*remix', r'[\(\[].*cover'], regex=True),
  #FrameWhitelistCheck('TPE3', ['xxx']), # conductor
  #FrameWhitelistCheck('TCOM', ['xxx']), # composer
  ]).checkup(sys.argv[1], recursive=True)
