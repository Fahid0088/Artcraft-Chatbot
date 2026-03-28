# ArtCraft Model and Conversation Guide

This README explains the three AI components used in the ArtCraft chatbot:

1. LLaMA for text generation
2. ASR for speech-to-text
3. TTS for text-to-speech

It also explains how the `ConversationManager` works step by step.

## 1. System Overview

The full voice conversation pipeline is:

1. User speaks into the microphone or sends audio from the browser.
2. ASR converts speech into text.
3. `ConversationManager` decides what kind of request it is.
4. If needed, LLaMA generates a reply through Ollama.
5. TTS converts the reply text into audio.
6. The audio reply is played back to the user.

For text chat, the ASR and TTS steps are skipped.

## 2. LLaMA Model

### What is used in this project

- The chatbot uses a LLaMA-family model through `ollama`.
- In code, the default model is `llama3.2:3b`.
- The model name can be changed with the environment variable `ARTCRAFT_OLLAMA_MODEL`.
- The root project `README.md` mentions `llama3.1:8b`, so the exact model may depend on local setup.

### Where it is used

- File: [conversation_manager.py](D:/Documents/Semester_6/NLP/Assignments/NLP_Assignment_3/Artcraft-Chatbot/phase3/conversation_manager.py)
- Main method: `llm_reply()`

### What it does

The LLaMA model is responsible for:

- answering art and craft questions
- giving short guidance and recommendations
- handling in-domain store queries that are not hardcoded
- following the ArtCraft system prompt

### How it works in steps

1. User text reaches `ConversationManager.chat()`.
2. The manager checks whether the message should use the LLM.
3. If the message is greeting, thanks, goodbye, order flow, cancel flow, or a simple fallback case, the LLM is skipped.
4. If the message is a normal art/craft question, the manager builds a prompt with:
   - system prompt
   - order status
   - recent chat history
   - current user message
5. `ollama.chat()` is called with the selected LLaMA model.
6. The returned text is sent back to the user.

### Limitations of the LLaMA part

- It depends on Ollama being installed and running locally.
- Response quality depends on the selected model size.
- Smaller models can miss nuance or give weak recommendations.
- The model is restricted by the ArtCraft prompt, so it is not intended for broad general knowledge.
- If Ollama fails, the system falls back to rule-based replies.

## 3. ASR Model

### What is used in this project

ASR means Automatic Speech Recognition.

This project uses:

- `moonshine_voice` as the preferred ASR backend if installed
- Whisper as the fallback backend

In code:

- preferred Moonshine model: `small-streaming`
- fallback Whisper model: `base`

### Where it is used

- File: [asr.py](D:/Documents/Semester_6/NLP/Assignments/NLP_Assignment_3/Artcraft-Chatbot/phase6/asr.py)
- Used by:
  - [voice_pipeline.py](D:/Documents/Semester_6/NLP/Assignments/NLP_Assignment_3/Artcraft-Chatbot/phase6/voice_pipeline.py)
  - [main.py](D:/Documents/Semester_6/NLP/Assignments/NLP_Assignment_3/Artcraft-Chatbot/phase4/main.py)

### What it does

ASR converts spoken audio into text so the chatbot can understand the user.

### How it works in steps

1. Audio is recorded from the microphone or received from the WebSocket.
2. Audio is stored temporarily as a `.wav` file.
3. The system tries to load the Moonshine transcriber.
4. Audio is cleaned before recognition:
   - convert stereo to mono if needed
   - normalize numeric format
   - normalize volume
   - resample to `16000 Hz`
5. Moonshine tries to transcribe the audio.
6. If Moonshine is unavailable or fails, Whisper transcribes the file instead.
7. The final text transcript is returned to the conversation manager.

### Limitations of the ASR part

- Recognition quality drops with background noise.
- Accent, pronunciation, and unclear speech can reduce accuracy.
- Very short or very soft speech may return empty text.
- Temporary file creation adds overhead.
- If Moonshine is not installed, the system uses Whisper fallback, which can be heavier.

### Why ASR can feel slow

ASR can be slow in this project for several practical reasons:

1. Audio is first recorded completely before transcription starts in `speech_to_text()`.
2. The file is written to disk and then read again for processing.
3. Audio preprocessing is done before recognition.
4. If the ASR backend is cold, model loading takes extra time.
5. Whisper is computationally heavier than a simple text pipeline, especially on CPU.
6. In the web voice flow, transcription happens before reply generation, so the user waits for ASR to finish first.

## 4. TTS Engine

### What is used in this project

TTS means Text-to-Speech.

This project uses:

- `pyttsx3` for server-side speech synthesis
- browser-side fallback behavior in some UI flows when server TTS is unavailable

Important note:

- TTS here is not a large neural model like LLaMA or Whisper.
- It is mainly a local speech engine wrapper through `pyttsx3`.

### Where it is used

- File: [tts.py](D:/Documents/Semester_6/NLP/Assignments/NLP_Assignment_3/Artcraft-Chatbot/phase6/tts.py)
- Used by:
  - [voice_pipeline.py](D:/Documents/Semester_6/NLP/Assignments/NLP_Assignment_3/Artcraft-Chatbot/phase6/voice_pipeline.py)
  - [main.py](D:/Documents/Semester_6/NLP/Assignments/NLP_Assignment_3/Artcraft-Chatbot/phase4/main.py)

### What it does

TTS converts the chatbot's text reply into spoken audio.

### How it works in steps

1. The reply text is cleaned using `sanitize_tts_text()`.
2. Bullet points and markdown-like formatting are removed.
3. The system tries to initialize the `pyttsx3` engine if `ARTCRAFT_SERVER_TTS=1`.
4. For normal output, the text is saved to a `.wav` file.
5. For streaming output, the text is split into sentences.
6. Each sentence is converted into a temporary audio file.
7. The audio bytes are sent back and played for the user.

### Limitations of the TTS part

- Voice quality depends on the operating system voice installed locally.
- Output may sound robotic compared to modern neural TTS systems.
- The engine may fail on some systems or configurations.
- Long replies take longer because they are synthesized sentence by sentence.
- Temporary audio file creation adds delay.

### Why TTS can feel slow

TTS can be slow in this project because:

1. The reply text must be fully generated before speech synthesis starts.
2. `pyttsx3` is not optimized like low-latency streaming neural APIs.
3. The code writes each sentence to a temporary `.wav` file.
4. `engine.runAndWait()` blocks until synthesis finishes.
5. In the voice WebSocket flow, sentence audio is generated after the text reply is ready, not in parallel with ASR.

## 5. How `ConversationManager` Works

### Main file

- File: [conversation_manager.py](D:/Documents/Semester_6/NLP/Assignments/NLP_Assignment_3/Artcraft-Chatbot/phase3/conversation_manager.py)

### Main responsibility

`ConversationManager` is the core brain of the chatbot. It keeps conversation state and decides whether a message should be handled by rules, by order logic, by cancellation logic, or by the LLaMA model.

### Step-by-step conversation flow

1. A new `ConversationManager` object is created.
2. It stores:
   - chat history
   - current order step
   - whether cancellation is pending
   - whether an order is placed or cancelled
   - customer name, phone, email, and selected items
3. The user sends a message.
4. `chat()` receives the message and cleans it.
5. The manager checks for goodbye messages first.
6. If cancellation confirmation is already pending, it routes to `handle_cancel()`.
7. If the text sounds like a cancel request, it routes to `handle_cancel()`.
8. If the user is already inside the order flow, it routes to `handle_order()`.
9. If the text is a new order request, it starts the ordering sequence.
10. If none of the above special flows apply, it decides whether to:
    - use fixed fallback logic
    - or call the LLaMA model
11. The final reply is added to history.
12. History is trimmed to the latest 12 messages.

### Order flow in steps

When the user wants to place an order, the manager follows these stages:

1. Ask for full name.
2. Validate the name.
3. Ask for phone number if missing.
4. Validate and normalize the phone number.
5. Ask for email if missing.
6. Validate and normalize the email.
7. Ask which item and quantity the user wants.
8. Match product names using aliases.
9. Calculate the total price.
10. Generate an order ID like `ART-1234`.
11. Return a structured order confirmation message.

### Cancel flow in steps

1. Check whether an active order exists.
2. If no active order exists, return a message immediately.
3. If an active order exists, ask for confirmation.
4. Wait for `yes` or `no`.
5. If `yes`, mark the order as cancelled.
6. If `no`, keep the order active.

### How LLM vs rule-based logic is chosen

The manager avoids calling LLaMA for many simple cases. It uses rules first for:

- greetings
- thanks
- goodbye
- yes/no replies
- acknowledgements
- order placement
- order cancellation
- unclear short inputs
- off-topic queries

It usually calls LLaMA only when the message is a meaningful art/craft query and there is no active order or cancel flow that should take priority.

## 6. Main Limitations of the Whole System

These are the major limitations across the full project:

1. The exact LLaMA model may differ by environment configuration.
2. ASR quality depends heavily on audio quality and installed backend.
3. TTS quality depends on the local system voice engine.
4. Voice responses are sequential:
   - transcribe first
   - generate reply second
   - synthesize speech third
5. Local models and local audio processing can be slow on CPU-only systems.
6. The chatbot is intentionally narrow and mainly supports ArtCraft-related conversations.

## 7. Summary

The ArtCraft chatbot combines:

- LLaMA through Ollama for language understanding and response generation
- Moonshine or Whisper for speech-to-text
- pyttsx3 for text-to-speech

The `ConversationManager` sits in the middle and controls the full interaction. It handles order state, cancel state, input validation, fallback replies, and only calls the LLM when it is really needed.
