# drawee_app.py

import streamlit as st
st.set_page_config(page_title="Drawee", page_icon="🖼️")

from st_supabase_connection import SupabaseConnection
import numpy as np
import plotly.graph_objects as go
import time
from PIL import Image
import cv2
from tensorflow.keras.models import load_model
from utils.auth import login, signup, is_authenticated, logout, get_supabase_client, get_supabase_admin_client
from classes_def import stages_info


# --- Connect to Supabase ---
supabase = get_supabase_client()
supabase_admin = get_supabase_admin_client()

# --- Streamlit UI ---

# --- Custom CSS Styling ---
st.markdown("""
    <style>
        html, body, [class*="css"] {
            background: url('https://images.unsplash.com/photo-1637248970116-838902fe389a?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D') no-repeat center center fixed;
            background-size: cover;
            font-family: "Comic Sans MS", "Segoe UI", sans-serif;
            color: #222 !important;
        }
        .stMainBlockContainer {
            padding-top: 20px;
        }
        .stAppHeader {
            display: none;
        }
        .stApp {
            background: rgba(255, 255, 255, 78%);
            backdrop-filter: blur(10px);
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        h1, h2, h3, h4, h5 {
            color: #ff6f61 !important;
        }
        .upload-box {
            border: 2px dashed #ffc1cc;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            background-color: #fff0f5;
            cursor: pointer;
        }
        .upload-box:hover {
            background-color: #ffeef2;
        }
        .confidence-box {
            background-color: #fff3cd;
            border-left: 5px solid #ffcc00;
            padding: 12px;
            border-radius: 8px;
            margin-top: 12px;
        }
        .stage-info {
            background-color: #ffecf1;
            color: #5a0033;
            padding: 15px;
            border-radius: 10px;
            margin-top: 10px;
            font-weight: 500;
        }
        .stImage img {
            max-width: 100%;
            height: auto;
        }
        .stExpanderHeader {
            font-weight: 600;
            font-size: 18px;
            color: #ff6f61;
        }
        
        /* Mobile-specific styles */
        @media (max-width: 768px) {
            .stApp {
                margin: 0;
                border-radius: 0;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 style='text-align: center;'>🎨 Drawee</h1>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center;'>Watch little hands tell big stories</h6>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; font-size: 14px; margin-bottom: 50px;'>Drawee helps parents, teachers, and child development experts understand a child's artistic growth by analyzing their drawings. Based on Lowenfeld’s stages of artistic development, Drawee reveals the creative journey behind every doodle, making it fun and easy to track artistic progress</p>", 
    unsafe_allow_html=True
    )

# --- If authenticated, show welcome and logout ---
if is_authenticated():
    if st.button("Analyze Drawings", use_container_width=True):
        st.switch_page("pages/1_Analyze.py")

else:
    st.markdown("<h5 style='text-align: center;'>Log in or create an account to start analyzing children's drawings.</h5>", unsafe_allow_html=True)
    
    tabs = st.tabs(["🔐 Login", "📝 Create an Account"])

    # --- Login Tab ---
    with tabs[0]:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", use_container_width=True):
            if login(username, password):
                st.success("Logged in successfully!")
                st.switch_page("pages/1_Analyze.py")
            else:
                st.error("Invalid username or password.")

    # --- Create Account Tab ---
    with tabs[1]:
        new_username = st.text_input("Choose a Username", key="signup_username")
        new_password = st.text_input("Choose a Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

        if st.button("Create Account", use_container_width=True):
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_username) < 3 or len(new_password) < 5:
                st.warning("Username must be at least 3 characters, password at least 5.")
            else:
                result = signup(new_username, new_password)
                if result:
                    st.success("Account created successfully! Logging you in...")
                    if login(new_username, new_password):
                        st.switch_page("pages/1_Analyze.py")
                else:
                    st.error("Username already taken or account creation failed.")



# --- Learning Section ---
st.markdown("<h5 style='margin-top: 40px;'>💡 Learn about the stages</h5>", unsafe_allow_html=True)
cols = st.columns(2)
for i, (label, desc) in enumerate(stages_info.items()):
    with cols[i % 2].expander(label, expanded=True):
        st.markdown(f"**{desc}**")

if st.button("Learn More About Drawee", use_container_width=True):
    st.switch_page("pages/2_About Drawee.py")

if is_authenticated():
    if st.button("Logout", use_container_width=True):
        logout()
        st.rerun()


st.markdown("---")

# --- Footer ---

st.markdown("<footer style='text-align:center; padding:10px; font-size:12px;'>© 2025 Drawee. This thesis project features an AI model powered by ResNet-50 for classifying children's drawings based on Lowenfeld's stages of artistic development.</footer>", unsafe_allow_html=True)
