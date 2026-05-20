import json
import random
import string
from datetime import datetime, timedelta

class BookingAgent:
    """
    Booking Agent for Service Orchestrator.
    Finalizes the transaction by creating booking records, generating unique IDs,
    scheduling automated reminders, and simulating SMS notifications.
    """
    
    def __init__(self):
        self.agent_name = "Booking_Agent"
        # Mock database to store all system bookings
        self.bookings_db = {}
        
    def generate_booking_id(self) -> str:
        """Generates a formatted booking ID: SRV-YYYYMMDD-XXXX"""
        date_str = datetime.now().strftime("%Y%m%d")
        rand_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"SRV-{date_str}-{rand_chars}"
        
    def execute(self, provider: dict, user_details: dict, service_details: dict, requested_time: str) -> dict:
        """
        Executes the booking transaction, handling status states and multi-lingual notifications.
        """
        timestamp = datetime.now().isoformat()
        
        # Parse semantic time to actual target datetimes for scheduling
        now = datetime.now()
        target_time = now
        time_display = requested_time
        
        if requested_time == "immediate":
            target_time = now + timedelta(minutes=30)
            time_display = "15-30 minute mein"
        elif requested_time == "tomorrow_morning":
            # Next day at 9 AM
            target_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
            time_display = "kal subah 9 baje"
        elif requested_time == "today_evening":
            # Today at 6 PM
            target_time = now.replace(hour=18, minute=0, second=0)
            if target_time < now:
                target_time += timedelta(days=1)
            time_display = "aaj shaam 6 baje"
        else:
            # Fallback flexible time
            target_time = now + timedelta(days=1)
            time_display = requested_time
            
        # Initialize log tracing variables
        decision = "Proceed"
        output_data = {}
        reasoning = ""
        tool_used = "db_transaction"
        tool_input = ""
        tool_output = ""
        
        # GUARD CONDITIONS
        if not service_details or not service_details.get("service"):
            return {
                "timestamp": timestamp, "agent_name": self.agent_name,
                "input": "N/A", "reasoning": "Missing service",
                "tool_used": "validation", "tool_input": "", "tool_output": "failed",
                "decision": "Error: Service not specified",
                "output": {"error": "Service not specified", "message": "Aapko konsi service chahiye? Plumber, Electrician, AC, Carpenter, ya Painter?"}
            }
            
        if not service_details or not service_details.get("location"):
            return {
                "timestamp": timestamp, "agent_name": self.agent_name,
                "input": "N/A", "reasoning": "Missing location",
                "tool_used": "validation", "tool_input": "", "tool_output": "failed",
                "decision": "Error: Location not specified",
                "output": {"error": "Location not specified", "message": "Aap ka area konsa hai? (e.g., G-13, Johar Town, DHA)"}
            }
            
        if not provider:
            return {
                "timestamp": timestamp, "agent_name": self.agent_name,
                "input": "N/A", "reasoning": "Missing provider",
                "tool_used": "validation", "tool_input": "", "tool_output": "failed",
                "decision": "Error: Provider not selected",
                "output": {"error": "Please select a provider first", "message": "Pehle provider select karein"}
            }

        # 1. Error Handling: Check if Provider suddenly went Offline
        if not provider.get("available", True):
            decision = "Error: Provider Offline"
            reasoning = f"Provider '{provider.get('name')}' went offline during the booking transaction."
            tool_output = "Transaction Failed: Provider Unavailable. Rolled back."
            
            output_data = {
                "status": "cancelled",
                "error": "Provider offline",
                "message": "Maazrat, provider abhi offline ho gaya hai. Hum aapko dusra best provider suggest kar rahe hain.",
                "suggest_next": True
            }
        else:
            # 2. Proceed with successful booking creation
            booking_id = self.generate_booking_id()
            
            tool_input = f"INSERT INTO bookings (id, provider_id, user_id, status) VALUES ('{booking_id}', '{provider.get('id')}', '{user_details.get('user_id')}', 'confirmed')"
            tool_output = "Transaction Successful: 1 row inserted."
            
            # 3. Status Machine Initialization
            status = "confirmed"
            
            # 4. Schedule Reminders
            reminders = []
            # 1 day before
            if target_time > now + timedelta(days=1):
                reminders.append((target_time - timedelta(days=1)).isoformat())
            # 1 hour before
            if target_time > now + timedelta(hours=1):
                reminders.append((target_time - timedelta(hours=1)).isoformat())
                
            # 5. Generate Multi-lingual Confirmation Message
            lang = user_details.get("language", "English")
            provider_name = provider.get("name", "Service Provider")
            
            if lang == "Roman Urdu":
                msg = f"Aapki booking {provider_name} ke sath confirm ho gayi hai. Technician {time_display} pohnch jayega. Booking ID: {booking_id}"
            elif lang == "Urdu":
                # Translate time display manually for MVP
                urdu_time_display = time_display
                if time_display == "kal subah 9 baje": urdu_time_display = "کل صبح 9 بجے"
                elif time_display == "15-30 minute mein": urdu_time_display = "15 سے 30 منٹ میں"
                elif time_display == "aaj shaam 6 baje": urdu_time_display = "آج شام 6 بجے"
                
                msg = f"آپکی بکنگ {provider_name} کے ساتھ کنفرم ہو گئی ہے۔ ٹیکنیشن {urdu_time_display} پہنچ جائے گا۔ بکنگ آئی ڈی: {booking_id}"
            else:
                # English Translations
                eng_time_display = time_display
                if time_display == "kal subah 9 baje": eng_time_display = "tomorrow at 9:00 AM"
                elif time_display == "15-30 minute mein": eng_time_display = "in 15-30 minutes"
                elif time_display == "aaj shaam 6 baje": eng_time_display = "today at 6:00 PM"
                
                msg = f"Your booking with {provider_name} is confirmed. Technician will arrive at {eng_time_display}. Booking ID: {booking_id}"

            # 6. Simulate Notifications
            user_phone = user_details.get("phone", "+923000000000")
            provider_phone = provider.get("phone", "0300-0000000")
            user_address = service_details.get("location", "Unknown Address")
            
            simulated_sms_logs = [
                f"SMS sent to User ({user_phone}): {msg}",
                f"SMS sent to Provider ({provider_phone}): New Booking {booking_id}. User Address: {user_address}. Time: {time_display}."
            ]
            
            # Save the record in the simulated database
            booking_record = {
                "booking_id": booking_id,
                "provider_id": provider.get("id"),
                "user_id": user_details.get("user_id"),
                "status": status,
                "scheduled_time": target_time.isoformat(),
                "reminders": reminders,
                "notifications_sent": simulated_sms_logs
            }
            self.bookings_db[booking_id] = booking_record
            
            decision = "Success: Booking Confirmed"
            reasoning = f"Booking created for {provider_name}. Status: {status}. Notifications simulated and reminders scheduled."
            output_data = {
                "booking_id": booking_id,
                "status": status,
                "message": msg,
                "reminders_scheduled": len(reminders) > 0,
                "simulated_logs": simulated_sms_logs
            }

        # 7. Construct standard Agent Log
        agent_log = {
            "timestamp": timestamp,
            "agent_name": self.agent_name,
            # Compact logging for inputs
            "input": json.dumps({
                "provider": provider.get("id"), 
                "user": user_details.get("user_id"), 
                "time": requested_time
            }),
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
    agent = BookingAgent()
    
    # --- Test Case 1: Successful Booking (AC Technician, Roman Urdu) ---
    provider_1 = {
        "id": "PROV-889",
        "name": "Kamran AC Services",
        "phone": "0333-1112223",
        "available": True
    }
    user_1 = {
        "user_id": "USR-101",
        "phone": "+923001234567",
        "language": "Roman Urdu"
    }
    svc_1 = {"location": "G-13, Islamabad"}
    
    print("--- Test Case 1: Successful Booking (Roman Urdu) ---")
    res1 = agent.execute(provider_1, user_1, svc_1, "tomorrow_morning")
    print(json.dumps(res1, indent=2))
    
    # Ensure booking was saved
    print(f"\nInternal Database Check: {len(agent.bookings_db)} bookings saved.")
    
    # --- Test Case 2: Cancellation Scenario (Provider Offline) ---
    provider_2 = {
        "id": "PROV-412",
        "name": "Irfan Technician",
        "phone": "0345-9998887",
        "available": False
    }
    user_2 = {
        "user_id": "USR-102",
        "phone": "+923217654321",
        "language": "English"
    }
    svc_2 = {"location": "F-11, Islamabad"}
    
    print("\n--- Test Case 2: Cancellation (Provider Offline) ---")
    res2 = agent.execute(provider_2, user_2, svc_2, "immediate")
    print(json.dumps(res2, indent=2))
