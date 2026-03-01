from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import ollama  
import json    
import sys     
import os      

# python -m uvicorn main:app --reload

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase3'))

from conversation_manager import ConversationManager

app = FastAPI()

sessions = {}

# Simple REST endpoint to check if server is running
@app.get("/")
def home():
    return {"status": "ArtCraft Chatbot is running!"}

# REST endpoint to start a new session
@app.post("/session/new")
def new_session(session_id: str):
    sessions[session_id] = ConversationManager()
    return {"message": f"Session {session_id} created"}

# REST endpoint to reset a session
@app.post("/session/reset")
def reset_session(session_id: str):

    if session_id in sessions:
        sessions[session_id].reset()  
        return {"message": f"Session {session_id} reset"}
    return {"error": "Session not found"}

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    # Accept the incoming WebSocket connection
    await websocket.accept()

    # Create a new conversation manager for this connection
    manager = ConversationManager()

    try:
        # Keep listening for messages
        while True:
            # Wait for message from user
            data = await websocket.receive_text()

            # Parse the JSON message
            message = json.loads(data)

            user_input = message.get("message", "")

            if user_input.lower() == "/reset":
                manager.reset()  
                await websocket.send_text(json.dumps({
                    "type": "reset",
                    "message": "Conversation reset!"
                }))
                continue  

            messages = manager.build_messages(user_input)

            await websocket.send_text(json.dumps({
                "type": "start",
                "message": ""
            }))

            # Stream response from AI model token by token
            full_reply = ""  
            stream = ollama.chat(
                model="llama3.2:3b",  
                messages=messages,
                stream=True  
            )

            for chunk in stream:
                token = chunk['message']['content']  
                full_reply += token 

                await websocket.send_text(json.dumps({
                    "type": "token",
                    "message": token
                }))

            manager.add_message("user", user_input)
            manager.add_message("assistant", full_reply)

            await websocket.send_text(json.dumps({
                "type": "end",
                "message": ""
            }))

    except WebSocketDisconnect:
        print("User disconnected")