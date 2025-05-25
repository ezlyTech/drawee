import streamlit as st
import re
import html
import pandas as pd
import plotly.express as px
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter

from utils.auth import get_supabase_admin_client
from classes_def import stage_insights, stages_info

def is_valid_uuid(val):
    return bool(re.match(r'^[0-9a-fA-F\-]{36}$', val))

def extract_simple_stage_name(stage: str) -> str:
    """Cleans up a prediction string to match stage_insights keys."""
    stage = re.sub(r'[^\w\s]', '', stage)
    stage = re.sub(r'\d.*$', '', stage)
    stage = stage.strip()
    for key in stage_insights:
        if key.lower() in stage.lower():
            return key
    return stage

def render_child_records(child_id: str):
    if not child_id or not is_valid_uuid(child_id):
        st.error("Invalid or missing child ID.")
        return

    supabase_admin = get_supabase_admin_client()
    user_id = st.session_state['user']['id']

    child_resp = supabase_admin.table("children").select("name").eq("id", child_id).eq("user_id", user_id).execute()
    if not child_resp.data:
        st.error("Child record not found or access denied.")
        return

    child_name = child_resp.data[0]["name"]
    st.markdown(f"<h5 style='text-align: center;'>Records for {child_name}</h5>", unsafe_allow_html=True)

    if st.button("⬅️ Back to Analyze"):
        st.session_state.pop('selected_child_id', None)
        st.rerun()

    results_resp = supabase_admin.table("results").select("*").eq("child_id", child_id).order("created_at", desc=True).execute()
    results = results_resp.data or []

    if not results:
        st.markdown("<h6 style='text-align: center;'>No analysis records found for this child.</h6>", unsafe_allow_html=True)
        if st.button("⬅️ Back to Analyze", key="back_bottom"):
            st.session_state.pop('selected_child_id', None)
            st.rerun()
        return

    # Format records
    records_for_chart = []
    for r in results:
        try:
            dt_utc = datetime.fromisoformat(r["created_at"])
            dt_pht = dt_utc.astimezone(ZoneInfo("Asia/Manila"))
            created_str = dt_pht.strftime("%b %d, %Y %I:%M %p")
            created_date = dt_pht.date()
        except:
            created_str = "Invalid date"
            created_date = None

        records_for_chart.append({
            "id": r["id"],
            "image_path": r["image_path"],
            "prediction": r["prediction"],
            "confidence": r["confidence"],
            "created_at_str": created_str,
            "created_date": created_date
        })

    # Build simplified mapping for stage descriptions
    simple_stage_info = {}
    for key, desc in stages_info.items():
        match = re.search(r"[A-Za-z\s]+(?:Art|Stage|Age|Reasoning)", key)
        if match:
            simple_name = match.group(0).strip()
            simple_stage_info[simple_name] = (key, desc)

    # Generate summary
    pred_counts = Counter(r['prediction'] for r in records_for_chart)
    if pred_counts:
        total = sum(pred_counts.values())
        summary_lines = [f"This child has {total} analyzed drawing(s) categorized into:"]

        for pred, count in pred_counts.items():
            key_desc_pair = simple_stage_info.get(pred, (pred, "No description available."))
            # summary_lines.append(f"- **{html.escape(pred)}**: {count} record(s). {key_desc_pair[1]}")
            summary_lines.append(f"- <b>{html.escape(pred)}</b>: {count} record(s). {key_desc_pair[1]}")


        most_common_pred = pred_counts.most_common(1)[0][0]
        insight = stage_insights.get(extract_simple_stage_name(most_common_pred), "")

        st.markdown(
            "<div style='background:#FFF;padding:10px 16px;border-radius:8px;margin-bottom:15px;'>"
            "<h6 style='margin-bottom:5px;'>Summary</h6>"
            + "<br>".join(summary_lines) +
            "</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"<div style='background:#e8fee8;padding:10px 16px;border-radius:8px;margin-bottom:15px;'>"
            f"<h6 style='margin-bottom:5px;'>Insight</h6>"
            f"{insight}"
            f"</div>", unsafe_allow_html=True
        )
    else:
        st.markdown("<p>No predictions to summarize.</p>")

    # Chart
    df_chart = pd.DataFrame([
        {"Date": r["created_date"], "Prediction": r["prediction"]}
        for r in records_for_chart if r["created_date"]
    ])

    if not df_chart.empty:
        pred_progress = df_chart.groupby(["Date", "Prediction"]).size().reset_index(name='Count')

        fig = px.line(
            pred_progress,
            x="Date",
            y="Count",
            color="Prediction",
            markers=True,
            title="Prediction Progress Over Time"
        ) if len(pred_progress['Date'].unique()) > 1 else px.bar(
            pred_progress,
            x="Date",
            y="Count",
            color="Prediction",
            title="Prediction Progress Over Time"
        )

        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            height=400,
            xaxis_title="Date",
            yaxis_title="Number of Predictions",
            legend_title="Prediction"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No valid dates found to plot prediction progress.")

    st.markdown("---")
    st.markdown(f"<h5>Review {child_name}'s Records Below</h5>", unsafe_allow_html=True)

    for record in records_for_chart:
        cols = st.columns([2, 2, 1])
        with cols[0]:
            st.markdown(f"<small style='color:gray;'>Date Analyzed: {record['created_at_str']}</small>", unsafe_allow_html=True)
            st.image(record["image_path"], width=250)
        with cols[1]:
            st.markdown(f"**Prediction:** {record['prediction']}")
            st.markdown(f"**Confidence:** {record['confidence']:.2f}%")
        with cols[2]:
            delete_key = f"delete_{record['id'] or record['created_at_str']}"
            if st.button("Delete Record", key=delete_key):
                try:
                    delete_resp = supabase_admin.table("results").delete().eq("id", record["id"]).execute()
                    if delete_resp.data:
                        st.success("Record deleted successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to delete the record.")
                except Exception as e:
                    st.error(f"Error: {e}")
        st.markdown("---")

    if st.button("⬅️ Back to Analyze", key="back_bottom"):
        st.session_state.pop('selected_child_id', None)
        st.rerun()
