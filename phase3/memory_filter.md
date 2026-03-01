# Phase III: Conversation Manager and Prompt Orchestration

## Overview
This phase implements the brain of the chatbot. It manages conversation 
history, enforces business rules, and builds structured prompts for the AI model.

## Files
| File | Purpose |
|------|---------|
| `prompt_template.py` | Defines how AI should behave |
| `conversation_manager.py` | Manages chat history and talks to AI |
| `memory_filter.py` | Filters important messages from noise |
| `test_conversation.py` | Tests multi-turn conversation |

## How It Works
1. User sends a message
2. Conversation manager adds it to history
3. Memory filter removes unimportant messages
4. System prompt + history + new message sent to AI
5. AI replies and reply is saved in history

## Prompt Template
- AI is told to act as ArtCraft store assistant
- Strict rules are defined to stay on topic
- AI is told to politely reject off-topic questions

## Memory Management (Score Base)
- Score based filtering is used
- Every message gets a score based on importance
- Top N highest scored messages are kept
- Recent messages always get higher score
- Noise messages like "ok", "thanks" get lower score
