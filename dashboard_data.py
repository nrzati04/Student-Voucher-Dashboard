"""
Data loading + UI helpers for US Pizza Student Voucher Dashboard
"""

from pathlib import Path
import io
import json
import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px
from openpyxl import load_workbook
from styles import apply_theme, render_top_navigation, render_footer

# Excel sits next to this file
WORKBOOK = Path(os.environ.get("WORKBOOK_PATH", str(Path(__file__).parent / "Student_Voucher_Route_Plan_2026_v3.xlsx")))


def _drive_file_id() -> str:
    try:
        return str(st.secrets.get("DRIVE_FILE_ID", "")).strip()
    except Exception:
        return os.environ.get("DRIVE_FILE_ID", "").strip()


def _drive_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    try:
        account_info = dict(st.secrets["gcp_service_account"])
    except Exception:
        account_info = None
    if not account_info:
        raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        if raw:
            account_info = json.loads(raw)
    if not account_info:
        raise RuntimeError("Google Drive credentials are not configured in Streamlit Secrets.")
    credentials = service_account.Credentials.from_service_account_info(
        account_info, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def sync_workbook_from_drive() -> None:
    file_id = _drive_file_id()
    if not file_id:
        return
    from googleapiclient.http import MediaIoBaseDownload
    request = _drive_service().files().get_media(fileId=file_id)
    temp_path = WORKBOOK.with_suffix(".download.tmp")
    WORKBOOK.parent.mkdir(parents=True, exist_ok=True)
    try:
        with io.FileIO(temp_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        temp_path.replace(WORKBOOK)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def sync_workbook_to_drive() -> None:
    file_id = _drive_file_id()
    if not file_id:
        return
    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(
        str(WORKBOOK),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=True,
    )
    _drive_service().files().update(fileId=file_id, media_body=media).execute()


def clean(value) -> str:
    return "" if pd.isna(value) else re.sub(r"\s+", " ", str(value)).strip()


@st.cache_data(show_spinner=False)
def load_routes(path_text: str) -> pd.DataFrame:
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")

    frames = []
    book = pd.ExcelFile(path, engine="openpyxl")

    for sheet in book.sheet_names:
        raw = book.parse(sheet_name=sheet, header=None)
        header_row = None
        for i in range(min(12, len(raw))):
            labels = {clean(x).upper() for x in raw.iloc[i].tolist()}
            if {"STOP", "SUGGESTED DAY", "LEVEL", "NAMA SEKOLAH", "TOTAL"}.issubset(labels):
                header_row = i
                break
        if header_row is None:
            continue

        headers = [clean(c).upper() or f"COLUMN_{j + 1}" for j, c in enumerate(raw.iloc[header_row].tolist())]
        df = raw.iloc[header_row + 1:].copy()
        df.columns = headers
        if not {"LEVEL", "NAMA SEKOLAH", "TOTAL"}.issubset(df.columns):
            continue

        df = df[df["NAMA SEKOLAH"].notna()].copy()
        df["MANAGER"] = sheet.strip()
        df["_SHEET"] = sheet
        df["_HEADER_ROW"] = header_row + 1
        # `raw` keeps its original worksheet row index, so index + 1 is the Excel row.
        df["_EXCEL_ROW"] = df.index + 1
        df["LEVEL"] = df["LEVEL"].map(clean).str.title()

        for col in ("TOTAL", "QTY GIVEN"):
            if col not in df:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        for col in ("STATUS", "STAFF NAME", "DATE", "CONTACT NUMBER", "EMAIL ADDRESS", "REJECTION REASON", "EVENT"):
            if col not in df:
                df[col] = ""
            df[col] = df[col].map(clean)

        df["STATUS_KEY"] = df["STATUS"].str.lower().str.replace(r"[^a-z]", "", regex=True)
        df["REJECTED"] = df["STATUS_KEY"].isin({"reject", "rejected", "declined", "unsuccessful"})
        df["SUCCESS"] = df["STATUS_KEY"].isin({
            "received", "success", "successful", "completed", "complete", "delivered", "done"
        })
        df["GIVEN"] = (df["QTY GIVEN"] > 0) | df["SUCCESS"]
        frames.append(df)

    if not frames:
        raise ValueError("No route tables found. Expected columns: LEVEL, NAMA SEKOLAH, TOTAL.")
    return pd.concat(frames, ignore_index=True)


def page_setup(title: str) -> pd.DataFrame:
    st.set_page_config(
        page_title=f"US Pizza · {title}",
        page_icon="🍕",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    sync_workbook_from_drive()
    load_routes.clear()
    apply_theme()
    render_top_navigation()

    with st.sidebar:
        if st.button("🔄 Refresh data", use_container_width=True):
            load_routes.clear()
            st.rerun()
        st.markdown("---")
        st.caption("Excel updates save back to the workbook.")

    try:
        routes = load_routes(str(WORKBOOK))
    except Exception as exc:
        st.error(f"Could not load workbook: {exc}")
        st.info(f"Expected file at: `{WORKBOOK}`")
        st.stop()

    return routes


def metric_cards(df: pd.DataFrame):
    total_schools = len(df)
    primary = int((df["LEVEL"].str.lower() == "primary").sum())
    secondary = int((df["LEVEL"].str.lower() == "secondary").sum())
    given_schools = int(df["GIVEN"].sum())
    rejected = int(df["REJECTED"].sum())
    left = max(total_schools - given_schools, 0)
    planned = int(df["TOTAL"].sum())
    issued = int(df["QTY GIVEN"].sum())
    balance = max(planned - issued, 0)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total schools", f"{total_schools:,}")
    c2.metric("Primary schools", f"{primary:,}")
    c3.metric("Secondary schools", f"{secondary:,}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Received schools", f"{given_schools:,}")
    c2.metric("Rejected schools", f"{rejected:,}")
    c3.metric("Schools left", f"{left:,}")
    c4.metric("% schools received", f"{(given_schools/total_schools*100) if total_schools else 0:.1f}%")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Planned vouchers*", f"{planned:,}")
    c2.metric("Vouchers given", f"{issued:,}")
    c3.metric("Voucher balance*", f"{balance:,}")
    pct = issued / planned if planned else 0
    c4.metric("% vouchers given", f"{pct*100:.1f}%")


def level_table(df: pd.DataFrame):
    rows = []
    for level in ["Primary", "Secondary"]:
        part = df[df["LEVEL"].str.lower() == level.lower()]
        if part.empty:
            continue
        planned = int(part["TOTAL"].sum())
        issued = int(part["QTY GIVEN"].sum())
        rows.append({
            "Level": level,
            "Schools": len(part),
            "Received schools": int(part["GIVEN"].sum()),
            "Schools left": max(len(part) - int(part["GIVEN"].sum()), 0),
            "Rejected schools": int(part["REJECTED"].sum()),
            "Planned vouchers*": planned,
            "Vouchers given": issued,
            "Voucher balance*": max(planned - issued, 0),
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def manager_table(df: pd.DataFrame):
    rows = []
    for manager, part in df.groupby("MANAGER", dropna=False):
        planned = int(part["TOTAL"].sum())
        issued = int(part["QTY GIVEN"].sum())
        rows.append({
            "Manager / PIC": manager,
            "Primary schools": int((part["LEVEL"].str.lower() == "primary").sum()),
            "Secondary schools": int((part["LEVEL"].str.lower() == "secondary").sum()),
            "Received schools": int(part["GIVEN"].sum()),
            "Schools left": max(len(part) - int(part["GIVEN"].sum()), 0),
            "Rejected schools": int(part["REJECTED"].sum()),
            "Planned vouchers*": planned,
            "Vouchers given": issued,
            "Voucher balance*": max(planned - issued, 0),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def progress_pie(df: pd.DataFrame, title: str, mode: str):
    """Create a labeled donut chart for school results or voucher balance."""
    if mode == "schools":
        received = int(df["SUCCESS"].sum())
        rejected = int(df["REJECTED"].sum())
        pending = max(len(df) - received - rejected, 0)
        labels = ["Received schools", "Rejected schools", "Pending schools"]
        values = [received, rejected, pending]
        colors = {"Received schools": "#C8202F", "Rejected schools": "#111111", "Pending schools": "#D9D9D9"}
    else:
        planned = int(df["TOTAL"].sum())
        issued = int(df["QTY GIVEN"].sum())
        labels = ["Vouchers given", "Voucher balance"]
        values = [min(issued, planned), max(planned - issued, 0)]
        colors = {"Vouchers given": "#C8202F", "Voucher balance": "#D9D9D9"}
    data = pd.DataFrame({"Category": labels, "Count": values})
    fig = px.pie(data, values="Count", names="Category", hole=0.52,
                 color="Category", color_discrete_map=colors)
    fig.update_traces(textposition="inside", textinfo="label+percent",
                      hovertemplate="%{label}: %{value:,}<extra></extra>")
    fig.update_layout(template="plotly_white", title=title,
                      title_font=dict(color="#111111", size=17),
                      margin=dict(t=48, b=10, l=8, r=8),
                      legend=dict(orientation="h", yanchor="bottom", y=-0.15,
                                  xanchor="center", x=0.5),
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#111111"))
    return fig


def filtered_school_list(df: pd.DataFrame, key: str):
    left, right = st.columns(2)
    status = left.selectbox(
        "Filter by result",
        ["All results", "Received", "Rejected", "Pending"],
        key=f"status_{key}",
    )
    search = right.text_input("Search school", key=f"search_{key}").strip().lower()

    result = df.copy()
    if status == "Received":
        result = result[result["SUCCESS"]]
    elif status == "Rejected":
        result = result[result["REJECTED"]]
    elif status == "Pending":
        result = result[~result["SUCCESS"] & ~result["REJECTED"]]

    if search:
        result = result[result["NAMA SEKOLAH"].astype(str).str.lower().str.contains(search, na=False)]

    cols = [
        c for c in [
            "MANAGER", "LEVEL", "NAMA SEKOLAH", "QTY GIVEN", "STAFF NAME",
            "CONTACT NUMBER", "EMAIL ADDRESS", "STATUS", "REJECTION REASON", "EVENT"
        ] if c in result.columns
    ]
    st.dataframe(result[cols], use_container_width=True, hide_index=True)


def save_school_update(row: pd.Series, status: str, qty: int, pic: str, phone: str, email: str, reason: str, event: str = ""):
    """Write one submitted school update into its original manager route row."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    sync_workbook_from_drive()
    path = WORKBOOK
    wb = load_workbook(path)
    ws = wb[row["_SHEET"]]
    header = int(row["_HEADER_ROW"])
    headers = {
        clean(ws.cell(header, c).value).upper(): c
        for c in range(1, ws.max_column + 1)
        if ws.cell(header, c).value is not None
    }
    date_value = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).strftime("%Y-%m-%d") if status != "Pending" else ""
    values = {
        "QTY GIVEN": qty,
        "STAFF NAME": pic,
        "CONTACT NUMBER": phone,
        "EMAIL ADDRESS": email,
        "STATUS": status,
        "REJECTION REASON": reason,
        "EVENT": event,
        "DATE": date_value,
    }
    for name, value in values.items():
        col = headers.get(name)
        if col is None:
            col = ws.max_column + 1
            ws.cell(header, col).value = name
            headers[name] = col
        ws.cell(int(row["_EXCEL_ROW"]), col).value = value

    # Save to a temporary sibling file, then replace the workbook after a complete save.
    temp_path = path.with_name(path.stem + ".dashboard-tmp" + path.suffix)
    try:
        wb.save(temp_path)
        temp_path.replace(path)
        sync_workbook_to_drive()
    finally:
        if temp_path.exists():
            temp_path.unlink()
    load_routes.clear()

