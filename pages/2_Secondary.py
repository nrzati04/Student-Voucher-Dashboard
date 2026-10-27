"""Secondary schools page."""

import streamlit as st
from dashboard_data import page_setup, filtered_school_list, route_filters, level_summary_panel
from styles import render_footer

routes = page_setup("Secondary Schools")
secondary = routes[routes["LEVEL"].str.lower() == "secondary"]
secondary = route_filters(secondary, "secondary")

st.markdown("Secondary school routes only.")
level_summary_panel(secondary, "secondary")

with st.expander("Secondary school list", expanded=False):
    filtered_school_list(secondary, "secondary")

render_footer()
