import os
import json
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Ensure we load the environment variables before importing the service
load_dotenv()

from agents.gemini_service import detect_intent_gemini

def run_tests():
    test_cases = [
        "mujhe plumber chahiye karachi mai",
        "jaldi electrician chahiye DHA mein",
        "ac band hogaya",
        "darwaza toot gaya lahore",
        "deewar pe rang karwana hai",
        "water leak ho raha hai"
    ]
    
    print(f"Testing Gemini API Integration...")
    print(f"API Key present: {'GEMINI_API_KEY' in os.environ}")
    print("-" * 50)
    
    for i, tc in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{tc}'")
        result = detect_intent_gemini(tc)
        print(f"Result: {json.dumps(result, indent=2) if result else 'None'}")
        
if __name__ == "__main__":
    run_tests()
