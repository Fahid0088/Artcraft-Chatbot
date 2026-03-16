import whisper        # speech to text library
import sounddevice as sd  # to record from microphone
import numpy as np    # to handle audio data
import scipy.io.wavfile as wav  # to save audio
import os

# Use "base" model instead of "tiny" for better accuracy
model = whisper.load_model("base")

def speech_to_text(duration=6, sample_rate=16000):
    # Record audio from microphone
    audio = sd.rec(
        int(duration * sample_rate),  # total samples
        samplerate=sample_rate,       # sample rate
        channels=1,                   # mono
        dtype=np.float32              # format
    )
    sd.wait()  # wait until recording done

    # Save recorded audio
    wav.write("recorded.wav", sample_rate, audio)

    # Convert audio to text
    # language="en" forces English only for better accuracy
    result = model.transcribe(
        "recorded.wav",
        language="en",        # force English only
        fp16=False            # use FP32 for CPU
    )

    return result["text"].strip()  # return clean text