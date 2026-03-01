import ollama  
from prompt_template import SYSTEM_PROMPT 
from memory_filter import filter_history  

class ConversationManager:
    def __init__(self):
        self.history = []
        self.capacity = 20

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

        if len(self.history) > self.capacity:
            self.history = filter_history(self.history, self.capacity)

    def build_messages(self, user_input):

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += self.history
        messages.append({"role": "user", "content": user_input})

        return messages

    def chat(self, user_input):
        messages = self.build_messages(user_input)

        response = ollama.chat(
            model="qwen3:0.6b",  
            messages=messages
        )

        reply = response['message']['content']

        self.add_message("user", user_input)
        self.add_message("assistant", reply)

        return reply

    def reset(self):
        self.history = []