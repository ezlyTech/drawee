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

# def get_model():
#     file_id = "1_4pP1CIC_DSRa7wHXaTMSjY4nJbR9XO0"
#     output_path = "model_cache/drawee-v1.7.h5"

#     # Make sure the directory exists
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)

#     # Download only if the file doesn't already exist
#     if not os.path.exists(output_path):
#         url = f"https://drive.google.com/uc?id={file_id}"
#         gdown.download(url, output_path, quiet=False)

#     return load_model(output_path)

def get_model(model_name):
    model_map = {
        "resnet": {
            "file_id": "1zx4ks1V2SPZem8oeqpNc2cYqN6l_z0oJ",
            "filename": "drawee-resnet.h5"
        },
        "xception": {
            "file_id": "1ibBelZfUwtr_GEP26mjStfJZYj3HeFtg",
            "filename": "drawee-xception.h5"
        }
    }

    model_info = model_map.get(model_name)
    if not model_info:
        raise ValueError(f"Unknown model name: {model_name}")

    output_path = f"model_cache/{model_info['filename']}"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(output_path):
        url = f"https://drive.google.com/uc?id={model_info['file_id']}"
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


            if upload:
                im = Image.open(upload).convert("RGB")
                img = np.asarray(im)

                # --- Preprocessing for ResNet ---
                resnet_img = cv2.resize(img, (256, 256)) / 255.0
                resnet_input = np.expand_dims(resnet_img, axis=0)

                # --- Preprocessing for Xception ---
                xception_img = cv2.resize(img, (256, 256)) / 255.0
                xception_input = np.expand_dims(xception_img, axis=0)

                @st.dialog("🎯 Analysis Result")
                def show_result_dialog():
                    with st.spinner("Analyzing your drawing..."):
                        time.sleep(2)

                        # Load both models
                        resnet_model = get_model("resnet")
                        xception_model = get_model("xception")

                        try:
                            resnet_pred = resnet_model.predict(resnet_input)
                        except Exception as e:
                            st.error(f"❌ ResNet model prediction failed: {e}")
                            return

                        try:
                            xception_pred = xception_model.predict(xception_input)
                        except Exception as e:
                            st.error(f"❌ Xception model prediction failed: {e}")
                            return

                        # Ensure shapes match for averaging
                        if resnet_pred.shape != xception_pred.shape:
                            st.error(f"⚠️ Prediction shape mismatch: ResNet shape {resnet_pred.shape}, Xception shape {xception_pred.shape}")
                            return

                        # Average predictions
                        final_pred = (resnet_pred + xception_pred) / 2
                        pred_class = np.argmax(final_pred)
                        stage_name = classes[pred_class]
                        confidence = final_pred[0][pred_class] * 100

                        # Save image to storage
                        image_bytes = io.BytesIO()
                        im.save(image_bytes, format='PNG')
                        image_bytes = image_bytes.getvalue()
                        filename = f"{uuid.uuid4().hex}.png"
                        storage_path = f"user_uploads/{filename}"

                        supabase_admin.storage.from_("drawings").upload(storage_path, image_bytes)
                        image_url = supabase_admin.storage.from_("drawings").get_public_url(storage_path)

                        # Store result in Supabase
                        supabase_admin.table("results").insert({
                            "user_id": user_id,
                            "child_id": child_id_local,
                            "image_path": image_url,
                            "prediction": stage_name,
                            "confidence": float(confidence)
                        }).execute()

                    # Display results
                    st.markdown(f"**{stage_name}** - {stage_insights[stage_name]}")
                    st.success(f"{stage_name}: **{confidence:.2f}%**")
                    st.image(im, caption='Uploaded Drawing', use_container_width=True)
                    # st.write("ResNet prediction:", resnet_pred)
                    # st.write("Xception prediction:", xception_pred)
                    # st.write("Final averaged prediction:", final_pred)
                    # st.image(im, caption='Uploaded Drawing', use_container_width=True)

                    # Plot bar chart
                    fig = go.Figure(go.Bar(
                        x=final_pred[0] * 100,
                        y=classes,
                        orientation='h',
                        text=[f"{p:.1f}%" for p in final_pred[0] * 100],
                        textposition='outside',
                        marker=dict(color=['#ff6666' if i == pred_class else '#ffcccc' for i in range(len(classes))])
                    ))
                    st.plotly_chart(fig, use_container_width=True)

                    # Tips and activities
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
