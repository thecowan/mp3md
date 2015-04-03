#!/usr/bin/python
from mp3md import *

# An extremely simple example instance of mp3md.
# Performs only 2 basic checks:
#   * file must have a version 2.4 IDv3 tag
#   * TIT2 frame (song title) must exist.
# If run in fix mode (with -f), the first will be automatically repaired.
# (The second obviously cannot be fixed automatically).
runchecks([
  TagVersionCheck(fix=UpdateTag()),
  FramePresentCheck(['TIT2']),
])
