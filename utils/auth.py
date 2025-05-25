import streamlit as st
from supabase import create_client, Client

# Load Supabase credentials from secrets.toml
SUPABASE_URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["connections"]["supabase"]["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_ROLE_KEY = st.secrets["connections"]["supabase"]["SUPABASE_SERVICE_ROLE_KEY"]
# cookie_secret = st.secrets["cookie_password"]

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_supabase_admin_client() -> Client:
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return None

def signup(email: str, password: str):
    """
    Create a new user using Supabase Auth and return the result object.
    """
    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if result.user:
            # Do NOT show success message here anymore (do it in your UI)
            return result  # Return full result to access user.id
    except Exception as e:
        st.error(f"Signup failed: {e}")
    return None


def login(email: str, password: str) -> bool:
    """
    Login with email and password using Supabase Auth.
    Stores user data as a dictionary in st.session_state["user"].
    """
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if result.session and result.user:
            # Extract relevant user details
            user_info = {
                "id": result.user.id,
                "email": result.user.email,
                "username": result.user.user_metadata.get("username", "")  # optional
            }

            # Store session and user info in session_state
            st.session_state["session"] = result.session
            st.session_state["user"] = user_info

            return True
    except Exception as e:
        st.error(f"Login failed: {e}")
    return False


def is_authenticated() -> bool:
    """
    Check if the user is authenticated.
    Restores session if available.
    """
    if "user" in st.session_state:
        return True

    # Try restoring session
    session_info = supabase.auth.get_session()
    if session_info and session_info.user:
        user = session_info.user
        user_info = {
            "id": user.id,
            "email": user.email,
            "username": user.user_metadata.get("username", "") if user.user_metadata else ""
        }
        st.session_state["session"] = session_info
        st.session_state["user"] = user_info
        return True

    return False

def logout():
    """
    Log the user out and clear session.
    """
    try:
        supabase.auth.sign_out()
    except Exception as e:
        st.warning(f"Logout failed: {e}")
    st.session_state.clear()

def get_supabase_client():
    """
    Get Supabase client with anon key.
    """
    return supabase
