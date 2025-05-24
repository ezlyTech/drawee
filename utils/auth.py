import streamlit as st
import bcrypt
from supabase import create_client
from streamlit_cookies_manager import EncryptedCookieManager

# Load Supabase credentials from secrets.toml
supabase_url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
supabase_anon_key = st.secrets["connections"]["supabase"]["SUPABASE_ANON_KEY"]
supabase_service_key = st.secrets["connections"]["supabase"]["SUPABASE_SERVICE_ROLE_KEY"]
cookie_secret = st.secrets["cookie_password"]

# Initialize Supabase clients
supabase = create_client(supabase_url, supabase_anon_key)
supabase_admin = create_client(supabase_url, supabase_service_key)

# Initialize EncryptedCookieManager
cookies = EncryptedCookieManager(prefix="drawee", password=cookie_secret)

if not cookies.ready():
    st.stop()  # Wait for cookies to initialize

def login(username: str, password: str) -> bool:
    """Authenticate user and store session and cookie if successful"""
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        if response.data:
            user = response.data[0]
            if bcrypt.checkpw(password.encode(), user["password"].encode()):
                st.session_state["user"] = user
                cookies["username"] = user["username"]  # Store cookie for session persistence
                return True
    except Exception as e:
        st.error(f"Login failed: {e}")
    return False

def signup(username: str, password: str) -> bool:
    """Create a new user account with hashed password"""
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        response = supabase.table("users").insert({
            "username": username,
            "password": hashed_pw
        }).execute()
        return response.data is not None
    except Exception as e:
        st.error(f"Signup failed: {e}")
        return False

def logout():
    """Clear user session and remove cookies"""
    st.session_state.pop("user", None)
    cookies["username"] = ""

def is_authenticated() -> bool:
    """Check if user is logged in, restore session from cookie if possible"""
    if "user" in st.session_state:
        return True
    elif "username" in cookies and cookies["username"]:
        username = cookies["username"]
        response = supabase.table("users").select("*").eq("username", username).execute()
        if response.data:
            st.session_state["user"] = response.data[0]
            return True
    return False

def get_supabase_client():
    return supabase

def get_supabase_admin_client():
    return supabase_admin
