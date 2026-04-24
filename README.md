# IA Companion: Smart Learning Companion for STEM Education

This project was built for the Smart Learning Companion Challenge in the IEEE Education Society ecosystem. The goal is to make STEM learning more interactive, accessible, and engaging by combining edge AI, real hardware, and immersive visualization.

IA Companion is a portable AI-powered system where students can talk to the assistant, interact with physical sensors, and see cause and effect in a virtual simulation.

## Why This Project Matters

Instead of passive learning, students can perform hands-on experimentation:

- Use real inputs: light sensors, gyroscope orientation, and physical buttons on a Raspberry Pi.
- Ask questions naturally through voice.
- Hear AI explanations in real time.
- See physical actions reflected in a 3D Unreal Engine environment.

This creates a learning loop between physical interaction, AI reasoning, and visual feedback.

## Core System Architecture

### Voice + AI Pipeline

```text
Microphone
  -> Silero VAD (speech detection)
  -> faster-whisper STT
  -> Ollama LLM (local on Pi or remote machine)
  -> Piper TTS (WAV)
  -> Raspberry Pi playback endpoint
  -> Speaker output
```

### Hardware + Simulation Bridge

```text
Raspberry Pi GPIO sensors/buttons
  -> Pi sensor server
  -> WebSocket/HTTP bridge
  -> Unreal Engine interactive scene

AI responses/events
  -> WebSocket events
  -> Virtual experiment reactions
```

This means students can manipulate real hardware and instantly observe the effect inside a virtual experiment.

## Key Features

- AI reasoning with Ollama (local-first, edge-ready).
- Voice interface with Whisper (STT) and Piper (TTS).
- Raspberry Pi sensor integration (light, gyro, buttons).
- GPIO-driven interaction patterns for STEM mini-experiments.
- Unreal Engine integration through WebSockets.
- Flexible deployment: all-local or split across Pi + remote machine.

## What Is Already Done In This Folder

The following setup has already been completed on this machine:

- Python dependencies installed in `.venv`
- Ollama model `tinyllama` pulled
- Whisper `small` model cached by faster-whisper
- Silero VAD model cached by torch hub
- Piper CLI installed in `.venv` (`.venv/Scripts/piper.exe`)
- Piper medium voice files present in `models/`

If you move this project to another machine, follow the full first-time setup below.

## Project Structure

```text
.
|-- README.md
|-- requirements.txt
|-- requirements_pi.txt
|-- config.py
|-- assistant.py
|-- listen.py
|-- audio/
|   |-- recorder.py
|-- stt/
|   |-- whisper_engine.py
|-- vad/
|   |-- silero_vad.py
|-- llm/
|   |-- ollama_client.py
|-- tts/
|   |-- piper_engine.py
|-- utils/
|   |-- audio_utils.py
|-- servers_in_pi/
|   |-- audio_server.py
|   |-- gpio_server.py
|-- models/
|   |-- en_US-lessac-medium.onnx
|   |-- en_US-lessac-medium.onnx.json
```

## First-Time Setup (Any New Machine)

### 1. Install Python 3.10+

- Windows: install from https://www.python.org/downloads/ and enable `Add Python to PATH`
- macOS: `brew install python@3.11`
- Linux (Ubuntu): `sudo apt update && sudo apt install -y python3 python3-venv`

### 2. Create virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install piper-tts
```

### 4. Install Ollama and TinyLlama

Install Ollama from:

- https://ollama.com/download

Then pull model:

```bash
ollama pull tinyllama
```

Verify:

```bash
ollama list
```

You should see `tinyllama`.

### 5. Download Piper medium voice model

Create models folder and download voice files.

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force models | Out-Null
Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -OutFile "models/en_US-lessac-medium.onnx"
Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -OutFile "models/en_US-lessac-medium.onnx.json"
```

macOS/Linux:

```bash
mkdir -p models
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -o models/en_US-lessac-medium.onnx
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -o models/en_US-lessac-medium.onnx.json
```

### 6. Create `.env`

Copy template:

Windows PowerShell:

```powershell
Copy-Item .env.example .env -Force
```

macOS/Linux:

```bash
cp .env.example .env
```

Important defaults in `.env`:

- CPU-first Whisper: `VA_WHISPER_DEVICE=cpu`
- Quantized compute: `VA_WHISPER_COMPUTE=int8`
- TinyLlama endpoint: `VA_OLLAMA_URL=http://localhost:11434/api/generate`
- Piper model paths point to `models/`

Windows users with local venv Piper should set:

```env
VA_PIPER_BIN=.venv/Scripts/piper.exe
```

macOS/Linux users should set:

```env
VA_PIPER_BIN=.venv/bin/piper
```

## Run

From project root:

Windows:

```powershell
.\.venv\Scripts\python.exe assistant.py
```

macOS/Linux:

```bash
.venv/bin/python assistant.py
```

The assistant runs continuously until you press `Ctrl+C`.

During each response, the PC sends raw WAV bytes to your Raspberry Pi endpoint:

- `POST http://jmalpi.local:5000/play`

## Raspberry Pi Services (Optional Split Deployment)

If you run hardware services on the Pi, use the scripts under `servers_in_pi/`:

- `audio_server.py` for audio playback endpoint
- `gpio_server.py` for sensor and GPIO state serving

Install Pi-side dependencies from `requirements_pi.txt`.

## One-Time Model Warmup (Optional but Recommended)

This pre-downloads model files so first voice request is faster.

Windows:

```powershell
.\.venv\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8'); print('whisper cached')"
.\.venv\Scripts\python.exe -c "import torch; torch.hub.load('snakers4/silero-vad','silero_vad', force_reload=False, onnx=False); print('silero cached')"
```

macOS/Linux:

```bash
.venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8'); print('whisper cached')"
.venv/bin/python -c "import torch; torch.hub.load('snakers4/silero-vad','silero_vad', force_reload=False, onnx=False); print('silero cached')"
```

## CPU and CUDA Fallback Behavior

- `.env` is set to CPU by default.
- If you manually set `VA_WHISPER_DEVICE=cuda` but CUDA is unavailable, the app falls back automatically to:
  - `device=cpu`
  - `compute_type=int8`

## Raspberry Pi Playback Server Settings

Set these in `.env`:

- `VA_PI_PLAY_URL=http://jmalpi.local:5000/play`
- `VA_PI_PLAY_TIMEOUT=30`

The assistant posts `audio/wav` in the request body, matching your Raspberry Pi Flask server contract.

## Performance Expectations (Typical)

- VAD: 10-40 ms per chunk
- STT (Whisper small, CPU int8): 300-1500 ms for short utterances
- LLM (TinyLlama local): 400-2000 ms
- TTS (Piper medium): 200-1000 ms
- End-to-end round-trip: about 1-5 s depending on hardware

## Troubleshooting

Piper not found:

- Use `.venv/Scripts/piper.exe` on Windows or `.venv/bin/piper` on macOS/Linux.
- Confirm with:
  - Windows: `.\.venv\Scripts\piper.exe --help`
  - macOS/Linux: `.venv/bin/piper --help`

Ollama not reachable:

- Start Ollama app/service.
- Test with `ollama list`.

No microphone input:

- Check OS microphone permissions.
- Ensure default input device is correct.

## Challenge Alignment

This project aligns directly with the Smart Learning Companion Challenge vision:

- AI + IoT integration for practical STEM education.
- Edge-first design for responsiveness and privacy.
- Interactive learning through physical experimentation and simulation.

It is a foundation for next-generation AI companions that help students learn by doing, not only by watching.
