import asyncio
import json
import sys
from pathlib import Path

import requests
import websockets

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'phase3') not in sys.path:
    sys.path.append(str(ROOT / 'phase3'))
if str(ROOT / 'phase6') not in sys.path:
    sys.path.append(str(ROOT / 'phase6'))

from conversation_manager import ConversationManager
from asr import get_asr_status
from tts import text_to_speech_stream

SUITE_PATH = Path(__file__).with_name('voice_test_suite.json')


def load_suite():
    return json.loads(SUITE_PATH.read_text(encoding='utf-8'))


def check(condition, success_message, failure_message, results):
    if condition:
        results.append((True, success_message))
        return True
    results.append((False, failure_message))
    return False


def run_http_checks(suite, results):
    try:
        response = requests.get(f"{suite['base_url']}/", timeout=5)
        data = response.json()
        check(response.status_code == 200, 'HTTP health check passed', f"HTTP health check failed: {response.status_code}", results)
        check('status' in data, 'Root endpoint returned JSON status', 'Root endpoint did not return expected JSON', results)
    except Exception as exc:
        results.append((False, f'HTTP health check exception: {exc}'))


async def run_websocket_checks(suite, results):
    try:
        async with websockets.connect(suite['ws_chat_url']) as websocket:
            await websocket.send(json.dumps({'message': 'Hello'}))
            received = []
            for _ in range(5):
                msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                received.append(msg)
                if '"type": "end"' in msg:
                    break
            joined = '\n'.join(received)
            check('voice' not in joined, 'Chat websocket responded', 'Chat websocket did not respond correctly', results)
    except Exception as exc:
        results.append((False, f'Chat websocket exception: {exc}'))

    try:
        async with websockets.connect(suite['ws_voice_url']) as websocket:
            check(True, 'Voice websocket connected', 'Voice websocket failed to connect', results)
    except Exception as exc:
        results.append((False, f'Voice websocket exception: {exc}'))


def run_conversation_tests(suite, results):
    for case in suite['conversation_tests']:
        manager = ConversationManager()
        case_ok = True
        for step in case['steps']:
            reply = manager.chat(step['input'])
            for expected in step['contains']:
                if expected.lower() not in reply.lower():
                    results.append((False, f"{case['name']} failed for input '{step['input']}'. Missing: {expected}. Reply was: {reply}"))
                    case_ok = False
                    break
            if not case_ok:
                break
        if case_ok:
            results.append((True, f"{case['name']} passed"))


def run_voice_stack_checks(results):
    try:
        status = get_asr_status()
        results.append((True, f'ASR module imported successfully (status: {status})'))
    except Exception as exc:
        results.append((False, f'ASR module import failed: {exc}'))

    try:
        segments = list(text_to_speech_stream('Hello. This is a test.'))
        ok = len(segments) >= 1
        check(ok, 'TTS stream produced output segments', 'TTS stream did not produce output segments', results)
    except Exception as exc:
        results.append((False, f'TTS stream failed: {exc}'))


def print_summary(results):
    passed = sum(1 for ok, _ in results if ok)
    total = len(results)
    print('\nArtCraft Voice Agent Test Report')
    print('=' * 36)
    for ok, message in results:
        prefix = 'PASS' if ok else 'FAIL'
        print(f'[{prefix}] {message}')
    print('-' * 36)
    print(f'Passed: {passed}/{total}')
    if passed != total:
        raise SystemExit(1)


async def main():
    suite = load_suite()
    results = []
    run_http_checks(suite, results)
    await run_websocket_checks(suite, results)
    run_conversation_tests(suite, results)
    run_voice_stack_checks(results)
    print_summary(results)


if __name__ == '__main__':
    asyncio.run(main())
