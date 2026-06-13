#!/usr/bin/env python3
import math
import os
import random
import struct
import wave


SAMPLE_RATE = 44100
BPM = 82
BEAT = 60 / BPM
BARS = 8
DURATION = BARS * 4 * BEAT


def midi_to_freq(note):
    return 440.0 * (2 ** ((note - 69) / 12))


def clamp(value, low=-1.0, high=1.0):
    return max(low, min(high, value))


def envelope(t, duration, attack=0.02, release=0.16):
    if t < 0 or t > duration:
        return 0.0
    attack_gain = min(1.0, t / max(attack, 0.001))
    release_gain = min(1.0, (duration - t) / max(release, 0.001))
    return max(0.0, min(attack_gain, release_gain))


def add_note(left, right, freq, start, duration, gain, instrument, pan=0.0):
    start_i = max(0, int(start * SAMPLE_RATE))
    end_i = min(len(left), int((start + duration) * SAMPLE_RATE))
    left_gain = gain * math.sqrt((1 - pan) / 2)
    right_gain = gain * math.sqrt((1 + pan) / 2)

    for i in range(start_i, end_i):
        t = i / SAMPLE_RATE - start
        env = envelope(t, duration, instrument["attack"], instrument["release"])
        phase = 2 * math.pi * freq * t
        vibrato = math.sin(2 * math.pi * instrument.get("vibrato_rate", 0) * t)
        vib_freq = freq * (1 + instrument.get("vibrato_depth", 0) * vibrato)
        vib_phase = 2 * math.pi * vib_freq * t

        if instrument["type"] == "flute":
            sample = (
                math.sin(vib_phase)
                + 0.18 * math.sin(2 * vib_phase)
                + 0.06 * math.sin(3 * vib_phase)
            ) * env
        elif instrument["type"] == "pluck":
            decay = math.exp(-t * instrument.get("decay", 4.0))
            sample = (
                math.sin(phase)
                + 0.42 * math.sin(2 * phase)
                + 0.22 * math.sin(3 * phase)
            ) * env * decay
        elif instrument["type"] == "bell":
            decay = math.exp(-t * instrument.get("decay", 3.6))
            mod = math.sin(2 * math.pi * freq * 1.52 * t) * 2.3
            sample = (
                math.sin(phase + mod)
                + 0.24 * math.sin(2.01 * phase)
            ) * env * decay
        elif instrument["type"] == "bass":
            sample = (
                math.sin(phase)
                + 0.16 * math.sin(2 * phase)
            ) * env
        else:
            sample = (
                math.sin(phase)
                + 0.3 * math.sin(2 * phase)
                + 0.12 * math.sin(0.5 * phase)
            ) * env

        left[i] += sample * left_gain
        right[i] += sample * right_gain


def add_shaker(left, right, start, duration, gain, pan=0.0):
    rng = random.Random(int(start * 1000))
    start_i = max(0, int(start * SAMPLE_RATE))
    end_i = min(len(left), int((start + duration) * SAMPLE_RATE))
    left_gain = gain * math.sqrt((1 - pan) / 2)
    right_gain = gain * math.sqrt((1 + pan) / 2)

    for i in range(start_i, end_i):
        t = i / SAMPLE_RATE - start
        env = envelope(t, duration, 0.002, duration * 0.8)
        sample = (rng.random() * 2 - 1) * env * math.exp(-t * 18)
        left[i] += sample * left_gain
        right[i] += sample * right_gain


def add_soft_drum(left, right, start, gain):
    start_i = max(0, int(start * SAMPLE_RATE))
    duration = 0.28
    end_i = min(len(left), int((start + duration) * SAMPLE_RATE))
    for i in range(start_i, end_i):
        t = i / SAMPLE_RATE - start
        freq = 94 - 42 * min(1, t / duration)
        phase = 2 * math.pi * freq * t
        env = math.exp(-t * 9)
        sample = math.sin(phase) * env * gain
        left[i] += sample * 0.58
        right[i] += sample * 0.58


def add_delay(left, right, delay_seconds=0.29, feedback=0.18):
    delay = int(delay_seconds * SAMPLE_RATE)
    for i in range(delay, len(left)):
        left[i] += right[i - delay] * feedback
        right[i] += left[i - delay] * feedback


def smooth_loop(left, right, fade_seconds=0.8):
    fade = int(fade_seconds * SAMPLE_RATE)
    total = len(left)
    for i in range(fade):
        in_gain = i / fade
        out_gain = (fade - i) / fade
        left[i] *= in_gain
        right[i] *= in_gain
        left[total - 1 - i] *= out_gain
        right[total - 1 - i] *= out_gain


def normalize(left, right, peak=0.86):
    current = max(max(abs(x) for x in left), max(abs(x) for x in right), 0.001)
    scale = peak / current
    for i in range(len(left)):
        left[i] = clamp(left[i] * scale)
        right[i] = clamp(right[i] * scale)


def write_wav(path, left, right):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = []
        for l_sample, r_sample in zip(left, right):
            frames.append(struct.pack("<hh", int(l_sample * 32767), int(r_sample * 32767)))
        wav.writeframes(b"".join(frames))


def build_track(path, root, scale, melody, chord_degrees, bell_offset=12):
    total_samples = int(DURATION * SAMPLE_RATE)
    left = [0.0] * total_samples
    right = [0.0] * total_samples

    flute = {
        "type": "flute",
        "attack": 0.09,
        "release": 0.28,
        "vibrato_rate": 5.1,
        "vibrato_depth": 0.003,
    }
    pluck = {"type": "pluck", "attack": 0.006, "release": 0.2, "decay": 3.9}
    bell = {"type": "bell", "attack": 0.003, "release": 0.75, "decay": 2.8}
    pad = {"type": "pad", "attack": 0.9, "release": 1.2}
    bass = {"type": "bass", "attack": 0.18, "release": 0.5}

    for bar in range(BARS):
        bar_start = bar * 4 * BEAT
        degree = chord_degrees[bar % len(chord_degrees)]
        chord = [
            root + scale[degree % len(scale)] - 12,
            root + scale[(degree + 2) % len(scale)],
            root + scale[(degree + 4) % len(scale)],
        ]
        for note in chord:
            add_note(left, right, midi_to_freq(note), bar_start, 4 * BEAT, 0.09, pad, pan=-0.2)
            add_note(left, right, midi_to_freq(note + 12), bar_start + 0.08, 3.8 * BEAT, 0.035, pad, pan=0.28)
        add_note(left, right, midi_to_freq(chord[0] - 12), bar_start, 3.9 * BEAT, 0.11, bass)

    step = BEAT / 2
    for idx, degree in enumerate(melody):
        start = idx * step
        note = root + scale[degree % len(scale)] + 12
        duration = step * (1.75 if idx % 4 == 3 else 1.05)
        add_note(left, right, midi_to_freq(note), start, duration, 0.13, flute, pan=-0.12)

        if idx % 2 == 0:
            add_note(
                left,
                right,
                midi_to_freq(note + bell_offset),
                start + 0.03,
                step * 1.7,
                0.045,
                bell,
                pan=0.34,
            )

        arp_note = root + scale[(degree + 2) % len(scale)]
        add_note(left, right, midi_to_freq(arp_note), start + step * 0.5, step * 1.35, 0.075, pluck, pan=0.22)

    for beat in range(BARS * 4):
        start = beat * BEAT
        if beat % 4 in (0, 2):
            add_soft_drum(left, right, start, 0.115)
        add_shaker(left, right, start + BEAT * 0.5, 0.13, 0.026, pan=-0.35 if beat % 2 else 0.35)

    add_delay(left, right)
    smooth_loop(left, right)
    normalize(left, right)
    write_wav(path, left, right)


def main():
    tracks = [
        (
            "audio/vietnam.wav",
            57,
            [0, 2, 4, 7, 9],
            [0, 1, 2, 4, 3, 2, 1, 0, 2, 4, 5, 4, 2, 1, 0, 1] * 2,
            [0, 2, 3, 1],
            12,
        ),
        (
            "audio/thailand.wav",
            60,
            [0, 2, 4, 7, 9],
            [2, 3, 4, 6, 5, 4, 3, 2, 4, 6, 7, 6, 4, 3, 2, 3] * 2,
            [0, 1, 3, 2],
            19,
        ),
        (
            "audio/japan.wav",
            57,
            [0, 2, 3, 7, 9],
            [0, 2, 3, 4, 3, 2, 0, 1, 2, 4, 5, 4, 3, 2, 0, 2] * 2,
            [0, 2, 1, 3],
            12,
        ),
    ]

    for args in tracks:
        build_track(*args)


if __name__ == "__main__":
    main()
