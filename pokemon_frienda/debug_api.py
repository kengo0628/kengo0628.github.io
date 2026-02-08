import os
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")

print(f"Checking API Key: {API_KEY[:4]}...{API_KEY[-4:] if API_KEY and len(API_KEY)>8 else '****'}")

if not API_KEY:
    print("FATAL: GEMINI_API_KEY is not set.")
    exit(1)

client = genai.Client(api_key=API_KEY)

print("\n--- Attempting to list models ---")
try:
    models = list(client.models.list())
    print(f"Found {len(models)} models.")
    for m in models:
        print(f"Model: {m.name}")
        # print(f"  Methods: {m.supported_generation_methods}") # Attribute might be different in this SDK version
except Exception as e:
    print(f"ERROR listing models: {e}")
    
print("\n--- Attempting a simpler test (gemini-2.5-flash) ---")
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Hello, are you working?',
    )
    print("SUCCESS: generate_content worked with gemini-2.5-flash")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"FAIL: generate_content failed with gemini-2.5-flash")
    print(f"Error: {e}")
