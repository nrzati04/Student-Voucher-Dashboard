"""Primary schools page."""

import streamlit as st
from dashboard_data import page_setup, filtered_school_list, route_filters, level_summary_panel
from styles import render_footer

routes = page_setup("Primary Schools")
primary = routes[routes["LEVEL"].str.lower() == "primary"]
primary = route_filters(primary, "primary")

st.markdown("Primary school routes only.")
level_summary_panel(primary, "primary")

with st.expander("Primary school list", expanded=False):
    filtered_school_list(primary, "primary")

render_footer()
