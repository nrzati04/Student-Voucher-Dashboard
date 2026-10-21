"""Primary schools page"""

import streamlit as st
from dashboard_data import page_setup, metric_cards, filtered_school_list, route_filters
from styles import render_footer

routes = page_setup("Primary Schools")
primary = routes[routes["LEVEL"].str.lower() == "primary"]
primary = route_filters(primary, "primary")

st.markdown("Primary school routes only.")
metric_cards(primary, include_vouchers=False)

st.subheader("Primary school list")
filtered_school_list(primary, "primary")

render_footer()
