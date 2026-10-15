"""School selection on the left; update and record actions on the right."""

import re
import streamlit as st
from dashboard_data import page_setup, save_school_update
from styles import render_footer

routes = page_setup("Update School")
st.caption("Select a route and school on the left. Update or review its distribution record on the right.")

selector_panel, record_panel = st.columns([0.95, 1.65], gap="large")
with selector_panel:
    st.subheader("School selection")
    managers = sorted(routes["MANAGER"].dropna().unique().tolist())
    manager = st.selectbox("Route manager", managers)
    subset = routes[routes["MANAGER"] == manager].copy()

    level = st.selectbox("School level", ["All levels", "Primary", "Secondary"])
    if level != "All levels":
        subset = subset[subset["LEVEL"].str.lower() == level.lower()]

    query = st.text_input("Search school", placeholder="Type part of the school name")
    if query.strip():
        subset = subset[subset["NAMA SEKOLAH"].astype(str).str.contains(query.strip(), case=False, na=False)]

    if subset.empty:
        st.info("No schools match these filters. Try another manager, level, or search.")
        render_footer()
        st.stop()

    name_counts = subset["NAMA SEKOLAH"].astype(str).value_counts()
    options = {}
    for idx, school_row in subset.iterrows():
        label = f"{school_row['NAMA SEKOLAH']} · {school_row['LEVEL']}"
        if name_counts.get(str(school_row["NAMA SEKOLAH"]), 0) > 1:
            label += f" · Stop {school_row.get('STOP', '')}"
        options[label] = idx
    selected = st.selectbox("School", list(options))
    row = routes.loc[options[selected]]

    status_now = str(row.get("STATUS", "") or "")
    status_label = status_now or "Pending"
    st.markdown(f"### {row['NAMA SEKOLAH']}")
    st.caption(f"{row['LEVEL']} · Route manager: {manager}")
    metric_left, metric_right = st.columns(2)
    metric_left.metric("Current result", status_label)
    metric_right.metric("Planned vouchers", f"{int(row['TOTAL']):,}")

with record_panel:
    st.subheader("Distribution record")
    update_tab, view_tab, clear_tab = st.tabs(["Update entry", "View record", "Clear entry"])

    with update_tab:
        old_status = status_now.strip().lower()
        if old_status in {"received", "success", "successful", "completed", "complete", "delivered", "done"}:
            default_status = "Received"
        elif old_status in {"rejected", "reject", "declined", "unsuccessful"}:
            default_status = "Rejected"
        else:
            default_status = "Pending"

        with st.form("update_form"):
            outcome_column, recipient_column = st.columns(2, gap="large")
            with outcome_column:
                st.markdown("**Distribution details**")
                status = st.selectbox(
                    "Outcome",
                    ["Pending", "Received", "Rejected"],
                    index=["Pending", "Received", "Rejected"].index(default_status),
                    help="Choose Received after handover, Rejected if the school declined, or Pending if no result is recorded.",
                )
                qty = st.number_input(
                    "Voucher quantity delivered",
                    min_value=0,
                    value=int(row["QTY GIVEN"]),
                    step=1,
                    help="Enter the number of vouchers handed to the school.",
                )
                reason = st.text_input(
                    "Reason for rejection (if applicable)",
                    value=str(row.get("REJECTION REASON", "") or ""),
                    placeholder="Only required if the outcome is Rejected",
                )
            with recipient_column:
                st.markdown("**Receiving contact**")
                pic = st.text_input(
                    "Name of person receiving vouchers",
                    value=str(row.get("STAFF NAME", "") or ""),
                    placeholder="e.g. School administrator",
                )
                phone = st.text_input(
                    "School contact number",
                    value=str(row.get("CONTACT NUMBER", "") or ""),
                    placeholder="e.g. 012-345 6789",
                )
                email = st.text_input(
                    "School email address",
                    value=str(row.get("EMAIL ADDRESS", "") or ""),
                    placeholder="e.g. office@school.edu.my",
                )
            save = st.form_submit_button("Save record", type="primary", use_container_width=True)

        if save:
            errors = []
            if status == "Received":
                if int(qty) <= 0: errors.append("Enter the number of vouchers delivered.")
                if not pic.strip(): errors.append("Enter the recipient or PIC name.")
                if not phone.strip(): errors.append("Enter a contact number.")
                if not email.strip(): errors.append("Enter an email address.")
                elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()): errors.append("Enter a valid email address.")
            if status == "Rejected" and not reason.strip(): errors.append("Enter the reason for rejection.")
            if errors:
                for error in errors: st.error(error)
            else:
                try:
                    save_school_update(row, status, int(qty), pic.strip(), phone.strip(), email.strip(), reason.strip())
                    st.success(f"Record saved for {row['NAMA SEKOLAH']}.")
                    st.rerun()
                except PermissionError:
                    st.error("The workbook is open or locked. Close it in Excel and try again.")
                except Exception as exc:
                    st.error(f"Unable to save the record: {exc}")

    with view_tab:
        st.markdown(f"**School:** {row['NAMA SEKOLAH']}  \n**Result:** {status_label}  \n**Vouchers delivered:** {int(row['QTY GIVEN']):,}")
        st.markdown(f"**Recipient / PIC:** {row.get('STAFF NAME', '') or '—'}  \n**Contact:** {row.get('CONTACT NUMBER', '') or '—'}  \n**Email:** {row.get('EMAIL ADDRESS', '') or '—'}")
        if row.get("REJECTION REASON", ""):
            st.markdown(f"**Rejection reason:** {row['REJECTION REASON']}")
        if row.get("DATE", ""):
            st.caption(f"Date recorded: {row['DATE']}")

    with clear_tab:
        st.caption("This clears the distribution entry but keeps the school assigned to its route.")
        confirm = st.checkbox("Confirm clearing this entry", key=f"confirm_clear_{row['_EXCEL_ROW']}")
        if st.button("Clear distribution entry", disabled=not confirm):
            try:
                save_school_update(row, "Pending", 0, "", "", "", "")
                st.success("Distribution entry cleared.")
                st.rerun()
            except PermissionError:
                st.error("The workbook is open or locked. Close it in Excel and try again.")
            except Exception as exc:
                st.error(f"Unable to clear the entry: {exc}")

render_footer()
