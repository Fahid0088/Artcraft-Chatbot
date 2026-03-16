from kokoro_onnx import Kokoro  
import soundfile as sf         

kokoro = Kokoro("kokoro-v0_19.onnx", "voices-v1.0.bin")
def text_to_speech(text, output_file="response.wav"):
    # Convert text to speech
    samples, sample_rate = kokoro.create(
        text,         
        voice="af_sarah",    
        speed=1.0,      
        lang="en-us"   
    )

    sf.write(output_file, samples, sample_rate)

    return output_file  