from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io import wavfile


def int16_to_float32(audio: np.ndarray) -> np.ndarray:
    return audio.astype(np.float32) / 32768.0


def float32_to_int16(audio: np.ndarray) -> np.ndarray:
    audio = np.clip(audio, -1.0, 1.0)
    return (audio * 32767.0).astype(np.int16)


def ensure_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio
    return np.mean(audio, axis=1, dtype=np.float32)


def play_wav_file(
    wav_path: str | Path,
    backend: str = "sounddevice",
    ffplay_executable: str = "ffplay",
) -> None:
    wav_path = str(wav_path)
    if backend == "ffplay":
        subprocess.run(
            [
                ffplay_executable,
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "error",
                wav_path,
            ],
            check=True,
        )
        return

    sample_rate, audio = wavfile.read(wav_path)
    sd.play(audio, sample_rate)
    sd.wait()
