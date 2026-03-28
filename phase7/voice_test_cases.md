# Voice Agent Test Cases

These test cases are for manual WebSocket testing of the voice agent in Postman.

## WebSocket Endpoint

- Voice endpoint: `ws://127.0.0.1:8000/ws/voice`

## Expected Event Types

The voice WebSocket sends JSON text frames and may also send binary audio frames.

Common text frames:

- `status`
- `transcription`
- `voice_start`
- `voice_token`
- `sentence`
- `voice_end`
- `error`

## Test Case 1: Greeting

Audio to speak:
- `Hello`

Expected behavior:
- `transcription` should contain a greeting close to `Hello`
- bot should respond with a greeting
- reply text should arrive gradually through `voice_start` and `voice_token`
- one or more `sentence` events should follow
- final event should be `voice_end`

## Test Case 2: Product Question

Audio to speak:
- `Can you tell me what type of brushes you have`

Expected behavior:
- transcription should be close to the spoken sentence
- bot should list brush options
- response should stay in art/craft domain

## Test Case 3: Off-topic Redirect

Audio to speak:
- `What is the price of laptops`

Expected behavior:
- bot should politely redirect to art/craft help
- bot should not answer the laptop question

## Test Case 4: Procedure Question

Audio to speak:
- `I want to make a doll house. Tell me how to make it`

Expected behavior:
- bot should answer in numbered steps
- response should mention art/craft materials

## Test Case 5: Order Placement

Audio sequence:
1. `I want to place my order`
2. `Fahid Imran`
3. `Zero one two three four five six seven eight nine`
4. `fahid at the rate gmail dot com`
5. `one glue`

Expected behavior:
- bot asks for name, then phone, then email, then items
- email and phone should normalize correctly
- final response should be `Order Confirmed!`

## Test Case 6: Cancel Order

Audio sequence:
1. `Cancel my order`
2. `Yes`

Expected behavior:
- bot asks for confirmation
- after `Yes`, order should be cancelled

## Test Case 7: Invalid Item During Order

Audio sequence:
1. `I want to place my order`
2. `Fahid Imran`
3. `0123456789`
4. `fahid@gmail.com`
5. `hot glue gun`

Expected behavior:
- bot should reject unsupported item
- bot should ask for a valid ArtCraft product
