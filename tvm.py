"""CRE Financial Dashboard — multi-page entry point.

Two pages:
- 📐 Commercial Math  — CCIM 101 calculators (TVM, DCF, APOD, Pro Forma,
  Financing, Leveraged Pro Forma). Lives in pages/commercial_math.py.
- 🎯 Deal Pipeline    — Live Crexi screening, single-deal analyzer, and the
  Claude AI Analyst. Lives in pages/deal_pipeline.py.

Streamlit Cloud is configured to use this file as the main entry point, so
the split works without any Cloud-settings change.
"""
import streamlit as st

st.set_page_config(
    page_title="CRE Financial Dashboard",
    layout="wide",
    page_icon="🏢",
)

commercial_math_page = st.Page(
    "pages/commercial_math.py",
    title="Commercial Math",
    icon="📐",
    default=True,
)
deal_pipeline_page = st.Page(
    "pages/deal_pipeline.py",
    title="Deal Pipeline",
    icon="🎯",
)

pg = st.navigation([commercial_math_page, deal_pipeline_page])
pg.run()
