"""
Name: sound.py
Function: Synthesize and play the game's sound effects and background music with pygame.mixer (no audio files needed).
Inputs: Action results from the game loop ("changed", "won", "lost") plus the action name, and an S-key mute toggle from main.py.
Outputs: Short sound effects (reveal, flag, explosion, win) and a looping background music track on the pygame audio mixer.
External sources: pygame documentation for mixer usage; Python standard library docs for array, math, random. Sound synthesis written with AI assistance from Hermes Agent (Nous Research).
Authors: Rijul Poudel
Date Created: 10/10/2026
"""

import array
import math
import random

import pygame

SAMPLE_RATE = 22050
MUSIC_CHANNEL = 0


def _square(phase):
    # Square wave from the sign of a sine; cheap and retro sounding.
    return 1.0 if math.sin(phase) >= 0 else -1.0


def _tone(freq, ms, volume=0.3, wave="square"):
    """One mono note with a linear fade-out."""
    length = int(SAMPLE_RATE * ms / 1000)
    mono = array.array("h")
    for i in range(length):
        phase = 2 * math.pi * freq * (i / SAMPLE_RATE)
        value = _square(phase) if wave == "square" else math.sin(phase)
        mono.append(int(32767 * volume * (1 - i / length) * value))
    return mono


def _explosion(ms=420, volume=0.5):
    """Noise burst plus a low thump, for hitting a mine."""
    length = int(SAMPLE_RATE * ms / 1000)
    rng = random.Random(17)  # fixed seed keeps the burst identical every run
    mono = array.array("h")
    for i in range(length):
        fade = (1 - i / length) ** 2
        noise = rng.uniform(-1.0, 1.0) * 0.8
        thump = math.sin(2 * math.pi * 75 * (i / SAMPLE_RATE))
        mono.append(int(32767 * volume * fade * (noise + 0.6 * thump)))
    return mono


def _jingle():
    """Four ascending notes for a win."""
    mono = array.array("h")
    for freq in (523.25, 659.25, 783.99, 1046.50):
        mono.extend(_tone(freq, 120, volume=0.28, wave="sine"))
    return mono


def _music(volume=0.12):
    """A short looping square-wave melody with a bass line."""
    beat_ms = 280
    lead = (220.00, 261.63, 329.63, 392.00,
            329.63, 261.63, 220.00, 220.00,
            196.00, 220.00, 261.63, 220.00,
            196.00, 164.81, 196.00, 196.00)
    bass = (110.00, 110.00, 98.00, 98.00)
    length = int(SAMPLE_RATE * beat_ms / 1000)
    mono = array.array("h")
    for index, freq in enumerate(lead):
        low = bass[index // 4]
        for i in range(length):
            t = i / SAMPLE_RATE
            fade = 1 - (i / length) * 0.5
            value = 0.7 * _square(2 * math.pi * freq * t) + 0.5 * _square(2 * math.pi * low * t)
            mono.append(int(32767 * volume * fade * value))
    return mono


def _buffers():
    """All sounds as raw mono int16 buffers, synthesized once at startup."""
    return {
        "reveal": _tone(660, 55),
        "flag": _tone(990, 40, volume=0.25),
        "explosion": _explosion(),
        "win": _jingle(),
        "music": _music(),
    }


def _stereo(mono):
    """Duplicate a mono buffer for the two-channel mixer."""
    stereo = array.array("h")
    for sample in mono:
        stereo.append(sample)
        stereo.append(sample)
    return stereo


class SoundManager:
    """Play one-shot effects and looping music; runs silently if audio is unavailable."""

    def __init__(self):
        self.available = False
        self.muted = False
        self.sounds = {}
        self.music = None
        self.music_channel = None
        try:
            # Own the mixer format so the raw buffers below always match it.
            pygame.mixer.quit()
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            pygame.mixer.set_reserved(1)  # channel 0 is kept for the music loop
            self.music_channel = pygame.mixer.Channel(MUSIC_CHANNEL)
            buffers = _buffers()
            self.sounds = {name: pygame.mixer.Sound(buffer=_stereo(data))
                           for name, data in buffers.items() if name != "music"}
            self.music = pygame.mixer.Sound(buffer=_stereo(buffers["music"]))
            self.available = True
        except pygame.error:
            # Machines without an audio device still run the game, just silently.
            self.available = False

    def play(self, name):
        """Play one effect sound, if sound is on."""
        if self.available and not self.muted:
            sound = self.sounds.get(name)
            if sound is not None:
                sound.play()

    def play_result(self, action, result):
        """Map a controller result (and the action that caused it) to a sound."""
        if result == "lost":
            self.play("explosion")
        elif result == "won":
            self.play("win")
        elif result == "changed" and action in ("reveal", "flag", "unflag"):
            self.play("reveal" if action == "reveal" else "flag")

    def start_music(self):
        """Start the music loop if sound is on and it is not already playing."""
        if self.available and not self.muted and not self.music_channel.get_busy():
            self.music_channel.play(self.music, loops=-1)

    def toggle_mute(self):
        """Toggle all sound; the music loop stops when muted and resumes when unmuted."""
        if not self.available:
            return
        self.muted = not self.muted
        if self.muted:
            self.music_channel.stop()
        else:
            self.start_music()


def _self_check():
    """Run with `python sound.py`: synthesize every buffer and load it into the mixer."""
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    buffers = _buffers()
    assert set(buffers) == {"reveal", "flag", "explosion", "win", "music"}
    for name, mono in buffers.items():
        assert len(mono) > 0, name
        assert len(_stereo(mono)) == 2 * len(mono), name
        print(f"{name}: {len(mono)} mono samples ({len(mono) / SAMPLE_RATE:.2f}s)")
    pygame.mixer.quit()
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
    for name, mono in buffers.items():
        pygame.mixer.Sound(buffer=_stereo(mono))
    print("mixer accepted all buffers")


if __name__ == "__main__":
    _self_check()
