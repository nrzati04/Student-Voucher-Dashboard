"""US Pizza Malaysia – Student Voucher Dashboard home page."""

import streamlit as st
from dashboard_data import page_setup, metric_cards, level_table, manager_table, filtered_school_list, progress_pie
from styles import render_footer

routes = page_setup("Overall")
st.markdown("Track school visits and voucher distribution across Malaysia.")
metric_cards(routes)

st.subheader("Progress at a glance")
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.plotly_chart(progress_pie(routes, "School result", "schools"), use_container_width=True, key="school_result_pie")
with chart_col2:
    st.plotly_chart(progress_pie(routes, "Voucher balance", "vouchers"), use_container_width=True, key="voucher_balance_pie")

st.subheader("Progress by school level")
level_table(routes)
st.subheader("Progress by manager / PIC")
manager_table(routes)
st.subheader("Find schools by result")
filtered_school_list(routes, "overall")
render_footer()

