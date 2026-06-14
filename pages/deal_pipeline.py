"""Deal Pipeline — Live Crexi screening, single-deal underwriting, AI Analyst.

Sub-page of the Streamlit MPA. The 3 tabs each defer to a render function
defined in app.py, which keeps the implementation reusable as a standalone
script too.
"""
import streamlit as st

from app import (
    render_sidebar,
    render_screener_tab,
    render_analyzer_tab,
    render_ai_analyst_tab,
)

st.title("🎯 Deal Pipeline")
st.caption(
    "Live Crexi screening → per-deal underwriting → Claude AI analysis. "
    "Sidebar filters are scoped to this page only."
)
st.markdown("---")

# Apify-driven tabs share these two session-state keys for the live fetch.
st.session_state.setdefault("deals_rows", None)
st.session_state.setdefault("data_source", "sample")

# Render the Apify-filter sidebar once. The sidebar widgets only appear on
# this page because Streamlit's MPA resets the sidebar between pages.
_sidebar_state = render_sidebar()

tab_deal_screener, tab_analyzer, tab_ai_analyst = st.tabs([
    "🌐 Deal Screener",
    "🔬 Deal Analyzer",
    "🤖 AI Analyst",
])

with tab_deal_screener:
    render_screener_tab(_sidebar_state)

with tab_analyzer:
    render_analyzer_tab(_sidebar_state)

with tab_ai_analyst:
    render_ai_analyst_tab(_sidebar_state)
