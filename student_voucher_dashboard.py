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

chart_column, region_column = st.columns([1, 1.15], gap="large")
with chart_column:
    st.subheader("Progress at a glance")
    st.plotly_chart(
        progress_pie(overview, "School result", "schools"),
        use_container_width=True,
        key="school_result_pie",
    )
with region_column:
    st.subheader("School coverage by region")
    region_table(overview)

with st.expander("School progress by area", expanded=False):
    area_progress_table(routes, overview_scope)

with st.expander("Progress by manager", expanded=False):
    person_progress_table(overview)

with st.expander("Progress by school level", expanded=False):
    level_table(overview, include_vouchers=False)

with st.expander("Find schools", expanded=False):
    filtered_school_list(
        overview,
        "overall",
        show_status_filter=False,
        include_distribution=False,
        status_filter=school_status,
    )

render_footer()
