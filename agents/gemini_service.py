import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def detect_intent_gemini(user_input: str) -> dict:
    """
    Uses Google Gemini to parse user intent for the Service Orchestrator.
    Returns structured output or None if it fails.
    """
    print(f"[GEMINI] Input: {user_input}")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[GEMINI] API Key not found. Please set GEMINI_API_KEY in .env.")
        return None
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
You are an expert NLP parser for a home services app in Pakistan.
The user will send a message in Urdu, Roman Urdu, or English.
Your job is to extract the core intent and return a valid JSON object.

Extract the following:
1. "service": "plumber", "electrician", "ac_technician", "carpenter", "painter", or null. Look carefully at local Urdu or Roman Urdu terms like 'bijli', 'water', 'nal', 'ac thanda nahi kar raha', 'darwaza toota hai' (carpenter), 'deewar rang'.
2. "city": "karachi", "lahore", "islamabad", "rawalpindi", "faisalabad", or null. Look for variations like 'khi', 'lhr', 'isb', 'pindi'.
3. "area": The local area or landmark if mentioned (e.g., "DHA", "Johar Town", "G-13", "Clifton", "Gulberg"), or null.
4. "urgency": "high" if emergency words like 'jaldi', 'urgently', 'emergency', 'pani beh raha hai', 'short circuit' are present; otherwise "medium" or "low".
5. "confidence": Score between 0.0 and 1.0.
6. "language": Detect which language the user wrote in. Return "english" if the message is in English, "roman_urdu" if written in Roman script Urdu/Urdu words using English letters, or "urdu" if written in Urdu script.

Rules:
- Respond ONLY with the JSON object. Do not include markdown code blocks.
- If you cannot detect a service, return null for "service".

JSON Schema:
{{
  "service": "plumber|electrician|ac_technician|carpenter|painter|null",
  "city": "karachi|lahore|islamabad|rawalpindi|faisalabad|null",
  "area": "string|null",
  "urgency": "low|medium|high",
  "confidence": 0.0-1.0,
  "language": "english|roman_urdu|urdu"
}}

User Message: "{user_input}"
        """
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        print(f"[GEMINI] Raw response: {response.text}")
        
        # Parse the JSON response
        text = response.text.strip()
        parsed = json.loads(text)
        print(f"[GEMINI] Parsed output: {parsed}")
        return parsed
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[GEMINI] ERROR: {e}\n{error_trace}")
        return None
