try:
    from .conversation_manager import ConversationManager
except ImportError:
    from conversation_manager import ConversationManager

manager = ConversationManager()

print("--- Test 1: Product Question ---")
reply = manager.chat("Hi! I need supplies for watercolor painting")
print(f"Bot: {reply}\n")

print("--- Test 2: Follow-up (Memory Test) ---")
reply = manager.chat("What size brushes should I get?")
print(f"Bot: {reply}\n")

print("--- Test 3: Off-topic Question ---")
reply = manager.chat("Can you help me with my math homework?")
print(f"Bot: {reply}\n")

print("--- Test 4: After Reset ---")
manager.reset()
reply = manager.chat("Hello!")
print(f"Bot: {reply}\n")
