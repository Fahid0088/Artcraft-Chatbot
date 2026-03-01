# Phase II: LLM Selection and Optimization

## Selected Model
- Model: Qwen 0.5B (quantized)
- Tool: Ollama
- Runs on: CPU only

## Why This Model?
- Very small size (~500MB)
- Fast on CPU
- Good instruction following

## Memory Management
- Only last 5 messages kept in history
- Old messages are removed to save memory
- System prompt is always kept

## System Prompts
You are a helpful assistant for ArtCraft, an art supply store.

## Test User Prompts
| Test | User Prompts |
|------|--------------|
| Test 1 | What brushes do I need for watercolor painting? |
| Test 2 | What brushes do I need for acrylic painting? |
| Test 3 | What paper do I need for making hand made paper houses? |

## Latency Benchmark
| Test | Response Time |
|------|--------------|
| Test 1 | 88.60 seconds |
| Test 2 | 10.47 seconds |
| Test 3 | 07.04 seconds |
