# Phase II: LLM Selection and Optimization

## Selected Model
- Model: Qwen3 0.6B (quantized)
- Tool: Ollama
- Runs on: CPU only

## Why This Model?
- Very small size (~500MB)
- Fast on CPU
- Newer version with better instruction following
- Good for conversational tasks

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
| Test 1 | 3.09 seconds |
| Test 2 | 3.98 seconds |
| Test 3 | 4.85 seconds |


## Known Limitations
- 0.6B model may sometimes ignore system prompt rules
- Larger models follow instructions better
- This is a known tradeoff of using very small CPU models
