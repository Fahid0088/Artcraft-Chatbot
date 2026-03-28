# ArtCraft Chatbot

AI powered art supply store assistant with text and voice support.

## Setup

### Requirements
- Python 3.10+
- NVIDIA GPU (recommended)
- Ollama installed

### Terminal Commands

Run these commands from the project root:

```powershell
cd "d:\Documents\Semester_6\NLP\Assignments\NLP_Assignment_3\Artcraft-Chatbot"
```

Create and activate a virtual environment:

```powershell
python -m venv voice_agent_env
.\voice_agent_env\Scripts\Activate.ps1
```

Install all required packages:

```powershell
pip install -r requirements.txt
pip install fastapi uvicorn
pip install sounddevice scipy numpy soundfile
pip install pyttsx3
pip install openai-whisper
pip install torch torchaudio
pip install ollama
```

Optional ASR dependency for Moonshine backend:

```powershell
pip install moonshine-voice
```

Pull the Ollama model:

```powershell
ollama pull llama3.2:3b
```

If you want to use another LLaMA model:

```powershell
$env:ARTCRAFT_OLLAMA_MODEL="llama3.2:3b"
```

Optional settings:

```powershell
$env:ARTCRAFT_SERVER_TTS="1"
$env:ARTCRAFT_MOONSHINE_MODEL="small-streaming"
```

Run the FastAPI backend:

```powershell
cd phase4
python -m uvicorn main:app --reload
```

### Open UI

Open this in your browser:

```text
http://localhost:8000/app
```

## Architecture
- Frontend: HTML/JS (phase5)
- Backend: FastAPI + WebSocket (phase4)
- Conversation Manager: Python (phase3)
- ASR: Moonshine preferred, Whisper fallback (phase6)
- TTS: pyttsx3 with browser speech fallback (phase6 + phase5)
- LLM: LLaMA via Ollama

## Known Limitations
- Runs locally only
- Requires Ollama running
- Browser microphone access must be allowed

