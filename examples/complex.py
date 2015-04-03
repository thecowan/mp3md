#!/usr/bin/python
from mp3md import *

metadata_regex = r'(?i) ?[(\[]([^)\]]*((single|album) version|explicit|remaster|clean))[)\]]$'

runchecks([
  TagVersionCheck(fix=UpdateTag()),
  FramePresentCheck(['TIT2', 'TPE1', 'APIC', 'TALB', 'TOWN', 'TRCK', 'TDRC']),
  TrailingArtistCheck(),
  FramePresentCheck(['TPE2'], fix=ApplyCommonValue(source='TPE1', target='TPE2', outliers=1)),
  MutualPresenceCheck(['TOAL', 'TOPE', 'TDOR']),
  FrameBlacklistCheck('TCON', ['Alternative Rock'], regex=False, fix=ApplyValue('TCON', 'Alternative')),
  FrameWhitelistCheck('TCON', ['Rock', 'Children\'s', 'Lullaby', 'Audiobook', 'Alternative', 'Poetry', 'Soundtrack', 'Indie',
                               'Christmas', 'Pop', 'Folk', 'Electronic', 'Folk', 'Comedy', 'Dance', 'Country', 'Classical',
                               'Bluegrass', 'Blues', 'World', 'Vocal', 'Swing', 'Punk', 'Hip-Hop', 'Musical', 'Latin', 'Jazz',]),
  FrameBlacklistCheck('TALB', [r'(?i)dis[kc] [0-9]+'], regex=True),
  FrameBlacklistCheck('TALB', [r'\[\+digital booklet\]'], regex=True),
  FrameBlacklistCheck('TPE2', ['Various', 'Assorted'], regex=False, fix=ApplyValue('TPE2', 'Various Artists')),
  DependentValueCheck('TCMP', '1', 'TPE2', 'Various Artists', fix=ApplyValue('TCMP', '1')),
  FrameConsistencyCheck(['TALB', 'TPE2', 'TOWN', 'TDRL', 'TCMP']),
  FrameAbsentCheck(['PRIV:contentgroup@emusic.com'], fix=StripFrame(['PRIV:contentgroup@emusic.com'])),
  FrameAbsentCheck(['PRIV:Google/StoreId'], fix=StripFrame(['PRIV:Google/StoreId'])),
  FrameAbsentCheck(['PRIV:PeakValue'], fix=StripFrame(['PRIV:PeakValue'])),
  FrameAbsentCheck(['PRIV:www.amazon.com'], fix=StripFrame(['PRIV:www.amazon.com'])),
  FrameBlacklistCheck('TIT2', [metadata_regex], regex=True, fix=MigrateRegex(regex=metadata_regex, from_frame='TIT2', to_frame='TIT3', overwrite=False, match_group=1)),
  Compressed24Tag(fix=UpdateTag()),
])
