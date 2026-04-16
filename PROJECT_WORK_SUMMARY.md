# IA_Companion Project Summary

## 1. Project Purpose

This repository is a local voice assistant pipeline that captures microphone audio, detects speech, transcribes speech to text, generates an answer from a local/hosted Ollama model, converts the answer to speech, and plays it through a Raspberry Pi speaker endpoint.

Primary runtime path:

Microphone -> VAD -> STT -> LLM -> TTS -> Raspberry Pi playback

## 2. High-Level Architecture

- `assistant.py` is the main orchestrator.
- `audio/recorder.py` captures real-time microphone audio and segments utterances using VAD signals.
- `vad/silero_vad.py` computes speech probability from audio chunks.
- `stt/whisper_engine.py` transcribes audio with faster-whisper.
- `llm/ollama_client.py` sends prompt requests to Ollama `/api/generate`.
- `tts/piper_engine.py` generates WAV audio with Piper and plays remotely (WebSocket preferred, HTTP fallback) or locally.
- `utils/audio_utils.py` provides conversion and local playback helpers.
- `config.py` loads `.env` and centralizes runtime settings in `AssistantConfig`.
- `listen.py` is a separate diagnostic script that continuously prints sensor data from the Raspberry Pi GPIO endpoint.

## 3. File-by-File Behavior

### `assistant.py`

Responsibilities:
- Loads `AssistantConfig`.
- Prints startup diagnostics.
- Initializes VAD, STT, LLM, TTS, and recorder.
- Warms up the LLM.
- Runs the main conversation loop:
  - record utterance
  - transcribe
  - generate reply
  - synthesize/play speech

Recent implementation added gyro level control:
- Orientation-driven mode mapping (`front`, `left`, `right`, `back`).
- Background polling thread for `gyro_orientation`.
- Spoken level announcements and rules playback when orientation changes.
- LLM kept in stable general STEM mode (no per-face prompt switching).
- TTS lock to avoid overlapping speech between assistant replies and level announcements.

### `config.py`

Responsibilities:
- Parses `.env` manually via `_load_dotenv`.
- Exposes typed runtime settings through `AssistantConfig` dataclass.
- Converts bool-like strings through `_env_bool`.

Recent implementation added:
- `VA_GYRO_URL`
- `VA_GYRO_POLL_INTERVAL`
- `VA_GYRO_TIMEOUT`

### `llm/ollama_client.py`

Responsibilities:
- HTTP client wrapper for Ollama generate endpoint.
- Supports optional system prompt and warmup.

Recent implementation added:
- Thread lock protection so prompt access and generation remain concurrency-safe.

### `audio/recorder.py`

Responsibilities:
- Opens input stream with `sounddevice`.
- Buffers chunks into queue.
- Uses VAD results to detect utterance start/end.
- Returns one concatenated utterance at a time.

### `stt/whisper_engine.py`

Responsibilities:
- Initializes `WhisperModel`.
- Transcribes waveform arrays using low-latency settings (`beam_size=1`, `temperature=0.0`, etc.).

### `vad/silero_vad.py`

Responsibilities:
- Loads Silero VAD via torch hub.
- Computes speech probability on fixed-size windows.
- Provides threshold-based speech decision.

### `tts/piper_engine.py`

Responsibilities:
- Calls Piper executable to produce WAV.
- Sends WAV to Raspberry Pi over WebSocket if enabled.
- Falls back to HTTP POST if WebSocket fails.
- Falls back to local playback if no remote endpoint configured.
- Removes temp audio file after each utterance.

### `utils/audio_utils.py`

Responsibilities:
- Audio type conversion between int16 and float32.
- Optional mono conversion.
- Local playback using `sounddevice` or `ffplay`.

### `listen.py`

Responsibilities:
- Polls Raspberry Pi endpoint (`/gpio`) repeatedly.
- Prints `buttons`, `lights`, `gyro_orientation`, `raw_velocity`.
- Useful for validating orientation values and sensor transport.

## 4. What We Implemented in This Session

### 4.1 Real-time Face Announcements by Gyro Orientation

Implemented a face-to-level mapping:
- `front` -> Logic Gate activation + Logic Gates rules
- `right` -> Mirror activation + Reflection rules
- `back` -> silent
- `left` -> silent

Behavior on face/orientation change:
1. Detect new orientation from Pi endpoint.
2. Select corresponding level profile.
3. Speak message via TTS only for `front` and `right`.

### 4.2 Stable Assistant Prompt Strategy

The LLM remains in one general STEM assistant mode regardless of orientation.

Orientation changes now affect spoken gameplay guidance only, while AI Q&A behavior remains stable.

### 4.3 Concurrency Safety Improvements

Added synchronization:
- TTS speech calls are protected by lock to avoid simultaneous playback collisions.
- LLM request path remains lock-safe for concurrent access patterns.

### 4.4 Environment Configuration Updates

Updated both local and example environment files to include gyro controls:
- `VA_GYRO_URL`
- `VA_GYRO_POLL_INTERVAL`
- `VA_GYRO_TIMEOUT`

This keeps runtime config and template aligned.

## 5. Environment and Dependency Snapshot

Dependencies in `requirements.txt`:
- faster-whisper
- torch
- torchaudio
- sounddevice
- numpy
- requests
- scipy
- websocket-client

Current `.env` indicates:
- Whisper on CPU/int8
- Ollama model set to `qwen3.5:cloud`
- Pi playback via WebSocket enabled
- Gyro endpoint set to `http://10.32.33.98:6000/gpio`
- LLM system prompt configured for general STEM assistance

## 6. How to Verify the New Gyro-Level Feature

1. Ensure Raspberry Pi endpoint at `VA_GYRO_URL` returns JSON with key `gyro_orientation` and values among `front/left/right/back`.
2. Start assistant:
   - `python assistant.py` (inside your virtual environment).
3. Rotate device to another face.
4. Confirm expected behavior:
   - Console logs mode switch.
   - Assistant speaks the face-specific level/rules message.
   - AI remains available for general STEM questions.

## 7. Current Known Limitations

- Gameplay rules are implemented as spoken guidance only; no in-process game state machine is enforced yet.
- If gyro endpoint temporarily fails, warnings are printed and polling continues.
- `README.md` still describes the baseline architecture and does not yet document all gyro level details (this summary does).

## 8. Suggested Next Improvements

- Add debounce/stability logic (e.g., require orientation to remain stable for N samples) to reduce accidental mode flips.
- Add a lightweight health endpoint checker at startup for gyro URL and Pi playback URL.
- Add tests for orientation normalization, mapping, and announcement correctness.
