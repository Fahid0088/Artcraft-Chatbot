import ollama  # import ollama library to talk to local model
import time    

start_time = time.time()

response = ollama.chat(
    model="qwen:0.5b", 
    messages=[
        {
            "role": "system", #System Prompt
            "content": "You are a helpful assistant for ArtCraft, an art supply store."
        },
        {
            "role": "user", #User Prompt
            "content": "What paper do I need for making hand made paper houses?"
        }
    ]
)

end_time = time.time()

print("Model Response:")
print(response['message']['content'])

print(f"\nResponse Time: {end_time - start_time:.2f} seconds")