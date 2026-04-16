from __future__ import annotations

import traceback

import torch

from audio.recorder import VoiceRecorder
from config import AssistantConfig
from llm.ollama_client import OllamaClient
from stt.whisper_engine import WhisperEngine
from tts.piper_engine import PiperEngine
from vad.silero_vad import SileroVAD


def main() -> None:
    cfg = AssistantConfig()
    
    # Diagnostics: show loaded config
    print("[config] Loaded settings:")
    print(f"  Whisper: {cfg.whisper_model_size} on {cfg.whisper_device} ({cfg.whisper_compute_type})")
    print(f"  Ollama: {cfg.ollama_model} at {cfg.ollama_url}")
    print(f"  System prompt enabled: {bool(cfg.ollama_system_prompt.strip())}")
    print(f"  Piper: {cfg.piper_executable} with model {cfg.piper_model_path}")
    print(f"  Pi playback: {cfg.pi_play_url} (timeout {cfg.pi_play_timeout_sec}s)")
    print(f"  Pi websocket: enabled={cfg.pi_ws_enabled} url={cfg.pi_ws_url or '(not set)'}")
    print()
    
    if cfg.whisper_device.lower() == "cuda" and not torch.cuda.is_available():
        print("[warn] CUDA requested but not available. Falling back to CPU int8 for faster-whisper.")
        cfg.whisper_device = "cpu"
        cfg.whisper_compute_type = "int8"

    chunk_size = cfg.chunk_size()

    print("Loading Silero VAD...")
    vad = SileroVAD(sample_rate=cfg.sample_rate, threshold=cfg.vad_threshold)

    print("Loading faster-whisper model...")
    stt = WhisperEngine(
        model_size=cfg.whisper_model_size,
        device=cfg.whisper_device,
        compute_type=cfg.whisper_compute_type,
        language=cfg.whisper_language,
    )

    print("Connecting to Ollama...")
    llm = OllamaClient(
        url=cfg.ollama_url,
        model=cfg.ollama_model,
        keep_alive=cfg.ollama_keep_alive,
        timeout_sec=cfg.ollama_timeout_sec,
        system_prompt=cfg.ollama_system_prompt,
    )

    print("Loading Piper TTS...")
    tts = PiperEngine(
        model_path=cfg.piper_model_path,
        executable=cfg.piper_executable,
        config_path=cfg.piper_config_path,
        remote_play_url=cfg.pi_play_url,
        remote_timeout_sec=cfg.pi_play_timeout_sec,
        remote_ws_enabled=cfg.pi_ws_enabled,
        remote_ws_url=cfg.pi_ws_url,
        remote_ws_timeout_sec=cfg.pi_ws_timeout_sec,
        playback_backend=cfg.playback_backend,
        ffplay_executable=cfg.ffplay_executable,
    )

    recorder = VoiceRecorder(
        sample_rate=cfg.sample_rate,
        chunk_size=chunk_size,
        vad=vad,
        start_speech_chunks=cfg.start_speech_chunks,
        end_silence_chunks=cfg.end_silence_chunks,
        pre_speech_chunks=max(1, int(cfg.pre_speech_seconds * cfg.sample_rate / chunk_size)),
        min_speech_chunks=max(1, int(cfg.min_speech_seconds * cfg.sample_rate / chunk_size)),
        max_utterance_chunks=max(1, int(cfg.max_utterance_seconds * cfg.sample_rate / chunk_size)),
    )

    print(f"Warming up {cfg.ollama_model} in Ollama...")
    try:
        llm.warmup()
    except Exception as exc:
        print(f"[warn] LLM warmup failed: {exc}")

    print("Assistant is live. Speak naturally. Press Ctrl+C to stop.")

    recorder.start()
    try:
        while True:
            audio = recorder.listen_for_utterance()
            if audio.size == 0:
                continue

            print("[user] transcribing...")
            user_text = stt.transcribe(audio)
            if not user_text:
                print("[user] (no transcription)")
                continue

            print(f"[user] {user_text}")
            if user_text.lower().strip() in {"exit", "quit", "stop assistant"}:
                print("Stopping assistant.")
                break

            print("[assistant] thinking...")
            reply = llm.generate(user_text)
            if not reply:
                reply = "I did not generate a response."
            print(f"[assistant] {reply}")

            try:
                tts.speak(reply)
            except Exception as exc:
                print(f"[warn] TTS/playback failed: {exc}")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception:
        print("[error] Unhandled exception in assistant loop:")
        traceback.print_exc()
    finally:
        recorder.stop()


if __name__ == "__main__":
    main()
