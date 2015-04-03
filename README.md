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

This example just does a few very basic checks: that every ID3 tag it finds is in v2.4 (the latest version, supported by most MP3 software), and that there's a title for the song (in MP3 terms, that the `TIT2` frame exists). Chances are your album will pass these tests; if it doesn't, you might see something like this:

```
$ ~/mp3md/mp3md/examples/minimal.py -r .
./01 - Some Artist - Some Song.mp3:
 ERROR: Frame version too old: (2, 3, 0)
 ERROR: Required frame TIT2 missing
```

Any time you see `ERROR` in the output, a track is unable to be repaired. Some fixes can be auto-repaired; some, of course, can't (mp3md has no way of knowing what the missing title should be, for example). Let's try auto-fix mode and see what happens; add the `-f` flag to try to fix any problems encountered:

```
$ ~/mp3md/mp3md/examples/minimal.py -r -f .
./01 - Some Artist - Some Song.mp3:
 WARNING: Frame version too old: (2, 3, 0)
 FIX: Updated tag to v2.4
 ERROR: Required frame TIT2 missing
```

We can see now that the 'Frame version' message is now only a `WARNING`, not an `ERROR`; that's nothing wrong with the track that we can't fix automatically. And, indeed, immediately afterwards we see a `FIX` message showing that we succeeded in fixing the tag version problem (by migrating the tag to v2.4). The `TIT2` message, though, remains an `ERROR`; we can't fix this automatically. You'll need to use your favourite MP3 tagging software to fix this (Mutagen, which we installed earlier, actually includes a command-line tool, `mid3v2`, which you might find useful: in this case, `~/mp3md/mutagen/tools/mid3v2 --TIT2="Some Song" "01 - Some Artist - Some Song.mp3"` would work nicely!).

