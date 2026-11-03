"""Ask questions about the student voucher routes.

Ready-made questions work without an AI key.
The compact Ask Data popover uses Anthropic when AI_API_KEY is configured.

The AI returns a small JSON plan. This page validates that plan and
calculates the answer locally. It does not send school names, phone
numbers, or email addresses as dataset context to the AI.
"""

import json

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_data import page_setup
from styles import render_footer


ALLOWED_COLUMNS = ["REGION", "MANAGER", "LEVEL", "AREA", "RESULT"]

COLUMN_LABELS = {
    "REGION": "Region",
    "MANAGER": "Manager",
    "LEVEL": "School level",
    "AREA": "Area",
    "RESULT": "Result",
}

METRIC_LABELS = {
    "schools": "Schools",
    "received": "Received",
    "rejected": "Rejected",
    "pending": "Pending",
    "visited": "Visited",
}

# Only these value lists are sent to the AI as context.
SHARE_VALUES_FOR = ["REGION", "LEVEL", "RESULT"]

MAX_AI_QUESTIONS_PER_SESSION = 30
BRAND_COLORS = ["#C8202F", "#111111", "#9A9A9A", "#D9D9D9", "#7A1018"]


PRESETS = {
    "How many schools are there in total?": {
        "metric": ["schools"]
    },
    "Received, rejected and pending by region": {
        "group_by": ["REGION"],
        "metric": ["schools", "received", "rejected", "pending"],
    },
    "Received, rejected and pending by school level": {
        "group_by": ["LEVEL"],
        "metric": ["schools", "received", "rejected", "pending"],
    },
    "Which managers have the most rejected schools?": {
        "group_by": ["MANAGER"],
        "metric": ["rejected"],
        "sort": "desc",
        "limit": 10,
    },
    "Which managers have the most schools left (pending)?": {
        "group_by": ["MANAGER"],
        "metric": ["pending"],
        "sort": "desc",
        "limit": 10,
    },
    "Which areas have the most pending schools?": {
        "group_by": ["AREA"],
        "metric": ["pending"],
        "sort": "desc",
        "limit": 15,
    },
    "Progress of each manager": {
        "group_by": ["MANAGER"],
        "metric": ["schools", "received", "rejected", "pending"],
        "sort": "desc",
    },
}


def run_plan(df: pd.DataFrame, plan: dict):
    """Apply a validated plan to the data."""
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
            mask = text.str.contains(
                str(value).lower().strip(),
                regex=False,
            )
        else:
            raise ValueError(f"The filter type '{op}' is not supported.")

        data = data[mask]

    metrics = plan.get("metric") or ["schools"]
    metrics = [metrics] if isinstance(metrics, str) else list(metrics)
    metrics = [str(metric).lower() for metric in metrics]

    for metric in metrics:
        if metric not in METRIC_LABELS:
            raise ValueError(
                f"I can only count: {', '.join(METRIC_LABELS)}."
            )

    group_by = [
        str(column).upper()
        for column in (plan.get("group_by") or [])
    ]

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
        result = (
            work.groupby(group_by, dropna=False)[metrics]
            .sum()
            .reset_index()
        )

        sort_order = str(plan.get("sort", "")).lower()
        if sort_order in ("asc", "desc"):
            result = result.sort_values(
                metrics[0],
                ascending=(sort_order == "asc"),
            )

        limit = plan.get("limit")
        if isinstance(limit, int) and limit > 0:
            result = result.head(min(limit, 100))
    else:
        result = pd.DataFrame([work[metrics].sum()])

    result = result.rename(
        columns={**METRIC_LABELS, **COLUMN_LABELS}
    ).reset_index(drop=True)

    return result, group_by


def show_answer(df: pd.DataFrame, plan: dict, key: str):
    """Display a result as metric cards or a table and chart."""
    try:
        table, group_by = run_plan(df, plan)
    except ValueError as exc:
        st.error(str(exc))
        return

    if not group_by:
        columns = st.columns(len(table.columns))
        for column, name in zip(columns, table.columns):
            column.metric(name, f"{int(table[name].iloc[0]):,}")
        return

    if table.empty:
        st.info("No schools match that question.")
        return

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )

    label = COLUMN_LABELS[group_by[0]]
    value_columns = [
        name for name in table.columns
        if name in METRIC_LABELS.values()
    ]

    if len(group_by) == 1 and len(table) <= 30 and value_columns:
        fig = px.bar(
            table,
            x=label,
            y=value_columns,
            barmode="group",
            color_discrete_sequence=BRAND_COLORS,
        )
        fig.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(t=20, b=10, l=8, r=8),
            legend_title_text="",
            yaxis_title=None,
            xaxis_title=None,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            key=f"ask_chart_{key}",
        )


def ai_enabled() -> bool:
    """Return whether an AI API key is configured in Streamlit secrets."""
    try:
        return bool(st.secrets.get("AI_API_KEY"))
    except Exception:
        return False


def extract_json(text: str) -> dict:
    """Extract a JSON object from the AI response."""
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end <= start:
        raise ValueError(
            "The AI did not return a usable answer. Try rewording the question."
        )

    return json.loads(text[start : end + 1])


def build_instructions(df: pd.DataFrame) -> str:
    """Describe the allowed query plan and safe context for the AI."""
    values = []

    for column in SHARE_VALUES_FOR:
        options = sorted(
            df[column].dropna().astype(str).unique().tolist()
        )
        values.append(f"- {column}: {', '.join(options)}")

    known_values = "\n".join(values)

    return f"""You turn a question about a school voucher distribution into a JSON plan.
Return ONLY JSON, no other text.

Columns you may use: REGION, MANAGER, LEVEL, AREA, RESULT.
Known values:
{known_values}

MANAGER and AREA have many values: filter them with op "contains"
and words from the question.

JSON format:
{{"filters": [{{"column": "REGION", "op": "==", "value": "KV"}}],
  "group_by": ["MANAGER"],
  "metric": ["rejected"],
  "sort": "desc",
  "limit": 10}}

Rules:
- op must be one of: "==", "!=", "in", "contains".
- metric must use only: schools, received, rejected, pending, visited.
- group_by, sort, limit and filters are optional.
- Leave group_by empty for a single total.
- "schools left" or "still to visit" means pending.
- "visited" means received plus rejected.
- If the question cannot be answered with these columns,
  return {{"error": "short reason"}}."""


def ask_ai(question: str, df: pd.DataFrame) -> dict:
    """Ask Anthropic to translate a question into a query plan."""
    import anthropic

    client = anthropic.Anthropic(
        api_key=st.secrets["AI_API_KEY"]
    )

    model = st.secrets.get("AI_MODEL", "claude-sonnet-5")

    reply = client.messages.create(
        model=model,
        max_tokens=500,
        system=build_instructions(df),
        messages=[{"role": "user", "content": question}],
    )

    plan = extract_json(reply.content[0].text)

    if "error" in plan:
        raise ValueError(
            f"I can't answer that with this data: {plan['error']}"
        )

    return plan


# ---------- page ----------

routes = page_setup("Ask Data")

st.markdown(
    "Ask a question about school visits and get an answer "
    "without clicking through filters."
)

# Only these columns are used on this page.
# Contact details and school names are not included in the AI context.
df = routes[["REGION", "MANAGER", "LEVEL", "AREA"]].copy()
df["RESULT"] = np.where(
    routes["REJECTED"],
    "Rejected",
    np.where(routes["SUCCESS"], "Received", "Pending"),
)

# Ready-made questions continue to work without an AI key.
st.subheader("Ready-made questions")
choice = st.selectbox(
    "Choose a question",
    list(PRESETS),
    key="ask_preset",
)
show_answer(df, PRESETS[choice], "preset")

st.divider()

# Compact chat-style popover for questions in the user's own words.
with st.popover("💬 Ask Data"):
    st.caption("Ask about school visits, results, regions, or managers.")

    if not ai_enabled():
        st.info(
            "This feature needs an Anthropic API key. "
            "Ask your supervisor which AI service the department can use, "
            "then add its key to this app's Streamlit secrets. "
            "Ready-made questions work without a key."
        )
    else:
        st.caption(
            "Examples: “How many primary schools in Northern are still pending?” "
            "or “Which manager has the most rejected schools in KV?”"
        )

        question = st.text_input(
            "Your question",
            key="ask_question",
        )

        if st.button(
            "Ask",
            type="primary",
            key="ask_button",
        ) and question.strip():
            asked = st.session_state.get("ai_question_count", 0)

            if asked >= MAX_AI_QUESTIONS_PER_SESSION:
                st.warning(
                    "Question limit reached for this visit. "
                    "Reload the page to continue."
                )
            else:
                st.session_state["ai_question_count"] = asked + 1

                try:
                    with st.spinner("Working it out..."):
                        plan = ask_ai(question.strip(), df)

                    show_answer(df, plan, "ai")
                except Exception as exc:
                    st.error(f"Could not answer that: {exc}")

        st.caption(
            "AI can misread a question. Compare answers with the dashboard "
            "before relying on them."
        )

render_footer()
