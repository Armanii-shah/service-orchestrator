import json
import re
import difflib
from datetime import datetime

class IntentAgent:
    """
    Intent Agent for Service Orchestrator.
    Parses user natural language input (Urdu, Roman Urdu, English)
    to extract actionable fields: service_type, location, time, and urgency.
    """
    
    def __init__(self):
        self.agent_name = "Intent_Agent"
        
        # Load dotenv to read environment variables (e.g. GEMINI_API_KEY)
        from dotenv import load_dotenv
        load_dotenv()
        
        # ----------------------------------------------------
        # NLP Keyword Mappings
        # ----------------------------------------------------
        
        # 1. Services
        self.services = {
            "electrician": ["bijli", "bijlee", "light", "fan", "wiring", "elec", "electric", "current", "board", "meter", "fuse", "tube", "bulb", "switch", "socket", "short circuit"],
            "plumber": ["plumber", "plmbr", "pumbler", "nal", "nala", "pipe", "pani", "water", "leak", "tap", "shower", "motor", "tank", "drain", "sewage", "washroom", "bathroom", "kitchen sink", "geyser", "heater"],
            "ac_technician": ["ac", "air conditioner", "cooling", "split", "compressor", "gas", "refill", "outdoor", "indoor", "remote", "thermostat", "chilling", "thanda", "garmi", "heat"],
            "carpenter": ["darwaza", "door", "khidki", "window", "table", "chair", "bed", "almari", "cabinet", "shelf", "wood", "lakar", "furniture", "repair", "tighten", "hinge", "handle"],
            "painter": ["rang", "paint", "color", "wall", "deewar", "whitewash", "distemper", "roof", "ceiling", "brush", "roller", "polish", "varnish", "texture", "design"]
        }
        
        # 2. Locations (Pakistani contexts)
        self.locations = [
            "g-13", "f-7", "f-11", "johar town", "dha phase 2", "dha", "saddar",
            "bahria town", "gulshan-e-iqbal", "جی تیرہ",
            # Islamabad
            "blue area", "f-6", "f-8", "f-10", "g-6", "g-7", "g-8", "g-11", "h-8", "h-12", "i-10", "i-14", "b-17",
            # Lahore
            "gulberg", "defence", "township", "wapda town", "iqbal town", "garden town",
            # Karachi
            "nazimabad", "north nazimabad", "korangi", "malir", "liaquatabad",
            # Rawalpindi
            "westridge", "chaklala", "shamsabad", "satellite town"
        ]
        
        # 3. Time Expressions
        self.times = {
            "tomorrow_morning": ["kal subah", "tomorrow morning", "کل صبح"],
            "today_evening": ["aaj shaam", "today evening", "آج شام"],
            "immediate": ["foran", "abhi", "immediate", "jaldi", "فوراً"],
            "next_week": ["next week", "agle hafte", "اگلے ہفتے"]
        }
        
        # 4. Urgency Indicators
        self.urgency_high = ["jaldi", "fori", "emergency", "urgent", "abhi", "instant", "critical", "立刻", "fauri"]

    def detect_language(self, text: str) -> str:
        """
        Detects whether the text is Urdu script, Roman Urdu, or English.
        """
        # Check for Urdu script characters (\u0600-\u06FF)
        if any('\u0600' <= char <= '\u06FF' for char in text):
            return "Urdu"
            
        text_lower = text.lower()
        # Common Roman Urdu stopwords/indicators
        roman_urdu_words = ["mujhe", "chahiye", "hai", "mein", "bhai", "nahi", "haan"]
        
        if any(word in text_lower.split() for word in roman_urdu_words):
            return "Roman Urdu"
            
        # Fallback to English
        return "English"

    def detect_service_from_keywords(self, user_input: str) -> dict:
        if not user_input or not isinstance(user_input, str):
            return {"service": None, "confidence": 0.0, "matched_keyword": None, "all_scores": {}}

        clean_input = re.sub(r'[^\w\s]', '', user_input.lower())
        tokens = clean_input.split()
        
        all_scores = {s: 0.0 for s in self.services.keys()}
        
        # 1. Exact Match Priority (Strict)
        for service, keywords in self.services.items():
            for kw in keywords:
                kw_tokens = kw.split()
                kw_len = len(kw_tokens)
                for i in range(len(tokens) - kw_len + 1):
                    phrase = " ".join(tokens[i:i+kw_len])
                    if phrase == kw:
                        all_scores[service] = 1.0
                        return {
                            "service": service,
                            "confidence": 1.0,
                            "matched_keyword": kw,
                            "all_scores": all_scores
                        }
        
        # 2. Fuzzy Match Fallback (Threshold: 0.7)
        best_service = None
        highest_score = 0.0
        matched_kw = None

        for service, keywords in self.services.items():
            service_best = 0.0
            for kw in keywords:
                kw_tokens = kw.split()
                kw_len = len(kw_tokens)
                
                for i in range(len(tokens) - kw_len + 1):
                    phrase = " ".join(tokens[i:i+kw_len])
                    score = difflib.SequenceMatcher(None, phrase, kw).ratio()
                    
                    if score > service_best:
                        service_best = score
                        
                    if score >= 0.7 and score > highest_score:
                        highest_score = score
                        best_service = service
                        matched_kw = kw
                        
            all_scores[service] = service_best
                        
        return {
            "service": best_service, 
            "confidence": round(highest_score, 2), 
            "matched_keyword": matched_kw,
            "all_scores": all_scores
        }

    def call_gemini_api(self, user_input: str) -> dict:
        """
        Attempts to call the Google Gemini API (gemini-1.5-flash) to parse the intent.
        Returns a parsed JSON dictionary, or None if the API fails or is not configured.
        """
        import os
        import requests
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        prompt = (
            "You are the Intent Agent for a Service Orchestrator application in Pakistan. "
            "Your job is to parse natural language user messages (which can be in English, Urdu, or Roman Urdu like 'mujhe plumber chahiye karachi mai') "
            "and extract structured intent details.\n\n"
            "Extract the following:\n"
            "1. 'service': One of 'plumber', 'electrician', 'ac_technician', 'carpenter', 'painter', or null. Look carefully at local Urdu or Roman Urdu terms like 'bijli', 'water', 'nal', 'ac thanda nahi kar raha', 'darwaza toota hai', 'deewar rang'.\n"
            "2. 'city': One of 'karachi', 'lahore', 'islamabad', 'rawalpindi', 'faisalabad', or null. Look for local variations or abbreviations like 'khi', 'lhr', 'isb', 'pindi'.\n"
            "3. 'area': The specific local area/landmark if mentioned (e.g., 'DHA', 'Johar Town', 'G-13', 'Clifton'), or null.\n"
            "4. 'urgency': 'high' if words indicating emergency or active flooding/short circuits are present; otherwise 'normal'.\n"
            "5. 'confidence': A score between 0.0 and 1.0 indicating how confident you are in your service detection.\n\n"
            "You must respond ONLY with a valid JSON block of this schema. Do not put markdown like ```json:\n"
            "{\n"
            "  \"service\": \"plumber|electrician|ac_technician|carpenter|painter|null\",\n"
            "  \"city\": \"karachi|lahore|islamabad|rawalpindi|faisalabad|null\",\n"
            "  \"area\": \"string|null\",\n"
            "  \"urgency\": \"low|medium|high\",\n"
            "  \"confidence\": 0.0-1.0\n"
            "}\n\n"
            f"User message: \"{user_input}\""
        )
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                text_response = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                # Clean up any potential markdown wraps
                text_response = re.sub(r"^```json\s*", "", text_response)
                text_response = re.sub(r"\s*```$", "", text_response)
                parsed = json.loads(text_response)
                return parsed
        except Exception as e:
            print(f"[Gemini API Exception] {e}")
            
        return None

    def execute(self, user_input: str, user_details: dict = None) -> dict:
        """
        Executes the agent's logic to parse intent and extract structured data.
        Returns a structured log object including the final output or error.
        """
        timestamp = datetime.now().isoformat()
        
        # Step 1: Attempt Gemini LLM extraction
        gemini_data = self.call_gemini_api(user_input)
        
        if gemini_data:
            language = self.detect_language(user_input)
            extracted_service = gemini_data.get("service")
            if extracted_service == "null" or not extracted_service:
                extracted_service = None
                
            service_confidence = gemini_data.get("confidence", 1.0)
            matched_keyword = "gemini_llm"
            all_scores = {extracted_service: service_confidence} if extracted_service else {}
            
            extracted_location = gemini_data.get("area")
            if extracted_location == "null" or not extracted_location:
                extracted_location = None
                
            extracted_city = gemini_data.get("city")
            if extracted_city == "null" or not extracted_city:
                extracted_city = None
                
            urgency = gemini_data.get("urgency", "normal")
            confidence = min(round(service_confidence, 2), 1.0)
            
            # Map/Normalize location
            if extracted_location:
                extracted_location = extracted_location.title().replace("Dha", "DHA")
                extracted_location = re.sub(r'\b([A-Za-z])-(\d+)\b', lambda m: f"{m.group(1).upper()}-{m.group(2)}", extracted_location)
                
            reasoning = "Extracted via Google Gemini API."
            extracted_time = "immediate"
        else:
            # Step 2: Fallback to Local Keyword-based parsing
            text_lower = user_input.lower()
            
            # Step 1: Detect Language
            language = self.detect_language(user_input)
            
            # Step 2: Extract Service Type via Fuzzy Keyword Matching
            service_data = self.detect_service_from_keywords(user_input)
            extracted_service = service_data["service"]
            service_confidence = service_data["confidence"]
            matched_keyword = service_data["matched_keyword"]
            all_scores = service_data.get("all_scores", {})
                    
            # Step 3: Extract Location
            extracted_location = None
            extracted_city = None
            location_confidence_bonus = 0.0
            
            # Pre-process text to convert things like "g 13" to "g-13"
            normalized_text = re.sub(r'\b([a-z])\s+(\d{1,2})\b', r'\1-\2', text_lower)
            
            # Match hardcoded locations (longest first)
            for loc in sorted(self.locations, key=len, reverse=True):
                if loc in normalized_text:
                    if loc == "جی تیرہ": 
                        extracted_location = "G-13" 
                    else:
                        extracted_location = loc.title().replace("Dha", "DHA")
                        extracted_location = re.sub(r'\b([A-Za-z])-(\d+)\b', lambda m: f"{m.group(1).upper()}-{m.group(2)}", extracted_location)
                    location_confidence_bonus = 0.4
                    break
                    
            # Regex fallback 1: sector formats like G-13, F-11
            if not extracted_location:
                match = re.search(r'\b([a-z])\s*-?\s*(\d{1,2})\b', text_lower)
                if match:
                    extracted_location = f"{match.group(1).upper()}-{match.group(2)}"
                    location_confidence_bonus = 0.4
    
            # Regex fallback 2: known locality names
            if not extracted_location:
                match = re.search(r'\b([a-z]+(?:\s+[a-z]+)?\s+(?:town|area|colony|phase\s+\d+|block\s+[a-z0-9]+))\b', text_lower)
                if match:
                    extracted_location = match.group(1).title()
                    location_confidence_bonus = 0.4
    
            # Regex fallback 3: Any capitalized word sequence from original input
            if not extracted_location:
                cap_matches = re.findall(r'\b[A-Z][a-z]+\b(?:\s+[A-Z][a-z]+)*', user_input)
                for cap_match in cap_matches:
                    if cap_match.lower() not in ["mujhe", "i", "we", "he", "she", "they", "kya", "please", "can"]:
                        extracted_location = cap_match
                        location_confidence_bonus = 0.1  # Low confidence
                        break
    
            # Step 4: Extract Time
            extracted_time = None
            for time_val, keywords in self.times.items():
                if any(kw in text_lower for kw in keywords):
                    extracted_time = time_val
                    break
                    
            # Step 5: Extract Urgency via Fuzzy Matching
            urgency = "normal"
            clean_input = re.sub(r'[^\w\s]', '', text_lower)
            tokens = clean_input.split()
            
            for kw in self.urgency_high:
                kw_tokens = kw.split()
                kw_len = len(kw_tokens)
                for i in range(len(tokens) - kw_len + 1):
                    phrase = " ".join(tokens[i:i+kw_len])
                    if difflib.SequenceMatcher(None, phrase, kw).ratio() >= 0.7:
                        urgency = "high"
                        if not extracted_time:
                            extracted_time = "immediate" 
                        break
                if urgency == "high":
                    break 
                    
            # Default time if still not found
            if not extracted_time:
                extracted_time = "flexible"
                
            # Step 6: Calculate Confidence Score (0.0 to 1.0)
            confidence = 0.0
            if extracted_service: confidence += (service_confidence * 0.5) # Weight service match heavily
            if extracted_location: confidence += location_confidence_bonus
            if extracted_time != "flexible": confidence += 0.1
            if urgency == "high": confidence += 0.1
            
            # Ensure precision limits
            confidence = min(round(confidence, 2), 1.0)
            
            # Generate trace reasoning
            reasoning_parts = [f"Language detected: {language}."]
            if extracted_service: reasoning_parts.append(f"Found service '{extracted_service}' (matched: '{matched_keyword}' score: {service_confidence}).")
            if extracted_location: reasoning_parts.append(f"Found location '{extracted_location}'.")
            if urgency == "high": reasoning_parts.append("High urgency detected.")
            reasoning = " ".join(reasoning_parts)
        
        # Step 7: Apply Error Handling and build final output payload
        decision = "Proceed"
        output_data = {}
        
        preferred_city = user_details.get("preferred_city") if user_details else None
        # Let Gemini detected city override preferred_city if available
        if 'extracted_city' in locals() and extracted_city:
            preferred_city = extracted_city
        elif gemini_data and gemini_data.get("city"):
            g_city = gemini_data.get("city")
            if g_city != "null" and g_city:
                preferred_city = g_city
        
        if not extracted_service:
            decision = "Error: Missing Service"
            output_data = {
                "error": "Service not detected",
                "clarification": "Aapko konsi service chahiye? Plumber, Electrician, AC, Carpenter, ya Painter?"
            }
        elif not extracted_location and not preferred_city:
            decision = "Error: Missing Location"
            output_data = {
                "error": "Location not detected",
                "clarification": "Aap ka area konsa hai? (e.g., G-13, Johar Town, DHA)"
            }
        elif not extracted_location and preferred_city:
            # We have a city, but no local area! We MUST ask for the area.
            decision = "Error: Missing Area"
            popular_areas = []
            city_lower = preferred_city.lower()
            if city_lower == "karachi": popular_areas = ["DHA", "Malir", "Chorangi", "Gulshan-e-Iqbal", "Clifton", "Nazimabad", "Korangi", "North Karachi", "Other"]
            elif city_lower == "lahore": popular_areas = ["Johar Town", "DHA", "Gulberg", "Model Town", "Wapda Town", "Garden Town", "Defence", "Other"]
            elif city_lower == "islamabad": popular_areas = ["G-13", "F-10", "Blue Area", "I-8", "G-11", "F-7", "E-11", "Other"]
            elif city_lower == "rawalpindi": popular_areas = ["Saddar", "Satellite Town", "Chaklala", "Westridge", "Murree Road", "Other"]
            elif city_lower == "faisalabad": popular_areas = ["Madina Town", "Jinnah Colony", "Peoples Colony", "Gulberg", "Other"]
            else: popular_areas = ["City Center", "Other"]
            
            output_data = {
                "error": "Missing Area",
                "clarification": "Pehle area select karein. " + preferred_city.title() + " ke kaunse area mein chahiye?",
                "suggested_areas": popular_areas,
                "city": preferred_city,
                "service": extracted_service,
                "matched_keyword": matched_keyword,
                "all_scores": all_scores
            }
            
        if not output_data and confidence < 0.6 and not preferred_city:
            decision = "Error: Low Confidence"
            output_data = {
                "error": "Low confidence",
                "clarification": "Kya aap repeat kar sakte hain?"
            }
        elif not output_data:
            decision = "Success: Intent Extracted"
            output_data = {
                "service_type": extracted_service,
                "location": extracted_location,
                "time": extracted_time,
                "urgency": urgency,
                "confidence": confidence,
                "matched_keyword": matched_keyword,
                "all_scores": all_scores
            }
            
        # Step 8: Construct and return standardized Agent Log format
        agent_log = {
            "timestamp": timestamp,
            "agent_name": self.agent_name,
            "input": user_input,
            "reasoning": reasoning,
            "decision": decision,
            "output": output_data
        }
        
        return agent_log

# =====================================================================
# Test Cases
# =====================================================================
if __name__ == "__main__":
    agent = IntentAgent()
    
    print("--- Test Case 1: Fuzzy Keyword Match (Electrician) ---")
    tc1 = "bijli theek karwani hai"
    print(f"Input: {tc1}")
    print(json.dumps(agent.execute(tc1), indent=2))
    
    print("\n--- Test Case 2: Fuzzy Keyword Match (AC Technician) ---")
    tc2 = "ac band hogaya"
    print(f"Input: {tc2}")
    print(json.dumps(agent.execute(tc2), indent=2))
    
    print("\n--- Test Case 3: Fuzzy Keyword Match (Plumber) ---")
    tc3 = "nal leak horaha hai"
    print(f"Input: {tc3}")
    print(json.dumps(agent.execute(tc3), indent=2))

    print("\n--- Test Case 4: Fuzzy Keyword Match (Carpenter) ---")
    tc4 = "darwaza toot gaya"
    print(f"Input: {tc4}")
    print(json.dumps(agent.execute(tc4), indent=2))

    print("\n--- Test Case 5: Urgency and Service ---")
    tc5 = "jaldi chahiye deewar ka rang karna hai"
    print(f"Input: {tc5}")
    print(json.dumps(agent.execute(tc5), indent=2))
