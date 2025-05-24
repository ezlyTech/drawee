import streamlit as st
st.set_page_config(page_title="Drawee | Analyze", page_icon="🖼️")

import uuid
import io
import numpy as np
import os
import gdown
import plotly.graph_objects as go
import time
from PIL import Image
import cv2
from tensorflow.keras.models import load_model
from utils.auth import login, signup, is_authenticated, logout, get_supabase_client, get_supabase_admin_client
from classes_def import stage_insights, development_tips, recommended_activities, classes
import Child_Records

supabase_admin = get_supabase_admin_client()
if supabase_admin is None:
    st.error("Error: Unable to connect to Supabase.")
    st.stop()

# --- Get query params to detect if showing Child Records or Analyze ---
# child_id = st.query_params.get("child_id", [None])[0]
child_id = st.session_state.get("selected_child_id", None)

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
            padding-top: 40px;
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
            
        .stFileUploader {
            border: 2px dashed #FF914D;
            padding: 40px;
            text-align: center;
            border-radius: 15px;
            background-color: #fff3e6;
            transition: background-color 0.3s ease;
        }
        .stFileUploader:hover {
            background-color: #ffe1c4;
        }
        .stFileUploader label { display: none; }
        
        @media (max-width: 768px) {
            .stApp {
                margin: 0;
                border-radius: 0;
            }
        }
    </style>
""", unsafe_allow_html=True)

def get_model():
    file_id = "1_4pP1CIC_DSRa7wHXaTMSjY4nJbR9XO0"
    output_path = "model_cache/drawee-v1.7.h5"

    # Make sure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Download only if the file doesn't already exist
    if not os.path.exists(output_path):
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output_path, quiet=False)

    return load_model(output_path)

if is_authenticated():

    if child_id is None:
        # --- Show Analyze UI ---
        
        with st.container():
            st.markdown("""
                <div style="
                    background-color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    margin-bottom: 2rem;
                ">
                    <div style="font-size: 1.2rem; font-weight: 600;">
                        👋 Welcome, <strong>{username}</strong>
                    </div>
                </div>
            """.format(username=st.session_state['user']['username']), unsafe_allow_html=True)


        # --- Existing Analyze UI here ---

        # Fetch existing children names for autocomplete
        user_id = st.session_state['user']['id']
        children_response = supabase_admin.table("children").select("name").eq("user_id", user_id).execute()
        existing_children = [c['name'] for c in children_response.data] if children_response.data else []

        options = ["New Record"] + existing_children
        selected_name = st.selectbox("Select a child or create a new record:", options)

        new_child_name = None
        if selected_name == "New Record":
            new_child_name = st.text_input("Enter new child's name")

        child_name = new_child_name.strip() if new_child_name else (selected_name if selected_name != "New Record" else "")

        if child_name:
            child_response = supabase_admin.table("children").select("id").eq("user_id", user_id).eq("name", child_name).execute()
            if child_response.data:
                child_id_local = child_response.data[0]['id']
            else:
                child_id_local = str(uuid.uuid4())
                supabase_admin.table("children").insert({
                    "id": child_id_local,
                    "user_id": user_id,
                    "name": child_name
                }).execute()

            st.session_state['current_child_id'] = child_id_local
            st.session_state['current_child_name'] = child_name

            st.markdown("<h5>📸 Upload the Drawing</h5>", unsafe_allow_html=True)
            upload = st.file_uploader("", type=["png", "jpg", "jpeg"], key="file_input", label_visibility="collapsed")

            # @st.cache_resource
            # def get_model():
            #     # return load_model("drawee-v1.6.h5") # okay naman, pero 40% accuracy
            #     # return load_model("drawee-v1.6.5.h5") # puro schematic sya 100%
            #     # return load_model("drawee-v1.6.4.h5") # puro gang sya, di tumatama sa scribbling
            #     # return load_model("drawee-v1.6.2.h5") # puro scribbling sya 100%
            #     return load_model("drawee-v1.7.h5")

            if upload:
                im = Image.open(upload).convert("RGB")
                img = np.asarray(im)

                # v.1.6+ (ResNet50 Model)
                # resized_img = cv2.resize(img, (182, 183)) / 255.0
                # image = resized_img.reshape(1, -1)  # Flatten image to 1D vector

                # # If needed, crop or pad to 100,352
                # expected_size = 100352

                # if image.shape[1] > expected_size:
                #     # Crop extra features
                #     image = image[:, :expected_size]
                # elif image.shape[1] < expected_size:
                #     # Pad with zeros
                #     padding = expected_size - image.shape[1]
                #     image = np.pad(image, ((0, 0), (0, padding)), mode='constant')


                # v.7 (Xception Model)
                resized_img = cv2.resize(img, (256, 256))
                resized_img = resized_img / 255.0
                image = np.expand_dims(resized_img, axis=0)

                @st.dialog("🎯 Analysis Result")
                def show_result_dialog():
                    with st.spinner("Analyzing your drawing..."):
                        time.sleep(2)
                        model = get_model()
                        preds = model.predict(image)
                        percentages = preds[0]
                        pred_class = np.argmax(percentages)
                        stage_name = classes[pred_class]
                        confidence = percentages[pred_class] * 100

                        image_bytes = io.BytesIO()
                        im.save(image_bytes, format='PNG')
                        image_bytes = image_bytes.getvalue()
                        filename = f"{uuid.uuid4().hex}.png"
                        storage_path = f"user_uploads/{filename}"

                        supabase_admin.storage.from_("drawings").upload(storage_path, image_bytes)
                        image_url = supabase_admin.storage.from_("drawings").get_public_url(storage_path)

                        supabase_admin.table("results").insert({
                            "user_id": user_id,
                            "child_id": child_id_local,
                            "image_path": image_url,
                            "prediction": stage_name,
                            "confidence": float(confidence)
                        }).execute()

                    st.markdown(f"**{stage_name}** - {stage_insights[stage_name]}")
                    st.markdown(f"Confidence: **{confidence:.2f}%**")
                    st.image(im, caption='Uploaded Drawing', use_container_width=True)

                    fig = go.Figure(go.Bar(
                        x=percentages * 100,
                        y=classes,
                        orientation='h',
                        text=[f"{p*100:.1f}%" for p in percentages],
                        textposition='outside',
                        marker=dict(color=['#ff6666' if i == pred_class else '#ffcccc' for i in range(len(classes))])
                    ))
                    st.plotly_chart(fig, use_container_width=True)

                    st.subheader("Development Tips")
                    for tip in development_tips[stage_name]:
                        st.markdown(f"- {tip}")
                    st.subheader("Recommended Activities")
                    for activity in recommended_activities[stage_name]:
                        st.markdown(f"- {activity}")

                show_result_dialog()

        st.markdown("---")

        # Inject CSS to style the "button" like a link
        st.markdown("""
        <style>
        .child-row {
            display: flex;
            flex-direction: row;
            align-items: center;
            border-bottom: 1px solid #ddd;
            padding: 8px 0;
            gap: 16px;
            margin-bottom: 10px;
        }
        .child-cell {
            flex: 1;
            min-width: 0;
            font-size: 13px;
        }
        .child-name {
            flex: 2;
            overflow-wrap: break-word;
        }
        .child-count {
            flex: 2;
            text-align: center;
        }
        .child-action {
            flex: 2;
            text-align: center;
        }
        button[data-testid="baseButton"] {
            background: none;
            border: none;
            color: #1a73e8;
            font-weight: 600;
            text-align: center;
            text-decoration: none;
            cursor: pointer;
            padding: 0;
            font-size: 13px;
        }
        button[data-testid="baseButton"]:hover {
            text-decoration: underline;
        }
        </style>
        """, unsafe_allow_html=True)

        # Title
        st.markdown("<h5>List of Children's Drawings Analyzed</h5>", unsafe_allow_html=True)

        try:
            # Fetch children from Supabase
            child_list = supabase_admin.table("children").select("id, name").eq("user_id", user_id).execute()

            # Handle delete via query param
            delete_child_id = st.query_params.get("delete_child_id")
            if delete_child_id:
                try:
                    supabase_admin.table("results").delete().eq("child_id", delete_child_id).execute()
                    supabase_admin.table("children").delete().eq("id", delete_child_id).execute()
                    st.success("Child and associated records deleted successfully.")
                    st.query_params.clear()  # Clear query params
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete child: {e}")

            if not child_list.data:
                st.info("No child records found yet.")
            else:
                # Header row
                st.markdown("""
                <div class="child-row" style="border-bottom: 2px solid #bbb; font-weight: 700;">
                    <div class="child-cell child-name">Child Name</div>
                    <div class="child-cell child-count">Number of Records</div>
                    <div class="child-cell child-action">Action</div>
                </div>
                """, unsafe_allow_html=True)

                # Handle view via query param
                if "child_id" in st.query_params:
                    st.session_state["selected_child_id"] = st.query_params["child_id"]
                    st.query_params.clear()
                    st.rerun()

                for idx, child in enumerate(child_list.data):
                    result_count = supabase_admin.table("results").select("id", count="exact").eq("child_id", child['id']).execute().count or 0
                    view_url = f"?child_id={child['id']}"
                    delete_form = f"""
                        <form method="get" style="margin: 0;" onsubmit="return confirm('Are you sure you want to delete this child and all associated records?');">
                            <input type="hidden" name="delete_child_id" value="{child['id']}" />
                            <button type="submit" style="
                                flex: 0;
                                padding: 0.4rem 0.6rem;
                                background-color: #eee;
                                color: #f00;
                                border-radius: 5px;
                                font-weight: bold;
                                border: none;
                                cursor: pointer;
                            " title="Delete">🗑️</button>
                        </form>
                    """

                    st.markdown(f"""
                        <div style="
                            border: 1px solid #ddd;
                            border-radius: 10px;
                            padding: 1rem;
                            margin-bottom: 1rem;
                            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
                            background-color: #fff;
                            display: flex;
                            gap: 1rem;
                            align-items: center;
                            font-size: 13px;
                        ">
                            <div style="flex: 3; font-weight: bold;">{child['name']}</div>
                            <div style="flex: 2; color: #888;">{result_count} record(s)</div>
                            <div style="flex: 2; display: flex; gap: 0.5rem;">
                                <a href="{view_url}" style="
                                    flex: 1;
                                    padding: 0.4rem;
                                    text-align: center;
                                    background-color: rgb(233 124 124);
                                    color: white;
                                    text-decoration: none;
                                    border-radius: 5px;
                                ">View Records</a>
                                <span style="display: flex; align-items: center;">{delete_form}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error loading child records: {e}")


    else:
        # --- Show Child Records UI ---
        Child_Records.render_child_records(child_id)
else:
    # --- Title ---
    st.markdown("<h1 style='text-align: center;'>🎨 Drawee</h1>", unsafe_allow_html=True)
    st.markdown("<h6 style='text-align: center;'>Please login or create an account first.</h6>", unsafe_allow_html=True)

    tabs = st.tabs(["🔐 Login", "📝 Create an Account"])

    with tabs[0]:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True):
            if login(username, password):
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

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
                        st.rerun()
                else:
                    st.error("Username already taken or account creation failed.")


# Footer

st.markdown("<footer style='text-align:center; padding:10px; font-size:12px; margin-top: 5em;'>© 2025 Drawee. This thesis project features an AI model powered by ResNet-50 for classifying children's drawings based on Lowenfeld's stages of artistic development.</footer>", unsafe_allow_html=True)
