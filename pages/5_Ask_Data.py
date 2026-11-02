"""Ask your data: type a question about the voucher routes and get the answer.

Two ways to ask:
  1. Ready-made questions (works straight away, no AI needed).
  2. Your own words (needs an AI API key in Streamlit secrets).

Safety design: the AI never sees your data and never writes code that gets run.
It only returns a small JSON "plan" (which filters, how to group, what to count).
This page checks the plan against a whitelist and does the calculation itself.
Only these columns are ever used: REGION, MANAGER, LEVEL, AREA, RESULT.
Names, phone numbers and emails are never read by this page.
"""

import json

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard_data import page_setup
from styles import render_footer

ALLOWED_COLUMNS = ["REGION", "MANAGER", "LEVEL", "AREA", "RESULT"]
COLUMN_LABELS = {"REGION": "Region", "MANAGER": "Manager", "LEVEL": "School level", "AREA": "Area", "RESULT": "Result"}
METRIC_LABELS = {"schools": "Schools", "received": "Received", "rejected": "Rejected", "pending": "Pending", "visited": "Visited"}
SHARE_VALUES_FOR = ["REGION", "LEVEL", "RESULT"]  # value lists sent to the AI (no names)
MAX_AI_QUESTIONS_PER_SESSION = 30
BRAND_COLORS = ["#C8202F", "#111111", "#9A9A9A", "#D9D9D9", "#7A1018"]

PRESETS = {
    "How many schools are there in total?": {"metric": ["schools"]},
    "Received, rejected and pending by region": {
        "group_by": ["REGION"], "metric": ["schools", "received", "rejected", "pending"]},
    "Received, rejected and pending by school level": {
        "group_by": ["LEVEL"], "metric": ["schools", "received", "rejected", "pending"]},
    "Which managers have the most rejected schools?": {
        "group_by": ["MANAGER"], "metric": ["rejected"], "sort": "desc", "limit": 10},
    "Which managers have the most schools left (pending)?": {
        "group_by": ["MANAGER"], "metric": ["pending"], "sort": "desc", "limit": 10},
    "Which areas have the most pending schools?": {
        "group_by": ["AREA"], "metric": ["pending"], "sort": "desc", "limit": 15},
    "Progress of each manager": {
        "group_by": ["MANAGER"], "metric": ["schools", "received", "rejected", "pending"], "sort": "desc"},
}


# ---------- running a plan (the only thing that touches the data) ----------

def run_plan(df: pd.DataFrame, plan: dict):
    """Apply a whitelisted plan to the data. Returns (result table, group-by columns)."""
    data = df
    for rule in plan.get("filters") or []:
        column = str(rule.get("column", "")).upper()
        op = str(rule.get("op", "==")).lower()
        value = rule.get("value")
        if column not in ALLOWED_COLUMNS:
            raise ValueError(f"The column '{column}' is not available.")
        text = data[column].astype(str).str.lower().str.strip()
        if op == "in":
            options = value if isinstance(value, list) else [value]
            mask = text.isin([str(v).lower().strip() for v in options])
        elif op == "==":
            mask = text == str(value).lower().strip()
        elif op == "!=":
            mask = text != str(value).lower().strip()
        elif op == "contains":
            mask = text.str.contains(str(value).lower().strip(), regex=False)
        else:
            raise ValueError(f"The filter type '{op}' is not supported.")
        data = data[mask]

    metrics = plan.get("metric") or ["schools"]
    metrics = [metrics] if isinstance(metrics, str) else list(metrics)
    metrics = [str(m).lower() for m in metrics]
    for metric in metrics:
        if metric not in METRIC_LABELS:
            raise ValueError(f"I can only count: {', '.join(METRIC_LABELS)}.")

    group_by = [str(c).upper() for c in (plan.get("group_by") or [])]
    for column in group_by:
        if column not in ALLOWED_COLUMNS:
            raise ValueError(f"I can't group by '{column}'.")

    work = data.assign(
        schools=1,
        received=(data["RESULT"] == "Received").astype(int),
        rejected=(data["RESULT"] == "Rejected").astype(int),
        pending=(data["RESULT"] == "Pending").astype(int),
        visited=(data["RESULT"] != "Pending").astype(int),
    )
    if group_by:
        out = work.groupby(group_by, dropna=False)[metrics].sum().reset_index()
        if str(plan.get("sort", "")).lower() in ("asc", "desc"):
            out = out.sort_values(metrics[0], ascending=str(plan["sort"]).lower() == "asc")
        limit = plan.get("limit")
        if isinstance(limit, int) and limit > 0:
            out = out.head(min(limit, 100))
    else:
        out = pd.DataFrame([work[metrics].sum()])
    return out.rename(columns={**METRIC_LABELS, **COLUMN_LABELS}).reset_index(drop=True), group_by


def show_answer(df: pd.DataFrame, plan: dict, key: str):
    try:
        table, group_by = run_plan(df, plan)
    except ValueError as exc:
        st.error(str(exc))
        return
    if not group_by:
        columns = st.columns(len(table.columns))
        for column, name in zip(columns, table.columns):
            column.metric(name, f"{int(table[name].iloc[0]):,}")
    else:
        if table.empty:
            st.info("No schools match that question.")
            return
        st.dataframe(table, use_container_width=True, hide_index=True)
        label = COLUMN_LABELS[group_by[0]]
        value_columns = [c for c in table.columns if c in METRIC_LABELS.values()]
        if len(group_by) == 1 and len(table) <= 30 and value_columns:
            fig = px.bar(table, x=label, y=value_columns, barmode="group",
                         color_discrete_sequence=BRAND_COLORS)
            fig.update_layout(template="plotly_white", height=360, margin=dict(t=20, b=10, l=8, r=8),
                              legend_title_text="", yaxis_title=None, xaxis_title=None)
            st.plotly_chart(fig, use_container_width=True, key=f"ask_chart_{key}")
    with st.expander("How the question was read", expanded=False):
        st.caption("Check this matches what you meant, especially for questions typed in your own words.")
        st.json(plan)


# ---------- the AI part (only this section talks to an AI service) ----------

def ai_enabled() -> bool:
    try:
        return bool(st.secrets.get("AI_API_KEY"))
    except Exception:
        return False


def extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("The AI did not return a usable answer. Try rewording the question.")
    return json.loads(text[start:end + 1])


def build_instructions(df: pd.DataFrame) -> str:
    values = []
    for column in SHARE_VALUES_FOR:
        options = sorted(df[column].dropna().astype(str).unique().tolist())
        values.append(f"- {column}: {', '.join(options)}")
    return f"""You turn a question about a school voucher distribution into a JSON plan. Return ONLY JSON, no other text.

Columns you may use: REGION, MANAGER, LEVEL, AREA, RESULT.
Known values:
{chr(10).join(values)}
MANAGER and AREA have many values: filter them with op "contains" and the words from the question.

JSON format:
{{"filters": [{{"column": "REGION", "op": "==", "value": "KV"}}],
  "group_by": ["MANAGER"],
  "metric": ["rejected"],
  "sort": "desc",
  "limit": 10}}

Rules:
- op must be one of: "==", "!=", "in", "contains".
- metric is a list from: schools, received, rejected, pending, visited ("visited" = received + rejected).
- group_by, sort, limit and filters are optional. Leave group_by empty for a single total.
- Use "schools left" or "still to visit" = pending.
- If the question cannot be answered with these columns, return {{"error": "short reason"}}."""


def ask_ai(question: str, df: pd.DataFrame) -> dict:
    """Swap this function if the department uses a different AI service. Nothing else needs to change."""
    import anthropic

    client = anthropic.Anthropic(api_key=st.secrets["AI_API_KEY"])
    reply = client.messages.create(
        model=st.secrets.get("AI_MODEL", "claude-sonnet-5-5"),
        max_tokens=500,
        system=build_instructions(df),
        messages=[{"role": "user", "content": question}],
    )
    plan = extract_json(reply.content[0].text)
    if "error" in plan:
        raise ValueError(f"I can't answer that with this data: {plan['error']}")
    return plan


# ---------- page ----------

routes = page_setup("Ask Data")
st.markdown("Ask a question about the school visits and get the answer without clicking through filters.")

# Only these five columns are used. Contact details are never read on this page.
df = routes[["REGION", "MANAGER", "LEVEL", "AREA"]].copy()
df["RESULT"] = np.where(routes["REJECTED"], "Rejected", np.where(routes["SUCCESS"], "Received", "Pending"))

ready_tab, ai_tab = st.tabs(["Ready-made questions", "Ask in your own words"])

with ready_tab:
    choice = st.selectbox("Choose a question", list(PRESETS), key="ask_preset")
    show_answer(df, PRESETS[choice], "preset")

with ai_tab:
    if not ai_enabled():
        st.info(
            "This needs an AI key. Ask your supervisor which AI service the department can use, then add "
            "AI_API_KEY to this app's Streamlit secrets. Until then, use the ready-made questions."
        )
    else:
        st.caption("Examples: 'How many primary schools in Northern are still pending?' · "
                   "'Which manager has the most rejected schools in KV?'")
        question = st.text_input("Your question", key="ask_question")
        asked = st.session_state.get("ai_question_count", 0)
        if st.button("Ask", type="primary", key="ask_button") and question.strip():
            if asked >= MAX_AI_QUESTIONS_PER_SESSION:
                st.warning("Question limit reached for this visit. Reload the page to continue.")
            else:
                st.session_state["ai_question_count"] = asked + 1
                try:
                    with st.spinner("Working it out..."):
                        plan = ask_ai(question.strip(), df)
                    show_answer(df, plan, "ai")
                except Exception as exc:
                    st.error(f"Could not answer that: {exc}")
        st.caption("AI can misread a question. Open 'How the question was read' and compare a few answers "
                   "with the dashboard before relying on them.")

render_footer()
