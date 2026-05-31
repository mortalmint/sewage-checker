"""
app.py — UK Sewage Upstream Checker
Streamlit entry point. Phase 7 will build this out fully.
For now: a minimal skeleton that confirms the app runs.
"""

import streamlit as st

st.set_page_config(
    page_title="Upstream Sewage Checker",
    page_icon="💧",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("💧 Upstream Sewage Checker")
st.caption("England (and Wales where data exists) · Data from Water UK / Stream")

st.info(
    "🚧 Under construction. Come back soon.",
    icon="🚧",
)

st.markdown(
    """
    **What this will do:**
    Drop a pin on any river in England or Wales and see which storm overflows
    are upstream of your chosen point — and whether they're currently spilling.

    **Important:** spilling ≠ unsafe. This app reports what is known.
    It never makes a safety judgement.
    """
)
