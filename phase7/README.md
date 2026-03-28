# Phase 7

This folder contains automated and Postman-based voice-agent evaluation assets.

Files:
- `postman_voice_collection.json`
- `voice_test_cases.md`
- `voice_test_suite.json`
- `run_voice_tests.py`

## Automated Demo Run

1. Start the backend:
   `cd phase4`
   `python -m uvicorn main:app`

2. In a new terminal from repo root, run:
   `voice_agent_env\Scripts\python phase7\run_voice_tests.py`

3. Show the PASS/FAIL report to the evaluator.

## Notes

- This runner checks HTTP health, WebSocket connectivity, core conversation behavior, and voice-stack imports.
- It does not send real recorded audio files; it is designed for fast automated demo evaluation.
