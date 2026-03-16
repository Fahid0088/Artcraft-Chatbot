import whisper        
import sounddevice as sd  
import numpy as np    
import scipy.io.wavfile as wav  

model = whisper.load_model("tiny")

def record_audio(duration=5, sample_rate=16000):
    print(f"Recording for {duration} seconds... Speak now!")
    audio = sd.rec(
        int(duration * sample_rate),  
        samplerate=sample_rate,       
        channels=1,                   
        dtype=np.float32           
    )
    sd.wait()  
    print("Recording done!")
    return audio, sample_rate

def speech_to_text():
    audio, sample_rate = record_audio(duration=5)
    
    wav.write("recorded.wav", sample_rate, audio)
    
    result = model.transcribe("recorded.wav")
    
    return result["text"]

print("Testing ASR...")
text = speech_to_text()
print(f"You said: {text}")