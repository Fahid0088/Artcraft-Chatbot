import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase3'))

from conversation_manager import ConversationManager  
from asr import speech_to_text                        
from tts import text_to_speech                        
import sounddevice as sd                              
import soundfile as sf                              

manager = ConversationManager()

GOODBYE_WORDS = ["goodbye", "good bye", "bye", "exit", "quit", 
                 "stop", "end", "see you", "take care", "later"]

def is_goodbye(text):
    text_lower = text.lower()
    return any(word in text_lower for word in GOODBYE_WORDS)

def play_audio(file_path):
    data, sample_rate = sf.read(file_path)
    sd.play(data, sample_rate)
    sd.wait()  

def voice_chat():
    print("ArtCraft Voice Assistant Started!")
    print("Say 'goodbye' to stop\n")

    while True:
        try:
            print("Listening... Speak now!")
            user_text = speech_to_text()

            if not user_text:
                print("Nothing heard, please speak again...")
                continue

            print(f"You said: {user_text}")

            if is_goodbye(user_text):
                reply = "Thank you for visiting ArtCraft! Have a creative day!"
                print(f"Bot: {reply}")
                audio_file = text_to_speech(reply)
                play_audio(audio_file)
                print("\nGoodbye!")
                break  

            reply = manager.chat(user_text)
            print(f"Bot: {reply}")

            audio_file = text_to_speech(reply)

            print("Playing response...")
            play_audio(audio_file)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    voice_chat()