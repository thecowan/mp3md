#!/usr/bin/python
from mp3md import *

# A simple mp3md instance to make sure files are Sonos-compatible.
# Sonos MP3 parsing fails if version 2.4 ID3 frames are compressed with zlib. Most tagging tools
# don't use zlib compression, but some older ones do. For example, old versions of mutagen
# used to compress frames over a certain size, commonly APIC (attached image) frames.
# If run in fix mode (with -f), any such frames will be automatically rewritten in uncompressed
# mode.
runchecks([
  Compressed24Tag(fix=UpdateTag()),
])
