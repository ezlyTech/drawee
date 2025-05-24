# drawee_app.py

import streamlit as st
from classes_def import stages_info_copy
import os

st.set_page_config(page_title="Drawee | About Drawee", page_icon="🖼️")

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
        .book-image-container {
          display: flex;
          justify-content: center;
          padding-top: 20px;
        }
        .book-image {
          width: 60%;
          height: auto;
        }
        .book-desc-container {
          align-self: center;
        }
        .book-desc {
          padding-inline: 20px;
          align-self: center;
        }
        /*.book-desc span {
          display: none;
        }*/
        
        /* Mobile-specific styles */
        @media (max-width: 768px) {
          .stApp {
            margin: 0;
            border-radius: 0;
          }
          .book-image-container {
            padding-top:10px;
          }
          .book-desc-container {
            padding: 20px 10px;
          }
          .book-desc {
            text-align: center;
          }
        }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 style='text-align: center;'>🎨 Drawee</h1>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center;'>Watch little hands tell big stories</h6>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; font-size: 14px;'>Drawee helps parents, teachers, and child development experts understand a child's artistic growth by analyzing their drawings. Based on Lowenfeld’s stages of artistic development, Drawee reveals the creative journey behind every doodle, making it fun and easy to track artistic progress</p>", 
    unsafe_allow_html=True
    )

# --- Learning Section ---
st.markdown("<h5>💡 Learn about the stages</h5>", unsafe_allow_html=True)
cols = st.columns(2)
for i, (label, info) in enumerate(stages_info_copy.items()):
    with cols[i % 2].expander(label, expanded=True):
        image_path = info["img"]
        if os.path.exists(image_path):
            st.image(image_path, use_container_width=True)
        else:
            st.warning(f"Image not found: {image_path}")
        st.markdown(f"<div style='font-size: 14px; margin-bottom: 20px;'>{info['desc']}</div>", unsafe_allow_html=True)
st.markdown("---")

# --- Lowenfeld Book Section ---
cols = st.columns(2)
with cols[0]:
    # st.image(
    #     "assets/images/book.jpg",  # Example cover image URL
    #     use_container_width=False,
    #     width=200
    # )
    st.markdown(
        """
        <div class="book-image-container">
        <img src="https://ia801204.us.archive.org/BookReader/BookReaderImages.php?zip=/3/items/creativementalgr00/creativementalgr00_jp2.zip&file=creativementalgr00_jp2/creativementalgr00_0001.jp2&id=creativementalgr00&scale=4&rotate=0" alt="Book Cover" class="book-image"/>
        </div>
        """,
        unsafe_allow_html=True
    )
with cols[1]:
    st.markdown(
        """
        <div class="book-desc-container">
        <h5 class="book-desc"> Creative and Mental Growth </h5>
        <p class="book-desc" style="font-weight: semibold; margin: 0;">By Viktor Lowenfeld</p>
        <br>
        <p class="book-desc">Viktor Lowenfeld’s influential book, <b>Creative and Mental Growth</b>, explores the stages of artistic development in children. This foundational work provides insights into how children express themselves through art and how their creativity evolves as they grow. Lowenfeld’s stages are widely used by educators and psychologists to understand and nurture artistic potential in young learners.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# --- Footer ---

st.markdown("<footer style='text-align:center; padding:10px; font-size:12px;'>© 2025 Drawee. This thesis project features an AI model powered by ResNet-50 for classifying children's drawings based on Lowenfeld's stages of artistic development.</footer>", unsafe_allow_html=True)
