import os
import re
from fastapi import HTTPException
from database import supabase

def register_user(email, password, full_name, phone):
    # 1. Validate
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if not re.match(r"^03[0-9]{9}$", phone):
        raise HTTPException(status_code=400, detail="Phone must start with 03 and be exactly 11 digits")

    # 2. Call supabase.auth.sign_up
    try:
        # Note: If email confirmations are enabled in Supabase, this auto-sends an email
        res = supabase.auth.sign_up({
            "email": email, 
            "password": password
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not res.user:
        raise HTTPException(status_code=400, detail="Signup failed, user is null")

    user_id = res.user.id

    # 3. Insert into profiles
    try:
        supabase.table('profiles').insert({
            "id": user_id,
            "full_name": full_name,
            "phone": phone,
            "role": "user",
            "preferred_city": None
        }).execute()
    except Exception as e:
        # If profile creation fails (e.g. phone already exists)
        raise HTTPException(status_code=400, detail=f"Failed to create profile: {str(e)}")

    # 5. Return
    return {
        "message": "Check your email for confirmation link",
        "user_id": user_id
    }

def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if not res.user:
        raise HTTPException(status_code=401, detail="Login failed")

    # Check if email is confirmed (email_confirmed_at not null)
    if not res.user.email_confirmed_at:
        raise HTTPException(status_code=403, detail="Please verify your email first")

    # Fetch profile
    prof_res = supabase.table('profiles').select('*').eq('id', res.user.id).execute()
    profile = prof_res.data[0] if prof_res.data else {}

    return {
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "user": {
            "id": res.user.id,
            "email": res.user.email,
            "full_name": profile.get('full_name'),
            "phone": profile.get('phone'),
            "preferred_city": profile.get('preferred_city')
        }
    }

def resend_confirmation(email):
    try:
        # Supabase Python client resend API
        supabase.auth.resend({"type": "signup", "email": email})
        return {"message": "Confirmation email resent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_current_user(token: str):
    try:
        user_res = supabase.auth.get_user(token)
        if not user_res.user:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        user_id = user_res.user.id
        prof_res = supabase.table('profiles').select('*').eq('id', user_id).execute()
        profile = prof_res.data[0] if prof_res.data else {}
        
        return {
            "id": user_id,
            "email": user_res.user.email,
            "full_name": profile.get('full_name'),
            "phone": profile.get('phone'),
            "role": profile.get('role'),
            "preferred_city": profile.get('preferred_city')
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

def logout(token: str):
    try:
        # Sign out globally or just clear on client - we can just return success
        # The Python client doesn't manage sessions for other users, 
        # so calling sign_out() on the global client logs out the service key if we aren't careful!
        # But we can just return logged out. The Flutter client clears its local session.
        return {"message": "Logged out"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
