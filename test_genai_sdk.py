import os
import json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
try:
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents="Say hi!",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
