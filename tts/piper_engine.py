from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from utils.audio_utils import play_wav_file


class PiperEngine:
    def __init__(
        self,
        model_path: str,
        executable: str = "piper",
        config_path: str | None = None,
        playback_backend: str = "sounddevice",
        ffplay_executable: str = "ffplay",
    ) -> None:
        self.executable = executable
        self.model_path = model_path
        self.config_path = config_path
        self.playback_backend = playback_backend
        self.ffplay_executable = ffplay_executable

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
            play_wav_file(
                wav_path,
                backend=self.playback_backend,
                ffplay_executable=self.ffplay_executable,
            )
        finally:
            Path(wav_path).unlink(missing_ok=True)
