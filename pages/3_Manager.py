"""Manager / PIC page"""

import streamlit as st
from dashboard_data import page_setup, metric_cards, level_table, filtered_school_list
from styles import render_footer

routes = page_setup("Manager / PIC")

managers = sorted(routes["MANAGER"].dropna().unique().tolist())
selected = st.selectbox("Select manager / PIC", managers)

part = routes[routes["MANAGER"] == selected]
st.markdown(f"### {selected}")
metric_cards(part)

st.subheader("By school level")
level_table(part)

st.subheader("Schools for this manager")
filtered_school_list(part, "manager")

render_footer()