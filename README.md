# 🛠️ AI Service Orchestrator — Pakistani Informal Economy

> **Hackathon Submission** | Google Antigravity Challenge  
> Connecting Pakistanis with local service providers through an intelligent multi-agent AI system.

---

## 📌 Overview

The **Service Orchestrator** is a production-ready, multi-agent AI system with a companion **Flutter mobile/web app**. It connects users in Pakistan with local service providers (plumbers, electricians, AC technicians, carpenters, painters) via a natural language chat interface that works in **Urdu, Roman Urdu, and English**.

The system handles the **complete end-to-end service lifecycle**:
```
User Message → Intent Extraction → City/Area Resolution → Provider Ranking → Booking + Reminders
```

**Supported Cities:** Karachi · Lahore · Islamabad · Rawalpindi · Faisalabad  
**Supported Services:** Plumber · Electrician · AC Technician · Carpenter · Painter  
**Languages:** English · Roman Urdu · Urdu script

---

## 🤖 How Google Antigravity Was Used

**Google Antigravity** served as the **core AI development and orchestration platform** throughout this project — from system design to code generation, debugging, and multi-step reasoning.

### Role of Antigravity in This Project

| Stage | How Antigravity Was Used |
|---|---|
| **System Architecture** | Designed the 4-agent sequential pipeline (Intent → Location → Provider → Booking) |
| **Agent Orchestration** | Planned and implemented context-propagation between all agents with session state |
| **NLU Integration** | Integrated Gemini 3.5 Flash via structured JSON prompts for multi-language parsing |
| **Tool Integration** | Built OpenStreetMap Nominatim geocoding with an internal coordinate cache |
| **Bug Diagnosis** | Diagnosed silent 500 errors, Pydantic field stripping, stale session bypasses, and Gemini rate-limit fallback failures |
| **Code Generation** | Generated all Python agents, FastAPI endpoints, Flutter UI screens, and mock provider DB |
| **Scoring Algorithm** | Designed urgency-weighted dynamic scoring (High/Medium/Low urgency weights) |
| **UX Design** | Designed the premium Flutter UI — city/area chips, provider cards, booking confirmation dialog |
| **Language Awareness** | Implemented auto-detected language routing so responses always match the user's language |

### Agentic Workflow

```
User Input (Urdu / Roman Urdu / English)
        ↓
[1. Intent Agent]    — Gemini 3.5 Flash extracts: service, city, area, urgency, language
        ↓                (fallback: keyword parser if Gemini rate-limited)
[2. Location Agent]  — Resolves area name → GPS coordinates (cache → OpenStreetMap)
        ↓
[3. Provider Agent]  — Scores & ranks top 3 providers (dynamic weights by urgency)
        ↓
[4. Booking Agent]   — Generates SRV-ID, simulates SMS logs, schedules reminders
        ↓
Flutter UI           — City chips → Area chips → Provider cards → Booking confirmation
```

---

## ✨ Key Features

### 🧠 Intelligent Multi-Turn Conversation
The system uses a **city-first conversational flow**:
1. User says any service request without specifying location
2. Bot asks: *"Which city?"* → shows 5 city chips
3. User taps a city → Bot asks: *"Which area?"* → shows local area chips
4. User taps area → Top 3 ranked providers appear with cards

### 🌐 Language-Aware Responses
Gemini detects whether the user wrote in **English**, **Roman Urdu**, or **Urdu script** and responds in the same language throughout the entire conversation.

| Input | Response Language |
|---|---|
| "I need a plumber urgently" | English |
| "Jaldi electrician chahiye" | Roman Urdu |
| "مجھے پلمبر چاہیے" | Urdu |

### ⚡ Urgency-Weighted Provider Ranking

The Provider Agent dynamically adjusts its scoring weights based on urgency:

| Urgency | Distance | Rating | Availability |
|---|---|---|---|
| **High** (jaldi, emergency) | 50% | 20% | 30% |
| **Medium** (default) | 40% | 40% | 20% |
| **Low** (flexible) | 30% | 50% | 20% |

### 📋 Booking Simulation with Follow-Up Workflow
Each booking confirmation shows:
- Unique `SRV-YYYYMMDD-XXXX` booking ID
- Simulated SMS logs to both user and provider
- Scheduled reminders (1 hour before + post-completion)
- Visual status stepper: `Booked → Notified → En Route → Done`

### 💡 Transparent AI Reasoning
Every provider card shows a **"Why recommended"** explanation chip powered by the Provider Agent's scoring reasoning.

---

## 🏗️ System Architecture

### Backend (Python / FastAPI)
```
Service_Orchestrator_P1/
├── main.py                     # FastAPI app, all API endpoints, Pydantic models
├── auth_service.py             # Supabase Auth & JWT validation
├── database.py                 # Supabase PostgreSQL connection
├── core/
│   └── orchestrator.py         # Master pipeline: session state, agent sequencing
├── agents/
│   ├── gemini_service.py       # Primary NLU: Gemini 3.5 Flash structured JSON extraction
│   ├── intent_agent.py         # Fallback NLU: keyword + fuzzy matching parser
│   ├── location_agent.py       # GPS resolution via cache + OpenStreetMap Nominatim
│   ├── provider_agent.py       # Dynamic scoring & ranking algorithm
│   └── booking_agent.py        # Booking creation, SMS simulation, reminder scheduling
└── test_gemini.py              # Standalone Gemini integration test
```

### Frontend (Flutter Web + Android APK)
```
flutter_app/
└── lib/
    ├── main.dart                       # App init, routing, Supabase setup
    ├── models/models.dart              # ProviderModel, Booking, AgentLog data classes
    ├── services/
    │   ├── api_service.dart            # HTTP client with JWT injection & retry logic
    │   └── http_service.dart           # processRequest endpoint wrapper
    └── screens/
        ├── login_screen.dart           # Auth portal (login/register)
        ├── chat_screen.dart            # Core chat UI with chips, cards, booking dialog
        └── agent_logs_screen.dart      # Color-coded developer trace log viewer
```

---

## 🔒 Security & Authentication

- **Supabase Auth**: Email/password registration and login
- **JWT Bearer Tokens**: All `/api/*` endpoints require a valid JWT
- **Persistent Profiles**: `preferred_city` stored in Supabase PostgreSQL
- **Environment Variables**: All secrets externalized via `.env` (never committed)

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create new Supabase user |
| `POST` | `/auth/login` | Validate credentials, return JWT |
| `GET` | `/auth/me` | Validate JWT, return user profile |
| `POST` | `/api/process-request` | **Main pipeline** — accepts NL message, runs all agents |
| `POST` | `/api/update-city` | Update user's preferred city |
| `GET` | `/api/agent-logs` | Return raw JSON execution trace |
| `GET` | `/api/health` | System health + Gemini readiness check |

### `POST /api/process-request` Payload
```json
{
  "message": "I need a plumber urgently",
  "service_type": null,
  "location": null,
  "selected_provider_id": null,
  "language": null
}
```

### Response Example (`need_city`)
```json
{
  "status": "need_city",
  "message": "Which city do you need the service in?",
  "suggested_cities": ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad"],
  "service": "plumber",
  "language": "english"
}
```

### Response Example (`show_providers`)
```json
{
  "status": "show_providers",
  "message": "We found these plumbers in Karachi [DHA]:",
  "providers": [
    {
      "id": "PROV-001",
      "name": "Ali Plumber",
      "distance_km": 1.2,
      "rating": 4.8,
      "score": 94.1,
      "reasoning": "Very close (1.2 km). Rating 4.8/5. Available now. Prioritised for fast response.",
      "phone": "0300-1234567"
    }
  ],
  "service_details": { "service": "plumber", "location": "DHA, Karachi, Pakistan" }
}
```

---

## 🚀 Setup & Running

### Prerequisites
- Python 3.10+
- Flutter 3.x (with Chrome or Android device/emulator)
- Supabase project
- Google Gemini API key (free tier works)

### 1. Environment Variables
Create `.env` in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_maps_key_optional
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

### 2. Backend
```bash
# From project root
cd Service_Orchestrator_P1

# Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server (auto-reloads on file changes)
python3 main.py
# → Running at http://localhost:8000
```

### 3. Flutter Frontend (Web)
```bash
cd flutter_app

flutter pub get

# Run in Chrome
flutter run -d chrome
```

### 4. Flutter Android APK (Mobile)
```bash
cd flutter_app

# Build debug APK (~70 MB)
flutter build apk --debug

# APK is at:
# build/app/outputs/flutter-apk/app-debug.apk

# Install on connected device
flutter install
```

> **Note:** If `flutter build apk` fails with a Gradle/Java error, run:
> ```bash
> flutter config --jdk-dir "/Library/Java/JavaVirtualMachines/jdk-17.0.14+7/Contents/Home"
> ```
> This pins Flutter to JDK 17 which is compatible with Gradle 7.6.1.

---

## 🧪 Testing

```bash
# Test Gemini API integration
source venv/bin/activate
python3 test_gemini.py

# Test the full agent pipeline directly (bypasses HTTP)
python3 -c "
from core.orchestrator import ServiceOrchestrator
orc = ServiceOrchestrator()
user = {'user_id': 'test', 'preferred_city': 'karachi'}
print(orc.process_request('I need a plumber urgently', user))
"
```

---

## 🗺️ City & Area Coverage

| City | Areas |
|---|---|
| **Karachi** | DHA, Malir, Chorangi, Gulshan-e-Iqbal, Clifton, Nazimabad, Korangi, North Karachi |
| **Lahore** | Johar Town, DHA, Gulberg, Model Town, Wapda Town, Garden Town, Defence |
| **Islamabad** | G-13, F-10, Blue Area, I-8, G-11, F-7, E-11 |
| **Rawalpindi** | Saddar, Satellite Town, Chaklala, Westridge, Murree Road |
| **Faisalabad** | Madina Town, Jinnah Colony, Peoples Colony, Gulberg |

---

## 📋 Agent Log Format

Every agent action is logged in a standardized JSON trace visible in the app's **Agent Logs** tab:

```json
{
  "timestamp": "2026-05-21T09:00:00+05:00",
  "agent_name": "Provider_Agent",
  "input": "{\"service\": \"plumber\", \"lat\": 24.8607, \"lng\": 67.0011}",
  "reasoning": "Urgency=high. Weights: dist=0.50, rating=0.20, avail=0.30. Score=94.1",
  "tool_used": "db_query",
  "decision": "Return top 3 providers sorted by urgency-weighted score",
  "output": { "top_provider": "PROV-001", "score": 94.1 }
}
```

---

## 🔧 Known Limitations & Notes

- **Gemini Rate Limits**: Free tier allows 20 requests/day. When exhausted, the system falls back to a keyword-based parser that handles Urdu/Roman Urdu/English without LLM.
- **Mock Provider DB**: 30+ providers are stored in `main.py` as a mock database. For production, connect `ProviderAgent` to a live Supabase table.
- **Location Geocoding**: Uses OpenStreetMap Nominatim (free, no key required) with an internal cache. Production should use Google Maps Geocoding API for better accuracy.
- **SMS Simulation**: Booking notifications are simulated locally — no real SMS is sent. Production integration would use Twilio or a local Pakistani SMS gateway.
