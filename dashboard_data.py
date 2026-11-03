from pathlib import Path
import re
import pandas as pd
import streamlit as st
from openpyxl import load_workbook

WORKBOOK = Path(r"D:\US Pizza\Week 3\Student Voucher Dashboard\Student_Voucher_Route_Plan_2026_v3.xlsx")


def apply_theme():
    st.markdown("""
    <style>
    :root { --pizza-red:#C8202F; --pizza-blue:#153B68; --pizza-yellow:#F6C445; }
    .stApp { background: #fffaf3; }
    [data-testid="stHeader"] { background: rgba(255,250,243,.92); }
    h1, h2, h3 { color: #153B68; }
    [data-testid="stMetric"] { background:#ffffff; border:1px solid #f0dfc6; padding:14px; border-radius:12px; }
    [data-testid="stMetricLabel"] { color:#153B68; }
    [data-testid="stMetricValue"] { color:#C8202F; }
    .stButton button[kind="primary"] { background:#C8202F; border-color:#C8202F; }
    section[data-testid="stSidebar"] { background:#153B68; }
    section[data-testid="stSidebar"] * { color:#fff !important; }
    </style>
    """, unsafe_allow_html=True)


def clean(value) -> str:
    return "" if pd.isna(value) else re.sub(r"\s+", " ", str(value)).strip()


@st.cache_data(ttl=10)
def load_routes(path_text: str) -> pd.DataFrame:
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")
    frames = []
    book = pd.ExcelFile(path, engine="openpyxl")
    for sheet in book.sheet_names:
        raw = pd.read_excel(path, sheet_name=sheet, header=None, engine="openpyxl")
        header_row = None
        for i in range(min(12, len(raw))):
            labels = {clean(x).upper() for x in raw.iloc[i].tolist()}
            if {"STOP", "SUGGESTED DAY", "LEVEL", "NAMA SEKOLAH", "TOTAL"}.issubset(labels):
                header_row = i
                break
        if header_row is None:
            continue
        df = pd.read_excel(path, sheet_name=sheet, header=header_row, engine="openpyxl")
        df.columns = [clean(c).upper() for c in df.columns]
        if not {"LEVEL", "NAMA SEKOLAH", "TOTAL"}.issubset(df.columns):
            continue
        df = df[df["NAMA SEKOLAH"].notna()].copy()
        df["MANAGER"] = sheet.strip()
        df["_SHEET"] = sheet
        df["_HEADER_ROW"] = header_row + 1  # Excel uses 1-based row numbers.
        df["_EXCEL_ROW"] = df.index + header_row + 2
        df["LEVEL"] = df["LEVEL"].map(clean).str.title()
        for col in ("TOTAL", "QTY GIVEN"):
            if col not in df: df[col] = 0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        for col in ("STATUS", "STAFF NAME", "DATE", "CONTACT NUMBER", "EMAIL ADDRESS", "REJECTION REASON"):
            if col not in df: df[col] = ""
            df[col] = df[col].map(clean)
        df["STATUS_KEY"] = df["STATUS"].str.lower().str.replace(r"[^a-z]", "", regex=True)
        df["REJECTED"] = df["STATUS_KEY"].isin({"reject", "rejected", "declined", "unsuccessful"})
        df["SUCCESS"] = df["STATUS_KEY"].isin({"received", "success", "successful", "completed", "complete", "delivered", "done"})
        df["GIVEN"] = (df["QTY GIVEN"] > 0) | df["SUCCESS"]
        frames.append(df)
    if not frames:
        raise ValueError("No route tables found. Expected route columns including LEVEL, NAMA SEKOLAH, and TOTAL.")
    return pd.concat(frames, ignore_index=True)


def page_setup(title: str):
    st.set_page_config(page_title=title, page_icon="🍕", layout="wide")
    apply_theme()
    st.title(title)
    try:
        routes = load_routes(str(WORKBOOK))
        from ask_data_widget import render_global_ask_data
        render_global_ask_data(routes)
        return routes
    except Exception as exc:
        st.error(str(exc))
        st.stop()


def metric_cards(df: pd.DataFrame):
    school_n, given_schools = len(df), int(df["GIVEN"].sum())
    a,b,c,d,e,f = st.columns(6)
    a.metric("Schools in route", f"{school_n:,}")
    b.metric("Received / given", f"{given_schools:,}")
    c.metric("Schools left", f"{max(school_n-given_schools,0):,}")
    d.metric("Rejected", f"{int(df['REJECTED'].sum()):,}")
    e.metric("Successful", f"{int(df['SUCCESS'].sum()):,}")
    f.metric("Vouchers given", f"{int(df['QTY GIVEN'].sum()):,}")
    g,h = st.columns(2)
    planned, issued = int(df["TOTAL"].sum()), int(df["QTY GIVEN"].sum())
    g.metric("Planned voucher allocation*", f"{planned:,}")
    h.metric("Voucher balance*", f"{max(planned-issued,0):,}")
    st.caption("* Planned allocation uses the workbook's TOTAL column; verify that it matches your voucher allocation definition.")


def level_table(df: pd.DataFrame):
    rows=[]
    for level in ("Primary","Secondary"):
        part=df[df["LEVEL"].str.lower()==level.lower()]
        count=len(part); given=int(part["GIVEN"].sum()); total=int(part["TOTAL"].sum()); qty=int(part["QTY GIVEN"].sum())
        rows.append({"School level":level,"Total schools":count,"Received/given":given,"Schools left":max(count-given,0),
            "Rejected":int(part["REJECTED"].sum()),"Successful":int(part["SUCCESS"].sum()),
            "Planned vouchers*":total,"Vouchers given":qty,"Voucher balance*":max(total-qty,0)})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)


def manager_table(df: pd.DataFrame):
    rows=[]
    for manager,part in df.groupby("MANAGER",dropna=False):
        planned,issued=int(part["TOTAL"].sum()),int(part["QTY GIVEN"].sum())
        rows.append({"Manager / PIC":manager,"Primary schools":int((part["LEVEL"].str.lower()=="primary").sum()),
            "Secondary schools":int((part["LEVEL"].str.lower()=="secondary").sum()),"Received/given":int(part["GIVEN"].sum()),
            "Schools left":max(len(part)-int(part["GIVEN"].sum()),0),"Rejected":int(part["REJECTED"].sum()),
            "Successful":int(part["SUCCESS"].sum()),"Planned vouchers*":planned,"Vouchers given":issued,
            "Voucher balance*":max(planned-issued,0)})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)


def filtered_school_list(df: pd.DataFrame, key: str):
    left,right=st.columns(2)
    status=left.selectbox("Filter by result",["All results","Received","Rejected","Pending"],key=f"status_{key}")
    search=right.text_input("Search school",key=f"search_{key}").strip().lower()
    result=df.copy()
    if status=="Received": result=result[result["SUCCESS"]]
    elif status=="Rejected": result=result[result["REJECTED"]]
    elif status=="Pending": result=result[~result["SUCCESS"] & ~result["REJECTED"]]
    if search: result=result[result["NAMA SEKOLAH"].astype(str).str.lower().str.contains(search,na=False)]
    cols=[c for c in ["MANAGER","LEVEL","NAMA SEKOLAH","QTY GIVEN","STAFF NAME","CONTACT NUMBER","EMAIL ADDRESS","STATUS","REJECTION REASON"] if c in result.columns]
    st.dataframe(result[cols],use_container_width=True,hide_index=True)


def save_school_update(row: pd.Series, status: str, qty: int, pic: str, phone: str, email: str, reason: str):
    path=WORKBOOK
    wb=load_workbook(path)
    ws=wb[row["_SHEET"]]
    header=int(row["_HEADER_ROW"])
    headers={clean(ws.cell(header,c).value).upper():c for c in range(1,ws.max_column+1) if ws.cell(header,c).value is not None}
    values={"QTY GIVEN":qty,"STAFF NAME":pic,"CONTACT NUMBER":phone,"EMAIL ADDRESS":email,"STATUS":status,
            "REJECTION REASON":reason,"DATE":pd.Timestamp.now().strftime("%Y-%m-%d") if status!="Pending" else ""}
    for name,value in values.items():
        col=headers.get(name)
        if col is None:
            col=ws.max_column+1
            ws.cell(header,col).value=name
            headers[name]=col
        ws.cell(int(row["_EXCEL_ROW"]),col).value=value
    wb.save(path)
    load_routes.clear()
