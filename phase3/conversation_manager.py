import ollama
import re
import random
from prompt_template import SYSTEM_PROMPT
from memory_filter import filter_history

class ConversationManager:
    def __init__(self):
        self.history = []        
        self.order_placed = False    
        self.order_cancelled = False 
        self.order_id = None        
        self.capacity = 30

    def add_message(self, role, content):

        self.history.append({"role": role, "content": content})

        if len(self.history) > self.capacity:
            self.history = filter_history(self.history)

    def get_order_status(self):

        if self.order_cancelled:
            return f"\nORDER STATUS: Order {self.order_id} was already CANCELLED. Do not cancel again."
        elif self.order_placed:
            return f"\nORDER STATUS: Order {self.order_id} is ACTIVE."
        else:
            return "\nORDER STATUS: No order placed yet in this session."

    def build_messages(self, user_input):

        full_prompt = SYSTEM_PROMPT + self.get_order_status()
        messages = [{"role": "system", "content": full_prompt}]
        messages += self.history
        messages.append({"role": "user", "content": user_input})

        return messages

    def chat(self, user_input):
        messages = self.build_messages(user_input)

        response = ollama.chat(
            model="llama3.2:3b",
            messages=messages
        )

        reply = response['message']['content']

        if "ART-" in reply and not self.order_placed:
            self.order_placed = True
            match = re.search(r'ART-(\d{4})', reply)
            if match:
                self.order_id = f"ART-{match.group(1)}"

        if "cancelled successfully" in reply.lower() and not self.order_cancelled:
            self.order_cancelled = True

        self.add_message("user", user_input)
        self.add_message("assistant", reply)

        return reply

    def reset(self):
        self.history = []
        self.order_placed = False
        self.order_cancelled = False
        self.order_id = None