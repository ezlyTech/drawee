import streamlit as st
from utils.auth import get_supabase_admin_client
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
import plotly.express as px
import pandas as pd
import html
from classes_def import stage_insights, stages_info, classes

def is_valid_uuid(val):
    uuid_regex = re.compile(
        r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    )
    return bool(uuid_regex.match(val))

def render_child_records(child_id: str):
    if not child_id:
        st.error("No child ID provided.")
        return

    if not is_valid_uuid(child_id):
        st.error("Invalid child ID.")
        return

    supabase_admin = get_supabase_admin_client()
    user_id = st.session_state['user']['id']

    # Fetch child info
    child_resp = supabase_admin.table("children").select("name").eq("id", child_id).eq("user_id", user_id).execute()
    if not child_resp.data:
        st.error("Child record not found or access denied.")
        return

    child_name = child_resp.data[0]["name"]
    st.markdown(f"<h5 style='text-align: center;'>Records for {child_name}</h5>", unsafe_allow_html=True)

    # Top Back Button
    if st.button("⬅️ Back to Analyze"):
        st.session_state.pop('selected_child_id', None)
        st.rerun()

    # Fetch results
    results_resp = supabase_admin.table("results").select("*").eq("child_id", child_id).order("created_at", desc=True).execute()
    results = results_resp.data if results_resp.data else []

    if not results:
        st.markdown("<h6 style='text-align: center;'>No analysis records found for this child.</h6>", unsafe_allow_html=True)
        # Bottom Back Button as well here
        if st.button("⬅️ Back to Analyze", key="back_bottom"):
            st.session_state.pop('selected_child_id', None)
            st.rerun()
        return

    # Prepare data for summary & chart
    records_for_chart = []
    for record in results:
        created_at = record.get("created_at")
        if created_at:
            try:
                # Parse ISO string with timezone info (if any)
                dt_utc = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                dt_pht = dt_utc.astimezone(ZoneInfo("Asia/Manila"))
                created_str = dt_pht.strftime("%b %d, %Y %I:%M %p")
                created_date = dt_pht.date()
            except ValueError:
                created_str = "Invalid date"
                created_date = None
        else:
            created_str = "Unknown date"
            created_date = None

        records_for_chart.append({
            "id": record["id"],
            "image_path": record["image_path"],
            "prediction": record["prediction"],
            "confidence": record["confidence"],
            "created_at_str": created_str,
            "created_date": created_date
        })

    # --- Generate Summary Text ---
    pred_counts = Counter(r['prediction'] for r in records_for_chart)

    if pred_counts:
        summary_lines = []
        total = sum(pred_counts.values())
        summary_lines.append(f"This child has {total} analyzed drawing(s) categorized into:")

        for pred, count in pred_counts.items():
            # Match key in stages_info ignoring emoji prefix
            matching_key = None
            for key in stages_info.keys():
                # Simple check ignoring emojis and spacing
                if pred in key or key.strip() in key:
                    matching_key = key
                    break
            description = stages_info.get(matching_key, "No description available.")
            summary_lines.append(f"- **{html.escape(pred)}**: {count} record(s). {description}")

        most_common_pred = pred_counts.most_common(1)[0][0]
        insight = stage_insights.get(most_common_pred, "")

        summary_md = "\n\n".join(summary_lines)
        st.markdown(
            f"<div style='background:#FFF;padding:10px 16px;border-radius:8px;margin-bottom:15px;'>"
            f"<h6 style='margin-bottom:5px;'>Summary</h6>"
            f"{summary_md}"
            f"</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:#e8fee8;padding:10px 16px;border-radius:8px;margin-bottom:15px;'>"
            f"<h6 style='margin-bottom:5px;'>Insight</h6>"
            f"{insight}"
            f"</div>", unsafe_allow_html=True)

    else:
        st.markdown("<p>No predictions to summarize.</p>")

    # --- Plotly Chart ---
    # Create dataframe for chart: counts per prediction per date
    df = pd.DataFrame(records_for_chart)
    if df.empty:
        st.info("No data to plot.")
    else:
        df_grouped = df.groupby(['created_date', 'prediction']).size().reset_index(name='count')
        # Sort dates ascending
        df_grouped = df_grouped.sort_values('created_date')

        fig = px.bar(df_grouped,
                     x='created_date',
                     y='count',
                     color='prediction',
                     labels={'created_date': 'Date', 'count': 'Number of Drawings', 'prediction': 'Prediction'},
                     title='Prediction Counts Over Time',
                     height=300)

        fig.update_layout(
            xaxis=dict(tickformat='%b %d', tickangle=-45),
            legend_title_text='Prediction',
            margin=dict(l=20, r=20, t=40, b=40),
            barmode='stack'
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.markdown(f"<h5>Review {child_name}'s Records Below</h5>", unsafe_allow_html=True)

    # Display each record with image, prediction, confidence, date, and delete button
    for record in records_for_chart:
        cols = st.columns([2, 2, 1])

        with cols[0]:
            st.markdown(f"<small style='color:gray;'>Date Analyzed: {record['created_at_str']}</small>", unsafe_allow_html=True)
            st.image(record["image_path"], width=250)

        with cols[1]:
            st.markdown(f"**Prediction:** {record['prediction']}")
            st.markdown(f"**Confidence:** {record['confidence']:.2f}%")

        with cols[2]:
            delete_key = f"delete_{record['id']}"
            if st.button("Delete Record", key=delete_key):
                try:
                    delete_resp = supabase_admin.table("results").delete().eq("id", record["id"]).execute()
                    if delete_resp.data is not None:
                        st.success("Record deleted successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to delete the record: No data returned.")
                except Exception as e:
                    st.error(f"Failed to delete the record: {e}")

        st.markdown("---")

    # Bottom Back Button
    if st.button("⬅️ Back to Analyze", key="back_bottom"):
        st.session_state.pop('selected_child_id', None)
        st.rerun()
