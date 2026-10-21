"""Manager / PIC page"""

import streamlit as st
from dashboard_data import page_setup, metric_cards, level_table, filtered_school_list, route_filters
from styles import render_footer

routes = page_setup("Manager / PIC")

managers = sorted(routes["MANAGER"].dropna().unique().tolist())
selected = st.selectbox("Select manager", managers)

part = routes[routes["MANAGER"] == selected]
part = route_filters(part, "manager_page", include_manager=False)
st.markdown(f"### {selected}")
metric_cards(part, include_vouchers=False)

with st.expander("Progress by school level", expanded=False):
    level_table(part, include_vouchers=False)

with st.expander("Schools for this manager", expanded=False):
    filtered_school_list(part, "manager")

render_footer()
