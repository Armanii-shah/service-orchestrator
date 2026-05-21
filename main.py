import sys
import os
import uvicorn
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime

SECRET_KEY = os.getenv("HACKATHON_SECRET", "HACKATHON_SECRET")
ALGORITHM = "HS256"
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Load environment variables
load_dotenv()

# Ensure core module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import ServiceOrchestrator, MOCK_PROVIDERS_DB as ORCH_DB

# ==========================================
# Mock Provider Database (15+ Providers)
# ==========================================
MOCK_PROVIDERS_DB = [
    # ================= AC Technicians =================
    {"id": "PROV-101", "name": "Kamran AC Services", "service": "ac_technician", "lat": 33.6844, "lng": 73.0479, "area": "G-13", "city": "islamabad", "rating": 4.8, "available": True, "phone": "0300-1111111"},
    {"id": "PROV-102", "name": "Irfan Technician", "service": "ac_technician", "lat": 33.6833, "lng": 72.9833, "area": "F-11", "city": "islamabad", "rating": 4.9, "available": True, "phone": "0300-2222222"},
    {"id": "PROV-103", "name": "Karachi Cool AC", "service": "ac_technician", "lat": 24.8229, "lng": 67.0321, "area": "Clifton", "city": "karachi", "rating": 4.7, "available": True, "phone": "0300-3333333"},
    {"id": "PROV-104", "name": "Lahore Chiller AC", "service": "ac_technician", "lat": 31.4697, "lng": 74.2800, "area": "Johar Town", "city": "lahore", "rating": 4.5, "available": True, "phone": "0300-1040000"},
    {"id": "PROV-105", "name": "Pindi AC Experts", "service": "ac_technician", "lat": 33.5950, "lng": 73.0820, "area": "Satellite Town", "city": "rawalpindi", "rating": 4.6, "available": True, "phone": "0300-1050000"},
    {"id": "PROV-106", "name": "Faisalabad AC Care", "service": "ac_technician", "lat": 31.4200, "lng": 73.0900, "area": "Madina Town", "city": "faisalabad", "rating": 4.4, "available": True, "phone": "0300-1060000"},
    
    # ================= Plumbers =================
    {"id": "PROV-201", "name": "Aslam Plumbing Works", "service": "plumber", "lat": 31.4697, "lng": 74.2800, "area": "Johar Town", "city": "lahore", "rating": 4.8, "available": True, "phone": "0300-4444444"},
    {"id": "PROV-202", "name": "Isloo Plumbers", "service": "plumber", "lat": 33.6844, "lng": 73.0479, "area": "G-13", "city": "islamabad", "rating": 4.5, "available": True, "phone": "0300-5555555"},
    {"id": "PROV-203", "name": "Saddar Pipe Fixers", "service": "plumber", "lat": 24.8580, "lng": 67.0211, "area": "Saddar", "city": "karachi", "rating": 4.2, "available": True, "phone": "0300-6666666"},
    {"id": "PROV-204", "name": "Pindi Plumber Point", "service": "plumber", "lat": 33.5415, "lng": 73.1118, "area": "Bahria Town", "city": "rawalpindi", "rating": 4.6, "available": True, "phone": "0300-2040000"},
    {"id": "PROV-205", "name": "DHA Plumbers", "service": "plumber", "lat": 24.8093, "lng": 67.0425, "area": "DHA", "city": "karachi", "rating": 4.9, "available": True, "phone": "0300-2050000"},
    {"id": "PROV-206", "name": "Jinnah Pipe Services", "service": "plumber", "lat": 31.4050, "lng": 73.0700, "area": "Jinnah Colony", "city": "faisalabad", "rating": 4.7, "available": True, "phone": "0300-2060000"},
    
    # ================= Electricians =================
    {"id": "PROV-301", "name": "F-7 Electric", "service": "electrician", "lat": 33.7298, "lng": 73.0370, "area": "F-7", "city": "islamabad", "rating": 4.6, "available": True, "phone": "0300-7777777"},
    {"id": "PROV-302", "name": "DHA Spark", "service": "electrician", "lat": 31.4842, "lng": 74.3262, "area": "Model Town", "city": "lahore", "rating": 4.9, "available": True, "phone": "0300-8888888"},
    {"id": "PROV-303", "name": "Clifton Wire Pros", "service": "electrician", "lat": 24.8229, "lng": 67.0321, "area": "Clifton", "city": "karachi", "rating": 4.7, "available": False, "phone": "0300-3030000"},
    {"id": "PROV-304", "name": "Nazimabad Electric", "service": "electrician", "lat": 24.9056, "lng": 67.0396, "area": "Nazimabad", "city": "karachi", "rating": 4.4, "available": True, "phone": "0300-3040000"},
    {"id": "PROV-305", "name": "Chaklala Electric", "service": "electrician", "lat": 33.6100, "lng": 73.1300, "area": "Chaklala", "city": "rawalpindi", "rating": 4.8, "available": True, "phone": "0300-3050000"},
    {"id": "PROV-306", "name": "Peoples Electric", "service": "electrician", "lat": 31.4100, "lng": 73.0800, "area": "Peoples Colony", "city": "faisalabad", "rating": 4.5, "available": True, "phone": "0300-3060000"},
    
    # ================= Carpenters =================
    {"id": "PROV-401", "name": "Bahria Woodworks", "service": "carpenter", "lat": 33.5415, "lng": 73.1118, "area": "Bahria Town", "city": "rawalpindi", "rating": 4.8, "available": False, "phone": "0300-9999999"},
    {"id": "PROV-402", "name": "I-8 Furniture Repair", "service": "carpenter", "lat": 33.6682, "lng": 73.0743, "area": "I-8", "city": "islamabad", "rating": 4.7, "available": True, "phone": "0300-1010101"},
    {"id": "PROV-403", "name": "DHA Wood Craft", "service": "carpenter", "lat": 24.8093, "lng": 67.0425, "area": "DHA", "city": "karachi", "rating": 4.5, "available": True, "phone": "0300-4030000"},
    {"id": "PROV-404", "name": "Gulberg Carpenters", "service": "carpenter", "lat": 31.5204, "lng": 74.3587, "area": "Gulberg", "city": "lahore", "rating": 4.9, "available": True, "phone": "0300-4040000"},
    {"id": "PROV-405", "name": "Madina Woodworks", "service": "carpenter", "lat": 31.4200, "lng": 73.0900, "area": "Madina Town", "city": "faisalabad", "rating": 4.6, "available": True, "phone": "0300-4050000"},
    
    # ================= Painters =================
    {"id": "PROV-501", "name": "Gulshan Colors", "service": "painter", "lat": 24.9200, "lng": 67.0988, "area": "Gulshan-e-Iqbal", "city": "karachi", "rating": 4.5, "available": True, "phone": "0300-2020202"},
    {"id": "PROV-502", "name": "Lahore Paint Masters", "service": "painter", "lat": 31.4842, "lng": 74.3262, "area": "Model Town", "city": "lahore", "rating": 4.8, "available": True, "phone": "0300-5020000"},
    {"id": "PROV-503", "name": "Capital Painters", "service": "painter", "lat": 33.7100, "lng": 73.0250, "area": "F-10", "city": "islamabad", "rating": 4.7, "available": True, "phone": "0300-5030000"},
    {"id": "PROV-504", "name": "Satellite Paint Works", "service": "painter", "lat": 33.5950, "lng": 73.0820, "area": "Satellite Town", "city": "rawalpindi", "rating": 4.4, "available": True, "phone": "0300-5040000"},
    {"id": "PROV-505", "name": "Jinnah Wall Care", "service": "painter", "lat": 31.4050, "lng": 73.0700, "area": "Jinnah Colony", "city": "faisalabad", "rating": 4.9, "available": True, "phone": "0300-5050000"}
]

# Override the orchestrator's mock DB with this expanded 15+ provider list
ORCH_DB.clear()
ORCH_DB.extend(MOCK_PROVIDERS_DB)

# ==========================================
# FastAPI Initialization
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    orchestrator = ServiceOrchestrator()
    print("ServiceOrchestrator initialized and ready.")
    yield

app = FastAPI(
    title="Service Orchestrator API",
    description="Backend for the Multi-Agent Service Orchestrator (Pakistani Informal Economy)",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Flutter app development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Orchestrator Instance
orchestrator = None


# ==========================================
# Pydantic Models
# ==========================================

class ProcessRequestPayload(BaseModel):
    message: str = Field(..., examples=["Mujhe kal subah G-13 mein AC technician chahiye"])
    user_id: Optional[str] = Field(default=None, examples=["USR-101"])
    phone: Optional[str] = Field(default=None, examples=["+923001234567"])
    language: str = Field(default="Roman Urdu", examples=["Roman Urdu"])
    selected_provider_id: Optional[str] = None
    service_type: Optional[str] = None
    location: Optional[str] = None

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ResendConfirmationRequest(BaseModel):
    email: str

class UpdateCityRequest(BaseModel):
    city: str

class OrchestratorResponse(BaseModel):
    status: str
    step: Optional[str] = None
    error: Optional[str] = None
    message: str
    booking_details: Optional[Dict[str, Any]] = None
    total_agents_run: Optional[int] = None
    trace: Optional[List[Dict[str, Any]]] = None
    # Location / area flow
    suggested_areas: Optional[List[str]] = None
    suggested_cities: Optional[List[str]] = None   # NEW: city selection chips
    city: Optional[str] = None
    service: Optional[str] = None
    language: Optional[str] = None                 # NEW: detected user language
    # Provider display
    providers: Optional[List[Dict[str, Any]]] = None
    service_details: Optional[Dict[str, Any]] = None

class ProviderModel(BaseModel):
    id: str
    name: str
    service: str
    lat: float
    lng: float
    area: str
    rating: float
    available: bool
    phone: str

class HealthResponse(BaseModel):
    status: str
    agents: List[str]


# ==========================================
# FastAPI Events
# ==========================================

# Lifespan now handles startup


# ==========================================
# Auth Endpoints
# ==========================================

import auth_service

@app.post("/auth/register")
async def register(payload: RegisterRequest):
    return auth_service.register_user(payload.email, payload.password, payload.full_name, payload.phone)

@app.post("/auth/login")
async def login(payload: LoginRequest):
    return auth_service.login_user(payload.email, payload.password)

@app.post("/auth/resend-confirmation")
async def resend_confirmation(payload: ResendConfirmationRequest):
    return auth_service.resend_confirmation(payload.email)

@app.get("/auth/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return auth_service.get_current_user(credentials.credentials)

@app.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return auth_service.logout(credentials.credentials)

@app.post("/api/update-city")
async def update_city(payload: UpdateCityRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    from database import supabase
    current_user = auth_service.get_current_user(credentials.credentials)
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    city = payload.city.lower()
    try:
        supabase.table("profiles").update({"preferred_city": city}).eq("id", user_id).execute()
        return {"status": "success", "preferred_city": city}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# API Endpoints
# ==========================================

@app.get("/api/health")
async def health_check():
    """
    Returns the health status of the API and loaded agents.
    Example: GET /api/health
    """
    return {
        "status": "ok",
        "gemini_ready": bool(os.getenv('GEMINI_API_KEY')),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/process-request", response_model=OrchestratorResponse)
async def process_request(payload: ProcessRequestPayload, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Main entrypoint for the Flutter app.
    Takes a natural language message and processes it through the 4-agent system.
    """
    if not payload.message:
        raise HTTPException(status_code=400, detail="Message is required.")
        
    try:
        print(f"[API] process-request payload: {payload.model_dump()}")
        
        # Verify token with Supabase and get user
        current_user = auth_service.get_current_user(credentials.credentials)
        user_details = {
            "user_id": current_user.get("id", "unknown"),
            "phone": current_user.get("phone", "unknown"),
            "preferred_city": current_user.get("preferred_city"),
            "language": payload.language,
            "selected_provider_id": payload.selected_provider_id,
            "service_type": payload.service_type,
            "location": payload.location
        }
        print(f"[API] user_details resolved: {user_details}")
        
        # Run orchestrator synchronously (or in thread pool if CPU bound)
        print("[API] Step: Calling orchestrator.process_request...")
        result = orchestrator.process_request(payload.message, user_details)
        print(f"[API] Orchestrator result status: {result.get('status')}")
        
        # Attach full log trace to response for the hackathon UI
        result["trace"] = orchestrator.get_execution_log()
        
        return result
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n{'='*50}\nCRITICAL 500 ERROR IN process-request\n{'='*50}")
        print(f"ERROR: {str(e)}")
        print(f"TRACEBACK:\n{error_trace}")
        print(f"{'='*50}\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers/{service_type}", response_model=List[ProviderModel])
async def get_providers(service_type: str):
    """
    Returns a list of all mock providers matching a specific service type.
    Example: GET /api/providers/plumber
    """
    matching = [p for p in MOCK_PROVIDERS_DB if p.get("service") == service_type.lower()]
    if not matching:
        raise HTTPException(status_code=404, detail=f"No providers found for service: {service_type}")
    return matching

@app.get("/api/booking/{booking_id}")
async def get_booking(booking_id: str):
    """
    Retrieves booking details from the BookingAgent's internal database.
    Example: GET /api/booking/SRV-20260518-A7B3
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized.")
        
    booking_db = orchestrator.booking_agent.bookings_db
    if booking_id not in booking_db:
        raise HTTPException(status_code=404, detail=f"Booking ID {booking_id} not found.")
        
    return booking_db[booking_id]

@app.get("/api/agent-logs")
async def get_agent_logs():
    """
    Returns all execution logs from the last run of the Orchestrator.
    Useful for debugging and rendering the "Agent Brain" UI in the demo.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized.")
        
    return orchestrator.get_execution_log()

if __name__ == "__main__":
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
