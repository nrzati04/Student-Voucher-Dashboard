"""Shared floating Ask Data popover used by every dashboard page."""

import json

import numpy as np
import pandas as pd
import streamlit as st


ALLOWED_COLUMNS = {"REGION", "MANAGER", "LEVEL", "AREA", "RESULT"}
METRICS = {
    "schools": "Schools",
    "received": "Received",
    "rejected": "Rejected",
    "pending": "Pending",
    "visited": "Visited",
}
SHARED_VALUE_COLUMNS = ["REGION", "LEVEL", "RESULT"]
MAX_QUESTIONS_PER_SESSION = 30

PRESETS = {
    "How many schools are there in total?": {"metric": ["schools"]},
    "Received, rejected and pending by region": {
        "group_by": ["REGION"],
        "metric": ["schools", "received", "rejected", "pending"],
    },
    "Received, rejected and pending by school level": {
        "group_by": ["LEVEL"],
        "metric": ["schools", "received", "rejected", "pending"],
    },
    "Which managers have the most rejected schools?": {
        "group_by": ["MANAGER"], "metric": ["rejected"], "sort": "desc", "limit": 10,
    },
    "Which managers have the most schools left (pending)?": {
        "group_by": ["MANAGER"], "metric": ["pending"], "sort": "desc", "limit": 10,
    },
    "Which areas have the most pending schools?": {
        "group_by": ["AREA"], "metric": ["pending"], "sort": "desc", "limit": 15,
    },
    "Progress of each manager": {
        "group_by": ["MANAGER"],
        "metric": ["schools", "received", "rejected", "pending"],
        "sort": "desc",
    },
}


def _question_data(routes: pd.DataFrame) -> pd.DataFrame:
    """Keep only non-contact fields used to answer dashboard questions."""
    data = routes[["REGION", "MANAGER", "LEVEL", "AREA"]].copy()
    data["RESULT"] = np.where(
        routes["REJECTED"],
        "Rejected",
        np.where(routes["SUCCESS"], "Received", "Pending"),
    )
    return data


def _run_plan(data: pd.DataFrame, plan: dict) -> tuple[pd.DataFrame, list[str]]:
    filtered = data
    for rule in plan.get("filters") or []:
        column = str(rule.get("column", "")).upper()
        op = str(rule.get("op", "==")).lower()
        value = rule.get("value")
        if column not in ALLOWED_COLUMNS:
            raise ValueError(f"The column '{column}' is not available.")

        values = filtered[column].fillna("").astype(str).str.lower().str.strip()
        if op == "in":
            options = value if isinstance(value, list) else [value]
            mask = values.isin([str(item).lower().strip() for item in options])
        elif op == "==":
            mask = values == str(value).lower().strip()
        elif op == "!=":
            mask = values != str(value).lower().strip()
        elif op == "contains":
            mask = values.str.contains(str(value).lower().strip(), regex=False)
        else:
            raise ValueError(f"Filter type '{op}' is not supported.")
        filtered = filtered[mask]

    metrics = plan.get("metric") or ["schools"]
    metrics = [metrics] if isinstance(metrics, str) else list(metrics)
    metrics = [str(metric).lower() for metric in metrics]
    if not metrics or any(metric not in METRICS for metric in metrics):
        raise ValueError("The requested measure is not available.")

    group_by = [str(column).upper() for column in (plan.get("group_by") or [])]
    if any(column not in ALLOWED_COLUMNS for column in group_by):
        raise ValueError("The requested grouping is not available.")

    work = filtered.assign(
        schools=1,
        received=(filtered["RESULT"] == "Received").astype(int),
        rejected=(filtered["RESULT"] == "Rejected").astype(int),
        pending=(filtered["RESULT"] == "Pending").astype(int),
        visited=(filtered["RESULT"] != "Pending").astype(int),
    )
    if group_by:
        result = work.groupby(group_by, dropna=False)[metrics].sum().reset_index()
        order = str(plan.get("sort", "")).lower()
        if order in {"asc", "desc"}:
            result = result.sort_values(metrics[0], ascending=order == "asc")
        limit = plan.get("limit")
        if isinstance(limit, int) and limit > 0:
            result = result.head(min(limit, 100))
    else:
        result = pd.DataFrame([work[metrics].sum()])

    labels = {**METRICS, "REGION": "Region", "MANAGER": "Manager", "LEVEL": "School level", "AREA": "Area", "RESULT": "Result"}
    return result.rename(columns=labels).reset_index(drop=True), group_by


def _show_compact_answer(data: pd.DataFrame, plan: dict, key: str) -> None:
    try:
        result, group_by = _run_plan(data, plan)
    except (ValueError, TypeError) as exc:
        st.error(str(exc))
        return

    if not group_by:
        columns = st.columns(len(result.columns))
        for column, name in zip(columns, result.columns):
            column.metric(name, f"{int(result[name].iloc[0]):,}")
    elif result.empty:
        st.info("No schools match that question.")
    else:
        st.dataframe(result, use_container_width=True, hide_index=True, key=f"ask_widget_result_{key}")


def _ai_enabled() -> bool:
    try:
        return bool(st.secrets.get("AI_API_KEY"))
    except Exception:
        return False


def _ask_ai(question: str, data: pd.DataFrame) -> dict:
    import anthropic

    known_values = []
    for column in SHARED_VALUE_COLUMNS:
        values = sorted(data[column].dropna().astype(str).unique().tolist())
        known_values.append(f"- {column}: {', '.join(values)}")

    system = f"""Turn the user's question about school voucher distribution into a JSON plan. Return only JSON.
Allowed columns: REGION, MANAGER, LEVEL, AREA, RESULT.
Known values:\n{chr(10).join(known_values)}
Use MANAGER or AREA filters with op 'contains'.
Format: {{"filters": [], "group_by": ["REGION"], "metric": ["pending"], "sort": "desc", "limit": 10}}
Allowed filter ops: ==, !=, in, contains. Allowed metrics: schools, received, rejected, pending, visited.
Leave group_by empty for one total. 'Schools left' means pending. 'Visited' means received plus rejected.
If not answerable, return {{"error": "short reason"}}."""

    client = anthropic.Anthropic(api_key=st.secrets["AI_API_KEY"])
    reply = client.messages.create(
        model=st.secrets.get("AI_MODEL", "claude-sonnet-5"),
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    text = reply.content[0].text
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("I couldn't understand the AI response. Try rewording the question.")
    plan = json.loads(text[start : end + 1])
    if "error" in plan:
        raise ValueError(f"I can't answer that with this data: {plan['error']}")
    return plan


def render_global_ask_data(routes: pd.DataFrame) -> None:
    """Render the fixed chat launcher on every dashboard page."""
    st.markdown(
        """
        <style>
        div[data-testid="stPopover"] {
            position: fixed;
            right: 24px;
            bottom: 24px;
            z-index: 9999;
        }
        div[data-testid="stPopover"] > button {
            width: 54px;
            height: 54px;
            border-radius: 50%;
            background: #C8202F;
            color: white;
            border: 0;
            box-shadow: 0 4px 14px rgba(0,0,0,.24);
            font-size: 22px;
        }
        div[data-testid="stPopover"] > button:hover {
            background: #9A101D;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    data = _question_data(routes)
    with st.popover("💬", help="Ask Data"):
        st.markdown("### Ask Data")
        ready_tab, own_tab = st.tabs(["Ready-made questions", "Ask in your own words"])

        with ready_tab:
            choice = st.selectbox("Choose a question", list(PRESETS), key="global_ask_preset")
            if st.button("Show answer", key="global_ask_preset_button"):
                _show_compact_answer(data, PRESETS[choice], "preset")

        with own_tab:
            if not _ai_enabled():
                st.info(
                    "Your own questions need an approved Anthropic API key in Streamlit secrets. "
                    "Ready-made questions work without a key."
                )
            else:
                question = st.text_input(
                    "Your question",
                    placeholder="For example: How many primary schools are pending?",
                    key="global_ask_question",
                )
                if st.button("Ask", type="primary", key="global_ask_button") and question.strip():
                    count = st.session_state.get("global_ai_question_count", 0)
                    if count >= MAX_QUESTIONS_PER_SESSION:
                        st.warning("Question limit reached for this visit. Reload the page to continue.")
                    else:
                        st.session_state["global_ai_question_count"] = count + 1
                        try:
                            with st.spinner("Working it out..."):
                                plan = _ask_ai(question.strip(), data)
                            _show_compact_answer(data, plan, "own")
                        except Exception as exc:
                            st.error(f"Could not answer that: {exc}")
                st.caption("Check the result against the dashboard before relying on it.")
