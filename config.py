from dataclasses import dataclass
from pathlib import Path
import os


def _load_dotenv(dotenv_path: str = ".env") -> None:
    path = Path(dotenv_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


@dataclass(slots=True)
class AssistantConfig:
    sample_rate: int = int(os.getenv("VA_SAMPLE_RATE", "16000"))
    channels: int = 1
    chunk_duration_ms: int = int(os.getenv("VA_CHUNK_MS", "32"))

    vad_threshold: float = float(os.getenv("VA_VAD_THRESHOLD", "0.5"))
    start_speech_chunks: int = int(os.getenv("VA_START_CHUNKS", "2"))
    end_silence_chunks: int = int(os.getenv("VA_END_SILENCE_CHUNKS", "20"))
    min_speech_seconds: float = float(os.getenv("VA_MIN_SPEECH_SEC", "0.3"))
    max_utterance_seconds: float = float(os.getenv("VA_MAX_UTTERANCE_SEC", "20"))
    pre_speech_seconds: float = float(os.getenv("VA_PRE_SPEECH_SEC", "0.4"))

    whisper_model_size: str = os.getenv("VA_WHISPER_MODEL", "small")
    whisper_device: str = os.getenv("VA_WHISPER_DEVICE", "cpu")
    whisper_compute_type: str = os.getenv("VA_WHISPER_COMPUTE", "int8")
    whisper_language: str | None = os.getenv("VA_WHISPER_LANG")

    ollama_url: str = os.getenv("VA_OLLAMA_URL", "http://localhost:11434/api/generate")
    ollama_model: str = os.getenv("VA_OLLAMA_MODEL", "tinyllama")
    ollama_keep_alive: str = os.getenv("VA_OLLAMA_KEEP_ALIVE", "30m")
    ollama_timeout_sec: int = int(os.getenv("VA_OLLAMA_TIMEOUT", "90"))

    piper_executable: str = os.getenv("VA_PIPER_BIN", "piper")
    piper_model_path: str = os.getenv(
        "VA_PIPER_MODEL",
        str(Path("models") / "en_US-lessac-medium.onnx"),
    )
    piper_config_path: str | None = os.getenv("VA_PIPER_CONFIG")

    playback_backend: str = os.getenv("VA_PLAYBACK_BACKEND", "sounddevice")
    ffplay_executable: str = os.getenv("VA_FFPLAY_BIN", "ffplay")

    def chunk_size(self) -> int:
        return int(self.sample_rate * self.chunk_duration_ms / 1000)
