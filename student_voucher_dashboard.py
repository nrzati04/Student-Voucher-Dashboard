"""US Pizza Malaysia – Student Voucher Dashboard home page."""

import streamlit as st
from dashboard_data import (
    page_setup, metric_cards, level_table, manager_table, filtered_school_list,
    progress_pie, overview_filters, region_table,
)
from styles import render_footer

routes = page_setup("Overall")
st.markdown("Track school visits and voucher distribution across Malaysia.")
overview = overview_filters(routes)
metric_cards(overview, include_vouchers=False)

st.subheader("Progress at a glance")
st.plotly_chart(
    progress_pie(overview, "School result", "schools"),
    use_container_width=True,
    key="school_result_pie",
)

st.subheader("School coverage by region")
region_table(overview)
st.subheader("Progress by school level")
level_table(overview, include_vouchers=False)
st.subheader("Progress by manager / PIC")
manager_table(overview, include_vouchers=False)
st.subheader("Find schools")
filtered_school_list(
    overview,
    "overall",
    show_status_filter=False,
    include_distribution=False,
)
render_footer()

