import ollama  
from prompt_template import SYSTEM_PROMPT  

class ConversationManager:
    def __init__(self):
        self.history = []
        self.max_history = 5

    def add_message(self, role, content):
        # role is either "user" or "assistant"
        self.history.append({"role": role, "content": content})

        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def build_messages(self, user_input):
        # Add system prompt 
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add previous messages
        messages += self.history

        # Add user message
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