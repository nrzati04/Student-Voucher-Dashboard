"""
US Pizza Malaysia – Dashboard theme
US Pizza-inspired red, white, and black theme
"""

import streamlit as st

# Official US Pizza Malaysia logo (from uspizza.my)
LOGO_URL = "https://uspizza.my/wp-content/uploads/2025/01/USpizza-logo-NEW.png"


def apply_theme():
    st.markdown("""
    <style>
    /* ===== Brand colours ===== */
    :root {
        --pizza-red: #C8202F;
        --pizza-black: #111111;
        --pizza-white: #ffffff;
        --cream: #ffffff;
        --text-dark: #111111;
        --text-muted: #555555;
        --card-bg: #ffffff;
        --border: #e1e1e1;
    }

    /* ===== App background ===== */
    .stApp {
        background: var(--cream) !important;
        color: var(--text-dark) !important;
        min-height: 100vh;
    }

    /* ===== Main content text – force dark readable text ===== */
    .main .block-container,
    .main .block-container p,
    .main .block-container span,
    .main .block-container label,
    .main .block-container div {
        color: var(--text-dark) !important;
    }

    h1, h2, h3, h4 {
        color: var(--pizza-black) !important;
        font-weight: 700 !important;
    }

    /* ===== Sidebar – dark blue, white text ===== */
    section[data-testid="stSidebar"] {
        background: var(--pizza-black) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
        background: rgba(255,255,255,0.15) !important;
        border-radius: 8px;
    }

    /* ===== Metric cards ===== */
    div[data-testid="stMetric"] {
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 7px 11px !important;
        min-height: 78px;
        border-radius: 9px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: var(--pizza-black) !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--pizza-red) !important;
        font-weight: 800 !important;
        font-size: 1.5rem !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: var(--text-muted) !important;
    }

    /* ===== Dataframes ===== */
    .stDataFrame, [data-testid="stDataFrame"] {
        background: white !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }

    /* ===== Buttons ===== */
    .stButton > button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background: var(--pizza-red) !important;
        border-color: var(--pizza-red) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #a91a26 !important;
    }

    /* ===== Inputs / selects in main area ===== */
    .main .stSelectbox label,
    .main .stTextInput label,
    .main .stNumberInput label,
    .main .stDateInput label {
        color: var(--pizza-black) !important;
        font-weight: 600 !important;
    }

    /* ===== Clear, high-contrast form controls ===== */
    .main [data-testid="stWidgetLabel"],
    .main [data-testid="stWidgetLabel"] p,
    .main [data-testid="stWidgetLabel"] *,
    .main .stTextInput label,
    .main .stSelectbox label,
    .main .stNumberInput label,
    .main .stTextArea label {
        color: #111111 !important;
        opacity: 1 !important;
        font-weight: 650 !important;
    }
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    .stTextInput label,
    .stSelectbox label,
    .stNumberInput label {
        color: #111111 !important;
        opacity: 1 !important;
    }
    .main input,
    .main textarea,
    .main [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #20242b !important;
        border-color: #aeb9c7 !important;
        opacity: 1 !important;
    }
    input,
    textarea,
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #20242b !important;
        border-color: #aeb9c7 !important;
    }
    .main [data-baseweb="select"] span,
    .main [data-baseweb="select"] input,
    .main [data-baseweb="select"] svg {
        color: #20242b !important;
        fill: #20242b !important;
    }
    .main input::placeholder,
    .main textarea::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }
    .main [data-testid="stNumberInput"] button {
        background: #f5f5f5 !important;
        color: #111111 !important;
        border-color: #aeb9c7 !important;
    }
    .main [data-testid="stTabs"] button[role="tab"] {
        color: #111111 !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    .main [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #C8202F !important;
    }

    /* ===== Custom header bar ===== */
    .usp-header {
        background: linear-gradient(90deg, #C8202F 0%, #A71926 100%);
        color: #ffffff;
        padding: 14px 24px;
        border-radius: 12px;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.16);
    }
    .usp-header img {
        height: 48px;
        width: auto;
        border-radius: 6px;
        background: #fff;
        padding: 4px;
    }
    .usp-header .brand-text {
        flex: 1;
    }
    .usp-header .brand-text h1 {
        color: #ffffff !important;
        margin: 0 !important;
        font-size: 1.45rem !important;
        font-weight: 800 !important;
        line-height: 1.2;
    }
    .usp-header .brand-text p {
        color: #ffffff !important;
        margin: 2px 0 0 0 !important;
        font-size: 0.85rem !important;
        font-weight: 500;
    }
    .usp-header .badge {
        background: #111111;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        white-space: nowrap;
    }

    /* ===== Footer ===== */
    .usp-footer {
        position: static;
        margin: 2.5rem 0 0;
        padding: 16px 20px;
        width: 100%;
        box-sizing: border-box;
        background: #111111;
        color: #ffffff;
        border-radius: 12px;
        text-align: center;
        font-size: 0.85rem;
    }
    .usp-footer a {
        color: #ffffff !important;
        text-decoration: none;
        font-weight: 600;
    }
    .usp-footer strong {
        color: #ffffff;
    }

    /* ===== Sticky top navigation ===== */
    .st-key-usp_topnav {
        position: sticky;
        top: 0;
        z-index: 999;
        width: 100%;
        box-sizing: border-box;
        background: #ffffff;
        padding: 0.8rem 1.2rem;
        border-bottom: 3px solid #C8202F;
        box-shadow: 0 2px 8px rgba(0,0,0,0.10);
        overflow: visible;
        margin-top: 0;
    }
    .usp-nav-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        min-height: 76px;
        height: 100%;
        margin: 0;
    }
    .usp-nav-brand img {
        display: block;
        width: 96px;
        height: 68px;
        object-fit: contain;
        flex: 0 0 96px;
        border: 0;
        border-radius: 0;
        padding: 0;
        background: transparent;
        box-sizing: border-box;
        box-shadow: none;
    }
    .usp-nav-brand strong {
        display: block;
        color: #111111;
        font-size: 1.05rem;
        line-height: 1.2;
    }
    .usp-nav-brand span {
        display: block;
        color: #555555;
        font-size: 0.75rem;
        line-height: 1.2;
        margin-top: 3px;
    }
    .st-key-usp_topnav a,
    .st-key-usp_topnav [data-testid*="stPageLink"] {
        justify-content: center;
        min-height: 42px;
        padding: 0.35rem 0.45rem;
        border-radius: 7px;
        white-space: nowrap;
        color: #111111 !important;
        opacity: 1 !important;
        font-weight: 600;
    }
    .st-key-usp_topnav a *,
    .st-key-usp_topnav [data-testid*="stPageLink"] * {
        color: #111111 !important;
        opacity: 1 !important;
    }
    .st-key-usp_topnav [aria-current="page"] {
        background: #ffffff !important;
        border-bottom: 3px solid #C8202F !important;
    }
    .st-key-usp_topnav [aria-current="page"],
    .st-key-usp_topnav [aria-current="page"] * {
        color: #C8202F !important;
        opacity: 1 !important;
    }
    .st-key-usp_topnav a:hover,
    .st-key-usp_topnav a:hover * {
        color: #C8202F !important;
        background: #fff5f5 !important;
    }

    /* ===== Hide default Streamlit chrome ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    </style>
    """, unsafe_allow_html=True)


def render_top_navigation():
    """Render the logo and page links together in a sticky top bar."""
    with st.container(key="usp_topnav"):
        brand, links = st.columns([2.2, 5.8], vertical_alignment="center")
        with brand:
            st.markdown(f"""
            <div class="usp-nav-brand">
                <img src="{LOGO_URL}" alt="US Pizza Malaysia logo">
                <div><strong>US Pizza Malaysia</strong><span>Student Voucher Distribution</span></div>
            </div>
            """, unsafe_allow_html=True)
        with links:
            nav = st.columns(5, vertical_alignment="center")
            nav[0].page_link("student_voucher_dashboard.py", label="Overview", icon="🏠")
            nav[1].page_link("pages/1_Primary.py", label="Primary", icon="🏫")
            nav[2].page_link("pages/2_Secondary.py", label="Secondary", icon="📚")
            nav[3].page_link("pages/3_Manager.py", label="Manager", icon="👤")
            nav[4].page_link("pages/4_Update_School.py", label="Update School", icon="✏️")


def render_footer():
    """Bottom footer"""
    st.markdown("""
    <div class="usp-footer">
        <strong>US Pizza Malaysia</strong> · Student Voucher Programme 2026<br>
        Data source: Route Plan workbook · Updates write back to Excel<br>
        Need help? Contact Operations / Area Manager team
    </div>
    """, unsafe_allow_html=True)
