"""Primary schools page"""

import streamlit as st
from dashboard_data import page_setup, metric_cards, filtered_school_list
from styles import render_footer

routes = page_setup("Primary Schools")
primary = routes[routes["LEVEL"].str.lower() == "primary"]

st.markdown("Primary school routes only.")
metric_cards(primary)

st.subheader("Primary school list")
filtered_school_list(primary, "primary")

render_footer()
