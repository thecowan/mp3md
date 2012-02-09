#!/usr/bin/python

import unittest
import mp3md

class RecordingCheck(mp3md.Check):
  def __init__(self):
    self.dirs = []
    self.fix=None
    
  def run_check(self, directory, files, severity, errors):
    self.dirs.append(directory)
    self.severity = severity

  
class TestDoctor(unittest.TestCase):
  def test_checks_single_dir(self):
    recorder = RecordingCheck()
    mp3md.Doctor([recorder]).checkup("testdata/", recursive=False, fix=False)
    self.assertEqual(recorder.dirs, ["testdata/"])

if __name__ == '__main__':
    unittest.main()
