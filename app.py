
import math
import streamlit as st
import pandas as pd
import io
import html as html_lib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from supabase import create_client
from smart_body_analysis_v2 import analyze_body


# ============================================================
# STREFA CZASOWA – PREZENTACJA DAT W HISTORII
# Dane w Supabase pozostają zapisane w UTC.
# ============================================================

WARSAW_TZ = ZoneInfo("Europe/Warsaw")


def format_local_datetime(value, date_format):
    """Formatuje znacznik czasu w lokalnej strefie Europe/Warsaw."""
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(WARSAW_TZ).strftime(date_format)
    except (TypeError, ValueError, AttributeError):
        return str(value)




# ============================================================
# BODYLAB | BMI & BODY ANALYTICS
# Regułowa analiza parametrów ciała i historii pomiarów
# Python + Streamlit
# ============================================================


# ============================================================
# 1. KONFIGURACJA APLIKACJI
# ============================================================

st.set_page_config(
    page_title="BODYLAB | BMI Analysis",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)



# ============================================================
# 2. KONFIGURACJA CSS
# ============================================================


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ==========================================================
   BODYLAB TECH ANALYTICS | VISUAL UPDATE – STAGE 1
   CSS only: no changes to calculations, data, or application flow
   ========================================================== */

:root {
    --bl-bg: #081321;
    --bl-sidebar: #0B1728;
    --bl-surface: #111F33;
    --bl-surface-elevated: #172941;
    --bl-cyan: #22D3EE;
    --bl-blue: #3B82F6;
    --bl-text: #F1F5F9;
    --bl-muted: #94A3B8;
    --bl-border: #263B54;
    --bl-shadow: 0 12px 32px rgba(0, 0, 0, .22);
}

/* Global foundation */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background: var(--bl-bg);
    color: var(--bl-text);
}
[data-testid="stAppViewContainer"] {
    background: var(--bl-bg);
}
.block-container {
    max-width: 1440px;
    padding: 2rem 2.5rem 4rem;
}

/* Sticky header: logged-in user and logout remain available while scrolling. */
.st-key-bodylab-sticky-header {
    position: sticky;
    top: 0;
    z-index: 999;
    background: rgba(8, 19, 33, .96);
    border-bottom: 1px solid var(--bl-border);
    padding: .55rem .8rem .25rem;
    margin: -1rem -.8rem 1rem;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}
[data-testid="stHeader"] {
    background: rgba(8, 19, 33, .92);
}
#MainMenu, footer {
    visibility: hidden;
}
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: var(--bl-text);
}
[data-testid="stCaptionContainer"],
.stCaption,
small {
    color: var(--bl-muted) !important;
}
a {
    color: var(--bl-cyan);
}
a:hover {
    color: #67E8F9;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bl-sidebar);
    border-right: 1px solid var(--bl-border);
}
[data-testid="stSidebar"] > div:first-child {
    background: var(--bl-sidebar);
    padding: 1.4rem 1rem;
}
[data-testid="stSidebar"] * {
    color: var(--bl-text);
}
[data-testid="stSidebar"] hr {
    border-color: var(--bl-border);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] .stCaption {
    color: var(--bl-muted) !important;
}
[data-testid="stSidebar"] a {
    color: var(--bl-text) !important;
    text-decoration: none !important;
}
[data-testid="stSidebar"] a:hover {
    color: var(--bl-cyan) !important;
}

/* Brand and navigation */
.brand, .bl-sidebar-brand {
    color: var(--bl-text);
    font-size: 28px;
    font-weight: 900;
    letter-spacing: 1.8px;
}
.brand-accent, .bl-sidebar-brand span {
    color: var(--bl-cyan);
}
.subtitle, .bl-sidebar-caption {
    color: var(--bl-muted);
    font-size: 10px;
    letter-spacing: 1.6px;
}
.bl-nav-title {
    color: #647F9E;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.7px;
}
.bl-nav a {
    display: flex;
    align-items: center;
    gap: 11px;
    padding: 11px 12px;
    margin: 4px 0;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
    background: transparent;
    transition: background .18s ease, color .18s ease;
}
.bl-nav a:hover {
    background: rgba(34, 211, 238, .09);
    color: var(--bl-cyan) !important;
}
.bl-nav .nav-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--bl-cyan);
    display: inline-block;
}
.bl-sidebar-foot {
    color: #647F9E;
    font-size: 10px;
    line-height: 1.6;
}

/* Section hierarchy */
.section-title {
    color: var(--bl-text);
    font-size: 22px;
    font-weight: 800;
    margin: 22px 0 18px;
    letter-spacing: -.4px;
}
hr, [data-testid="stDivider"] {
    border-color: var(--bl-border) !important;
}

/* Hero */
.bl-hero {
    background: linear-gradient(120deg, #10243B 0%, #12334C 72%, #124B5A 130%);
    border: 1px solid rgba(34, 211, 238, .16);
    border-radius: 18px;
    padding: 30px 34px;
    margin: 2px 0 26px;
    box-shadow: var(--bl-shadow);
    position: relative;
    overflow: hidden;
}
.bl-hero:after {
    content: '';
    position: absolute;
    width: 250px;
    height: 250px;
    border: 1px solid rgba(34, 211, 238, .14);
    border-radius: 50%;
    right: -45px;
    top: -110px;
    box-shadow: 0 0 0 28px rgba(34, 211, 238, .025),
                0 0 0 58px rgba(34, 211, 238, .018);
}
.bl-hero-kicker {
    color: var(--bl-cyan);
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 10px;
}
.bl-hero-title {
    color: #FFFFFF;
    font-size: clamp(25px, 3vw, 36px);
    font-weight: 850;
    letter-spacing: -.8px;
    line-height: 1.15;
}
.bl-hero-copy {
    color: #B7C9D9;
    font-size: 13px;
    line-height: 1.7;
    margin-top: 10px;
    max-width: 650px;
}
.bl-hero-tag {
    display: inline-block;
    color: #CFFAFE;
    background: rgba(34, 211, 238, .10);
    border: 1px solid rgba(34, 211, 238, .25);
    padding: 6px 10px;
    border-radius: 30px;
    font-size: 10px;
    letter-spacing: .5px;
    margin-top: 16px;
}

/* Metric and result cards */
.metric-card, .result-card, .tip-card {
    background: var(--bl-surface);
    border: 1px solid var(--bl-border);
    border-radius: 16px;
    padding: 23px;
    min-height: 150px;
    color: var(--bl-text);
    box-shadow: 0 8px 24px rgba(0, 0, 0, .14);
    box-sizing: border-box;
    height: 100%;
    transition: border-color .2s ease, transform .2s ease, box-shadow .2s ease;
}
.metric-card:hover, .result-card:hover, .tip-card:hover {
    border-color: rgba(34, 211, 238, .38);
    box-shadow: var(--bl-shadow);
    transform: translateY(-1px);
}
.metric-label {
    color: var(--bl-muted);
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.25px;
    text-transform: uppercase;
}
.metric-value {
    color: var(--bl-text);
    font-size: 30px;
    font-weight: 850;
    margin-top: 14px;
    letter-spacing: -.7px;
}
.metric-description, .result-description {
    color: var(--bl-muted);
    font-size: 12px;
    margin-top: 10px;
    line-height: 1.7;
}

/* BMI result and scale */
.bmi-number {
    color: var(--bl-cyan);
    font-size: 64px;
    font-weight: 900;
    line-height: 1.15;
    margin-top: 12px;
    letter-spacing: -2px;
}
.category-label {
    font-size: 18px;
    font-weight: 800;
    margin-top: 12px;
}
.bmi-scale {
    width: 100%;
    height: 15px;
    border-radius: 20px;
    position: relative;
    background: linear-gradient(to right,
        #3B82F6 0%, #3B82F6 14%,
        #10B981 14%, #10B981 40%,
        #F59E0B 40%, #F59E0B 60%,
        #F97316 60%, #F97316 80%,
        #EF4444 80%, #EF4444 100%);
}
.bmi-marker {
    position: absolute;
    top: -8px;
    width: 5px;
    height: 31px;
    background: var(--bl-cyan);
    border: 2px solid var(--bl-bg);
    border-radius: 5px;
    transform: translateX(-50%);
    box-shadow: 0 0 12px rgba(34, 211, 238, .45);
}
.scale-labels {
    position: relative;
    height: 25px;
    margin-top: 12px;
}
.scale-label {
    position: absolute;
    transform: translateX(-50%);
    color: var(--bl-muted);
    font-size: 11px;
}
.scale-label:first-child { transform: none; }
.scale-label:last-child { transform: translateX(-100%); }

/* Smart analysis and tips */
.insight-card {
    background: #10283A;
    border: 1px solid #21445A;
    border-left: 4px solid var(--bl-cyan);
    border-radius: 14px;
    padding: 20px 22px;
    margin-top: 14px;
    color: #D7E7F2;
    line-height: 1.75;
    box-shadow: 0 6px 20px rgba(0, 0, 0, .12);
}
.insight-heading, .tip-heading {
    color: var(--bl-cyan);
    font-weight: 800;
    font-size: 15px;
    margin-bottom: 10px;
}
.tip-card {
    font-size: 13px;
    line-height: 1.7;
}

/* Disclaimer and footer */
.disclaimer {
    background: var(--bl-surface-elevated);
    border: 1px solid var(--bl-border);
    border-radius: 14px;
    padding: 21px;
    color: var(--bl-muted);
    font-size: 12px;
    line-height: 1.8;
    margin-top: 24px;
}
.footer {
    text-align: center;
    color: var(--bl-muted);
    font-size: 11px;
    padding: 24px;
}

/* Streamlit forms and controls */
[data-testid="stForm"] {
    background: var(--bl-surface);
    border: 1px solid var(--bl-border);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, .14);
}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"],
[data-testid="stMultiSelect"] div[data-baseweb="select"] {
    background: var(--bl-surface-elevated);
    color: var(--bl-text);
    border-color: var(--bl-border);
    border-radius: 10px;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--bl-cyan);
    box-shadow: 0 0 0 1px var(--bl-cyan);
}
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] p {
    color: var(--bl-text) !important;
}
div.stButton > button,
div.stFormSubmitButton > button,
div.stDownloadButton > button,
.stLinkButton a {
    background: var(--bl-surface-elevated);
    color: var(--bl-text);
    border: 1px solid var(--bl-border);
    border-radius: 10px;
    font-weight: 700;
    min-height: 43px;
    transition: all .18s ease;
}
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button[kind="primary"] {
    background: var(--bl-cyan);
    border-color: var(--bl-cyan);
    color: #06202B;
}
div.stButton > button:hover,
div.stFormSubmitButton > button:hover,
div.stDownloadButton > button:hover,
.stLinkButton a:hover {
    border-color: var(--bl-cyan);
    color: var(--bl-cyan);
}
div.stButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button[kind="primary"]:hover {
    background: #67E8F9;
    color: #06202B;
}

/* Metrics, tables, charts and expanders */
[data-testid="stMetric"] {
    background: var(--bl-surface);
    border: 1px solid var(--bl-border);
    border-radius: 14px;
    padding: 15px 17px;
}
[data-testid="stMetricLabel"] {
    color: var(--bl-muted);
}
[data-testid="stMetricValue"] {
    color: var(--bl-text);
}
[data-testid="stMetricDelta"] {
    color: #075985 !important;
    background: #BAE6FD !important;
    border-radius: 999px;
    padding: 3px 9px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
[data-testid="stMetricDelta"] {
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] p,
[data-testid="stMetricDelta"] span,
[data-testid="stMetricDelta"] div {
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] svg {
    color: #000000 !important;
    fill: none !important;
    stroke: #000000 !important;
    stroke-width: 2.6px !important;
}
[data-testid="stMetricDelta"] svg path,
[data-testid="stMetricDelta"] svg line,
[data-testid="stMetricDelta"] svg polyline,
[data-testid="stMetricDelta"] svg polygon {
    fill: none !important;
    stroke: #000000 !important;
}
[data-testid="stMetricDelta"] p,
[data-testid="stMetricDelta"] span {
    color: #075985 !important;
}
[data-testid="stMetricLabel"] [data-testid="stTooltipIcon"],
[data-testid="stTooltipIcon"] {
    color: #7DD3FC !important;
    opacity: 1 !important;
}
[data-testid="stMetricLabel"] [data-testid="stTooltipIcon"] svg,
[data-testid="stTooltipIcon"] svg {
    color: #7DD3FC !important;
    fill: none !important;
    stroke: #7DD3FC !important;
    opacity: 1 !important;
}
[data-testid="stMetricLabel"] [data-testid="stTooltipIcon"] svg path,
[data-testid="stTooltipIcon"] svg path {
    fill: none !important;
    stroke: #7DD3FC !important;
}
[data-testid="stExpander"] {
    background: var(--bl-surface);
    border: 1px solid var(--bl-border);
    border-radius: 13px;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--bl-border);
    border-radius: 12px;
    overflow: hidden;
}
[data-testid="stAlert"] {
    border-radius: 12px;
    color: #0B1728 !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] div,
[data-testid="stAlert"] label {
    color: #0B1728 !important;
}
[data-testid="stAlert"] svg {
    color: #0B1728 !important;
    fill: none !important;
    stroke: #0B1728 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px;
}
[data-testid="stTabs"] button[role="tab"] {
    color: var(--bl-muted);
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--bl-cyan);
    border-bottom-color: var(--bl-cyan);
}
[id^="bodylab-"] {
    scroll-margin-top: 24px;
}

/* Responsive */
@media (max-width: 900px) {
    .block-container {
        padding: 1.2rem 1rem 3rem;
    }
    .bl-hero {
        padding: 24px 22px;
    }
}
@media (max-width: 768px) {
    .brand { font-size: 29px; }
    .section-title { font-size: 19px; }
    .bmi-number { font-size: 49px; }
    .metric-value { font-size: 25px; }
    .result-card, .metric-card, .tip-card { padding: 18px; }
    .insight-card { padding: 17px; }
    [data-testid="stForm"] { padding: 17px; }
}

/* ==========================================================
   BODYLAB TYPOGRAPHY SYSTEM | SINGLE FONT FAMILY: INTER
   One family throughout; hierarchy remains controlled by
   existing sizes and weights of individual components.
   ========================================================== */
:root {
    --bl-font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                      'Segoe UI', sans-serif;
    --bl-font-regular: 400;
    --bl-font-medium: 500;
    --bl-font-semibold: 600;
    --bl-font-bold: 700;
    --bl-font-extrabold: 800;
    --bl-font-black: 900;
}

/* Apply Inter consistently without flattening the hierarchy. */
html,
body,
.stApp,
.stApp *,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] *,
[data-testid="stSidebar"],
[data-testid="stSidebar"] *,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] *,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
[data-testid="stMetric"],
[data-testid="stMetric"] *,
[data-testid="stForm"],
[data-testid="stForm"] *,
[data-baseweb],
[data-baseweb] *,
button,
input,
textarea,
select {
    font-family: var(--bl-font-family) !important;
    font-synthesis: none;
}

/* Keep semantic text weights predictable across Streamlit widgets. */
body,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stCaptionContainer"],
.stCaption,
small,
input,
textarea,
select {
    font-weight: var(--bl-font-regular);
}

button,
.stButton button,
.stFormSubmitButton button,
.stDownloadButton button,
.stLinkButton a {
    font-weight: var(--bl-font-semibold) !important;
}

/* Native headings keep their individual size; only standardize weight. */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--bl-font-family) !important;
    font-synthesis: none;
}

/* Preserve Streamlit's icon fonts: global Inter rules must not turn
   Material Symbols ligatures (e.g. expander arrows) into visible text. */
.material-symbols-rounded,
.material-symbols-outlined,
.material-symbols-sharp,
.material-icons,
.material-icons-outlined,
.material-icons-round,
.material-icons-sharp,
.material-icons-two-tone,
span[class*="material-symbols"],
span[class*="material-icons"] {
    font-family: "Material Symbols Rounded", "Material Symbols Outlined",
                 "Material Icons", sans-serif !important;
    font-weight:  normal !important;
    font-style: normal !important;
    font-feature-settings: "liga" !important;
    -webkit-font-feature-settings: "liga" !important;
}

/* Streamlit renders Material Symbols through this test-id in several
   widget versions. Restore the icon font specifically for these nodes. */
[data-testid="stIconMaterial"],
[data-testid="stExpander"] [data-testid="stIconMaterial"],
[data-testid="stExpander"] summary [data-testid="stIconMaterial"],
[data-testid="stExpander"] button [data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded" !important;
    font-weight: 400 !important;
    font-style: normal !important;
    font-size: 1.25rem !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    font-feature-settings: "liga" 1 !important;
    -webkit-font-feature-settings: "liga" !important;
    font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24 !important;
}

</style>
""", unsafe_allow_html=True)



# ============================================================
# 3. FUNKCJE POMOCNICZE
# ============================================================

def render_html(html):
    """Renderuje HTML w aplikacji Streamlit."""
    st.html(html)


def format_number(value, decimals=2):
    """Formatuje liczby z polskim separatorem dziesiętnym."""
    return (
        f"{value:,.{decimals}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# ============================================================
# 4. SILNIK OBLICZENIOWY BMI
# ============================================================

def calculate_bmi(weight, height_cm):
    """Oblicza BMI na podstawie masy i wzrostu."""

    height_m = height_cm / 100
    return weight / (height_m ** 2)


# ============================================================
# 5. KLASYFIKACJA BMI
# ============================================================

def get_bmi_category(bmi):
    """Klasyfikacja BMI dla osób dorosłych."""

    if bmi < 16:
        return {
            "name": "Znaczna niedowaga",
            "color": "#2563EB",
            "description": (
                "BMI znajduje się znacznie poniżej "
                "standardowego zakresu."
            )
        }

    elif bmi < 17:
        return {
            "name": "Umiarkowana niedowaga",
            "color": "#3B82F6",
            "description": (
                "Wynik wskazuje na umiarkowaną niedowagę."
            )
        }

    elif bmi < 18.5:
        return {
            "name": "Łagodna niedowaga",
            "color": "#60A5FA",
            "description": (
                "Wynik wskazuje na niedowagę "
                "według klasyfikacji BMI."
            )
        }

    elif bmi < 25:
        return {
            "name": "Masa prawidłowa",
            "color": "#059669",
            "description": (
                "Wynik mieści się w standardowym "
                "zakresie BMI."
            )
        }

    elif bmi < 30:
        return {
            "name": "Nadwaga",
            "color": "#D97706",
            "description": (
                "Wynik wskazuje na nadwagę "
                "według klasyfikacji BMI."
            )
        }

    elif bmi < 35:
        return {
            "name": "Otyłość I stopnia",
            "color": "#EA580C",
            "description": (
                "Wynik wskazuje na otyłość I stopnia."
            )
        }

    elif bmi < 40:
        return {
            "name": "Otyłość II stopnia",
            "color": "#DC2626",
            "description": (
                "Wynik wskazuje na otyłość II stopnia."
            )
        }

    else:
        return {
            "name": "Otyłość III stopnia",
            "color": "#991B1B",
            "description": (
                "Wynik wskazuje na otyłość III stopnia."
            )
        }


# ============================================================
# 6. ZAKRES PRAWIDŁOWEJ MASY CIAŁA
# ============================================================

def calculate_healthy_weight(height_cm):
    """
    Oblicza zakres masy odpowiadający BMI 18,5–24,9.
    """

    height_m = height_cm / 100

    min_weight = 18.5 * (height_m ** 2)
    max_weight = 24.9 * (height_m ** 2)

    return round(min_weight, 1), round(max_weight, 1)


# ============================================================
# 7. ANALIZA RÓŻNICY MASY CIAŁA
# ============================================================

def calculate_weight_difference(weight, min_weight, max_weight):
    """
    Określa odległość aktualnej masy od zakresu
    odpowiadającego BMI 18,5–24,9.
    """

    if weight < min_weight:
        difference = min_weight - weight

        return {
            "value": difference,
            "direction": "poniżej",
            "description": (
                "Tyle kilogramów dzieli aktualną masę "
                "od dolnej granicy zakresu BMI 18,5–24,9."
            )
        }

    elif weight > max_weight:
        difference = weight - max_weight

        return {
            "value": difference,
            "direction": "powyżej",
            "description": (
                "Tyle kilogramów dzieli aktualną masę "
                "od górnej granicy zakresu BMI 18,5–24,9."
            )
        }

    else:
        return {
            "value": 0,
            "direction": "w zakresie",
            "description": (
                "Aktualna masa mieści się w zakresie "
                "odpowiadającym BMI 18,5–24,9."
            )
        }

# ============================================================
# 8. ANALIZA WHtR
# ============================================================

def calculate_whtr(waist_cm, height_cm):
    """
    Oblicza Waist-to-Height Ratio.
    """

    return waist_cm / height_cm


def get_whtr_category(whtr, bmi):
    """
    Klasyfikacja WHtR dla dorosłych.
    Kategorie stosujemy przy BMI poniżej 35.
    """

    if bmi >= 35:
        return {
            "name": "Ograniczona interpretacja",
            "color": "#64748B",
            "description": (
                "Przy BMI równym lub wyższym niż 35 "
                "nie stosujemy w BODYLAB standardowej "
                "klasyfikacji WHtR. Wskazana jest "
                "indywidualna ocena specjalistyczna."
            )
        }

    elif whtr < 0.4:
        return {
            "name": "Poniżej typowego zakresu",
            "color": "#64748B",
            "description": (
                "Wynik jest poniżej przedziału 0,40–0,49. "
                "Nie oznacza to automatycznie problemu, "
                "ale warto interpretować go w kontekście "
                "pozostałych parametrów."
            )
        }

    elif whtr < 0.5:
        return {
            "name": "Prawidłowy zakres",
            "color": "#059669",
            "description": (
                "Wynik mieści się w zakresie 0,40–0,49, "
                "który nie wskazuje na zwiększone ryzyko "
                "związane z centralnym rozmieszczeniem "
                "tkanki tłuszczowej."
            )
        }

    elif whtr < 0.6:
        return {
            "name": "Podwyższony poziom",
            "color": "#D97706",
            "description": (
                "Wynik wskazuje na zwiększone ryzyko "
                "związane z centralnym rozmieszczeniem "
                "tkanki tłuszczowej."
            )
        }

    else:
        return {
            "name": "Wysoki poziom",
            "color": "#DC2626",
            "description": (
                "Wynik wskazuje na wysoki poziom "
                "centralnej otyłości i dalsze zwiększenie "
                "ryzyka zdrowotnego."
            )
        }


# ============================================================
# 9. ANALIZA WHR – TALIA / BIODRA
# ============================================================

def calculate_whr(waist_cm, hip_cm):
    """Oblicza Waist-to-Hip Ratio na podstawie obwodów w cm."""
    return waist_cm / hip_cm


def get_whr_category(whr, sex):
    """
    Orientacyjna klasyfikacja WHR według progów WHO:
    kobiety >= 0,85; mężczyźni >= 0,90.
    WHO opisuje te wartości jako próg znacznie zwiększonego
    ryzyka powikłań metabolicznych.
    """
    threshold = 0.85 if sex == "Kobieta" else 0.90

    if whr >= threshold:
        return {
            "name": "Wynik powyżej progu WHO",
            "color": "#D97706",
            "threshold": threshold,
            "description": (
                f"Wynik osiąga lub przekracza próg {threshold:.2f} "
                "stosowany dla wybranej płci. Według kryterium WHO "
                "wiąże się to ze znacznie zwiększonym ryzykiem "
                "powikłań metabolicznych. Nie jest to diagnoza."
            )
        }

    return {
        "name": "Poniżej progu WHO",
        "color": "#059669",
        "threshold": threshold,
        "description": (
            f"Wynik znajduje się poniżej progu {threshold:.2f} "
            "stosowanego dla wybranej płci. Sam ten rezultat "
            "nie wyklucza innych czynników ryzyka."
        )
    }


# ============================================================
# 10. ROZSZERZONA INTERPRETACJA BMI
# ============================================================

def get_bmi_insight(bmi):

    if bmi < 16:
        return (
            "Wynik znajduje się w zakresie znacznej niedowagi. "
            "Tak niskie BMI może wiązać się ze zwiększonym "
            "ryzykiem niedożywienia i innych problemów zdrowotnych. "
            "Warto skonsultować wynik z lekarzem, szczególnie "
            "jeśli niska masa ciała pojawiła się niezamierzenie."
        )

    elif bmi < 17:
        return (
            "BMI wskazuje na umiarkowaną niedowagę. Warto "
            "przyjrzeć się zmianom masy ciała, sposobowi "
            "odżywiania i ogólnemu samopoczuciu. Jeśli masa "
            "spada bez wyraźnej przyczyny, wskazana jest "
            "konsultacja ze specjalistą."
        )

    elif bmi < 18.5:
        return (
            "Wynik wskazuje na łagodną niedowagę. Warto ocenić, "
            "czy aktualna masa ciała jest stabilna oraz czy "
            "dieta dostarcza odpowiedniej ilości energii "
            "i składników odżywczych."
        )

    elif bmi < 25:
        return (
            "Wynik mieści się w standardowym zakresie BMI. "
            "To korzystna informacja, ale nie oznacza automatycznie "
            "pełnej oceny zdrowia. Dla szerszego obrazu warto "
            "uwzględnić obwód talii, skład ciała, aktywność "
            "fizyczną i ogólną kondycję organizmu."
        )

    elif bmi < 27:
        return (
            "Wynik znajduje się w dolnej części zakresu nadwagi. "
            "BMI jest wskaźnikiem przesiewowym i nie rozróżnia "
            "tkanki tłuszczowej od mięśniowej. Warto rozszerzyć "
            "analizę o obwód talii oraz skład ciała."
        )

    elif bmi < 30:
        return (
            "Wynik znajduje się w wyższej części zakresu nadwagi. "
            "Warto przyjrzeć się obwodowi talii, poziomowi "
            "aktywności i zmianom masy ciała w czasie. "
            "Sam wskaźnik BMI nie pozwala określić ilości "
            "tkanki tłuszczowej."
        )

    elif bmi < 35:
        return (
            "BMI wskazuje na otyłość I stopnia. Warto potraktować "
            "wynik jako sygnał do szerszej oceny zdrowia, "
            "uwzględniającej między innymi obwód talii, ciśnienie "
            "tętnicze i parametry metaboliczne. Pomocna może być "
            "konsultacja z lekarzem lub dietetykiem."
        )

    elif bmi < 40:
        return (
            "BMI wskazuje na otyłość II stopnia. Warto skonsultować "
            "wynik z lekarzem i przeprowadzić szerszą ocenę "
            "czynników zdrowotnych. BMI samo w sobie nie określa "
            "indywidualnego stanu zdrowia ani składu ciała."
        )

    else:
        return (
            "BMI wskazuje na otyłość III stopnia. Wskazana jest "
            "konsultacja lekarska i indywidualna ocena stanu "
            "zdrowia. Dalsze postępowanie powinno uwzględniać "
            "całość sytuacji zdrowotnej, a nie wyłącznie "
            "wartość wskaźnika BMI."
        )


# ============================================================
# 9. INTELIGENTNE WSKAZÓWKI
# ============================================================

def get_bmi_tips(bmi):

    if bmi < 18.5:
        return [
            {
                "title": "Ocena masy ciała",
                "text": (
                    "Zwróć uwagę na stabilność masy ciała "
                    "i ewentualne niezamierzone spadki."
                )
            },
            {
                "title": "Odżywianie",
                "text": (
                    "Warto ocenić regularność posiłków "
                    "i podaż energii oraz składników odżywczych."
                )
            },
            {
                "title": "Kolejny krok",
                "text": (
                    "Rozważ konsultację ze specjalistą, "
                    "szczególnie jeśli niska masa ciała "
                    "jest nowym zjawiskiem."
                )
            }
        ]

    elif bmi < 25:
        return [
            {
                "title": "Monitoruj obwód talii",
                "text": (
                    "Obwód talii dostarcza dodatkowych "
                    "informacji o rozmieszczeniu tkanki tłuszczowej."
                )
            },
            {
                "title": "Dbaj o aktywność",
                "text": (
                    "Regularny ruch wspiera kondycję, "
                    "sprawność i zdrowie metaboliczne."
                )
            },
            {
                "title": "Rozszerz analizę",
                "text": (
                    "Rozważ analizę składu ciała, jeśli chcesz "
                    "uzyskać pełniejszy obraz swoich parametrów."
                )
            }
        ]

    else:
        return [
            {
                "title": "Sprawdź obwód talii",
                "text": (
                    "To ważny parametr uzupełniający BMI "
                    "w ocenie rozmieszczenia tkanki tłuszczowej."
                )
            },
            {
                "title": "Przeanalizuj aktywność",
                "text": (
                    "Uwzględnij codzienny ruch, trening "
                    "i czas spędzany w pozycji siedzącej."
                )
            },
            {
                "title": "Rozważ szerszą ocenę",
                "text": (
                    "Konsultacja ze specjalistą może pomóc "
                    "dobrać dalsze kroki do indywidualnej sytuacji."
                )
            }
        ]


# ============================================================
# 10. KALKULATOR BMR / TDEE
# ============================================================

def calculate_bmr(weight, height_cm, age, sex):
    """Szacuje BMR wzorem Mifflina-St Jeora dla osób dorosłych."""
    sex_constant = 5 if sex == "Mężczyzna" else -161
    return (10 * weight) + (6.25 * height_cm) - (5 * age) + sex_constant


ACTIVITY_FACTORS = {
    "Siedzący tryb życia (mało ruchu)": 1.20,
    "Lekka aktywność (1–3 dni w tygodniu)": 1.375,
    "Umiarkowana aktywność (3–5 dni w tygodniu)": 1.55,
    "Wysoka aktywność (6–7 dni w tygodniu)": 1.725,
    "Bardzo wysoka aktywność (ciężka praca lub intensywne treningi)": 1.90,
}


def calculate_tdee(bmr, activity_level):
    """Szacuje całkowity wydatek energetyczny na podstawie współczynnika aktywności."""
    return bmr * ACTIVITY_FACTORS[activity_level]


def calculate_calorie_target(tdee, goal):
    """Wyznacza orientacyjny punkt startowy, nie indywidualną dietę."""
    if goal == "Redukcja masy ciała":
        return tdee * 0.85
    if goal == "Zwiększenie masy ciała":
        return tdee * 1.07
    return tdee


# ============================================================
# 10. SUPABASE – POŁĄCZENIE I UWIERZYTELNIANIE
# ============================================================

def get_supabase_client():
    """Tworzy klienta Supabase raz na sesję Streamlit."""
    if "supabase_client" not in st.session_state:
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
        except Exception as exc:
            st.error("Brakuje konfiguracji SUPABASE_URL lub SUPABASE_KEY w Streamlit Secrets.")
            st.stop()
        st.session_state["supabase_client"] = create_client(url, key)
    return st.session_state["supabase_client"]


def render_auth_screen(client):
    """Ekran logowania i rejestracji BODYLAB."""
    st.markdown("""<div class="brand">🧬 BODY<span class="brand-accent">LAB</span></div>
    <div class="subtitle">BODY COMPOSITION & HEALTH ANALYTICS</div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("### Dostęp do BODYLAB")
    st.caption("Zaloguj się, aby korzystać z kalkulatora i swojej prywatnej historii pomiarów.")
    login_tab, signup_tab = st.tabs(["Logowanie", "Utwórz konto"])

    with login_tab:
        with st.form("bodylab_login_form"):
            email = st.text_input("Adres e-mail", key="login_email")
            password = st.text_input("Hasło", type="password", key="login_password")
            submitted = st.form_submit_button("ZALOGUJ SIĘ", type="primary", use_container_width=True)
        if submitted:
            if not email.strip() or not password:
                st.warning("Wpisz adres e-mail i hasło.")
            else:
                try:
                    response = client.auth.sign_in_with_password({"email": email.strip(), "password": password})
                    user = response.user
                    if user is None:
                        st.error("Nie udało się uzyskać danych zalogowanego użytkownika.")
                    else:
                        st.session_state["bodylab_user_id"] = user.id
                        st.session_state["bodylab_user_email"] = user.email
                        st.rerun()
                except Exception:
                    st.error("Logowanie nie powiodło się. Sprawdź adres e-mail, hasło i potwierdzenie adresu e-mail.")

        
        # Odzyskiwanie hasła – obsługiwane na stronie GitHub Pages.
        st.markdown("### Nie pamiętasz hasła?")
        st.caption(
            "Przejdź do strony odzyskiwania hasła, "
            "aby otrzymać link na swoją skrzynkę e-mail."
        )
        st.link_button(
            "ODZYSKAJ HASŁO",
            "https://martinezszymandero.github.io/kalkulator-bmi/password-reset/",
            use_container_width=True
        )
    with signup_tab:
        with st.form("bodylab_signup_form"):
            new_email = st.text_input("Adres e-mail", key="signup_email")
            new_password = st.text_input("Hasło", type="password", key="signup_password")
            confirm_password = st.text_input("Powtórz hasło", type="password", key="signup_confirm_password")
            signup = st.form_submit_button("UTWÓRZ KONTO", type="primary", use_container_width=True)
        if signup:
            if not new_email.strip() or not new_password:
                st.warning("Wpisz adres e-mail i hasło.")
            elif len(new_password) < 8:
                st.warning("Hasło powinno mieć co najmniej 8 znaków.")
            elif new_password != confirm_password:
                st.warning("Podane hasła nie są identyczne.")
            else:
                try:
                    response = client.auth.sign_up({"email": new_email.strip(), "password": new_password})
                    if response.session is None:
                        st.success("Konto zostało utworzone. Sprawdź skrzynkę e-mail i potwierdź adres, a następnie zaloguj się.")
                    else:
                        user = response.user
                        if user is None:
                            st.error("Konto zostało utworzone, ale nie udało się uzyskać danych użytkownika. Zaloguj się ręcznie.")
                        else:
                            st.session_state["bodylab_user_id"] = user.id
                            st.session_state["bodylab_user_email"] = user.email or new_email.strip()
                            st.success("Konto utworzone. Możesz już korzystać z BODYLAB.")
                            st.rerun()
                except Exception as exc:
                    st.error("Supabase odrzucił rejestrację. Szczegóły błędu:")
                    st.code(str(exc))

    st.caption("Twoje pomiary są przypisywane do konta i chronione regułami RLS w bazie danych.")


supabase_client = get_supabase_client()

if "bodylab_user_id" not in st.session_state:
    render_auth_screen(supabase_client)
    st.stop()

# Przyklejony nagłówek użytkownika i wylogowanie
with st.container(key="bodylab-sticky-header"):
    user_col, logout_col = st.columns([5, 1])

    with user_col:
        st.caption(
            f"Zalogowano jako: "
            f"{st.session_state.get('bodylab_user_email', '')}"
        )

    with logout_col:
        if st.button("Wyloguj", use_container_width=True):

            # Próba zakończenia sesji Supabase
            try:
                supabase_client.auth.sign_out()
            except Exception:
                pass

            # Czyszczenie danych użytkownika i wyników analizy
            session_keys_to_clear = [
                "bodylab_user_id",
                "bodylab_user_email",
                "bmi_result",
                "supabase_client",
                "login_email",
                "login_password",
                "signup_email",
                "signup_password",
                "signup_confirm_password",
            ]

            for key in session_keys_to_clear:
                st.session_state.pop(key, None)

            # Powrót do ekranu logowania
            st.rerun()



def fetch_measurement_history(client, user_id):
    """Pobiera wyłącznie pomiary bieżącego użytkownika (RLS jest dodatkową ochroną)."""
    response = (client.table("measurements")
                .select("id, created_at, weight, height, waist, hips, sex, age, bmi, whtr, whr, bmr, tdee, calorie_target, goal, activity_level")
                .eq("user_id", user_id)
                .order("created_at", desc=False)
                .execute())
    return response.data or []


def measurement_to_display(row):
    """Mapuje rekord bazy na polskie etykiety, bez awarii przy brakach danych."""
    def safe_number(value, cast=float):
        if value is None or value == "":
            return None
        try:
            number = cast(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if isinstance(number, float) and not math.isfinite(number):
            return None
        return number

    created = format_local_datetime(
        row.get("created_at", ""),
        "%Y-%m-%d %H:%M:%S %z"
    )

    return {
        "Data zapisu": created,
        "Masa ciała (kg)": safe_number(row.get("weight")),
        "Wzrost (cm)": safe_number(row.get("height")),
        "Obwód talii (cm)": safe_number(row.get("waist")),
        "Obwód bioder (cm)": safe_number(row.get("hips")),
        "BMI": safe_number(row.get("bmi")),
        "WHtR": safe_number(row.get("whtr")),
        "WHR": safe_number(row.get("whr")),
        "Płeć": row.get("sex"),
        "Wiek (lata)": safe_number(row.get("age"), int),
        "BMR (kcal/dzień)": safe_number(row.get("bmr"), int),
        "TDEE (kcal/dzień)": safe_number(row.get("tdee"), int),
        "Cel energetyczny": row.get("goal"),
        "Cel kaloryczny (kcal/dzień)": safe_number(row.get("calorie_target"), int),
        "Poziom aktywności": row.get("activity_level"),
    }


# ============================================================
# 10. NAGŁÓWEK APLIKACJI
# ============================================================

# Logo i stała nawigacja boczna – odnośniki prowadzą do modułów dashboardu.
# Plik bodylab_logo.png musi znajdować się w głównym katalogu repozytorium.
st.sidebar.image("bodylab_logo.png", width=112)
st.sidebar.markdown("""
<div class="bl-sidebar-brand">BODY<span>LAB</span></div>
<div class="bl-sidebar-caption">BODY COMPOSITION & HEALTH ANALYTICS</div>
<div class="bl-nav-title">NAWIGACJA</div>
<div class="bl-nav">
  <a href="#bodylab-measurement"><span class="nav-dot"></span> Nowy pomiar</a>
  <a href="#bodylab-overview"><span class="nav-dot"></span> Przegląd wyników</a>
  <a href="#bodylab-body"><span class="nav-dot"></span> Analiza ciała</a>
  <a href="#bodylab-smart"><span class="nav-dot"></span> Smart Body Analysis</a>
  <a href="#bodylab-lifestyle"><span class="nav-dot"></span> Lifestyle Intelligence</a>
  <a href="#bodylab-rule-engine"><span class="nav-dot"></span> Podsumowanie BODYLAB</a>
  <a href="#bodylab-energy"><span class="nav-dot"></span> Profil energetyczny</a>
  <a href="#bodylab-progress"><span class="nav-dot"></span> Postępy i historia pomiarów</a>
</div>
<div class="bl-sidebar-foot">Twoje dane. Twoje pomiary. Twoja analiza.<br>Wersja testowa · BODYLAB 3.1</div>
""", unsafe_allow_html=True)

render_html("""
<div class="bl-hero">
  <div class="bl-hero-kicker">BODY COMPOSITION & HEALTH ANALYTICS</div>
  <div class="bl-hero-title">Twoje zdrowie. Twoje dane. Twoja analiza.</div>
  <div class="bl-hero-copy">Witaj w swoim centrum BODYLAB. Sprawdź ostatnie pomiary, porównaj zmiany i obserwuj trendy.</div>
  <div class="bl-hero-tag">PERSONAL HEALTH DASHBOARD · BODYLAB 3.1</div>
</div>
<div id="bodylab-overview"></div>
<div class="section-title">Twój dashboard</div>
<p style="color:#748399;margin-top:-10px;margin-bottom:18px;font-size:13px;">Podsumowanie ostatniego zapisanego pomiaru i zmian względem poprzedniego.</p>
""")

# Dashboard startowy: dane pobierane z historii przypisanej do zalogowanego konta.
try:
    dashboard_history = fetch_measurement_history(
        supabase_client, st.session_state["bodylab_user_id"]
    )
except Exception:
    dashboard_history = None
    st.warning("Nie udało się pobrać danych dashboardu. Odśwież aplikację, aby spróbować ponownie.")

if dashboard_history:
    latest_measurement = dashboard_history[-1]
    previous_measurement = dashboard_history[-2] if len(dashboard_history) >= 2 else None

    # Wykorzystujemy zapisany wynik BMI i istniejącą klasyfikację.
    bmi_value = float(latest_measurement["bmi"])
    bmi_category = get_bmi_category(bmi_value)
    bmi_color = bmi_category["color"]
    bmi_category_name = bmi_category["name"]
    bmi_description = bmi_category["description"]

    # Pozycja markera na skali 15–40; ograniczona do jej widocznego zakresu.
    bmi_scale_min = 15.0
    bmi_scale_max = 40.0
    bmi_marker_position = max(
        0.0,
        min(100.0, ((bmi_value - bmi_scale_min) / (bmi_scale_max - bmi_scale_min)) * 100.0)
    )

    render_html(f"""
    <section class="bl-bmi-hero-card" style="
        background:linear-gradient(120deg,#111F33 0%,#132B43 100%);
        border:1px solid #263B54;border-radius:18px;padding:26px 28px;
        margin:8px 0 18px 0;box-shadow:0 12px 30px rgba(0,0,0,.12);">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
        <div style="color:#94A3B8;font-size:12px;font-weight:700;letter-spacing:1.5px;">
          BODY COMPOSITION ANALYTICS
        </div>
        <div style="color:#22D3EE;border:1px solid #23617A;background:rgba(34,211,238,.08);
                    border-radius:999px;padding:6px 11px;font-size:11px;font-weight:700;">
          GŁÓWNY WSKAŹNIK
        </div>
      </div>
      <div style="margin-top:20px;color:#94A3B8;font-size:12px;font-weight:700;letter-spacing:1.2px;">
        TWÓJ WSKAŹNIK BMI
      </div>
      <div style="display:flex;align-items:baseline;gap:15px;flex-wrap:wrap;margin-top:2px;">
        <div style="font-size:clamp(48px,7vw,68px);line-height:1.08;font-weight:800;
                    letter-spacing:-2px;color:#22D3EE;">{bmi_value:.2f}</div>
        <div style="background:{bmi_color};color:#FFFFFF;border-radius:999px;
                    padding:7px 13px;font-size:13px;font-weight:700;">
          {bmi_category_name}
        </div>
      </div>
      <div style="color:#CBD5E1;font-size:14px;line-height:1.55;margin-top:8px;">
        {bmi_description}
      </div>
      <div style="margin-top:25px;">
        <div style="position:relative;height:13px;border-radius:999px;
                    background:linear-gradient(to right,
                    #60A5FA 0%,#60A5FA 14%,
                    #10B981 14%,#10B981 40%,
                    #F59E0B 40%,#F59E0B 60%,
                    #7F1D3A 60%,#7F1D3A 100%);">
          <div style="position:absolute;left:calc({bmi_marker_position:.2f}% - 2px);
                      top:-6px;width:4px;height:25px;background:#FFFFFF;
                      border:1px solid #081321;border-radius:4px;
                      box-shadow:0 0 0 2px rgba(255,255,255,.18);"></div>
        </div>
        <div style="display:grid;grid-template-columns:14fr 26fr 20fr 40fr;
                    gap:0;margin-top:10px;color:#94A3B8;font-size:11px;">
          <span style="text-align:center;">Niedowaga</span>
          <span style="text-align:center;">Masa prawidłowa</span>
          <span style="text-align:center;">Nadwaga</span>
          <span style="text-align:center;">Otyłość</span>
        </div>
        <div style="color:#64748B;font-size:11px;margin-top:8px;">
          Zakres referencyjny BMI dla dorosłych: 18,5–24,9
        </div>
      </div>
    </section>
    """)

    # Wskaźniki uzupełniające – BMI jest już wyróżnione w karcie HERO.
    metric_cols = st.columns(3)
    dashboard_metrics = [
        ("MASA CIAŁA", f"{float(latest_measurement['weight']):.1f} kg", "weight", "kg"),
        ("WHtR", f"{float(latest_measurement['whtr']):.3f}", "whtr", "pkt"),
        ("WHR", f"{float(latest_measurement['whr']):.3f}", "whr", "pkt"),
    ]
    for metric_col, (label, value, field, unit) in zip(metric_cols, dashboard_metrics):
        with metric_col:
            delta = None
            if previous_measurement is not None:
                difference = float(latest_measurement[field]) - float(previous_measurement[field])
                delta = f"{difference:+.2f} {unit}" if field == "weight" else f"{difference:+.3f} {unit}"
            st.metric(
                label,
                value,
                delta=delta,
                help="Zmiana względem poprzedniego zapisanego pomiaru." if delta
                else "Wykonaj kolejny pomiar, aby zobaczyć zmianę."
            )

    created_at = latest_measurement.get("created_at", "")
    created_label = (
        format_local_datetime(created_at, "%d.%m.%Y, %H:%M")
        if created_at else "brak daty"
    )
    st.caption(f"Ostatni zapisany pomiar: {created_label} · Łącznie zapisanych pomiarów: {len(dashboard_history)}")

    if len(dashboard_history) >= 2:
        st.caption(
            "Zmiany względem poprzedniego zapisu widoczne są przy wskaźnikach powyżej. "
            "Pełne wykresy i długoterminowe trendy znajdziesz w historii pomiarów."
        )
    else:
        st.info("Masz już pierwszy zapisany pomiar. Kolejny pozwoli BODYLAB pokazać zmiany i trendy.")

    st.markdown("[Przejdź do nowego pomiaru](#bodylab-measurement) · [Zobacz pełną historię](#bodylab-progress)")
else:
    st.info("Nie masz jeszcze zapisanych pomiarów. Wykonaj pierwszy pomiar, aby uruchomić swój osobisty dashboard BODYLAB.")
    st.caption("Po zapisaniu wyniku zobaczysz tutaj swoje BMI, masę ciała, wskaźniki obwodowe i zmiany w czasie.")



# ============================================================
# 11. FORMULARZ DANYCH
# ============================================================

render_html("""
<div id="bodylab-measurement"></div>
<div class="section-title">Nowy pomiar</div>
<p style="color:#748399;margin-top:-10px;margin-bottom:18px;font-size:13px;">Uzupełnij parametry, aby wygenerować aktualny raport BODYLAB.</p>
""")

with st.form("bmi_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        weight = st.number_input(
            "Masa ciała (kg)",
            min_value=1.0,
            max_value=300.0,
            value=70.0,
            step=0.1,
            format="%.2f"
        )

    with col2:
        height = st.number_input(
            "Wzrost (cm)",
            min_value=100.0,
            max_value=250.0,
            value=175.0,
            step=1.0,
            format="%.2f"
        )

    with col3:
        waist = st.number_input(
            "Obwód talii (cm)",
            min_value=30.0,
            max_value=200.0,
            value=80.0,
            step=1.0,
            format="%.1f"
        )

    col4, col5 = st.columns(2)

    with col4:
        hips = st.number_input(
            "Obwód bioder (cm)",
            min_value=40.0,
            max_value=250.0,
            value=95.0,
            step=1.0,
            format="%.1f",
            help="Zmierz najszersze miejsce bioder i pośladków."
        )

    with col5:
        sex = st.selectbox(
            "Płeć biologiczna – do interpretacji WHR i BMR",
            options=["Kobieta", "Mężczyzna"],
            index=1,
            help="Wybór służy do doboru progu WHR oraz równania Mifflina-St Jeora."
        )

    st.markdown("**Dane do obliczenia zapotrzebowania energetycznego**")
    col6, col7, col8 = st.columns(3)

    with col6:
        age = st.number_input(
            "Wiek (lata)", min_value=18, max_value=100, value=30, step=1,
            help="Moduł BMR/TDEE jest przeznaczony dla osób dorosłych."
        )

    with col7:
        activity_level = st.selectbox(
            "Poziom aktywności",
            options=list(ACTIVITY_FACTORS.keys()),
            index=0,
            help="Wybierz poziom najlepiej opisujący typowy tydzień, a nie pojedynczy trening."
        )

    with col8:
        goal = st.selectbox(
            "Cel energetyczny",
            options=["Utrzymanie masy ciała", "Redukcja masy ciała", "Zwiększenie masy ciała"],
            index=0,
            help="Cel zmienia orientacyjny punkt startowy względem oszacowanego TDEE."
        )

    submitted = st.form_submit_button(
        "ANALIZUJ MOJE BMI",
        use_container_width=True

    )


# ============================================================
# 12. OBLICZENIA I ZAPIS WYNIKÓW
# ============================================================

if submitted:

    bmi = calculate_bmi(weight, height)

    category = get_bmi_category(bmi)

    min_weight, max_weight = calculate_healthy_weight(height)

    insight = get_bmi_insight(bmi)

    weight_difference = calculate_weight_difference(
        weight,
        min_weight,
        max_weight
    )

    tips = get_bmi_tips(bmi)
    whtr = calculate_whtr(waist, height)
    whtr_category = get_whtr_category(whtr, bmi)
    whr = calculate_whr(waist, hips)
    whr_category = get_whr_category(whr, sex)
    

    bmr = calculate_bmr(weight, height, age, sex)
    tdee = calculate_tdee(bmr, activity_level)
    calorie_target = calculate_calorie_target(tdee, goal)

    # Historia jest pobierana tylko dla zalogowanego użytkownika.
    # Jeśli baza chwilowo nie odpowiada, analiza bieżących danych nadal działa.
    try:
        analysis_history = fetch_measurement_history(
            supabase_client,
            st.session_state["bodylab_user_id"]
        )
    except Exception:
        analysis_history = []

    analysis_profile = {
        "bmi": bmi,
        "weight": weight,
        "height": height,
        "waist": waist,
        "hips": hips,
        "sex": sex,
        "age": age,
        "whtr": whtr,
        "whr": whr,
        "bmr": bmr,
        "tdee": tdee,
        "calorie_target": calorie_target,
        "goal": goal,
        "activity_level": activity_level,
        "history": analysis_history,
    }

    smart_analysis = analyze_body(analysis_profile)

    st.session_state.pop("bodylab_saved_result_signature", None)

    st.session_state["bmi_result"] = {
        "bmi": round(bmi, 2),
        "weight": weight,
        "height": height,
        "category": category,
        "min_weight": min_weight,
        "max_weight": max_weight,
        "insight": insight,
        "weight_difference": weight_difference,
        "tips": tips,
        "waist": waist,
        "hips": hips,
        "sex": sex,
        "whtr": round(whtr, 3),
        "whtr_category": whtr_category,
        "whr": round(whr, 3),
        "whr_category": whr_category,
        "smart_analysis": smart_analysis,
        "age": age,
        "activity_level": activity_level,
        "activity_factor": ACTIVITY_FACTORS[activity_level],
        "goal": goal,
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calorie_target": round(calorie_target)
    }


# ============================================================
# 13. DASHBOARD WYNIKÓW
# ============================================================

result = st.session_state.get("bmi_result")

if result:

    bmi = result["bmi"]
    category = result["category"]

    st.divider()

    render_html("""
    <div id="bodylab-report"></div>
    <div class="section-title">Szczegółowy raport ostatniej analizy</div>
    <p style="color:#748399;margin-top:-10px;margin-bottom:18px;font-size:13px;">Najważniejsze wskaźniki z ostatniej analizy.</p>
    """)

    # --------------------------------------------------------
    # TRZY KARTY GŁÓWNE
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        bmi_formatted = format_number(bmi, 2)

        render_html(f"""
        <div class="result-card">

            <div class="metric-label">
                TWÓJ WSKAŹNIK BMI
            </div>

            <div class="bmi-number">
                {bmi_formatted}
            </div>

            <div class="category-label"
                 style="color: {category["color"]};">
                {category["name"]}
            </div>

            <div class="result-description">
                {category["description"]}
            </div>

        </div>
        """)

    with col2:

        min_weight = format_number(result["min_weight"], 1)
        max_weight = format_number(result["max_weight"], 1)

        render_html(f"""
        <div class="metric-card">

            <div class="metric-label">
                PRAWIDŁOWY ZAKRES MASY CIAŁA
            </div>

            <div class="metric-value">
                {min_weight}–{max_weight}
            </div>

            <div class="metric-description">
                kg | Zakres odpowiadający BMI 18,5–24,9
            </div>

        </div>
        """)

    with col3:

        difference = result["weight_difference"]

        if difference["direction"] == "w zakresie":
            difference_value = "0,0 kg"
            difference_label = "Masa w zakresie"
        else:
            difference_value = (
                f"{format_number(difference['value'], 1)} kg"
            )
            difference_label = (
                f"{difference['direction']} zakresu"
            )

        render_html(f"""
        <div class="metric-card">

            <div class="metric-label">
                RÓŻNICA DO ZAKRESU BMI
            </div>

            <div class="metric-value">
                {difference_value}
            </div>

            <div class="metric-description">
                {difference_label}
                <br>
                {difference["description"]}
            </div>

        </div>
        """)

    # ========================================================
    # 14. ANALIZA WHtR
    # ========================================================

    st.divider()

    render_html("""
    <div id="bodylab-body"></div>
    <div class="section-title">Analiza ciała</div>
    <p style="color:#748399;margin-top:-10px;margin-bottom:18px;font-size:13px;">Wskaźniki uzupełniające BMI: relacja talii do wzrostu i bioder.</p>
    <div class="section-title" style="font-size:17px;">Obwód talii – WHtR</div>
    """)

    whtr_category = result["whtr_category"]

    whtr_value = format_number(result["whtr"], 3)

    waist_value = format_number(result["waist"], 1)

    whtr_col1, whtr_col2 = st.columns(2)

    with whtr_col1:

        render_html(f"""
        <div class="result-card">

            <div class="metric-label">
                WAIST-TO-HEIGHT RATIO
            </div>

            <div class="bmi-number">
                {whtr_value}
            </div>

            <div class="category-label"
                 style="color: {whtr_category["color"]};">

                {whtr_category["name"]}

            </div>

            <div class="result-description">
                {whtr_category["description"]}
            </div>

        </div>
        """)

    with whtr_col2:

        render_html(f"""
        <div class="metric-card">

            <div class="metric-label">
                OBWÓD TALII
            </div>

            <div class="metric-value">
                {waist_value} cm
            </div>

            <div class="metric-description">
                Wprowadzony pomiar talii.
                <br>
                Wzrost: {format_number(result["height"], 1)} cm
            </div>

        </div>
        """)

    render_html("""
    <div class="insight-card">

        <div class="insight-heading">
            Jak interpretować WHtR?
        </div>

        WHtR pokazuje relację obwodu talii do wzrostu.
        Pomaga uzupełnić BMI o informację dotyczącą
        rozmieszczenia tkanki tłuszczowej.

        <br><br>

        Orientacyjna zasada dla dorosłych:
        obwód talii powinien być mniejszy niż połowa wzrostu.

    </div>
    """)


    # ========================================================
    # 15. ANALIZA WHR
    # ========================================================

    st.divider()

    render_html("""
    <div class="section-title">
        Analiza proporcji talii do bioder – WHR
    </div>
    """)

    whr_category = result["whr_category"]
    whr_value = format_number(result["whr"], 3)

    whr_col1, whr_col2 = st.columns(2)

    with whr_col1:
        render_html(f"""
        <div class="result-card">
            <div class="metric-label">WAIST-TO-HIP RATIO</div>
            <div class="bmi-number">{whr_value}</div>
            <div class="category-label" style="color: {whr_category["color"]};">
                {whr_category["name"]}
            </div>
            <div class="result-description">
                {whr_category["description"]}
            </div>
        </div>
        """)

    with whr_col2:
        render_html(f"""
        <div class="metric-card">
            <div class="metric-label">WPROWADZONE OBWODY</div>
            <div class="metric-value">{format_number(result["waist"], 1)} / {format_number(result["hips"], 1)} cm</div>
            <div class="metric-description">
                Talia / biodra · Płeć do interpretacji: {result["sex"]}
                <br>Próg WHO: {format_number(whr_category["threshold"], 2)}
            </div>
        </div>
        """)

    render_html("""
    <div class="insight-card">
        <div class="insight-heading">Jak interpretować WHR?</div>
        WHR to stosunek obwodu talii do obwodu bioder. Pomaga ocenić,
        czy obwód talii jest duży w relacji do obwodu bioder.
        <br><br>
        Wartości progowe stosowane w kryteriach WHO to 0,90 dla mężczyzn
        i 0,85 dla kobiet. Osiągnięcie lub przekroczenie progu oznacza
        znacznie zwiększone ryzyko powikłań metabolicznych w klasyfikacji
        populacyjnej, ale nie stanowi rozpoznania choroby.
    </div>
    """)

    # ========================================================
    # 16. WIZUALIZACJA SKALI BMI
    # ========================================================

    render_html("""
    <div class="section-title">
        Pozycja na skali BMI
    </div>
    """)

    marker_position = ((bmi - 15) / 25) * 100
    marker_position = max(0, min(100, marker_position))

    scale_thresholds = [
        (15, "15"),
        (18.5, "18,5"),
        (25, "25"),
        (30, "30"),
        (35, "35"),
        (40, "40+")
    ]

    labels_html = ""

    for value, label in scale_thresholds:

        position = ((value - 15) / 25) * 100

        labels_html += f"""
        <span class="scale-label"
              style="left: {position}%;">
            {label}
        </span>
        """

    render_html(f"""
    <div style="padding: 15px 5px 25px 5px;">

        <div class="bmi-scale">

            <div class="bmi-marker"
                 style="left: {marker_position}%;">

            </div>

        </div>

        <div class="scale-labels">
            {labels_html}
        </div>

    </div>
    """)


    # ========================================================
    # 17. SMART BODY ANALYSIS – RAPORT WIELOWYMIAROWY
    # ========================================================

    smart = result["smart_analysis"]

    render_html("""
    <div id="bodylab-smart"></div>
    <div class="section-title">Smart Body Analysis</div>
    <p style="color:#748399;margin-top:-10px;margin-bottom:18px;font-size:13px;">Regułowa interpretacja dostępnych danych i praktyczne kolejne kroki.</p>
    """)

    summary = smart["overall_summary"]
    render_html(f"""
    <div class="insight-card">
        <div class="insight-heading">{summary["title"]}</div>
        {summary["description"]}
    </div>
    """)

    st.caption(
        "To syntetyczna interpretacja całego zestawu danych. "
        "Szczegółowe wyniki poszczególnych obszarów przedstawiono "
        "w dedykowanych modułach poniżej."
    )

    # --------------------------------------------------------
    # BODY COMPOSITION INTELLIGENCE – INTERPRETACJA WSKAŹNIKÓW
    # --------------------------------------------------------

    body_composition = smart.get("body_composition_intelligence", {})

    def body_composition_caption(value):
        safe_text = html_lib.escape(str(value))
        render_html(
            f'<p style="color:#B0C4D8 !important;font-size:13px;'
            f'line-height:1.55;margin:0.25rem 0 0.65rem 0;">{safe_text}</p>'
        )


    st.divider()
    st.markdown("### Body Composition Intelligence")
    body_composition_caption(
        "Łączna, regułowa interpretacja BMI, WHtR i WHR. "
        "Moduł pokazuje zgodność lub rozbieżności między wskaźnikami; "
        "nie określa bezpośrednio procentowej zawartości tkanki tłuszczowej."
    )

    if not body_composition:
        st.info(
            "Moduł Body Composition Intelligence nie zwrócił danych. "
            "Sprawdź, czy zaktualizowany silnik analizy został wdrożony."
        )
    else:
        consistency_labels = {
            "convergent_signal": "Zgodny sygnał wskaźników obwodowych",
            "no_elevated_central_signal": "Brak podwyższonego sygnału obwodowego",
            "mixed_central_signal": "Niejednoznaczny obraz wskaźników obwodowych",
            "partial_central_assessment": "Częściowa ocena wskaźników obwodowych",
            "not_assessed": "Nie oceniono zgodności wskaźników",
            "insufficient_data": "Niewystarczające dane",
        }

        st.markdown("**Podsumowanie interpretacji**")
        st.markdown(body_composition.get(
            "overall_summary",
            "Brak podsumowania dla dostępnych danych."
        ))
        body_composition_caption(
            "Spójność wyników: "
            + consistency_labels.get(
                body_composition.get("consistency"),
                "Nie określono"
            )
        )

        composition_metrics = body_composition.get("metrics", {})
        metric_labels = [
            ("bmi", "BMI"),
            ("whtr", "WHtR"),
            ("whr", "WHR"),
        ]
        metric_cols = st.columns(3)

        for col, (metric_key, metric_title) in zip(metric_cols, metric_labels):
            metric_data = composition_metrics.get(metric_key, {})
            with col:
                st.markdown(f"**{metric_title}**")
                metric_value = metric_data.get("value")
                if metric_value is None:
                    st.metric(metric_title, "—")
                else:
                    decimals = 2 if metric_key == "bmi" else 3
                    st.metric(metric_title, f"{metric_value:.{decimals}f}")
                body_composition_caption(metric_data.get("label", "Brak danych"))
                st.write(metric_data.get(
                    "interpretation",
                    "Brak interpretacji dla tego wskaźnika."
                ))
                if metric_data.get("status") == "needs_reference":
                    st.info("Do pełnej interpretacji potrzebny jest punkt odniesienia.")

        signals = body_composition.get("signals", [])
        st.markdown("**Najważniejsze sygnały**")
        if signals:
            for signal in signals:
                st.markdown(f"- {signal}")
        else:
            body_composition_caption("Brak dodatkowych sygnałów dla dostępnych danych.")

        composition_limitations = body_composition.get("limitations", [])
        if composition_limitations:
            with st.expander("Ograniczenia Body Composition Intelligence"):
                for limitation in composition_limitations:
                    st.markdown(f"- {limitation}")

        disclaimer = body_composition.get("disclaimer")
        if disclaimer:
            body_composition_caption(disclaimer)

    # --------------------------------------------------------
    # WEIGHT INTELLIGENCE – INTERPRETACJA ZMIAN MASY
    # --------------------------------------------------------

    weight_analysis = smart.get("weight_intelligence", {})

    st.divider()
    st.markdown("### Weight Intelligence")
    st.caption(
        "Analiza kierunku i tempa zmian masy na podstawie zapisanej historii "
        "oraz wybranego celu. Nie wyznacza docelowej masy ani nie ocenia "
        "bezpieczeństwa tempa zmian."
    )

    if weight_analysis.get("status") != "available":
        observations = weight_analysis.get("observations", [])
        if observations:
            for observation in observations:
                st.info(
                    f"**{observation.get('title', 'Informacja')}**\n\n"
                    f"{observation.get('description', '')}"
                )
        else:
            st.info("Za mało danych, aby ocenić kierunek zmian masy ciała.")
    else:
        weight_cols = st.columns(4)
        weight_metrics = [
            ("ZMIANA MASY", f"{weight_analysis.get('change_kg', 0):+.2f} kg"),
            ("ZMIANA PROCENTOWA", f"{weight_analysis.get('change_percent', 0):+.2f}%"),
            ("TEMPO / 30 DNI", f"{weight_analysis.get('change_per_30_days_kg', 0):+.2f} kg"),
            ("OKRES ANALIZY", f"{weight_analysis.get('period_days', 0):.0f} dni"),
        ]
        for col, (label, value) in zip(weight_cols, weight_metrics):
            with col:
                st.metric(label, value)

        st.caption(
            f"Masa początkowa: {weight_analysis.get('start_weight', 0):.2f} kg · "
            f"Ostatnia masa w historii: "
            f"{weight_analysis.get('latest_recorded_weight', 0):.2f} kg · "
            f"Liczba pomiarów: {weight_analysis.get('measurement_count', 0)}"
        )

        alignment_labels = {
            "aligned": "Kierunek zmian jest zgodny z wybranym celem.",
            "opposite": "Kierunek zmian jest przeciwny do wybranego celu.",
            "stable": "Masa pozostała stabilna w analizowanym okresie.",
            "change_observed": "Odnotowano zmianę masy; sam wynik nie przesądza o realizacji celu.",
            "goal_not_recognized": "Nie rozpoznano celu — nie oceniono zgodności kierunku zmian.",
        }
        alignment = weight_analysis.get("goal_alignment")
        if alignment:
            st.markdown(f"**Relacja do celu:** {alignment_labels.get(alignment, 'Brak interpretacji celu.')}")

        for observation in weight_analysis.get("observations", []):
            st.markdown(f"**{observation.get('title', 'Obserwacja')}**  ")
            st.write(observation.get("description", ""))

    weight_limitations = weight_analysis.get("limitations", [])
    if weight_limitations:
        with st.expander("Ograniczenia Weight Intelligence"):
            for limitation in weight_limitations:
                st.markdown(f"- {limitation}")

    # --------------------------------------------------------
    # LIFESTYLE INTELLIGENCE – WSKAZÓWKI EDUKACYJNE
    # --------------------------------------------------------

    lifestyle = smart.get("lifestyle_intelligence", {})

    st.divider()
    render_html("""
    <div id="bodylab-lifestyle"></div>
    <div class="section-title">Lifestyle Intelligence</div>
    <p style="color:#748399;margin-top:-10px;margin-bottom:18px;font-size:13px;">
        Krótkie wskazówki edukacyjne na podstawie wybranego poziomu aktywności i celu.
    </p>
    """)

    if not lifestyle:
        st.info(
            "Moduł Lifestyle Intelligence nie zwrócił danych. "
            "Sprawdź, czy moduł analizy BODYLAB został prawidłowo wdrożony."
        )
    else:
        lifestyle_status = lifestyle.get("status", "insufficient_data")
        st.markdown(
            lifestyle.get(
                "overall_summary",
                "Brak podsumowania dla dostępnych danych."
            )
        )

        if lifestyle_status == "insufficient_data":
            st.info("Za mało danych, aby przygotować wskazówki dotyczące stylu życia.")
        else:
            activity_guidance = lifestyle.get("activity_guidance")
            goal_guidance = lifestyle.get("goal_guidance")
            lifestyle_cols = st.columns(2)

            with lifestyle_cols[0]:
                st.markdown("**Aktywność fizyczna**")
                if activity_guidance:
                    observation = activity_guidance.get("observation")
                    if observation:
                        st.caption(observation)
                    st.write(activity_guidance.get(
                        "recommendation",
                        "Brak dodatkowej wskazówki."
                    ))
                else:
                    st.caption("Brak danych pozwalających przygotować wskazówkę dotyczącą aktywności.")

            with lifestyle_cols[1]:
                st.markdown("**Wybrany cel**")
                if goal_guidance:
                    st.write(goal_guidance.get(
                        "recommendation",
                        "Brak dodatkowej wskazówki."
                    ))
                else:
                    st.caption("Brak danych pozwalających przygotować wskazówkę dotyczącą celu.")

        lifestyle_limitations = lifestyle.get("limitations", [])
        if lifestyle_limitations:
            with st.expander("Ograniczenia Lifestyle Intelligence"):
                for limitation in lifestyle_limitations:
                    st.markdown(f"- {limitation}")

        lifestyle_disclaimer = lifestyle.get("disclaimer")
        if lifestyle_disclaimer:
            st.caption(lifestyle_disclaimer)

    # --------------------------------------------------------
    # BODYLAB – KRÓTKIE PODSUMOWANIE ANALIZY
    # --------------------------------------------------------

    rule_engine = smart.get("rule_engine", {})

    st.divider()
    render_html("""
    <div id="bodylab-rule-engine"></div>
    <div class="section-title">Podsumowanie BODYLAB</div>
    <p style="color:#748399;margin-top:-10px;margin-bottom:18px;font-size:13px;">
        Najważniejsze wnioski wynikające z dostępnych pomiarów i analiz.
    </p>
    """)

    if not rule_engine:
        st.info(
            "Podsumowanie nie jest obecnie dostępne. Sprawdź konfigurację "
            "silnika analizy BODYLAB."
        )
    elif rule_engine.get("status") == "insufficient_data":
        st.info(
            "Potrzeba więcej danych, aby połączyć wyniki w wiarygodne wnioski. "
            "Zapisz kolejne pomiary i uzupełnij dostępne dane profilu."
        )
    else:
        insights = rule_engine.get("insights", [])
        if not insights:
            st.info("Na podstawie dostępnych danych nie ma dodatkowych wniosków.")
        else:
            for index, insight in enumerate(insights[:3]):
                title = insight.get("title", "Wniosek BODYLAB")
                summary_text = insight.get("summary", "")
                recommendation = insight.get("recommendation")

                with st.container(border=True):
                    if index == 0:
                        st.caption("NAJWAŻNIEJSZY WNIOSEK")
                    elif index == 1:
                        st.caption("DODATKOWA OBSERWACJA")
                    else:
                        st.caption("CO WARTO WZIĄĆ POD UWAGĘ")

                    st.markdown(f"**{title}**")
                    if summary_text:
                        st.write(summary_text)
                    if recommendation:
                        st.markdown(f"**Co dalej?** {recommendation}")

    st.caption(
        "Podsumowanie ma charakter informacyjny i edukacyjny. "
        "Nie stanowi diagnozy ani indywidualnej porady medycznej."
    )

    def render_finding_list(title, findings, empty_message):
        st.markdown(f"**{title}**")
        if not findings:
            st.caption(empty_message)
            return
        for finding in findings:
            st.markdown(f"- **{finding['title']}** — {finding['description']}")

    render_finding_list(
        "Mocne strony",
        smart.get("strengths", []),
        "Raport nie wskazał odrębnych mocnych stron na podstawie dostępnych danych."
    )
    render_finding_list(
        "Obszary wymagające uwagi",
        smart.get("attention_areas", []),
        "Brak obszarów wyróżnionych przez reguły analizy. Nie oznacza to pełnej oceny zdrowia."
    )
    render_finding_list(
        "Rekomendowane kolejne kroki",
        smart.get("recommendations", []),
        "Brak dodatkowych rekomendacji dla dostępnego zestawu danych."
    )

    with st.expander("Ograniczenia analizy BODYLAB"):
        for limitation in smart.get("limitations", []):
            st.markdown(f"- {limitation}")

    st.caption(
        "Analiza BODYLAB jest przejrzystą analizą regułową. "
        "Nie jest zwalidowanym kalkulatorem ryzyka, diagnozą ani poradą medyczną."
    )

    # ========================================================
    # 18. PERSONAL ENERGY PROFILE – BMR / TDEE
    # ========================================================

    st.divider()
    render_html("""
    <div id="bodylab-energy"></div>
    <div class="section-title">Profil energetyczny</div>
    <p style="color:#748399;margin-top:-10px;margin-bottom:18px;font-size:13px;">Szacunkowe zapotrzebowanie energetyczne i punkt startowy dla wybranego celu.</p>
    """)

    energy_cols = st.columns(3)
    energy_metrics = [
        ("BMR", result["bmr"], "kcal / dzień", "Szacowana podstawowa przemiana materii"),
        ("TDEE", result["tdee"], "kcal / dzień", "Szacowane całkowite zapotrzebowanie energetyczne"),
        ("CEL KALORYCZNY", result["calorie_target"], "kcal / dzień", result["goal"]),
    ]
    for col, metric in zip(energy_cols, energy_metrics):
        label, value, unit, description = metric
        with col:
            render_html(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value:,} {unit}</div>
                <div class="metric-description">{description}</div>
            </div>
            """.replace(",", " "))

    st.markdown(
        f"**Profil obliczenia:** {result['age']} lat · {result['sex']} · "
        f"{result['activity_level']} (współczynnik {result['activity_factor']:.3f})"
    )

    st.info(
        "BMR oszacowano równaniem Mifflina–St Jeora, a TDEE przez "
        "pomnożenie BMR przez wybrany współczynnik aktywności. "
        "Cel kaloryczny jest orientacyjnym punktem startowym: redukcja "
        "ok. 15% poniżej TDEE, utrzymanie na poziomie TDEE lub zwiększenie "
        "ok. 7% powyżej TDEE. Rzeczywiste zapotrzebowanie może się różnić "
        "i warto je weryfikować na podstawie trendu masy ciała, samopoczucia "
        "oraz poziomu aktywności."
    )

    st.caption(
        "Wynik nie jest indywidualnym zaleceniem dietetycznym. Równanie "
        "ma charakter szacunkowy; szczególnej ostrożności wymagają m.in. "
        "ciąża, karmienie piersią, choroby przewlekłe i zaburzenia odżywiania."
    )

    # ========================================================
    # ZAPIS BIEŻĄCEGO WYNIKU ANALIZY
    # ========================================================

    st.divider()
    st.markdown("### Zapis bieżącego pomiaru")
    st.caption("Raport przedstawia ostatnią wykonaną analizę. Zapisanie wyniku dodaje go do historii konta.")

    result_signature = tuple(result.get(key) for key in (
        "weight", "height", "waist", "hips", "bmi", "whtr", "whr",
        "bmr", "tdee", "calorie_target", "goal", "activity_level"
    ))
    if st.session_state.get("bodylab_saved_result_signature") == result_signature:
        st.success("Ten wynik analizy został już zapisany na Twoim koncie.")
    else:
        st.info("Wynik bieżącej analizy nie jest jeszcze zapisany w historii. Zapisz go, jeśli chcesz zachować go na swoim koncie.")

    if st.button("ZAPISZ AKTUALNY POMIAR", type="primary", use_container_width=True):
        snapshot = {
            "weight": round(float(result["weight"]), 2),
            "height": round(float(result["height"]), 1),
            "waist": round(float(result["waist"]), 1),
            "hips": round(float(result["hips"]), 1),
            "sex": result["sex"],
            "age": int(result["age"]),
            "bmi": round(float(result["bmi"]), 2),
            "whtr": round(float(result["whtr"]), 3),
            "whr": round(float(result["whr"]), 3),
            "bmr": int(result["bmr"]),
            "tdee": int(result["tdee"]),
            "calorie_target": int(result["calorie_target"]),
            "goal": result["goal"],
            "activity_level": result["activity_level"],
        }
        try:
            supabase_client.table("measurements").insert(snapshot).execute()
            st.session_state["bodylab_saved_result_signature"] = result_signature
            st.rerun()
        except Exception:
            st.error("Nie udało się zapisać pomiaru. Sprawdź połączenie i uprawnienia bazy danych.")


    with st.expander("Jak interpretować BMR i TDEE?"):
        st.markdown(
            "**BMR** to szacunkowa ilość energii potrzebna organizmowi "
            "w warunkach spoczynku do podtrzymania podstawowych funkcji.\n\n"
            "**TDEE** uwzględnia także codzienną aktywność i ćwiczenia. "
            "Wynik zależy od trafności wyboru poziomu aktywności.\n\n"
            "**Cel kaloryczny** jest matematycznym punktem startowym, "
            "a nie gwarancją określonego tempa zmiany masy ciała. "
            "Nie należy traktować go jako sztywnego limitu."
        )

    with st.expander("Szczegółowa interpretacja BMI"):
        render_html(f"""
        <div class=\"insight-card\">
            <div class=\"insight-heading\">{category["name"]}</div>
            {result["insight"]}
        </div>
        """)


    # ========================================================
    # 20. INTELIGENTNE WSKAZÓWKI
    # ========================================================

    render_html("""
    <div class="section-title">
        Rekomendowane kolejne kroki
    </div>
    """)

    tip_columns = st.columns(3)

    for index, tip in enumerate(result["tips"]):

        with tip_columns[index]:

            render_html(f"""
            <div class="tip-card">

                <div class="tip-heading">
                    {tip["title"]}
                </div>

                {tip["text"]}

            </div>
            """)


    # ========================================================
    # 21. OGRANICZENIA I POMIARY
    # ========================================================

    with st.expander("Dowiedz się więcej o wskaźniku BMI"):

        st.markdown("""
        ### Czym jest BMI?

        BMI (Body Mass Index) to wskaźnik masy ciała
        obliczany na podstawie masy i wzrostu.

        Jest narzędziem przesiewowym, a nie diagnozą
        medyczną.

        ### Czego BMI nie określa?

        - Procentowej zawartości tkanki tłuszczowej.
        - Ilości masy mięśniowej.
        - Rozmieszczenia tkanki tłuszczowej.
        - Indywidualnego stanu zdrowia.

        ### Ograniczenia wskaźnika

        U osób o dużej masie mięśniowej BMI może
        zawyżać ocenę nadmiernej masy ciała.

        BMI nie powinno być interpretowane w oderwaniu
        od pozostałych parametrów organizmu.

        Klasyfikacja przedstawiona w BODYLAB dotyczy
        osób dorosłych. U dzieci i młodzieży stosuje
        się interpretację uwzględniającą wiek i płeć.

        ### Jak prawidłowo zmierzyć obwód talii?

        1. Znajdź dolną krawędź żeber i górną krawędź bioder.
        2. Zmierz talię w połowie odległości między tymi punktami.
        3. Utrzymuj miarkę poziomo i nie ściskaj skóry.
        4. Odczytaj wynik po naturalnym wydechu.

        WHtR obliczamy, dzieląc obwód talii przez wzrost,
        wyrażone w tych samych jednostkach.

        ### Jak zmierzyć obwód bioder?

        Stań prosto ze złączonymi stopami. Owiń miarkę poziomo
        wokół najszerszej części bioder i pośladków. Miarka powinna
        przylegać do ciała, ale nie uciskać skóry.

        WHR obliczamy, dzieląc obwód talii przez obwód bioder.
        Do obu pomiarów użyj tych samych jednostek.

        ### Ograniczenia WHtR i WHR

        To wskaźniki przesiewowe, a nie diagnoza. Wyniki mogą być
        mniej miarodajne m.in. w ciąży, przy niektórych zmianach
        budowy ciała lub trudnościach z wykonaniem pomiaru.
        Interpretuj je razem z innymi informacjami o zdrowiu.
        """)

    render_html("""
    <div class="disclaimer">

        <b>INFORMACJA EDUKACYJNA</b>

        <br><br>

        BODYLAB jest narzędziem edukacyjnym i analitycznym.

        Wyniki nie stanowią diagnozy medycznej ani
        indywidualnej porady lekarskiej.

        BMI jest jednym z wielu parametrów wykorzystywanych
        do oceny masy ciała i nie stanowi pełnej oceny
        stanu zdrowia.

        Zakres masy ciała prezentowany przez aplikację
        jest obliczeniem matematycznym opartym na BMI,
        a nie indywidualnym celem terapeutycznym.

    </div>
    """)


# ============================================================
# HISTORIA POMIARÓW – DOSTĘPNA NIEZALEŻNIE OD RAPORTU
# ============================================================

render_html("""
<div id="bodylab-progress"></div>
<div class="section-title">Postępy i historia pomiarów</div>
<p style="color:#748399;margin-top:-10px;margin-bottom:18px;font-size:13px;">Twoje zapisane pomiary, trendy i porównanie zmian w czasie.</p>
""")
st.caption("Historia zapisanych pomiarów jest dostępna niezależnie od wykonania nowej analizy.")

try:
    db_history = fetch_measurement_history(supabase_client, st.session_state["bodylab_user_id"])
except Exception:
    db_history = []
    st.error("Nie udało się pobrać historii z Supabase. Spróbuj odświeżyć aplikację.")

if db_history:
    history_df = pd.DataFrame([measurement_to_display(row) for row in db_history])
    st.markdown(f"**Liczba zapisanych pomiarów: {len(db_history)}**")

    if len(db_history) >= 2:
        comparison_specs = [
            ("Zmiana masy", "Masa ciała (kg)", "kg"),
            ("Zmiana obwodu talii", "Obwód talii (cm)", "cm"),
            ("Zmiana BMI", "BMI", "pkt"),
        ]
        comparison_cols = st.columns(3)
        for col, (label, field, unit) in zip(comparison_cols, comparison_specs):
            valid_values = history_df[field].dropna()
            with col:
                if len(valid_values) >= 2:
                    delta = float(valid_values.iloc[-1]) - float(valid_values.iloc[0])
                    st.metric(label, f"{delta:+.2f} {unit}", help="Porównanie pierwszego i ostatniego poprawnego zapisu dla tego wskaźnika.")
                else:
                    st.metric(label, "Brak danych")
        st.caption("Każdy wskaźnik jest porównywany na podstawie własnych poprawnych zapisów. Brakujące lub nieprawidłowe wartości są pomijane.")
        for label, field in [
            ("Trend masy ciała", "Masa ciała (kg)"),
            ("Trend BMI", "BMI"),
            ("Trend obwodu talii", "Obwód talii (cm)"),
        ]:
            chart_data = history_df[["Data zapisu", field]].dropna(subset=[field])
            if not chart_data.empty:
                st.markdown(f"**{label}**")
                st.line_chart(chart_data.set_index("Data zapisu"))
            else:
                st.caption(f"{label}: brak poprawnych danych do wykresu.")
    else:
        st.info("Zapisz co najmniej dwa pomiary, aby zobaczyć wykresy trendu i porównanie zmian.")

    with st.expander("Zobacz tabelę zapisanych pomiarów"):
        st.dataframe(history_df, use_container_width=True, hide_index=True)

    csv_buffer = io.StringIO()
    history_df.to_csv(csv_buffer, index=False, sep=";", decimal=",")
    st.download_button(
        "POBIERZ HISTORIĘ POMIARÓW (CSV)",
        data="\ufeff" + csv_buffer.getvalue(),
        file_name="bodylab_historia_pomiarow.csv",
        mime="text/csv",
        use_container_width=True
    )

    with st.expander("Usuń zapisany pomiar"):
        delete_options = {
            f"{format_local_datetime(row.get('created_at', ''), '%Y-%m-%d %H:%M:%S')} | {row.get('weight')} kg | BMI {row.get('bmi')}": row["id"]
            for row in reversed(db_history)
        }
        selected_label = st.selectbox("Wybierz pomiar do usunięcia", list(delete_options.keys()))
        confirm_delete = st.checkbox("Potwierdzam, że chcę trwale usunąć wybrany pomiar.")
        if st.button("USUŃ WYBRANY POMIAR", disabled=not confirm_delete):
            try:
                (supabase_client.table("measurements")
                 .delete()
                 .eq("id", delete_options[selected_label])
                 .eq("user_id", st.session_state["bodylab_user_id"])
                 .execute())
                st.success("Pomiar został usunięty.")
                st.rerun()
            except Exception:
                st.error("Nie udało się usunąć pomiaru.")
else:
    st.info("Nie masz jeszcze zapisanych pomiarów. Wykonaj nową analizę i zapisz wynik, aby rozpocząć historię.")

st.caption("Historia jest przechowywana w bazie Supabase. Dostęp do rekordów jest dodatkowo ograniczony politykami RLS do zalogowanego użytkownika.")

# ============================================================
# 22. STOPKA
# ============================================================

st.divider()

render_html("""
<div class="footer">

    🧬 BODYLAB © 2026

    <br>

    BODY COMPOSITION & HEALTH ANALYTICS

    <br><br>

    Educational tool – not a medical diagnostic system.

</div>
""")
