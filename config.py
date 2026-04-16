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
        value = value.strip()

        if value and value[0] not in {'"', "'"}:
            comment_index = value.find(" #")
            if comment_index != -1:
                value = value[:comment_index].rstrip()

        value = value.strip('"').strip("'")
        os.environ[key] = value


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


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
    ollama_system_prompt: str = os.getenv("VA_OLLAMA_SYSTEM_PROMPT", "")

    piper_executable: str = os.getenv("VA_PIPER_BIN", "piper")
    piper_model_path: str = os.getenv(
        "VA_PIPER_MODEL",
        str(Path("models") / "en_US-lessac-medium.onnx"),
    )
    piper_config_path: str | None = os.getenv("VA_PIPER_CONFIG")

    pi_play_url: str = os.getenv("VA_PI_PLAY_URL", "http://jmalpi.local:5000/play")
    pi_play_timeout_sec: int = int(os.getenv("VA_PI_PLAY_TIMEOUT", "120"))
    pi_ws_enabled: bool = _env_bool("VA_PI_WS_ENABLED", False)
    pi_ws_url: str = os.getenv("VA_PI_WS_URL", "")
    pi_ws_timeout_sec: int = int(os.getenv("VA_PI_WS_TIMEOUT", "15"))

    playback_backend: str = os.getenv("VA_PLAYBACK_BACKEND", "sounddevice")
    ffplay_executable: str = os.getenv("VA_FFPLAY_BIN", "ffplay")

    def chunk_size(self) -> int:
        return int(self.sample_rate * self.chunk_duration_ms / 1000)
