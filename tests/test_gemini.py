import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print("API KEY Starts with:", api_key[:10] if api_key else "None")
genai.configure(api_key=api_key)

try:
    print("Listing models...")
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(f"Embedding Model: {m.name}")
except Exception as e:
    print("Error listing models:", e)
