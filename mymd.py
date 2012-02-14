#!/usr/bin/python
from mp3md import *

runchecks([
  # document recommended order - version checks to make sure everything's OK, check presence + apply sets before bulk dir operations
  # percentage of nice-to-haves: e.g. TDRL
  # Strip id3v1, or check it's consistent?
  # are there fields which should be stripped?
  # Find incorrect directory structure (Various Artists TPE2 not in Various Artists, non-two-levels-deep structures)
  # Sort alphabetically when scanning
  # Coloured output for errors, or dump to stderr
  # Check TPE2 consistent per folder? What about TCON?
  # "conducted by" banned in TPE1 (cf. BBC Philharmonic)
  # "strict" version - check full release date (yyyy-mm-dd)
  #FrameAbsentCheck(['COMM'], fix=StripFrame(['COMM'])),
  #FrameWhitelistCheck('TPE3', ['xxx']), # conductor
  #FrameWhitelistCheck('TCOM', ['xxx']), # composer
  #Strip PRIV= DRM frames.

  TagVersionCheck(fix=UpdateTag()),
  FramePresentCheck(['APIC', 'TALB', 'TOWN', 'TRCK', 'TDRC']), # RVA2, TCON
  FramePresentCheck(['TPE2'], fix=ApplyCommonValue(source='TPE1', target='TPE2', outliers=1)),
  MutualPresenceCheck(['TOAL', 'TOPE', 'TDOR']),
  #TrackNumberContinuityCheck(),
  FrameWhitelistCheck('TOWN', ['allofmp3', 'cdbaby', 'purchasedonline', 'amazon', 'bleep', 'emusic', 'rip', 'hmm', 'nic', 'nate', 'free']),
  FrameWhitelistCheck('TCON', ['Rock', 'Children\'s', 'Lullaby', 'Audiobook', 'Alternative', 'Poetry', 'Soundtrack', 'Indie',
                               'Christmas', 'Pop', 'Folk', 'Electronic', 'Folk', 'Comedy', 'Dance', 'Country', 'Classical',
                               'Bluegrass', 'Blues', 'World', 'Vocal', 'Swing', 'Punk', 'Hip-Hop', 'Musical', 'Latin', 'Jazz',
                               'Lounge', 'R&B', 'Reggae', 'Mashup', 'Techno', 'Trip Hop', 'A Capella', 'Instrumental']),
  #FrameBlacklistCheck('TIT2', [r'[\(\[].*with', r'[\(\[].*live', r'[\(\[].*remix', r'[\(\[].*cover'], regex=True),
  FrameBlacklistCheck('TALB', [r'[dD]is[kc] [0-9]+'], regex=True),
  #FrameBlacklistCheck('TPE1', [r'[Vv]arious', r' and ', r' with ', r' feat(uring|\.)? '], regex=True),
  FrameBlacklistCheck('TPE2', ['Various', 'Assorted'], regex=False, fix=ApplyValue('TPE2', 'Various Artists')),
  DependentValueCheck('TCMP', '1', 'TPE2', 'Various Artists', fix=ApplyValue('TCMP', '1')),
  FrameConsistencyCheck(['TALB', 'TPE2', 'TOWN', 'TDRL', 'TCMP']), # TCON?
])
