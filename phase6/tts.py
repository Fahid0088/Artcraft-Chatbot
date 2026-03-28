import os
import re
import tempfile

import pyttsx3


_ENGINE = None
_ENGINE_FAILED = False
USE_SERVER_TTS = os.getenv("ARTCRAFT_SERVER_TTS", "0") == "1"


def sanitize_tts_text(text):
    cleaned = text.replace("**", "")
    cleaned = re.sub(r"(?m)^\s*[*-]\s+", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*\d+\.\s+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def get_tts_engine():
    global _ENGINE, _ENGINE_FAILED
    if not USE_SERVER_TTS:
        return None
    if _ENGINE_FAILED:
        return None
    if _ENGINE is None:
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 1.0)
            voices = engine.getProperty("voices")
            if voices:
                engine.setProperty("voice", voices[1].id if len(voices) > 1 else voices[0].id)
            _ENGINE = engine
        except Exception:
            _ENGINE_FAILED = True
            return None
    return _ENGINE


def text_to_speech(text, output_file="response.wav"):
    text = sanitize_tts_text(text)
    engine = get_tts_engine()
    if engine is None:
        raise RuntimeError("No server-side TTS engine is available.")
    engine.save_to_file(text, output_file)
    engine.runAndWait()
    return output_file


def text_to_speech_stream(text):
    cleaned_text = sanitize_tts_text(text)
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned_text) if part.strip()]
    engine = get_tts_engine()

    if engine is None:
        for sentence in sentences:
            yield None, sentence
        return

    for sentence in sentences:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = temp_file.name

        try:
            engine.save_to_file(sentence, temp_path)
            engine.runAndWait()
            with open(temp_path, "rb") as audio_file:
                yield audio_file.read(), sentence
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
