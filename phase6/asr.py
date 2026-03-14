import whisper

# "tiny" model is fast and works well on CPU
model = whisper.load_model("tiny")

def speech_to_text(audio_file_path):
    result = model.transcribe(audio_file_path)
    return result["text"]