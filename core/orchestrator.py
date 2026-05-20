import sys
import os
import json
from datetime import datetime

# Adjust sys.path so we can import from the sibling 'agents' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.intent_agent import IntentAgent
from agents.location_agent import LocationAgent
from agents.provider_agent import ProviderAgent
from agents.booking_agent import BookingAgent

# Provider database is populated by main.py at startup via ORCH_DB.extend(...)
# main.py is the single source of truth — it holds the full provider list with city fields.
MOCK_PROVIDERS_DB = []


class ServiceOrchestrator:
    """
    Central brain of the multi-agent system.
    Runs user input through the 4-agent pipeline and manages contextual states.
    """
    
    # Global memory dictionary to store conversation context per user
    USER_SESSIONS = {}

    def __init__(self):
        # Initialize all 4 agents
        self.intent_agent = IntentAgent()
        self.location_agent = LocationAgent()
        self.provider_agent = ProviderAgent(providers_db=MOCK_PROVIDERS_DB)
        self.booking_agent = BookingAgent()
        
        # State management for traceability
        self.execution_log = []

    def get_execution_log(self) -> list:
        """Returns the full trace of the multi-agent workflow."""
        return self.execution_log
        
    def export_logs(self, filename: str):
        """Exports the execution log trace to a JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.execution_log, f, indent=2, ensure_ascii=False)

    def process_request(self, user_input: str, user_details: dict) -> dict:
        """
        Processes a complete user request from start to finish across all agents.
        """
        # Reset execution log for a new request
        self.execution_log = []
        
        # ==========================================
        # DIRECT TO BOOKING CHECK
        # ==========================================
        selected_provider_id = user_details.get("selected_provider_id")
        if selected_provider_id:
            service_type = user_details.get("service_type")
            location_name = user_details.get("location")
            requested_time = "immediate"
            
            selected_provider = next((p for p in MOCK_PROVIDERS_DB if p["id"] == selected_provider_id), None)
            service_details = {"service": service_type, "location": location_name}
            
            booking_log = self.booking_agent.execute(selected_provider, user_details, service_details, requested_time)
            self.execution_log.append(booking_log)
            book_out = booking_log.get("output", {})
            
            if "error" in book_out:
                return {
                    "status": "failed", 
                    "step": "booking", 
                    "error": book_out.get("error"), 
                    "message": book_out.get("message", "Provider offline. Suggesting next best option.")
                }
                
            return {
                "status": "success",
                "message": "Transaction complete",
                "booking_details": book_out,
                "total_agents_run": 1,
            }
        
        # ==========================================
        # CONTEXT-AWARE BYPASS (Awaiting Area)
        # ==========================================
        user_id = user_details.get("user_id", "unknown")
        user_context = self.USER_SESSIONS.get(user_id, {})
        
        prev_service = user_context.get("service")
        prev_city = user_context.get("city")
        
        if user_context.get("status") == "awaiting_area" and prev_service and prev_city and not selected_provider_id:
            # Clear context so it doesn't loop infinitely
            self.USER_SESSIONS[user_id] = {}
            
            # Build area string, e.g. "DHA, karachi"
            area_str = f"{user_input.strip()}, {prev_city}"
            
            intent_out = {
                "service_type": prev_service,
                "location": area_str,          # ← correct key, used by line 234
                "detected_city": prev_city,    # ← carry city forward for ProviderAgent
                "time": "immediate",
                "urgency": "normal",
                "confidence": 1.0
            }
            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "agent_name": "Intent_Agent",
                "input": f"Bypass to Area Detection. User message: {user_input}",
                "reasoning": f"Context: Service={prev_service}, City={prev_city}. Using '{user_input}' as area.",
                "tool_used": "context_bypass",
                "tool_input": "",
                "tool_output": "",
                "decision": "Bypass Intent Agent",
                "output": intent_out
            })
        else:
            # ==========================================
            # 1. INTENT AGENT (Gemini with Fallback)
            # ==========================================
            from agents.gemini_service import detect_intent_gemini
            
            gemini_data = detect_intent_gemini(user_input)
            
            if gemini_data:
                extracted_service = gemini_data.get("service")
                if extracted_service == "null": extracted_service = None
                
                extracted_city = gemini_data.get("city")
                if extracted_city == "null": extracted_city = None
                
                extracted_location = gemini_data.get("area")
                if extracted_location == "null": extracted_location = None
                
                urgency = gemini_data.get("urgency", "normal")
                confidence = gemini_data.get("confidence", 1.0)
                
                preferred_city = extracted_city or user_details.get("preferred_city")
                
                if not extracted_service:
                    intent_out = {
                        "error": "Service not detected",
                        "clarification": "Aapko konsi service chahiye? Plumber, Electrician, AC, Carpenter, ya Painter?"
                    }
                elif not extracted_location and not preferred_city:
                    intent_out = {
                        "error": "Location not detected",
                        "clarification": "Aap ka area konsa hai? (e.g., G-13, Johar Town, DHA)"
                    }
                elif not extracted_location and preferred_city:
                    city_lower = preferred_city.lower()
                    if city_lower == "karachi": popular_areas = ["DHA", "Malir", "Chorangi", "Gulshan-e-Iqbal", "Clifton", "Nazimabad", "Korangi", "North Karachi", "Other"]
                    elif city_lower == "lahore": popular_areas = ["Johar Town", "DHA", "Gulberg", "Model Town", "Wapda Town", "Garden Town", "Defence", "Other"]
                    elif city_lower == "islamabad": popular_areas = ["G-13", "F-10", "Blue Area", "I-8", "G-11", "F-7", "E-11", "Other"]
                    elif city_lower == "rawalpindi": popular_areas = ["Saddar", "Satellite Town", "Chaklala", "Westridge", "Murree Road", "Other"]
                    elif city_lower == "faisalabad": popular_areas = ["Madina Town", "Jinnah Colony", "Peoples Colony", "Gulberg", "Other"]
                    else: popular_areas = ["City Center", "Other"]
                    
                    intent_out = {
                        "error": "Missing Area",
                        "clarification": "Pehle area select karein. " + preferred_city.title() + " ke kaunse area mein chahiye?",
                        "suggested_areas": popular_areas,
                        "city": preferred_city,
                        "service": extracted_service
                    }
                else:
                    if extracted_location:
                        extracted_location = extracted_location.title().replace("Dha", "DHA")
                        
                    if extracted_location and preferred_city and preferred_city.lower() not in extracted_location.lower():
                        full_loc = f"{extracted_location}, {preferred_city}"
                    else:
                        full_loc = extracted_location
                        
                    intent_out = {
                        "service_type": extracted_service,
                        "location": full_loc,
                        "time": "immediate",
                        "urgency": urgency,
                        "confidence": confidence
                    }
                
                intent_log = {
                    "timestamp": datetime.now().isoformat(),
                    "agent_name": "Intent_Agent_Gemini",
                    "input": user_input,
                    "reasoning": "Extracted via Google Gemini API.",
                    "output": intent_out
                }
                self.execution_log.append(intent_log)
            else:
                intent_log = self.intent_agent.execute(user_input, user_details)
                self.execution_log.append(intent_log)
                intent_out = intent_log.get("output", {})
            
            # Check Intent Error
            if "error" in intent_out:
                is_missing_area = intent_out.get("error") == "Missing Area"
                
                if is_missing_area:
                    # Save to memory context for the next turn
                    self.USER_SESSIONS[user_id] = {
                        "status": "awaiting_area",
                        "service": intent_out.get("service"),
                        "city": intent_out.get("city")
                    }
                    
                return {
                    "status": "need_area" if is_missing_area else "failed",
                    "step": "intent", 
                    "error": intent_out.get("error"), 
                    "message": intent_out.get("clarification", "Aapko kis ilaqay mein service chahiye?"),
                    "suggested_areas": intent_out.get("suggested_areas", []),
                    "city": intent_out.get("city"),
                    "service": intent_out.get("service")
                }
            
        service_type = intent_out.get("service_type")
        location_name = intent_out.get("location")
        requested_time = intent_out.get("time")
        # City may come from Gemini intent OR from the awaiting_area bypass context
        context_city = intent_out.get("detected_city")
        
        # ==========================================
        # 2. LOCATION AGENT
        # ==========================================
        preferred_city = context_city or user_details.get("preferred_city")
        location_log = self.location_agent.execute(location_name, user_input, preferred_city)
        self.execution_log.append(location_log)
        loc_out = location_log.get("output", {})
        
        detected_city = loc_out.get("city")
        if detected_city and detected_city != preferred_city and detected_city != "unknown":
            # Update user's preferred city in database
            user_id = user_details.get("user_id")
            if user_id and user_id != "unknown":
                try:
                    from database import supabase
                    supabase.table("profiles").update({"preferred_city": detected_city}).eq("id", user_id).execute()
                    user_details["preferred_city"] = detected_city
                except Exception as e:
                    print("Failed to update user city:", str(e))
        
        # Check Location Error (though our agent mocks fallback coords, a real failure drops here)
        if "error" in loc_out:
            return {
                "status": "failed", 
                "step": "location", 
                "error": loc_out.get("error"), 
                "message": "Sorry, invalid area. Aapko kis ilaqay mein service chahiye?"
            }
            
        user_coords = {"lat": loc_out.get("lat"), "lng": loc_out.get("lng")}
        service_details = {"location": loc_out.get("formatted")}
        
        # ==========================================
        # 3. PROVIDER AGENT
        # ==========================================
        city_for_provider = detected_city if detected_city else preferred_city
        provider_log = self.provider_agent.execute(service_type, user_coords, requested_time, city_for_provider)
        self.execution_log.append(provider_log)
        prov_out = provider_log.get("output", {})
        
        # Check Provider Error (e.g., late night, or no match)
        if "error" in prov_out:
            return {
                "status": "failed", 
                "step": "provider", 
                "error": prov_out.get("error"), 
                "message": "Sorry, no providers found. Try nearby area?"
            }
            
        top_providers = prov_out.get("top_providers", [])
        if not top_providers:
            return {
                "status": "failed", 
                "step": "provider", 
                "error": "No providers", 
                "message": "Sorry, no providers found. Try nearby area?"
            }
            
        # ==========================================
        # 4. SHOW PROVIDERS TO USER (WAIT FOR SELECTION)
        # ==========================================
        # Instead of auto-booking, we return the top providers and prompt the user.
        return {
            "status": "show_providers",
            "step": "Provider Selection",
            "message": f"Humne {detected_city.title() if detected_city else 'aapke ilaqay'} [{loc_out.get('formatted', '').split(',')[0]}] mein yeh providers dhoonde hain:",
            "providers": top_providers,
            "service_details": {"service": service_type, "location": loc_out.get("formatted")},
            "total_agents_run": len(self.execution_log)
        }

# =====================================================================
# Test Cases
# =====================================================================
if __name__ == "__main__":
    
    orchestrator = ServiceOrchestrator()
    
    # User Profile Mock
    user_details = {
        "user_id": "USR-101",
        "phone": "+923001234567",
        "language": "Roman Urdu"
    }
    
    print("==========================================================")
    print("--- Test Case 1: Full Success Workflow (AC Technician) ---")
    print("==========================================================\n")
    
    tc1_input = "Mujhe kal subah G-13 mein AC technician chahiye"
    print(f"User Input: {tc1_input}")
    
    response1 = orchestrator.process_request(user_input=tc1_input, user_details=user_details)
    print("\n[Final Orchestrator Response]:")
    print(json.dumps(response1, indent=2))
    
    print("\n[Execution Log / Trace Length]:", len(orchestrator.get_execution_log()))
    
    # Exporting trace to local file
    orchestrator.export_logs("orchestrator_log_tc1.json")
    print("Exported full trace to orchestrator_log_tc1.json")
    
    
    print("\n\n==========================================================")
    print("--- Test Case 2: Intent Error (Missing Location) ---------")
    print("==========================================================\n")
    
    user_details_eng = {
        "user_id": "USR-102",
        "phone": "+923217654321",
        "language": "English"
    }
    
    tc2_input = "I need a plumber"
    print(f"User Input: {tc2_input}")
    
    response2 = orchestrator.process_request(user_input=tc2_input, user_details=user_details_eng)
    print("\n[Final Orchestrator Response]:")
    print(json.dumps(response2, indent=2))
    
    print("\n[Execution Log / Trace Length]:", len(orchestrator.get_execution_log()))
    
    # Exporting trace to local file
    orchestrator.export_logs("orchestrator_log_tc2.json")
    print("Exported full trace to orchestrator_log_tc2.json")
