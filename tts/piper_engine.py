from __future__ import annotations

import subprocess
import tempfile
import wave
from pathlib import Path

import requests
import websocket

from utils.audio_utils import play_wav_file


class PiperEngine:
    def __init__(
        self,
        model_path: str,
        executable: str = "piper",
        config_path: str | None = None,
        remote_play_url: str | None = None,
        remote_timeout_sec: int = 30,
        remote_ws_enabled: bool = False,
        remote_ws_url: str | None = None,
        remote_ws_timeout_sec: int = 15,
        playback_backend: str = "sounddevice",
        ffplay_executable: str = "ffplay",
    ) -> None:
        self.executable = executable
        self.model_path = model_path
        self.config_path = config_path
        self.remote_play_url = remote_play_url.strip() if remote_play_url else None
        self.remote_timeout_sec = remote_timeout_sec
        self.remote_ws_enabled = remote_ws_enabled
        self.remote_ws_url = remote_ws_url.strip() if remote_ws_url else None
        self.remote_ws_timeout_sec = remote_ws_timeout_sec
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

            wav_bytes = Path(wav_path).read_bytes()

            if self.remote_ws_enabled and self.remote_ws_url:
                try:
                    ws = websocket.create_connection(
                        self.remote_ws_url,
                        timeout=self.remote_ws_timeout_sec,
                    )
                    try:
                        ws.send_binary(wav_bytes)
                        ack = ws.recv()
                        if isinstance(ack, (bytes, bytearray)):
                            ack_text = ack.decode("utf-8", errors="ignore").strip()
                        else:
                            ack_text = str(ack).strip()

                        if ack_text.lower() != "played":
                            raise RuntimeError(f"Unexpected WS ack: {ack_text}")
                    finally:
                        ws.close()
                    return
                except Exception as exc:
                    print(f"[warn] WebSocket playback failed, falling back to HTTP: {exc}")

            if self.remote_play_url:
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
