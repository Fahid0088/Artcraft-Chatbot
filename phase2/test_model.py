import ollama  # import ollama library to talk to local model
import time    

start_time = time.time()

response = ollama.chat(
    model="qwen3:0.6b", 
    messages=[
        {
            "role": "system", #System Prompt
            "content": "You are a helpful assistant for ArtCraft, an art supply store."
        },
        {
            "role": "user", #User Prompt
            "content": "What brushes do I need for watercolor painting?"
        }
    ]
)

end_time = time.time()

print("Model Response:")
print(response['message']['content'])

print(f"\nResponse Time: {end_time - start_time:.2f} seconds")