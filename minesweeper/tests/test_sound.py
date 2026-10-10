"""
Name: test_sound.py
Function: Verify the synthesized sound buffers and the SoundManager result mapping.
Inputs: None
Outputs: None
External sources: none (original test code)
Authors: Rijul Poudel
Date Created: 10/10/2026
"""

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sound import SoundManager, _buffers, _stereo


class SoundTests(unittest.TestCase):
    def test_buffers_synthesized(self):
        buffers = _buffers()
        self.assertEqual(set(buffers), {"reveal", "flag", "explosion", "win", "music"})
        for name, mono in buffers.items():
            self.assertGreater(len(mono), 0, name)
            self.assertEqual(len(_stereo(mono)), 2 * len(mono), name)

    def test_result_mapping_and_mute(self):
        sound = SoundManager()
        if not sound.available:
            self.skipTest("no audio device")
        for action, result in (("reveal", "changed"), ("flag", "changed"),
                               ("reveal", "won"), ("reveal", "lost")):
            sound.play_result(action, result)  # must never raise
        sound.play_result("reveal", "no_change")  # rejected actions stay silent
        sound.start_music()
        self.assertTrue(sound.music_channel.get_busy())
        sound.toggle_mute()
        self.assertTrue(sound.muted)
        self.assertFalse(sound.music_channel.get_busy())
        sound.toggle_mute()
        self.assertTrue(sound.music_channel.get_busy())


if __name__ == "__main__":
    unittest.main()
