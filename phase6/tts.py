from kokoro_onnx import Kokoro  
import soundfile as sf           

kokoro = Kokoro("kokoro-v0_19.onnx", "voices.bin")

def text_to_speech(text, output_file="response.wav"):

    samples, sample_rate = kokoro.create(
        text,           
        voice="af",     
        speed=1.0,      
        lang="en-us"    
    )
    
    sf.write(output_file, samples, sample_rate)
    
    return output_file  