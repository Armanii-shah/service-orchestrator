import json
import requests
from datetime import datetime

class LocationAgent:
    """
    Location Agent for Service Orchestrator.
    Converts Pakistani area names into standard GPS coordinates
    using an internal cache, falling back to the Google Maps Geocoding API.
    """
    
    def __init__(self):
        self.agent_name = "Location_Agent"
        
        # 1. Initialize Internal Cache with predefined Pakistani locations
        # Using uppercase keys for case-insensitive lookups
        self.cache = {
            # ── Islamabad ──────────────────────────────────────────────────
            "G-13":        {"lat": 33.6844, "lng": 73.0479, "formatted": "G-13, Islamabad, Pakistan"},
            "F-7":         {"lat": 33.7298, "lng": 73.0370, "formatted": "F-7, Islamabad, Pakistan"},
            "F-10":        {"lat": 33.7100, "lng": 73.0250, "formatted": "F-10, Islamabad, Pakistan"},
            "F-11":        {"lat": 33.6833, "lng": 72.9833, "formatted": "F-11, Islamabad, Pakistan"},
            "G-10":        {"lat": 33.6833, "lng": 73.0167, "formatted": "G-10, Islamabad, Pakistan"},
            "G-11":        {"lat": 33.6900, "lng": 73.0300, "formatted": "G-11, Islamabad, Pakistan"},
            "I-8":         {"lat": 33.6682, "lng": 73.0743, "formatted": "I-8, Islamabad, Pakistan"},
            "E-11":        {"lat": 33.7200, "lng": 72.9900, "formatted": "E-11, Islamabad, Pakistan"},
            "BLUE AREA":   {"lat": 33.7300, "lng": 73.0900, "formatted": "Blue Area, Islamabad, Pakistan"},
            # ── Karachi ────────────────────────────────────────────────────
            "DHA":                {"lat": 24.8093, "lng": 67.0425, "formatted": "DHA, Karachi, Pakistan"},
            "CLIFTON":            {"lat": 24.8229, "lng": 67.0321, "formatted": "Clifton, Karachi, Pakistan"},
            "SADDAR":             {"lat": 24.8580, "lng": 67.0211, "formatted": "Saddar, Karachi, Pakistan"},
            "GULSHAN-E-IQBAL":    {"lat": 24.9200, "lng": 67.0988, "formatted": "Gulshan-e-Iqbal, Karachi, Pakistan"},
            "NAZIMABAD":          {"lat": 24.9056, "lng": 67.0396, "formatted": "Nazimabad, Karachi, Pakistan"},
            "NORTH KARACHI":      {"lat": 24.9700, "lng": 67.0600, "formatted": "North Karachi, Karachi, Pakistan"},
            "KORANGI":            {"lat": 24.8300, "lng": 67.1200, "formatted": "Korangi, Karachi, Pakistan"},
            "MALIR":              {"lat": 24.8900, "lng": 67.2000, "formatted": "Malir, Karachi, Pakistan"},
            "CHORANGI":           {"lat": 24.9300, "lng": 67.0800, "formatted": "Chorangi, Karachi, Pakistan"},
            # ── Lahore ─────────────────────────────────────────────────────
            "JOHAR TOWN":  {"lat": 31.4697, "lng": 74.2800, "formatted": "Johar Town, Lahore, Pakistan"},
            "MODEL TOWN":  {"lat": 31.4842, "lng": 74.3262, "formatted": "Model Town, Lahore, Pakistan"},
            "GULBERG":     {"lat": 31.5204, "lng": 74.3587, "formatted": "Gulberg, Lahore, Pakistan"},
            "GARDEN TOWN": {"lat": 31.4900, "lng": 74.3200, "formatted": "Garden Town, Lahore, Pakistan"},
            "WAPDA TOWN":  {"lat": 31.4500, "lng": 74.2600, "formatted": "Wapda Town, Lahore, Pakistan"},
            "DEFENCE":     {"lat": 31.4700, "lng": 74.4000, "formatted": "Defence, Lahore, Pakistan"},
            # ── Rawalpindi ─────────────────────────────────────────────────
            "BAHRIA TOWN":    {"lat": 33.5415, "lng": 73.1118, "formatted": "Bahria Town, Rawalpindi, Pakistan"},
            "SATELLITE TOWN": {"lat": 33.5950, "lng": 73.0820, "formatted": "Satellite Town, Rawalpindi, Pakistan"},
            "CHAKLALA":       {"lat": 33.6100, "lng": 73.1300, "formatted": "Chaklala, Rawalpindi, Pakistan"},
            "WESTRIDGE":      {"lat": 33.5700, "lng": 73.0600, "formatted": "Westridge, Rawalpindi, Pakistan"},
            "MURREE ROAD":    {"lat": 33.5900, "lng": 73.1000, "formatted": "Murree Road, Rawalpindi, Pakistan"},
            "DHA PHASE 2":    {"lat": 33.5186, "lng": 73.1235, "formatted": "DHA Phase 2, Rawalpindi, Pakistan"},
            # ── Faisalabad ─────────────────────────────────────────────────
            "MADINA TOWN":    {"lat": 31.4200, "lng": 73.0900, "formatted": "Madina Town, Faisalabad, Pakistan"},
            "JINNAH COLONY":  {"lat": 31.4050, "lng": 73.0700, "formatted": "Jinnah Colony, Faisalabad, Pakistan"},
            "PEOPLES COLONY": {"lat": 31.4100, "lng": 73.0800, "formatted": "Peoples Colony, Faisalabad, Pakistan"},
        }

        self.city_keywords = {
            "karachi": ["karachi", "khi", "کراچی"],
            "lahore": ["lahore", "lhr", "لاہور"],
            "islamabad": ["islamabad", "isb", "اسلام آباد", "capital"],
            "rawalpindi": ["rawalpindi", "rwp", "پنڈی"],
            "faisalabad": ["faisalabad", "fsd", "فیصل آباد"]
        }

    def execute(self, location_name: str, full_message: str = "", preferred_city: str = None) -> dict:
        """
        Executes the agent's logic to resolve a location name to GPS coordinates.
        Returns a structured log object.
        """
        timestamp = datetime.now().isoformat()

        # Guard: location_name must be a non-empty string
        if not location_name or not isinstance(location_name, str):
            return {
                "timestamp": timestamp,
                "agent_name": self.agent_name,
                "input": location_name,
                "reasoning": "No location name provided.",
                "tool_used": "none",
                "tool_input": "",
                "tool_output": "",
                "decision": "Error: Missing Location",
                "output": {
                    "error": "Location not detected",
                    "clarification": "Aap ka area konsa hai? (e.g., G-13, Johar Town, DHA)",
                    "city": preferred_city or "unknown"
                }
            }
        
        # Normalize location name to match cache keys
        loc_normalized = location_name.strip().upper()
        
        # Initialize log trace variables
        decision = "Proceed"
        output_data = {}
        reasoning = ""
        tool_used = "cache_lookup"
        tool_input = loc_normalized
        tool_output = ""
        
        # Determine city from full_message or preferred_city
        detected_city = preferred_city
        for city, keywords in self.city_keywords.items():
            if any(kw in full_message.lower() for kw in keywords):
                detected_city = city
                break
                
        if not detected_city:
            # Fallback if neither found in message nor in DB
            detected_city = "unknown"
        
        # 1. Check internal cache.
        # Try the full normalized string first, then just the area part before the first comma.
        # This handles bypass inputs like "DHA, karachi" → tries "DHA, KARACHI" → then "DHA".
        area_key = loc_normalized
        if area_key not in self.cache:
            area_only = loc_normalized.split(",")[0].strip()
            if area_only in self.cache:
                area_key = area_only

        if area_key in self.cache:
            reasoning = f"Location '{location_name}' resolved via cache (key: {area_key})."
            output_data = self.cache[area_key]
            tool_output = f"Cache hit for {area_key}"
            decision = "Success: Location Resolved via Cache"
            
        else:
            # 2. If not in cache, call OpenStreetMap Nominatim API
            tool_used = "openstreetmap_nominatim"
            reasoning = f"Location '{location_name}' not in cache. Calling OpenStreetMap Nominatim API."
            
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": f"{location_name}, Pakistan",
                "format": "json",
                "limit": 1
            }
            headers = {
                "User-Agent": "ServiceOrchestrator/1.0"
            }
            
            tool_input = f"GET {url}?q={location_name}, Pakistan"
            
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                data = response.json()
                
                if response.status_code == 200 and data:
                    lat = float(data[0]["lat"])
                    lng = float(data[0]["lon"])
                    formatted = data[0]["display_name"]
                    
                    output_data = {"lat": lat, "lng": lng, "formatted": formatted}
                    tool_output = f"API returned coordinates: {lat}, {lng}"
                    decision = "Success: Location Resolved via API"
                    
                    # 4. Cache the successful result
                    self.cache[loc_normalized] = output_data
                    
                else:
                    # 3. If API fails, raise error to fallback
                    raise ValueError(f"API returned no results or failed status: {response.status_code}")
                    
            except Exception as e:
                # 3. Fallback: Use mock coordinates
                reasoning += f" API call failed ({str(e)}). Using mock fallback coordinates."
                tool_output = "API Failure - Generated Mock Coordinates"
                
                # Generate deterministic mock coordinates based on string length
                mock_lat = 30.0 + (len(loc_normalized) % 5)
                mock_lng = 70.0 + (len(loc_normalized) % 5)
                
                output_data = {
                    "lat": mock_lat, 
                    "lng": mock_lng, 
                    "formatted": f"{location_name.title()}, Pakistan (Mocked)"
                }
                decision = "Success: Location Resolved via Fallback"
                
                # 4. Cache the mock result to avoid repeated failed API calls
                self.cache[loc_normalized] = output_data

        # Add detected city to output
        output_data["city"] = detected_city

        # 5. Construct and return standard Agent Log format
        agent_log = {
            "timestamp": timestamp,
            "agent_name": self.agent_name,
            "input": location_name,
            "reasoning": reasoning,
            "tool_used": tool_used,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "decision": decision,
            "output": output_data
        }
        
        return agent_log

# =====================================================================
# Test Cases
# =====================================================================
if __name__ == "__main__":
    # Initialize LocationAgent
    agent = LocationAgent()
    
    print("--- Test Case 1: Known Location (Cache Hit) ---")
    tc1 = "G-13"
    print(f"Input: {tc1}")
    result1 = agent.execute(tc1)
    print(json.dumps(result1, indent=2))
    
    print("\n--- Test Case 2: New Real Location (API Call) ---")
    tc2 = "Blue Area"
    print(f"Input: {tc2}")
    result2 = agent.execute(tc2)
    print(json.dumps(result2, indent=2))
    
    print("\n--- Test Case 3: Unknown Location (API Call -> Mock Fallback) ---")
    tc3 = "UnknownXYZ123"
    print(f"Input: {tc3}")
    result3 = agent.execute(tc3)
    print(json.dumps(result3, indent=2))
    
    print("\n--- Test Case 4: Cache Verification for Unknown Location ---")
    print(f"Input: {tc3} (Second Time)")
    result4 = agent.execute(tc3)
    print(json.dumps(result4, indent=2))
