from __future__ import annotations

import subprocess
import tempfile
import wave
from pathlib import Path

import requests

from utils.audio_utils import play_wav_file


class PiperEngine:
    def __init__(
        self,
        model_path: str,
        executable: str = "piper",
        config_path: str | None = None,
        remote_play_url: str | None = None,
        remote_timeout_sec: int = 30,
        playback_backend: str = "sounddevice",
        ffplay_executable: str = "ffplay",
    ) -> None:
        self.executable = executable
        self.model_path = model_path
        self.config_path = config_path
        self.remote_play_url = remote_play_url.strip() if remote_play_url else None
        self.remote_timeout_sec = remote_timeout_sec
        self.playback_backend = playback_backend
        self.ffplay_executable = ffplay_executable
        self.session = requests.Session()

        if not Path(self.model_path).exists():
            raise FileNotFoundError(
                f"Piper model file not found at: {self.model_path}. "
                "Set VA_PIPER_MODEL to a valid .onnx path."
            )

    def speak(self, text: str) -> None:
        text = text.strip()
        if not text:
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        cmd = [
            self.executable,
            "--model",
            self.model_path,
            "--output_file",
            wav_path,
        ]
        if self.config_path:
            cmd.extend(["--config", self.config_path])

        try:
            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            if self.remote_play_url:
                wav_bytes = Path(wav_path).read_bytes()
                # Your Raspberry Pi server replies only after playback completes,
                # so read timeout must be longer than audio duration.
                with wave.open(wav_path, "rb") as wf:
                    frames = wf.getnframes()
                    sample_rate = wf.getframerate() or 1
                    duration_sec = frames / sample_rate

                read_timeout = max(self.remote_timeout_sec, int(duration_sec) + 10)
                response = self.session.post(
                    self.remote_play_url,
                    data=wav_bytes,
                    headers={"Content-Type": "audio/wav", "Connection": "close"},
                    timeout=(5, read_timeout),
                )
                response.raise_for_status()
                return

            play_wav_file(
                wav_path,
                backend=self.playback_backend,
                ffplay_executable=self.ffplay_executable,
            )
        finally:
            Path(wav_path).unlink(missing_ok=True)
