"""US Pizza Malaysia – Student Voucher Dashboard home page."""

import streamlit as st
from dashboard_data import (
    page_setup, metric_cards, level_table, filtered_school_list,
    progress_pie, overview_filters, region_table, area_progress_table, person_progress_table,
)
from styles import render_footer

routes = page_setup("Overall")
st.markdown("Track school visits and voucher distribution across Malaysia.")
overview, overview_scope, school_status = overview_filters(routes)
metric_cards(overview, include_vouchers=False)

st.subheader("Progress at a glance")
_, chart_column, _ = st.columns([1, 1.25, 1])
with chart_column:
    st.plotly_chart(
        progress_pie(overview, "School result", "schools"),
        use_container_width=True,
        key="school_result_pie",
    )

st.subheader("School coverage by region")
region_table(overview)
st.subheader("Progress by person in charge")
person_progress_table(overview)

st.subheader("School progress by area")
area_progress_table(routes, overview_scope)
st.subheader("Progress by school level")
level_table(overview, include_vouchers=False)
st.subheader("Find schools")
filtered_school_list(
    overview,
    "overall",
    show_status_filter=False,
    include_distribution=False,
    status_filter=school_status,
)
render_footer()

