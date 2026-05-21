import json
import math
from datetime import datetime

class ProviderAgent:
    """
    Provider Agent for Service Orchestrator.
    Queries the mock database of registered service providers and ranks them
    based on a distance, rating, and availability scoring algorithm.
    """
    
    def __init__(self, providers_db: list):
        self.agent_name = "Provider_Agent"
        self.providers_db = providers_db

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates distance in kilometers between two GPS coordinates using the Haversine formula."""
        R = 6371.0 # Radius of the earth in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return round(R * c, 2)

    def execute(self, service_type: str, user_coords: dict, requested_time: str, city: str = "unknown", urgency: str = "medium") -> dict:
        """
        Executes the agent's logic to find and rank the best service providers.
        Urgency level adjusts the scoring weights:
          - high:   Distance 50%, Availability 30%, Rating 20%  (speed matters most)
          - medium: Distance 40%, Rating 40%, Availability 20%  (balanced)
          - low:    Rating 50%, Distance 30%, Availability 20%  (quality matters most)
        """
        timestamp = datetime.now().isoformat()
        
        user_lat = user_coords.get("lat")
        user_lng = user_coords.get("lng")

        # Dynamic weights based on urgency
        if urgency == "high":
            w_dist, w_rating, w_avail = 50, 20, 30
        elif urgency == "low":
            w_dist, w_rating, w_avail = 30, 50, 20
        else:  # medium / normal
            w_dist, w_rating, w_avail = 40, 40, 20
        
        # 1. Filter providers by required service and city
        matching_providers = [p for p in self.providers_db if p.get("service") == service_type]
        if city and city != "unknown":
            matching_providers = [p for p in matching_providers if p.get("city", "").lower() == city.lower()]
            
        ranked_providers = []
        
        # 2. Score each matching provider
        for provider in matching_providers:
            # Calculate distance
            dist_km = self.calculate_distance(user_lat, user_lng, provider["lat"], provider["lng"])
            
            # Distance Score — scaled to weight
            distance_score = max(0, w_dist - (dist_km * (w_dist / 20)))
            
            # Rating Score — scaled to weight
            rating = provider.get("rating", 0.0)
            rating_score = (rating / 5.0) * w_rating
            
            # Availability Score — scaled to weight
            is_available = provider.get("available", False)
            availability_score = w_avail if is_available else 0
            
            # Total Score (Max 100)
            total_score = distance_score + rating_score + availability_score
            
            # Construct human-readable reasoning for the user UI
            dist_label = "Very close" if dist_km < 3 else "Nearby" if dist_km < 10 else "Further away"
            urgency_note = " Prioritised for fast response due to high urgency." if urgency == "high" else ""
            reasoning_ui = (
                f"{dist_label} ({dist_km} km away). "
                f"Rating: ⭐{rating}/5. "
                f"Available: {'Yes' if is_available else 'No'}."
                f"{urgency_note}"
            )
            
            ranked_providers.append({
                "id": provider["id"],
                "name": provider["name"],
                "distance_km": dist_km,
                "rating": rating,
                "score": round(total_score, 1),
                "reasoning": reasoning_ui,
                "_debug_math": f"Urgency={urgency}. Weights: dist={w_dist}, rating={w_rating}, avail={w_avail}. Dist_Score={round(distance_score,1)}, Rating_Score={round(rating_score,1)}, Avail={availability_score}"
            })

        # 3. Sort providers by total score descending
        ranked_providers.sort(key=lambda x: x["score"], reverse=True)
        
        # 4. Take top 3
        top_3 = ranked_providers[:3]
        
        # 5. Build Agent Log and Decision handling
        decision = "Proceed"
        output_data = {}
        reasoning_log = ""
        
        tool_used = "db_query"
        tool_input = f"SELECT * FROM providers WHERE service='{service_type}' AND city='{city}'"
        
        if not top_3:
            decision = "Error: No Providers Found"
            reasoning_log = f"Found 0 providers for service '{service_type}' in city '{city}'."
            output_data = {
                "error": "No providers available",
                "message": f"Sorry, abhi {city.title() if city != 'unknown' else 'is ilaqay'} mein providers available nahi hain."
            }
            tool_output = "0 rows returned"
        else:
            best_match = top_3[0]
            decision = "Success: Return top 3 providers sorted by score"
            reasoning_log = (f"Found {len(matching_providers)} providers. Top match '{best_match['name']}' "
                             f"with score {best_match['score']}. {best_match['_debug_math']}")
            
            # Remove debug math before sending to user
            for p in top_3:
                p.pop("_debug_math", None)
                
            output_data = {"top_providers": top_3}
            tool_output = f"{len(matching_providers)} rows returned. Sorted and ranked."

        # 6. Construct standard Agent Log format
        agent_log = {
            "timestamp": timestamp,
            "agent_name": self.agent_name,
            "input": json.dumps({"service": service_type, "lat": user_lat, "lng": user_lng, "time": requested_time, "urgency": urgency}),
            "reasoning": reasoning_log,
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
    
    # Mock Database of Pakistani Service Providers
    MOCK_PROVIDERS = [
        {
            "id": "PROV-889",
            "name": "Kamran AC Services",
            "service": "ac_technician",
            "lat": 33.6844, "lng": 73.0479, # G-13 Islamabad
            "area": "G-13",
            "rating": 4.8,
            "available": True
        },
        {
            "id": "PROV-412",
            "name": "Irfan Technician",
            "service": "ac_technician",
            "lat": 33.6833, "lng": 72.9833, # F-11 Islamabad (Further away from G-13)
            "area": "F-11",
            "rating": 4.9,
            "available": True
        },
        {
            "id": "PROV-992",
            "name": "Aslam Plumbing Works",
            "service": "plumber",
            "lat": 31.4697, "lng": 74.2800, # Johar Town Lahore
            "area": "Johar Town",
            "rating": 4.8,
            "available": True
        }
    ]
    
    agent = ProviderAgent(providers_db=MOCK_PROVIDERS)
    
    print("--- Test Case 1: AC Technician in Islamabad (G-13) ---")
    # Coordinates for G-13: 33.6844, 73.0479
    tc1_coords = {"lat": 33.6844, "lng": 73.0479}
    result1 = agent.execute(service_type="ac_technician", user_coords=tc1_coords, requested_time="tomorrow_morning")
    print(json.dumps(result1, indent=2))
    
    print("\n--- Test Case 2: Plumber in Lahore (Johar Town) ---")
    # Coordinates for Johar Town: 31.4697, 74.2800
    tc2_coords = {"lat": 31.4697, "lng": 74.2800}
    result2 = agent.execute(service_type="plumber", user_coords=tc2_coords, requested_time="immediate")
    print(json.dumps(result2, indent=2))
    
    print("\n--- Test Case 3: No Provider Found (Carpenter) ---")
    result3 = agent.execute(service_type="carpenter", user_coords=tc1_coords, requested_time="flexible")
    print(json.dumps(result3, indent=2))
