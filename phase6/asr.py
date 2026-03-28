from __future__ import annotations

import os
import tempfile
from pathlib import Path
from math import gcd

import numpy as np
import scipy.io.wavfile as wav
from scipy import signal
import sounddevice as sd
import torch
import whisper


BASE_DIR = Path(__file__).resolve().parents[1]
MOONSHINE_CACHE_DIR = BASE_DIR / ".moonshine_cache"
os.environ.setdefault("MOONSHINE_VOICE_CACHE", str(MOONSHINE_CACHE_DIR))
MOONSHINE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

try:
    from moonshine_voice import ModelArch, get_model_for_language, load_wav_file
    from moonshine_voice.transcriber import Transcriber as MoonshineTranscriber
except ImportError:  # pragma: no cover - optional runtime dependency
    MoonshineTranscriber = None
    ModelArch = None
    get_model_for_language = None
    load_wav_file = None


WHISPER_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DEVICE = "moonshine" if MoonshineTranscriber is not None else f"whisper-{WHISPER_DEVICE}"

_moonshine_transcriber = None
_whisper_model = None
_printed_backend = False

MOONSHINE_MODEL_ARCHES = {
    "tiny-streaming": getattr(ModelArch, "TINY_STREAMING", None),
    "small-streaming": getattr(ModelArch, "SMALL_STREAMING", None),
    "medium-streaming": getattr(ModelArch, "MEDIUM_STREAMING", None),
}


def _log_backend(message: str) -> None:
    global _printed_backend
    if not _printed_backend:
        print(message)
        _printed_backend = True


def get_moonshine_transcriber():
    global _moonshine_transcriber
    if MoonshineTranscriber is None or get_model_for_language is None:
        return None

    if _moonshine_transcriber is None:
        wanted_model = os.getenv("ARTCRAFT_MOONSHINE_MODEL", "small-streaming").strip().lower()
        model_arch = MOONSHINE_MODEL_ARCHES.get(wanted_model)
        model_path, model_arch = get_model_for_language(
            wanted_language="en",
            wanted_model_arch=model_arch,
        )
        _moonshine_transcriber = MoonshineTranscriber(
            model_path=str(model_path),
            model_arch=model_arch,
        )
        _log_backend(f"ASR using: moonshine ({model_path})")
    return _moonshine_transcriber


def preload_asr():
    if MoonshineTranscriber is not None:
        try:
            return get_moonshine_transcriber()
        except Exception as exc:
            print(f"Moonshine preload failed, Whisper will be used as fallback: {exc}")
    return get_whisper_model()


def get_asr_status() -> str:
    if _moonshine_transcriber is not None:
        return "ready"
    if _whisper_model is not None:
        return "ready"
    return "cold"


def get_whisper_model(model_name: str = "base"):
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model(model_name, device=WHISPER_DEVICE)
        _log_backend(f"ASR using: whisper-{WHISPER_DEVICE}")
    return _whisper_model


def _prepare_audio_for_asr(audio_data, sample_rate: int, target_rate: int = 16000):
    audio = np.asarray(audio_data)

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    if audio.dtype.kind in {"i", "u"}:
        max_value = max(abs(np.iinfo(audio.dtype).min), np.iinfo(audio.dtype).max)
        audio = audio.astype(np.float32) / float(max_value)
    else:
        audio = audio.astype(np.float32, copy=False)

    peak = np.max(np.abs(audio)) if audio.size else 0.0
    if peak > 0:
        audio = audio / peak

    if sample_rate != target_rate and audio.size:
        factor = gcd(int(sample_rate), int(target_rate))
        up = target_rate // factor
        down = sample_rate // factor
        audio = signal.resample_poly(audio, up, down).astype(np.float32, copy=False)
        sample_rate = target_rate

    return audio, sample_rate


def transcribe_file(file_path: str, language: str = "en") -> str:
    if MoonshineTranscriber is not None and load_wav_file is not None:
        try:
            transcriber = get_moonshine_transcriber()
            if transcriber is not None:
                audio_data, sample_rate = load_wav_file(file_path)
                audio_data, sample_rate = _prepare_audio_for_asr(audio_data, sample_rate)
                transcript = transcriber.transcribe_without_streaming(audio_data, sample_rate)
                text = " ".join(line.text.strip() for line in transcript.lines if line.text.strip()).strip()
                if text:
                    return text
        except Exception as exc:
            print(f"Moonshine ASR failed, falling back to Whisper: {exc}")

    model = get_whisper_model()
    result = model.transcribe(file_path, language=language, fp16=torch.cuda.is_available())
    return result["text"].strip()


def speech_to_text(duration: int = 6, sample_rate: int = 16000) -> str:
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32,
    )
    sd.wait()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_path = temp_file.name

    try:
        wav.write(temp_path, sample_rate, audio)
        return transcribe_file(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
