# Local Voice Assistant (Offline, CPU-First)

This project runs fully on your computer (no cloud APIs) with this pipeline:

Microphone -> Silero VAD -> faster-whisper STT -> TinyLlama (Ollama localhost API) -> Piper TTS -> Speaker

## What Is Already Done In This Folder

The following setup has already been completed on this machine:

- Python dependencies installed in `.venv`
- Ollama model `tinyllama` pulled
- Whisper `small` model cached by faster-whisper
- Silero VAD model cached by torch hub
- Piper CLI installed in `.venv` (`.venv/Scripts/piper.exe`)
- Piper medium voice files present in `models/`

If you move this project to another machine, follow the full first-time setup below.

## Architecture

```text
+------------------+
|   Microphone     |
+---------+--------+
          |
          v
+------------------+
|   Silero VAD     |  Detect speech start/end
+---------+--------+
          |
          v
+------------------+
| faster-whisper   |  STT (small/base)
+---------+--------+
          |
          v
+------------------------------+
| Ollama API (localhost:11434) |
| model: tinyllama             |
+---------+--------------------+
          |
          v
+------------------+
|    Piper TTS     |  medium voice model
+---------+--------+
          |
          v
+------------------+
|     Speaker      |
+------------------+
```

## Project Structure

```text
.
|-- .env
|-- .env.example
|-- README.md
|-- requirements.txt
|-- config.py
|-- assistant.py
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
