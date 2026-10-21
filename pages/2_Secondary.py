"""Secondary schools page"""

import streamlit as st
from dashboard_data import page_setup, metric_cards, filtered_school_list, route_filters
from styles import render_footer

routes = page_setup("Secondary Schools")
secondary = routes[routes["LEVEL"].str.lower() == "secondary"]
secondary = route_filters(secondary, "secondary")

st.markdown("Secondary school routes only.")
metric_cards(secondary, include_vouchers=False)

st.subheader("Secondary school list")
filtered_school_list(secondary, "secondary")

render_footer()
