import asyncio
import json
import os
import sys
import tempfile
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

try:
    import ollama
except ImportError:  # pragma: no cover - optional runtime dependency
    ollama = None


BASE_DIR = os.path.dirname(__file__)
PHASE3_DIR = os.path.join(BASE_DIR, "..", "phase3")
PHASE5_DIR = os.path.join(BASE_DIR, "..", "phase5")
PHASE6_DIR = os.path.join(BASE_DIR, "..", "phase6")

if PHASE3_DIR not in sys.path:
    sys.path.append(PHASE3_DIR)
if PHASE6_DIR not in sys.path:
    sys.path.append(PHASE6_DIR)

from conversation_manager import ConversationManager
from asr import DEVICE as ASR_DEVICE, get_asr_status, preload_asr, transcribe_file
from tts import text_to_speech_stream


app = FastAPI(title="ArtCraft Chatbot API")
sessions: Dict[str, ConversationManager] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

asr_warmup_task = None


async def stream_text_reply(websocket: WebSocket, reply: str, chunk_size: int = 10):
    await websocket.send_text(json.dumps({"type": "start", "message": ""}))
    for index in range(0, len(reply), chunk_size):
        chunk = reply[index:index + chunk_size]
        await websocket.send_text(json.dumps({"type": "token", "message": chunk}))
        await asyncio.sleep(0.02)
    await websocket.send_text(json.dumps({"type": "end", "message": ""}))


async def send_voice_status(websocket: WebSocket, message: str):
    await websocket.send_text(json.dumps({"type": "status", "message": message}))


async def stream_voice_reply_text(websocket: WebSocket, reply: str, chunk_size: int = 10):
    await websocket.send_text(json.dumps({"type": "voice_start", "message": ""}))
    for index in range(0, len(reply), chunk_size):
        chunk = reply[index:index + chunk_size]
        await websocket.send_text(json.dumps({"type": "voice_token", "message": chunk}))
        await asyncio.sleep(0.02)


def should_stream_llm(manager: ConversationManager, user_input: str) -> bool:
    return manager.should_use_llm(user_input)


def get_session_manager(session_id: str) -> ConversationManager:
    if session_id not in sessions:
        sessions[session_id] = ConversationManager()
    return sessions[session_id]


@app.on_event("startup")
async def startup_event():
    global asr_warmup_task
    if asr_warmup_task is None:
        asr_warmup_task = asyncio.create_task(asyncio.to_thread(preload_asr))


@app.get("/")
def home():
    return {
        "status": "ArtCraft Chatbot is running!",
        "asr_device": ASR_DEVICE,
        "asr_status": get_asr_status(),
        "ollama_available": ollama is not None,
        "default_model": os.getenv("ARTCRAFT_OLLAMA_MODEL", "llama3.2:3b"),
        "moonshine_model": os.getenv("ARTCRAFT_MOONSHINE_MODEL", "small-streaming"),
    }


@app.get("/app")
def app_ui():
    return FileResponse(os.path.join(PHASE5_DIR, "index.html"))


@app.post("/session/new")
def new_session(session_id: str):
    sessions[session_id] = ConversationManager()
    return {"message": f"Session {session_id} created"}


@app.post("/session/reset")
def reset_session(session_id: str):
    manager = get_session_manager(session_id)
    manager.reset()
    return {"message": f"Session {session_id} reset"}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    manager = ConversationManager()

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_input = payload.get("message", "").strip()

            if not user_input:
                await websocket.send_text(json.dumps({"type": "error", "message": "Empty message received."}))
                continue

            if user_input.lower() == "/reset":
                manager.reset()
                await websocket.send_text(json.dumps({"type": "reset", "message": "Conversation reset!"}))
                continue

            if not should_stream_llm(manager, user_input):
                reply = manager.chat(user_input)
                await stream_text_reply(websocket, reply)
                continue

            await websocket.send_text(json.dumps({"type": "start", "message": ""}))
            full_reply = ""

            try:
                stream = ollama.chat(
                    model=manager.model_name,
                    messages=manager.build_messages(user_input),
                    stream=True,
                )

                for chunk in stream:
                    token = chunk["message"]["content"]
                    full_reply += token
                    await websocket.send_text(json.dumps({"type": "token", "message": token}))
            except Exception as exc:
                print(f"Ollama streaming failed, using fallback: {exc}")
                full_reply = manager.fallback_reply(user_input)
                for index in range(0, len(full_reply), 10):
                    token = full_reply[index:index + 10]
                    await websocket.send_text(json.dumps({"type": "token", "message": token}))
                    await asyncio.sleep(0.02)

            manager.add_message("user", user_input)
            manager.add_message("assistant", full_reply)
            await websocket.send_text(json.dumps({"type": "end", "message": ""}))

    except WebSocketDisconnect:
        print("Text user disconnected")


@app.websocket("/ws/voice")
async def websocket_voice(websocket: WebSocket):
    await websocket.accept()
    manager = ConversationManager()

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            await send_voice_status(websocket, "Preparing voice engine...")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            try:
                await send_voice_status(websocket, "Transcribing...")
                user_text = await asyncio.to_thread(transcribe_file, temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

            if not user_text:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "I could not hear anything clearly. Please try again."
                }))
                continue

            await websocket.send_text(json.dumps({"type": "transcription", "text": user_text}))
            await send_voice_status(websocket, "Generating response...")

            try:
                reply = await asyncio.to_thread(manager.chat, user_text)
                await stream_voice_reply_text(websocket, reply)
                segments = await asyncio.to_thread(lambda: list(text_to_speech_stream(reply)))
                for reply_audio, sentence in segments:
                    await websocket.send_text(json.dumps({
                        "type": "sentence",
                        "text": sentence,
                        "audio": reply_audio is not None,
                    }))
                    if reply_audio is not None:
                        await websocket.send_bytes(reply_audio)
                await websocket.send_text(json.dumps({"type": "voice_end", "text": ""}))
            except Exception:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Voice reply generation failed. Please try again."
                }))

    except asyncio.CancelledError:
        print("Voice task cancelled during shutdown")
    except WebSocketDisconnect:
        print("Voice user disconnected")
