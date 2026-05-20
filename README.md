# AI Service Orchestrator - Pakistani Informal Economy

## Overview
The **Service Orchestrator** is a comprehensive multi-agent AI system with a companion Flutter Web frontend. Powered by **Google's Gemini API**, it acts as an intelligent intermediary connecting users in Pakistan with local service providers (plumbers, electricians, AC technicians, carpenters, and painters). It parses natural language (Urdu/Roman Urdu/English) to handle the end-to-end booking flow seamlessly across **5 major cities: Karachi, Lahore, Islamabad, Rawalpindi, and Faisalabad**.

---

## 🔒 Security & Authentication (Supabase)

This project features a fully integrated **Supabase Authentication system**:
- **Email & Password Setup**: Secure account creation replacing the legacy shared-preferences phone validation.
- **JWT Protection**: All Fast API endpoints are strictly protected by standard JWT Bearer Token validation.
- **Persistent Profiles**: User profiles are securely tied to Supabase PostgreSQL, persisting critical details like `preferred_city` across sessions.

---

## 🏗️ Architecture

The system is broken down into two main components:
1. **Python FastAPI Backend**: Hosts the 4-agent Orchestrator and Supabase integration.
2. **Flutter Web Frontend**: A responsive, intelligent Chat UI for seamless interaction.

### The Multi-Agent Backend
The backend utilizes four specialized agents working in a strict, sequential pipeline:

1. **Intent Agent (Powered by Gemini)**
   - **Role**: Parses user text (e.g., *"Mujhe kal G-13 mein AC technician chahiye"*) using **Gemini 3.5 Flash** for highly accurate Natural Language Understanding.
   - **Output**: Extracts service type, city, area, and urgency using structured JSON function calling.
   - **Smart Fallbacks**: Actively detects missing parameters and generates quick-select UI suggestions (e.g., suggesting 25+ local area chips if only the city is known).

2. **Location Agent**
   - **Role**: Standardizes local areas into exact latitude/longitude coordinates to measure distances to providers. Maps local keywords (like 'khi' or 'lhr') intelligently.

3. **Provider Agent**
   - **Role**: Queries the internal database of **30+ mock providers spanning 5 cities** and ranks the top 3 available providers specific to the user's city and area.
   - **Algorithm**: Distance (40%), Rating (40%), Availability (20%).

4. **Booking Agent**
   - **Role**: Finalizes the selection upon explicit user confirmation. Contains strict **Guard Conditions** to prevent illegal bookings. Generates an `SRV` Booking ID and schedules reminders.

---

## 📱 Flutter Web Frontend
The frontend is built using **Flutter Web** and recently received a **massive premium UI overhaul**.

### UI & UX Highlights
- **Premium Chat Interface**: Modern chat bubbles with dynamic borders, soft drop-shadows, and gorgeous teal-to-dark-slate gradients on the AppBar.
- **Pill-Shaped Action Chips**: If a user forgets to type their local area, the agent prompts them and dynamic, vibrant teal ActionChips appear for single-tap selection (with auto-scroll to keep them in view).
- **Interactive Provider Cards**: Modern, floating provider cards with inline Blue Gradient Avatars, amber star ratings, and full-width Green Gradient "Book Now" buttons.
- **Automated Scrolling**: Smooth UX that automatically scrolls to the newest message/cards.
- **2-Step Onboarding UI**: First-time users are presented with a gorgeous City & Area Setup Dialog forcing them to establish a baseline location (`preferred_city`) for accurate orchestration.
- **Quick-Select Action Chips**: If a user forgets to type their local area, the agent prompts them and dynamic ActionChip buttons appear for single-tap selection!
- **Interactive Provider Cards**: Instead of auto-booking, users review ranked providers directly inline in the chat and must tap a confirmation modal to proceed.
- **Agent Trace Logs Screen**: A dedicated debugger tab parses nested JSON execution logs in real-time. Logs are color-coded to monitor the agent pipeline.
- **Robust HTTP Client**: Features custom token injection, a 3-attempt retry loop, and robust error surfacing.

---

## 🚀 Setup & Execution Guide

### 1. Environment Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_maps_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
```

### 2. Running the Python Backend
```bash
# Navigate to the root directory
cd Service_Orchestrator_P1

# Activate the virtual environment
source venv/bin/activate

# Start the server (runs on http://localhost:8000)
python3 main.py
```

### 3. Running the Flutter Web Frontend
```bash
# Navigate to the Flutter directory
cd flutter_app

# Install dependencies
flutter pub get

# Launch the app in Chrome
flutter run -d chrome
```

---

## 📡 API Endpoints

The Flutter app communicates with the backend via the following protected endpoints:

- **Auth**
  - `POST /auth/register`: Creates new Supabase Auth user.
  - `POST /auth/login`: Validates credentials and returns JWT.
  - `GET /auth/me`: Validates JWT and returns synced profile data.
- **Core Orchestration**
  - `POST /api/process-request`: Primary pipeline. Accepts `{"message": "..."}` and optional explicit routing for bookings.
  - `POST /api/update-city`: Updates user's localized city preference.
- **System**
  - `GET /api/agent-logs`: Returns the raw JSON execution trace of the backend agents.
  - `GET /api/providers/{service_type}`: Direct lookup of providers by type.

---

## 📂 Project Structure

```text
Service_Orchestrator_P1/
├── main.py                     # FastAPI entry point & Endpoint definitions
├── auth_service.py             # Supabase Authentication logic & JWT Validation
├── database.py                 # PostgreSQL connection layer
├── core/
│   └── orchestrator.py         # Multi-Agent Logic & Workflow pipeline
├── agents/                     # Specialized agent modules
├── flutter_app/                # Flutter Frontend 
│   ├── lib/
│   │   ├── main.dart                 # App initialization & Routing
│   │   ├── services/api_service.dart # Singleton HTTP client & JWT injection
│   │   └── screens/
│   │       ├── login_screen.dart        # Authentication Portal
│   │       ├── chat_screen.dart         # Core multi-agent interaction UI
│   │       └── agent_logs_screen.dart   # Developer trace log UI
└── README.md                   # Project Documentation
```
