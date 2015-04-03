# ![mp3md](resources/mp3md-sm.png)

## Introduction 

mp3md is an MP3 'sanity checker', which runs a series of pre-defined (but customisable) checks against 
an MP3 collection. This can be used by the anal-retentive (like the author) to ensure that their MP3
collection is consistently tagged to a high quality.

Where possible, fixes can be automatically applied, so you don't even have to tidy things up yourself!

### Examples 

Some examples of some rules that can be enforced:

* no extraneous tags (for example, remove all the rights-enforcement tags associated with MP3s 
purchased from Amazon or eMusic)
* certain tags must be consistently applied (so, for example, all MP3s in a given directory 
have the exact same 'TALB' (Album name) or 'TCON' (genre))
* ensure that every MP3 has an embedded artwork (APIC) tag

## Getting Started

### Prerequisites

mp3md depends on the [mutagen](https://bitbucket.org/lazka/mutagen) project for reading IDv2 tags from MP3 files, so you'll need to grab the source for that too.

A minimal set of steps might look like:

* Install [Mercurial](http://mercurial.selenic.com/) and [Git](http://git-scm.com/) for your platform. On Ubuntu, `sudo apt-get install mercurial git`
* Grab the source code of the two projects: 

```
mkdir ~/mp3md
cd ~/mp3md
git clone https://github.com/funkwit/mp3md.git
hg clone https://bitbucket.org/lazka/mutagen
```

* Set up your `PYTHONPATH`, so mp3md can find Mutagen and its own libraries:

```
export PYTHONPATH=~/mp3md:$PYTHONPATH
```

* You're now ready to run mp3md! 

### First run

To actually repair your MP3 files, you need to write your own script which specifies the rules you wish to apply to your MP3 collection. To get you started, there are a few example files in the `examples` subdirectory.

Try the minimal example (this won't change any of your files!):

```
cd /PATH/TO/AN/MP3/ALBUM/
~/mp3md/mp3md/examples/minimal.py -r .
```

This example just does a few very basic checks: that every ID3 tag it finds uses version 2.4 (the latest version, supported by most MP3 software), and that there's a title for the song (in MP3 terms, that the `TIT2` frame exists). Chances are your album will pass these tests; if it doesn't, you might see something like this:

```
$ ~/mp3md/mp3md/examples/minimal.py -r .
./01 - Some Artist - Some Song.mp3:
 ERROR: Frame version too old: (2, 3, 0)
 ERROR: Required frame TIT2 missing
```

Any time you see `ERROR` in the output, a track is unable to be repaired. Some fixes can be made automatically; some, of course, can't (mp3md has no way of knowing what the missing title should be, for example). Let's try auto-fix mode and see what happens; just add the `-f` flag to try to fix any problems encountered:

```
$ ~/mp3md/mp3md/examples/minimal.py -r -f .
./01 - Some Artist - Some Song.mp3:
 WARNING: Frame version too old: (2, 3, 0)
 FIX: Updated tag to v2.4
 ERROR: Required frame TIT2 missing
```

We can see now that the 'frame version' message is now only a `WARNING`, not an `ERROR`; that's nothing wrong with the track that we can't fix automatically. And, indeed, immediately afterwards we see a `FIX` message showing that we succeeded in fixing the tag version problem (by migrating the tag to v2.4). The `TIT2` message, though, remains an `ERROR`; we can't fix this automatically. You'll need to use your favourite MP3 tagging software to fix this (Mutagen, which we installed earlier, actually includes a command-line tool, `mid3v2`, which you might find useful: in this case, 

```
~/mp3md/mutagen/tools/mid3v2 --TIT2="Some Song" \
  "01 - Some Artist - Some Song.mp3"` 
```  

would work nicely).

## Writing a configuration

### A simple configuration

To use mp3md in anger, you'll want to set up your own configuration file. You can use any of the files in the `examples` subdirectory as a template. The configuration file is just Python code, which sets up a list of checks (anything in `mp3md.py` which extends the `Check` class). For example, let's look at the non-comment lines of `minimal.py`:

```
#!/usr/bin/python
from mp3md import *
runchecks([
  TagVersionCheck(fix=UpdateTag()),
  FramePresentCheck(['TIT2']),
])
```

The first three lines, and the last, are boilerplate. What we care about is lines 4 & 5: the lines which specify the checks to be run.

There are 2 types of checks in `mp3md.py`: those which are self-fixing (these extend both `Check` and `Fix`), and those which require an instance of the `Fix` class to be supplied in their constructor. `TagVersionCheck` is an example of the former. If we just had the line

```TagVersionCheck()```

then there would be no fix, so the check would be of "Error" severity if found during a fix run (one with the `-f` flag set). By adding `fix=UpdateTag()`, we're supplying an instance of a `Fix` class which will be used to fix the problem.

When running with `-f`, the `TagVersionCheck` will be run across each file. If every file passes the check (has an ID3 tag version >= 2.4.0), then nothing else will happen. Every time a file fails the check, the `Fix` object (in this case, `UpdateTag`) will attempt to fix the problem (in this case, but updating the tag). After this, the `Check` is run again. If it fails the second time, then that is an `Error` (because the `Fix` didn't work).

### A more complex configuration

To see a more complex example of what mp3md can do, have a look at `examples/complex.py`. This is a stripped-down version the author's own configuration, and uses a number of the more complex `Checks` and `Fixes`. To look at some individual examples:

```
FramePresentCheck(['TIT2', 'TPE1', 'APIC', 'TALB', 'TOWN', 'TRCK', 'TDRC']),
```

This checks that all of the frames specified (Song title, Artist, Picture, Album, File owner/Licensee, Track #, and Recording Date) exist. These is no fix for this, as this information would obviously need to be sourced from elsewhere.

```
FramePresentCheck(['TPE2'], fix=ApplyCommonValue(source='TPE1', target='TPE2', outliers=1)),
```

This is a more complex example; in this case, we are checking if the frame 'TPE2' (used by most MP3 software as 'Album artist') is present. If it's not, we apply a fix: `ApplyCommonValue`, which will take the value from 'TPE1' (Artist), and put it into 'TPE2', if and only if it's mostly consistent across the entire folder (all values for all MP3s in the album are the same, with one outlier permitted). This means that if all tracks have TPE1="Spice Girls", then that will be copied into TPE2. One value that's *not* "Spice Girls" will be permitted: for example, one track by "Spice Girls featuring Metallica" would not block the copy. More than one, however, would leave it to be manually resolves.

```
FrameBlacklistCheck('TPE2', ['Various', 'Assorted'], regex=False, fix=ApplyValue('TPE2', 'Various Artists')),
```

A `FrameBlacklistCheck` makes sure the value for a frame isn't in a list of banned values. In this case, `Various` and `Assorted` (commonly used by Amazon) are banned from "Album Artist"; if found, they'll be replaced with `Various Artists` for consistency with the rest of the collection.

```
FrameAbsentCheck(['PRIV:contentgroup@emusic.com'], fix=StripFrame(['PRIV:contentgroup@emusic.com'])),
```

A `FrameAbsentCheck` does much what you'd expect: makes sure the given frame doesn't exist. This example is checking for the `PRIV:contentgroup@emusic.com` frame, used by eMusic to record copyright information. If found, it will be stripped out.

```
MutualPresenceCheck(['TOAL', 'TOPE', 'TDOR']),
```

This test makes sure that if any of `TOAL` (Original Album), `TOPE` (Original Artist), and `TDOR` (Original Release) are specified, they *all* are. This ensures that information for songs maked as covers are consistent.

```
FrameConsistencyCheck(['TALB', 'TPE2', 'TOWN', 'TDRL', 'TCMP']),
```

This ensures that the values for the specified frames (e.g. Album name and Album artist) are the same for all files in a folder (that is, all tracks in an album).

```
FrameWhitelistCheck('TCON', ['Rock', 'Audiobook', 'Alternative' ... ]),
```

The opposite of a `FrameBlacklistCheck`; this ensures that *only* the specified values are valid values for the TCON (Genre) frame. Any other values will be rejected.

```
TrailingArtistCheck(),
```

One of the more complex checks, the `TrailingArtistCheck` looks for the Artist name appearing at the end of the track name. For example, for the Artist (TPE1) "Spice Girls", this check would fail (and attempt to fix) the track name (TIT2) "Wannabe - Spice Girls". This is common on compliation albums purchased from some sources.