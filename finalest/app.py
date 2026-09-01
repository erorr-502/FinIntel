"""FININTEL — newspaper-style multi-agent financial intelligence dashboard.

This file intentionally keeps the UI in one place so a first-year team can explain it:
1) collect profile + portfolio inputs,
2) load a simulated market snapshot,
3) call engine.run_analysis(),
4) render the structured outputs in different views.
"""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from engine import load_market_data, run_analysis
from performance_log import append_run, load_runs
from profiles import PROFILES
from rag import retrieve


# -----------------------------------------------------------------------------
# APP + STATE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FININTEL — The AI Market Daily",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

ASSET_DIR = Path(__file__).parent / "assets"
WALL_STREET_IMG = ASSET_DIR / "wall-street.jpg"
BULL_IMG = ASSET_DIR / "bull-neon.png"

NAV_ITEMS = [
    "Front Page",
    "Markets",
    "Investigations",
    "Filings",
    "AI Desk",
    "Portfolio",
    "Watchlist",
    "Scenario Lab",
    "Performance",
    "Archive",
    "Settings",
]
NAV_ICONS = {
    "Front Page": "⌂",
    "Markets": "⌁",
    "Investigations": "⌕",
    "Filings": "▤",
    "AI Desk": "✥",
    "Portfolio": "▣",
    "Watchlist": "☆",
    "Scenario Lab": "◌",
    "Performance": "⌁",
    "Archive": "▤",
    "Settings": "⚙",
}
NAV_SUB = {
    "Front Page": "Market Brief",
    "Markets": "Live Overview",
    "Investigations": "AI Deep Dive",
    "Filings": "Regulatory Desk",
    "AI Desk": "Agent Room",
    "Portfolio": "Holdings & Risk",
    "Watchlist": "My Signals",
    "Scenario Lab": "What-If Simulator",
    "Performance": "Analytics",
    "Archive": "Past Insights",
    "Settings": "Preferences",
}

DEFAULTS = {
    "theme_mode": "Light",
    "nav_page": "Front Page",
    "stock": "RELIANCE",
    "user_name": "Juee",
    "risk_profile": "Moderate",
    "new_investment": 25000.0,
    "holding_RELIANCE": 20000.0,
    "holding_TCS": 20000.0,
    "holding_INFY": 20000.0,
    "reaction": "Review data before acting",
    "decision_style": "Research before deciding",
    "missing_feed": False,
    "missing_filing": False,
    "conflicting_signals": False,
    "market_tick": 0,
    "runs": 0,
    "last_result": None,
    "last_refresh": None,
    "watch_RELIANCE": True,
    "watch_TCS": True,
    "watch_INFY": True,
    "search_box": "",
    "search_message": "",
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def go_to(page: str) -> None:
    """Navigation callback used by action buttons."""
    st.session_state.nav_page = page


def handle_search() -> None:
    """Turn the masthead search box into working internal navigation."""
    q = st.session_state.search_box.strip().upper()
    st.session_state.search_message = ""
    if not q:
        return
    exact_stock = next((symbol for symbol in ["RELIANCE", "TCS", "INFY"] if symbol in q), None)
    if exact_stock:
        st.session_state.stock = exact_stock
        st.session_state.search_message = f"Selected {exact_stock}."
        return
    if any(term in q for term in ["FILING", "EARNINGS", "DISCLOSURE"]):
        st.session_state.nav_page = "Filings"
        st.session_state.search_message = "Opened Regulatory Desk."
    elif any(term in q for term in ["RISK", "PORTFOLIO", "CONCENTRATION"]):
        st.session_state.nav_page = "Portfolio"
        st.session_state.search_message = "Opened Portfolio & Risk."
    elif any(term in q for term in ["WHY", "AGENT", "DECISION", "EXPLAIN"]):
        st.session_state.nav_page = "Investigations"
        st.session_state.search_message = "Opened the explainable investigation."
    elif any(term in q for term in ["MARKET", "PRICE", "VOLUME", "SENTIMENT"]):
        st.session_state.nav_page = "Markets"
        st.session_state.search_message = "Opened Markets."
    else:
        st.session_state.search_message = "Try RELIANCE, TCS, INFY, filings, risk, agents, volume or sentiment."


def image_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


# -----------------------------------------------------------------------------
# THEME
# -----------------------------------------------------------------------------
dark = st.session_state.theme_mode == "Dark"
C = {
    "bg": "#050b18" if dark else "#e9e2d3",
    "paper": "#0b1629" if dark else "#f8f2e6",
    "paper2": "#101f38" if dark else "#fffaf0",
    "ink": "#f3f5f8" if dark else "#101724",
    "muted": "#aebcd2" if dark else "#5e625f",
    "line": "rgba(255,255,255,.16)" if dark else "rgba(33,27,20,.22)",
    "softline": "rgba(255,255,255,.09)" if dark else "rgba(33,27,20,.12)",
    "navy": "#051225",
    "accent": "#8e59ff" if dark else "#005ea8",
    "green": "#8be45b" if dark else "#0b7e50",
    "orange": "#ffc04f" if dark else "#b16a00",
    "red": "#ff6673" if dark else "#bb281e",
    "control": "#0e1b31" if dark else "#fffaf0",
    "control2": "#132540" if dark else "#f4ecdc",
    "shadow": "rgba(0,0,0,.45)" if dark else "rgba(64,48,25,.14)",
}

paper_texture = (
    "radial-gradient(circle at 10% 20%,rgba(255,255,255,.025) 0 1px,transparent 1px),"
    "radial-gradient(circle at 75% 62%,rgba(255,255,255,.02) 0 1px,transparent 1px)"
    if dark
    else
    "radial-gradient(circle at 10% 20%,rgba(77,56,28,.055) 0 1px,transparent 1px),"
    "radial-gradient(circle at 75% 62%,rgba(77,56,28,.04) 0 1px,transparent 1px)"
)

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Libre+Franklin:wght@500;600;700;800&family=Playfair+Display:wght@600;700;800;900&display=swap');
:root {{
  --bg:{C['bg']}; --paper:{C['paper']}; --paper2:{C['paper2']}; --ink:{C['ink']};
  --muted:{C['muted']}; --line:{C['line']}; --softline:{C['softline']}; --accent:{C['accent']};
  --green:{C['green']}; --orange:{C['orange']}; --red:{C['red']}; --control:{C['control']};
  --control2:{C['control2']}; --shadow:{C['shadow']};
}}
html,body,[class*="css"]{{font-family:'DM Sans',Arial,sans-serif;}}
.stApp{{background:var(--bg)!important;color:var(--ink)!important;}}
[data-testid="stAppViewContainer"]{{background:var(--bg)!important;color:var(--ink)!important;}}
[data-testid="stMain"]{{background:transparent!important;color:var(--ink)!important;}}
.block-container{{max-width:1510px;padding:1.15rem 1.35rem 2.4rem!important;background:var(--paper)!important;border:1px solid var(--line);box-shadow:0 18px 55px var(--shadow);margin-top:.7rem;margin-bottom:1.5rem;background-image:{paper_texture}!important;background-size:7px 7px,9px 9px!important;}}
header[data-testid="stHeader"]{{background:transparent!important;}}
[data-testid="stToolbar"]{{background:transparent!important;}}
.stDeployButton,[data-testid="stDecoration"]{{display:none!important;}}
/* Keep the navigation rail stable during demos. The open-sidebar collapse button is hidden
   so it cannot be dismissed accidentally; if Streamlit auto-collapses it on a narrow window,
   the restore control is forced to stay visible. */
[data-testid="stSidebarCollapseButton"]{{display:none!important;}}
[data-testid="stSidebarCollapsedControl"]{{
  display:flex!important;visibility:visible!important;opacity:1!important;
  position:fixed!important;left:10px!important;top:10px!important;z-index:999999!important;
}}
[data-testid="stSidebarCollapsedControl"] button{{
  display:flex!important;visibility:visible!important;opacity:1!important;
  width:42px!important;height:42px!important;border-radius:7px!important;
  background:#071a31!important;border:1px solid rgba(255,255,255,.22)!important;
  box-shadow:0 5px 16px rgba(0,0,0,.22)!important;
}}
[data-testid="stSidebarCollapsedControl"] button *{{color:#fff!important;fill:#fff!important;}}


/* SIDEBAR */
[data-testid="stSidebar"]{{background:#051225!important;border-right:1px solid rgba(255,255,255,.12)!important;}}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{{padding-top:.5rem;}}
[data-testid="stSidebar"] *{{color:#f5f7ff!important;}}
.sidebar-logo{{font-family:'Playfair Display',Georgia,serif;font-size:31px;font-weight:900;letter-spacing:1.2px;line-height:1;}}
.sidebar-kicker{{font-size:9px;letter-spacing:2.2px;color:#9cadc7!important;font-weight:800;margin:5px 0 15px;}}
[data-testid="stSidebar"] [role="radiogroup"]{{gap:2px;}}
[data-testid="stSidebar"] [role="radiogroup"] label{{
  border:1px solid transparent!important;border-radius:5px!important;padding:7px 8px!important;margin:0!important;
  transition:.15s ease;background:transparent!important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{{background:rgba(255,255,255,.07)!important;}}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){{
  background:#f5eddd!important;border-color:#dccca8!important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{{color:#0d1829!important;font-weight:900!important;}}
[data-testid="stSidebar"] [role="radiogroup"] [data-baseweb="radio"]>div:first-child{{display:none!important;}}
[data-testid="stSidebar"] [role="radiogroup"] p{{font-size:12px!important;font-weight:800!important;letter-spacing:.15px!important;}}
.sidebar-status{{border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.045);padding:12px;border-radius:6px;margin:15px 0 4px;}}
.sidebar-status b{{color:#8be45b!important;font-size:10px;letter-spacing:1.1px;}}
.sidebar-status div{{font-size:10px;color:#9cadc7!important;margin-top:4px;}}

/* MAIN PAPER */
.paper{{
  background:var(--paper);color:var(--ink);border:1px solid var(--line);box-shadow:0 18px 55px var(--shadow);
  position:relative;overflow:hidden;padding:19px 21px 22px;
  background-image:{paper_texture};background-size:7px 7px,9px 9px;
}}
.paper:before{{content:'FININTEL · WALL STREET · MARKET INTELLIGENCE';position:absolute;left:0;right:0;top:0;
  font-family:Georgia,serif;font-size:9px;letter-spacing:8px;color:var(--ink);opacity:.022;white-space:nowrap;overflow:hidden;}}
.paper > *{{position:relative;z-index:1;}}
.masthead{{display:grid;grid-template-columns:1.15fr 1fr .72fr;gap:20px;align-items:center;border-bottom:3px double var(--ink);padding:4px 3px 10px;}}
.brand{{font-family:'Playfair Display',Georgia,serif;font-size:49px;font-weight:900;letter-spacing:1.5px;line-height:.88;}}
.brand-sub{{font-family:'Libre Franklin',Arial,sans-serif;font-size:11px;font-weight:900;letter-spacing:2px;margin-top:8px;}}
.date-line{{font-family:Georgia,serif;font-size:10px;font-weight:700;letter-spacing:.45px;margin-top:5px;}}
.market-open{{font-size:10px;font-weight:900;letter-spacing:.8px;margin-top:10px;}}
.live-dot{{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--red);margin-right:5px;box-shadow:0 0 0 3px color-mix(in srgb,var(--red) 15%,transparent);}}
.mast-center{{font-family:Georgia,serif;font-style:italic;text-align:center;font-size:14px;color:var(--muted);}}
.mast-user{{text-align:right;font-size:11px;line-height:1.45;}}
.avatar{{display:inline-grid;place-items:center;width:33px;height:33px;border-radius:50%;background:var(--ink);color:var(--paper)!important;font-weight:900;margin-left:8px;}}

/* TOP CONTROLS */
.toolbar{{display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center;margin:9px 0 12px;}}
.search-note{{font-size:10px;color:var(--muted)!important;}}

/* HERO */
.hero{{display:grid;grid-template-columns:1.75fr .85fr;gap:18px;align-items:stretch;border-bottom:1px solid var(--line);padding:6px 0 12px;}}
.hero-copy{{display:flex;flex-direction:column;justify-content:center;}}
.hero-title{{font-family:'Playfair Display',Georgia,serif;font-size:46px;line-height:.96;font-weight:900;letter-spacing:-.8px;text-transform:uppercase;}}
.hero-title .red{{color:var(--red)!important;}}
.hero-dek{{font-family:Georgia,serif;font-size:14px;line-height:1.45;margin-top:8px;}}
.hero-quote{{display:inline-flex;gap:9px;align-items:center;margin-top:12px;font-family:Georgia,serif;font-size:11px;font-style:italic;color:var(--muted)!important;}}
.hero-photo{{height:165px;border:1px solid var(--line);overflow:hidden;position:relative;background:var(--paper2);}}
.hero-photo img{{width:100%;height:100%;object-fit:cover;filter:{'brightness(.70) saturate(.9)' if dark else 'grayscale(.25) sepia(.15) contrast(.96)'};}}
.hero-photo:after{{content:'WALL STREET · MARKET INTELLIGENCE';position:absolute;left:7px;bottom:6px;background:rgba(0,0,0,.72);color:white!important;padding:4px 7px;font-size:8px;font-weight:900;letter-spacing:.7px;}}

.section-title{{font-family:'Libre Franklin',Arial,sans-serif;font-size:12px;font-weight:900;letter-spacing:.25px;text-transform:uppercase;margin:0 0 8px;}}
.section-title:before{{content:'◆';font-size:8px;color:var(--accent);margin-right:7px;}}
.rule{{border-top:1px solid var(--line);margin:11px 0;}}
.muted{{color:var(--muted)!important;}}
.green{{color:var(--green)!important;}} .orange{{color:var(--orange)!important;}} .red{{color:var(--red)!important;}} .blue{{color:var(--accent)!important;}}
.label{{font-size:9px;font-weight:900;letter-spacing:1px;color:var(--muted)!important;text-transform:uppercase;}}
.badge{{display:inline-block;font-size:8px;font-weight:900;letter-spacing:.55px;border:1px solid var(--line);padding:3px 6px;border-radius:3px;}}
.badge.good{{color:var(--green)!important;border-color:color-mix(in srgb,var(--green) 40%,transparent);background:color-mix(in srgb,var(--green) 9%,transparent);}}
.badge.warn{{color:var(--orange)!important;border-color:color-mix(in srgb,var(--orange) 45%,transparent);background:color-mix(in srgb,var(--orange) 10%,transparent);}}
.badge.bad{{color:var(--red)!important;border-color:color-mix(in srgb,var(--red) 45%,transparent);background:color-mix(in srgb,var(--red) 10%,transparent);}}
.badge.info{{color:var(--accent)!important;border-color:color-mix(in srgb,var(--accent) 45%,transparent);background:color-mix(in srgb,var(--accent) 10%,transparent);}}

/* TICKER */
.ticker{{display:grid;grid-template-columns:repeat(5,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin:9px 0 13px;}}
.ticker-item{{padding:8px 11px;border-right:1px dotted var(--line);min-width:0;}}
.ticker-item:last-child{{border-right:0;}}
.ticker-name{{font-size:9px;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.ticker-value{{font-family:'Playfair Display',Georgia,serif;font-size:16px;font-weight:800;}}
.ticker-change{{font-size:9px;font-weight:900;}}

/* CARDS */
.card{{border:1px solid var(--line);background:color-mix(in srgb,var(--paper2) 93%,transparent);padding:12px;box-shadow:0 3px 12px color-mix(in srgb,var(--shadow) 30%,transparent);}}
.card-flat{{border:1px solid var(--line);background:transparent;padding:12px;}}
.lead-img{{height:170px;border:1px solid var(--line);overflow:hidden;margin-bottom:9px;}}
.lead-img img{{width:100%;height:100%;object-fit:cover;filter:{'brightness(.70) saturate(1.1)' if dark else 'grayscale(.2) sepia(.12)'};}}
.lead-title{{font-family:'Playfair Display',Georgia,serif;font-size:22px;font-weight:900;line-height:1.02;text-transform:uppercase;margin:5px 0 8px;}}
.copy{{font-family:Georgia,serif;font-size:11px;line-height:1.45;}}
.consensus-row{{display:grid;grid-template-columns:1fr 96px 34px;gap:7px;align-items:center;margin:9px 0;font-size:9px;font-weight:800;}}
.bar{{height:7px;background:var(--softline);overflow:hidden;border-radius:1px;}}
.bar span{{display:block;height:100%;background:var(--green);}}
.kpi-big{{font-family:'Playfair Display',Georgia,serif;font-size:30px;font-weight:900;}}
.kpi-medium{{font-family:'Playfair Display',Georgia,serif;font-size:21px;font-weight:900;}}
.risk-ring{{width:92px;height:92px;border-radius:50%;margin:7px auto;background:conic-gradient(var(--red) 0 30%,var(--orange) 30% 62%,var(--green) 62% 100%);display:grid;place-items:center;}}
.risk-inner{{width:68px;height:68px;border-radius:50%;background:var(--paper2);display:grid;place-items:center;text-align:center;font-family:'Playfair Display',Georgia,serif;font-size:18px;font-weight:900;line-height:1;}}

/* STEP FLOW */
.steps{{display:grid;grid-template-columns:repeat(7,1fr);border:1px solid var(--line);margin:12px 0;}}
.step{{padding:8px 7px;border-right:1px dotted var(--line);font-size:8px;line-height:1.25;}}
.step:last-child{{border-right:0;}}
.step-num{{display:inline-grid;place-items:center;width:22px;height:22px;border:1px solid var(--ink);border-radius:50%;font-weight:900;margin-right:4px;}}
.step.active .step-num{{background:var(--ink);color:var(--paper)!important;}}
.step b{{font-size:8px;}}

/* AGENTS + SYNTHESIS */
.agent-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;}}
.agent-card{{border:1px solid var(--line);background:var(--paper2);padding:10px;min-height:138px;}}
.agent-name{{font-family:'Libre Franklin',Arial,sans-serif;font-size:10px;font-weight:900;text-transform:uppercase;}}
.agent-status{{font-size:10px;font-weight:900;margin:5px 0;}}
.agent-copy{{font-family:Georgia,serif;font-size:10px;line-height:1.35;color:var(--muted)!important;}}
.agent-confidence{{font-size:9px;font-weight:900;margin-top:8px;}}
.spark{{height:22px;margin-top:6px;opacity:.78;background:linear-gradient(160deg,transparent 44%,var(--accent) 45%,var(--accent) 49%,transparent 50%);}}
.synthesis{{background:#06172d;color:#f6f5ef!important;border:1px solid #203957;padding:12px 15px;margin:10px 0;display:grid;grid-template-columns:2fr .8fr .8fr auto;gap:17px;align-items:center;box-shadow:0 6px 18px rgba(0,0,0,.18);}}
.synthesis *{{color:#f6f5ef!important;}}
.synth-label{{font-size:8px;font-weight:900;letter-spacing:1px;color:#a9bad1!important;}}
.synth-main{{font-family:'Playfair Display',Georgia,serif;font-size:20px;font-weight:900;}}
.synth-num{{font-family:'Playfair Display',Georgia,serif;font-size:25px;font-weight:900;}}

/* EVIDENCE */
.source-card{{border:1px solid var(--line);background:var(--paper2);padding:12px;height:100%;}}
.source-title{{font-family:'Playfair Display',Georgia,serif;font-size:17px;font-weight:800;margin:4px 0 6px;}}
.trace-row{{font-family:Georgia,serif;font-size:11px;line-height:1.45;padding:8px 0;border-bottom:1px dotted var(--line);}}
.trace-row:last-child{{border-bottom:0;}}
.flow-box{{border:1px solid var(--line);background:var(--paper2);padding:14px;text-align:center;font-weight:800;}}
.flow-row{{display:flex;flex-wrap:wrap;gap:7px;justify-content:center;}}
.flow-node{{border:1px solid var(--line);background:var(--paper);padding:8px 10px;font-size:10px;font-weight:900;min-width:118px;}}
.flow-arrow{{text-align:center;color:var(--accent)!important;font-size:20px;margin:4px 0;}}

/* STREAMLIT CONTROLS — force readable light/dark inputs */
[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
[data-testid="stMain"] label p{{color:var(--ink)!important;font-weight:800!important;}}
[data-testid="stMain"] input,
[data-testid="stMain"] textarea{{background:var(--control)!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;caret-color:var(--ink)!important;}}
[data-testid="stMain"] [data-baseweb="input"],
[data-testid="stMain"] [data-baseweb="input"]>div,
[data-testid="stMain"] [data-baseweb="base-input"],
[data-testid="stMain"] [data-baseweb="select"]>div{{background:var(--control)!important;color:var(--ink)!important;border-color:var(--line)!important;}}
[data-testid="stMain"] [data-testid="stNumberInput"]{{border-radius:6px!important;overflow:hidden!important;}}
[data-testid="stMain"] [data-testid="stNumberInput"]>div,
[data-testid="stMain"] [data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stMain"] [data-testid="stNumberInput"] [data-baseweb="input"]>div,
[data-testid="stMain"] [data-testid="stNumberInput"] [data-baseweb="base-input"]{{background:var(--control)!important;color:var(--ink)!important;border-color:var(--line)!important;}}
[data-testid="stMain"] [data-testid="stNumberInput"] input{{background:var(--control)!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;opacity:1!important;}}
[data-testid="stMain"] [data-testid="stNumberInput"] button{{background:var(--control2)!important;color:var(--ink)!important;border-color:var(--line)!important;min-width:42px!important;}}
[data-testid="stMain"] [data-testid="stNumberInput"] button:hover{{background:color-mix(in srgb,var(--accent) 11%,var(--control2))!important;}}
[data-testid="stMain"] [data-testid="stNumberInput"] button *{{color:var(--ink)!important;fill:var(--ink)!important;}}
[data-testid="stMain"] [data-baseweb="select"] *{{color:var(--ink)!important;}}
[data-testid="stMain"] input:focus,[data-testid="stMain"] textarea:focus{{outline:2px solid color-mix(in srgb,var(--accent) 55%,transparent)!important;outline-offset:1px!important;}}
a,a:visited{{color:var(--accent)!important;text-decoration-thickness:1px!important;text-underline-offset:2px!important;}}
a:hover{{filter:brightness(1.15);}}
[data-baseweb="popover"],[role="listbox"],[role="option"]{{background:var(--paper2)!important;color:var(--ink)!important;}}
[role="option"] *{{color:var(--ink)!important;}}
[role="option"]:hover,[role="option"][aria-selected="true"]{{background:var(--control2)!important;}}

[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea{{background:#0c1c34!important;color:#f5f7ff!important;-webkit-text-fill-color:#f5f7ff!important;}}
[data-testid="stSidebar"] [data-baseweb="input"],[data-testid="stSidebar"] [data-baseweb="input"]>div,
[data-testid="stSidebar"] [data-baseweb="select"]>div{{background:#0c1c34!important;border-color:rgba(255,255,255,.15)!important;}}
[data-testid="stSidebar"] [data-testid="stNumberInput"] button{{background:#132744!important;border-color:rgba(255,255,255,.15)!important;}}
[data-testid="stSidebar"] [data-testid="stNumberInput"] button *{{color:#fff!important;fill:#fff!important;}}

.stButton>button{{border-radius:3px!important;border:1px solid var(--line)!important;background:var(--paper2)!important;color:var(--ink)!important;font-weight:900!important;box-shadow:none!important;}}
.stButton>button:hover{{border-color:var(--accent)!important;color:var(--accent)!important;}}
.stButton>button[kind="primary"]{{background:#071a31!important;color:#f8f5ed!important;border-color:#071a31!important;}}
.stButton>button[kind="primary"] *{{color:#f8f5ed!important;}}
[data-testid="stMetric"]{{border:1px solid var(--line)!important;background:var(--paper2)!important;padding:10px!important;}}
[data-testid="stMetric"] *{{color:var(--ink)!important;}}
[data-testid="stDataFrame"]{{border:1px solid var(--line)!important;}}
[data-testid="stAlert"]{{border-radius:3px!important;}}
[data-testid="stExpander"]{{border:1px solid var(--line)!important;background:var(--paper2)!important;}}
[data-testid="stExpander"] summary *{{color:var(--ink)!important;}}
[data-testid="stSlider"] *{{color:var(--ink)!important;}}
[data-testid="stTabs"] button p{{color:var(--muted)!important;font-weight:800!important;}}
[data-testid="stTabs"] button[aria-selected="true"] p{{color:var(--ink)!important;}}

.page-title{{font-family:'Playfair Display',Georgia,serif;font-size:38px;font-weight:900;line-height:1;margin:5px 0 7px;text-transform:uppercase;}}
.page-dek{{font-family:Georgia,serif;color:var(--muted)!important;font-size:13px;margin-bottom:14px;}}
.footer{{text-align:center;font-size:8px;letter-spacing:.8px;color:var(--muted)!important;padding:15px 0 3px;}}

@media(max-width:1050px){{
  .masthead{{grid-template-columns:1fr;}} .mast-center,.mast-user{{text-align:left;}}
  .hero{{grid-template-columns:1fr;}} .ticker{{grid-template-columns:repeat(2,1fr);}}
  .agent-grid{{grid-template-columns:repeat(2,1fr);}} .steps{{grid-template-columns:repeat(2,1fr);}}
  .synthesis{{grid-template-columns:1fr 1fr;}} .hero-title{{font-size:37px;}}
}}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-logo">FININTEL</div><div class="sidebar-kicker">THE AI MARKET DAILY</div>', unsafe_allow_html=True)

    st.radio(
        "Navigation",
        NAV_ITEMS,
        key="nav_page",
        label_visibility="collapsed",
        format_func=lambda item: f"{NAV_ICONS[item]}  {item.upper()}  ·  {NAV_SUB[item]}",
    )

    st.markdown('<div class="sidebar-status"><b>AI STATUS</b><div>● All specialist agents ready</div><div>Local, explainable demo pipeline</div></div>', unsafe_allow_html=True)

    st.markdown("#### Investor controls")
    st.segmented_control("Appearance", ["Light", "Dark"], key="theme_mode", selection_mode="single")
    st.text_input("User name", key="user_name")
    st.selectbox("Risk profile", list(PROFILES.keys()), key="risk_profile")
    st.caption(f"Planned investment: ₹{st.session_state.new_investment:,.0f} · edit it in Portfolio or the Front Page card.")

    with st.expander("Behavioral profile"):
        st.selectbox(
            "If the market suddenly falls",
            [
                "Review data before acting",
                "Sell quickly when prices fall",
                "Buy more immediately after a rise",
                "I am unsure what I would do",
            ],
            key="reaction",
        )
        st.selectbox(
            "Usual decision style",
            [
                "Research before deciding",
                "Follow social-media tips",
                "Choose what recently performed best",
            ],
            key="decision_style",
        )

    with st.expander("Demo failure controls"):
        st.checkbox("Simulate missing market feed", key="missing_feed")
        st.checkbox("Simulate missing filing", key="missing_filing")
        st.checkbox("Simulate conflicting signals", key="conflicting_signals")


# -----------------------------------------------------------------------------
# DATA + ANALYSIS HELPERS
# -----------------------------------------------------------------------------
market_data = load_market_data()
SYMBOLS = market_data["symbol"].tolist()


def refreshed_snapshot(symbol: str) -> dict:
    row = market_data.query("symbol == @symbol").iloc[0].to_dict()
    tick = int(st.session_state.market_tick)
    movement = ((tick % 7) - 3) * 0.035
    row["price"] = round(float(row["price"]) * (1 + movement / 100), 2)
    row["day_change"] = round(float(row["day_change"]) + movement, 2)
    row["momentum"] = float(np.clip(float(row["momentum"]) + movement * 2.2, 0, 100))
    return row


def portfolio_values() -> tuple[dict, float]:
    holdings = {symbol: float(st.session_state[f"holding_{symbol}"]) for symbol in SYMBOLS}
    total = sum(holdings.values())
    return holdings, total


def analysis_for(profile_name: str | None = None, symbol: str | None = None, use_demo_failures: bool = True) -> dict:
    symbol = symbol or st.session_state.stock
    profile_name = profile_name or st.session_state.risk_profile
    holdings, total = portfolio_values()
    return run_analysis(
        symbol=symbol,
        profile=PROFILES[profile_name],
        missing_feed=st.session_state.missing_feed if use_demo_failures else False,
        missing_filing=st.session_state.missing_filing if use_demo_failures else False,
        conflict=st.session_state.conflicting_signals if use_demo_failures else False,
        snapshot=refreshed_snapshot(symbol),
        portfolio={
            "value": total,
            "selected_holding": holdings[symbol],
            "new_investment": float(st.session_state.new_investment),
        },
        behavior={"reaction": st.session_state.reaction, "decision_style": st.session_state.decision_style},
        question="What does the current evidence mean for my portfolio?",
    )


def run_and_log() -> None:
    result = analysis_for()
    st.session_state.last_result = result
    st.session_state.runs += 1
    append_run(
        {
            "run": st.session_state.runs,
            "stock": result["asset"],
            "profile": st.session_state.risk_profile,
            "latency_ms": round(result["latency_ms"], 2),
            "signal_score": result["signal_score"],
            "confidence_pct": round(result["confidence"] * 100, 1),
            "concentration_pct": result["portfolio"]["concentration"],
            "projected_concentration_pct": result["portfolio"]["projected_concentration"],
            "stance": result["stance"],
            "final_signal": result["final_signal"],
            "conflict": result["conflict_detected"],
            "safety_status": result["safety"]["status"],
        }
    )


def score_class(score: float) -> str:
    if score > 0.25:
        return "good"
    if score < -0.25:
        return "bad"
    return "warn"


def signal_class(signal: str) -> str:
    s = signal.upper()
    if any(token in s for token in ["BULLISH", "POSITIVE", "LOW RISK", "CLEAR", "NORMAL", "HIGH ACTIVITY"]):
        return "good"
    if any(token in s for token in ["BEARISH", "NEGATIVE", "HIGH RISK", "SKEPTICAL", "UNAVAILABLE"]):
        return "bad"
    return "warn"


def agent_by_name(result: dict, name: str) -> dict:
    for agent in result["agents"]:
        if agent["name"] == name:
            return agent
    return {"name": name, "signal": "N/A", "confidence": 0, "score": 0, "reasoning": "No output."}


def price_history(symbol: str, days: int = 30) -> pd.DataFrame:
    row = refreshed_snapshot(symbol)
    seed = sum(ord(ch) for ch in symbol) + 17
    rng = np.random.default_rng(seed)
    volatility = max(float(row["volatility"]), .08)
    returns = rng.normal(0.0008, volatility / 28, days)
    prices = float(row["price"]) * np.cumprod(1 + returns)
    prices *= float(row["price"]) / prices[-1]
    return pd.DataFrame({"Date": pd.date_range(end=pd.Timestamp.today().normalize(), periods=days), "Price": prices})


def line_chart(frame: pd.DataFrame, x: str, y: str, height: int = 210) -> None:
    chart = (
        alt.Chart(frame)
        .mark_line(strokeWidth=2.2)
        .encode(
            x=alt.X(f"{x}:T", axis=alt.Axis(title=None, labelColor=C["muted"], grid=False)),
            y=alt.Y(f"{y}:Q", axis=alt.Axis(title=None, labelColor=C["muted"], gridColor=C["softline"])),
            tooltip=[x, alt.Tooltip(y, format=",.2f")],
        )
        .properties(height=height)
    )
    st.altair_chart(chart, use_container_width=True, theme=None)


def bar_chart(frame: pd.DataFrame, x: str, y: str, height: int = 220) -> None:
    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
        .encode(
            x=alt.X(f"{x}:N", axis=alt.Axis(title=None, labelAngle=0, labelColor=C["muted"])),
            y=alt.Y(f"{y}:Q", axis=alt.Axis(title=None, labelColor=C["muted"], gridColor=C["softline"])),
            tooltip=[x, alt.Tooltip(y, format=".2f")],
        )
        .properties(height=height)
    )
    st.altair_chart(chart, use_container_width=True, theme=None)


def page_intro(title: str, description: str) -> None:
    st.markdown(f'<div class="page-title">{title}</div><div class="page-dek">{description}</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# COMMON MASTHEAD + SEARCH
# -----------------------------------------------------------------------------
hero_uri = image_data_uri(BULL_IMG if dark else WALL_STREET_IMG)
lead_uri = image_data_uri(WALL_STREET_IMG if dark else BULL_IMG)

st.markdown(
    f"""
<div class="masthead">
  <div>
    <div class="brand">FININTEL</div>
    <div class="brand-sub">THE AI MARKET DAILY</div>
    <div class="date-line">TUESDAY, 1 SEPTEMBER 2026 &nbsp; · &nbsp; VIT CHENNAI HACKVERSE</div>
    <div class="market-open"><span class="live-dot"></span>MARKET OPEN · SIMULATED LIVE FEED</div>
  </div>
  <div class="mast-center">“The more you know, the less you guess.”<br><b>Explainable intelligence over black-box tips.</b></div>
  <div class="mast-user"><b>{st.session_state.user_name or 'Investor'}</b> · {st.session_state.risk_profile} profile <span class="avatar">{(st.session_state.user_name[:1] or 'I').upper()}</span><br>
  {datetime.now().strftime('%I:%M:%S %p')} IST</div>
</div>
""",
    unsafe_allow_html=True,
)

search_col, stock_col, refresh_col = st.columns([4.2, 1.25, 1.05])
with search_col:
    st.text_input(
        "Search",
        placeholder="Search stocks, filings, risk, agents...",
        label_visibility="collapsed",
        key="search_box",
        on_change=handle_search,
    )
with stock_col:
    st.selectbox("Stock", SYMBOLS, key="stock", label_visibility="collapsed")
with refresh_col:
    if st.button("↻ Refresh", use_container_width=True):
        st.session_state.market_tick += 1
        st.session_state.last_refresh = datetime.now().strftime("%I:%M:%S %p")
        st.rerun()

if st.session_state.search_message:
    st.caption(st.session_state.search_message)

preview = analysis_for()
snapshot = refreshed_snapshot(st.session_state.stock)
holdings, portfolio_total = portfolio_values()
selected_concentration = preview["portfolio"]["concentration"]


# -----------------------------------------------------------------------------
# FRONT PAGE
# -----------------------------------------------------------------------------
def render_front_page() -> None:
    st.markdown(
        f"""
<div class="hero">
  <div class="hero-copy">
    <div class="hero-title">AI INVESTIGATES.<br>YOU INVEST <span class="red">INTELLIGENTLY.</span></div>
    <div class="hero-dek">Real-time market data. Regulatory filings. Behavioral signals. Multi-agent intelligence.</div>
    <div class="hero-quote">◆ <span>Every conclusion shows its evidence, disagreement and uncertainty.</span></div>
  </div>
  <div class="hero-photo"><img src="{hero_uri}"></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title" style="margin-top:10px">Market Pulse <span class="badge good">LIVE</span></div>', unsafe_allow_html=True)
    fixed_indices = [
        ("NIFTY 50", "25,180.60", "+0.86%"),
        ("SENSEX", "82,940.21", "+0.83%"),
        ("NASDAQ", "21,430.33", "+0.68%"),
        ("GOLD (MCX)", "70,812", "+0.59%"),
        ("VIX", "15.32", "-4.26%"),
    ]
    html = '<div class="ticker">'
    for name, value, change in fixed_indices:
        cls = "red" if change.startswith("-") else "green"
        html += f'<div class="ticker-item"><div class="ticker-name">{name}</div><div class="ticker-value">{value}</div><div class="ticker-change {cls}">{change}</div></div>'
    st.markdown(html + '</div>', unsafe_allow_html=True)

    lead, consensus, portfolio = st.columns([1.34, 1.04, .95], gap="small")
    with lead:
        tech = agent_by_name(preview, "Technical Agent")
        risk = agent_by_name(preview, "Risk Agent")
        st.markdown(
            f"""
<div class="card">
  <div class="lead-img"><img src="{lead_uri}"></div>
  <div class="label">TODAY'S LEAD STORY · {st.session_state.stock}</div>
  <div class="lead-title">SIGNAL BUILDS — BUT THE RISK LAYER GETS THE FINAL WORD</div>
  <div class="copy">{tech['reasoning']} {risk['reasoning']} FININTEL keeps both views visible instead of hiding the disagreement.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.button(f"Investigate {st.session_state.stock} →", key="front_investigate", use_container_width=True, on_click=go_to, args=("Investigations",))

    with consensus:
        front_agents = ["Technical Agent", "Fundamental Agent", "Sentiment Agent", "Risk Agent", "Skeptic Agent"]
        html = '<div class="card"><div class="section-title">AI Consensus</div>'
        for name in front_agents:
            agent = agent_by_name(preview, name)
            pct = round(agent["confidence"] * 100)
            cls = signal_class(agent["signal"])
            color = C["green"] if cls == "good" else (C["red"] if cls == "bad" else C["orange"])
            html += f'<div class="consensus-row"><span>{name}</span><div class="bar"><span style="width:{pct}%;background:{color}"></span></div><b>{pct}%</b></div>'
        html += f'<div class="rule"></div><div style="display:flex;justify-content:space-between;font-size:10px"><b>OVERALL SIGNAL</b><span class="badge {score_class(preview["raw_score"])}">{preview["stance"]}</span></div>'
        html += f'<div style="display:flex;justify-content:space-between;font-size:10px;margin-top:8px"><b>CONFIDENCE</b><b>{preview["confidence"]:.0%}</b></div></div>'
        st.markdown(html, unsafe_allow_html=True)

    with portfolio:
        with st.container(border=True):
            st.markdown('<div class="section-title">My Portfolio & Risk</div>', unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            with p1:
                st.number_input("RELIANCE ₹", min_value=0.0, step=5000.0, key="holding_RELIANCE")
                st.number_input("TCS ₹", min_value=0.0, step=5000.0, key="holding_TCS")
            with p2:
                st.number_input("INFY ₹", min_value=0.0, step=5000.0, key="holding_INFY")
                st.number_input("NEW INVESTMENT ₹", min_value=0.0, step=5000.0, key="new_investment")
            risk_score = int(np.clip(30 + selected_concentration * .7 + float(snapshot["volatility"]) * 60, 15, 92))
            risk_label = "HIGH" if risk_score >= 70 else ("MODERATE" if risk_score >= 42 else "LOW")
            st.markdown(
                f'<div class="kpi-big">₹{portfolio_total:,.2f}</div><div class="copy">Total entered portfolio</div>'
                f'<div class="green" style="font-weight:900;font-size:10px;margin-top:5px">+1.32% DEMO DAY CHANGE</div>'
                f'<div class="risk-ring"><div class="risk-inner">{risk_score}<br><span style="font:800 8px DM Sans">{risk_label}</span></div></div>'
                f'<div class="copy"><b>{st.session_state.stock}</b> concentration: {selected_concentration:.1f}% · profile limit: {PROFILES[st.session_state.risk_profile]["max_concentration"]}%</div>',
                unsafe_allow_html=True,
            )
        st.button("Open portfolio analysis →", key="front_portfolio", use_container_width=True, on_click=go_to, args=("Portfolio",))

    st.markdown('<div class="section-title">AI Agent Insights</div>', unsafe_allow_html=True)
    shown = ["Technical Agent", "Fundamental Agent", "Sentiment Agent", "Risk Agent", "Skeptic Agent"]
    html = '<div class="agent-grid">'
    for name in shown:
        agent = agent_by_name(preview, name)
        cls = signal_class(agent["signal"])
        html += (
            f'<div class="agent-card"><div class="agent-name">{name}</div>'
            f'<div class="agent-status"><span class="badge {cls}">{agent["signal"]}</span></div>'
            f'<div class="agent-copy">{agent["reasoning"]}</div>'
            f'<div class="agent-confidence">CONFIDENCE {agent["confidence"]:.0%}</div><div class="spark"></div></div>'
        )
    st.markdown(html + '</div>', unsafe_allow_html=True)

    if st.button("⚡ ANALYSE STOCK WITH ALL AGENTS", type="primary", use_container_width=True):
        with st.spinner("Running specialists in parallel → synthesis → safety check…"):
            run_and_log()
        st.rerun()

    result = st.session_state.last_result or preview
    st.markdown(
        f"""
<div class="synthesis">
  <div><div class="synth-label">AI SYNTHESIS</div><div class="synth-main">{result['stance']}</div><div style="font-size:9px;color:#afbdd0!important">{result['advisory']['headline']}</div></div>
  <div><div class="synth-label">FINAL SIGNAL</div><div class="synth-num">{result['final_signal']}</div></div>
  <div><div class="synth-label">CONFIDENCE</div><div class="synth-num">{result['confidence']:.0%}</div></div>
  <div><span class="badge {'bad' if result['safety']['status']=='CAUTION' else 'good'}">SAFETY {result['safety']['status']}</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

    trends, behavior, alerts = st.columns([1.35, .85, .85], gap="small")
    with trends:
        with st.container(border=True):
            st.markdown('<div class="section-title">Market Trends</div>', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.markdown(f'<div class="label">{st.session_state.stock} PRICE</div><div class="kpi-medium">₹{snapshot["price"]:,.2f}</div><div class="green" style="font-size:10px;font-weight:900">{snapshot["day_change"]:+.2f}%</div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="label">VOLUME</div><div class="kpi-medium">{snapshot["volume_anomaly"]:.2f}×</div><div class="orange" style="font-size:10px;font-weight:900">vs baseline</div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="label">SENTIMENT</div><div class="kpi-medium">{snapshot["sentiment"]:+.2f}</div><div class="green" style="font-size:10px;font-weight:900">normalized</div>', unsafe_allow_html=True)
            line_chart(price_history(st.session_state.stock), "Date", "Price", 145)
    with behavior:
        b = preview["behavioral"]
        st.markdown(
            f'<div class="card"><div class="section-title">Behavioral Insights</div><div class="label">STATUS</div><div class="kpi-medium">{b["status"]}</div><div class="copy">{b["reasoning"]}</div><div class="rule"></div><div class="label">CONFIDENCE FACTOR</div><div class="kpi-medium">{b["confidence_factor"]:.0%}</div></div>',
            unsafe_allow_html=True,
        )
    with alerts:
        warnings = []
        if preview["portfolio"]["risk_flag"] == "REVIEW":
            warnings.append(("bad", "CONCENTRATION", "Selected position exceeds the profile limit."))
        if preview["conflict_detected"]:
            warnings.append(("warn", "CONFLICT", "Independent signals disagree; confidence is reduced."))
        if st.session_state.missing_feed or st.session_state.missing_filing:
            warnings.append(("bad", "DEGRADED DATA", "One source is unavailable; affected agents abstain."))
        if not warnings:
            warnings.append(("good", "SYSTEM NORMAL", "No synthetic failure condition is active."))
        html = '<div class="card"><div class="section-title">AI Alerts</div>'
        for cls, title, copy in warnings:
            html += f'<div class="trace-row"><span class="badge {cls}">{title}</span><br>{copy}</div>'
        st.markdown(html + '</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# MARKETS
# -----------------------------------------------------------------------------
def render_markets() -> None:
    page_intro("Markets", "Three independent signal dimensions make the market classification visible instead of hiding everything inside one AI answer.")
    row = refreshed_snapshot(st.session_state.stock)
    dimensions = preview["market_dimensions"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current price", f"₹{row['price']:,.2f}", f"{row['day_change']:+.2f}%")
    c2.metric("Momentum", f"{row['momentum']:.1f}/100", dimensions["price_momentum"]["label"])
    c3.metric("Volume anomaly", f"{row['volume_anomaly']:.2f}×", dimensions["volume_anomaly"]["label"])
    c4.metric("Sentiment", f"{row['sentiment']:+.2f}", dimensions["sentiment"]["label"])

    left, right = st.columns([1.55, 1], gap="medium")
    with left:
        st.markdown('<div class="section-title">30-Day Demo Price Path</div>', unsafe_allow_html=True)
        line_chart(price_history(st.session_state.stock, 45), "Date", "Price", 285)
    with right:
        st.markdown('<div class="section-title">Signal Classification</div>', unsafe_allow_html=True)
        for key, pretty in [("price_momentum", "Price momentum"), ("volume_anomaly", "Volume anomaly"), ("sentiment", "Sentiment")]:
            d = dimensions[key]
            st.markdown(f'<div class="source-card" style="margin-bottom:8px"><div class="label">{pretty}</div><div class="source-title">{d["label"]}</div><div class="copy">{d["explanation"]}</div></div>', unsafe_allow_html=True)

    st.markdown("#### Simulated market table")
    display = market_data.copy().rename(columns={
        "symbol": "Stock", "price": "Price", "day_change": "Day change %", "volume_anomaly": "Volume ×", "momentum": "Momentum", "sentiment": "Sentiment", "volatility": "Volatility"
    })
    st.dataframe(display, hide_index=True, use_container_width=True)


# -----------------------------------------------------------------------------
# INVESTIGATIONS
# -----------------------------------------------------------------------------
def render_investigations() -> None:
    result = st.session_state.last_result or preview
    page_intro("What Happened Today?", "The investigation page answers the hackathon's core question: what happened, what does it mean for this user, and why did the system reach that conclusion?")

    top1, top2, top3 = st.columns([1.3, .9, .9])
    top1.markdown(f'<div class="card"><div class="label">FINAL RESEARCH STANCE</div><div class="kpi-big">{result["stance"]}</div><div class="copy">{result["summary"]}</div></div>', unsafe_allow_html=True)
    top2.markdown(f'<div class="card"><div class="label">FINAL SIGNAL</div><div class="kpi-big">{result["final_signal"]}</div><div class="copy">{result["advisory"]["action"]}</div></div>', unsafe_allow_html=True)
    top3.markdown(f'<div class="card"><div class="label">CONFIDENCE</div><div class="kpi-big">{result["confidence"]:.0%}</div><div class="copy">Uncertainty: {result["safety"]["uncertainty"]}% · {result["safety"]["status"]}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title" style="margin-top:12px">Agent contributions</div>', unsafe_allow_html=True)
    contribution_df = pd.DataFrame(result["agent_contributions"])
    if not contribution_df.empty:
        contribution_df["Contribution"] = contribution_df["weighted_score"] * 100
        bar_chart(contribution_df, "agent", "Contribution", 245)

    st.markdown('<div class="section-title">Complete reasoning trace</div>', unsafe_allow_html=True)
    html = '<div class="card-flat">'
    for index, item in enumerate(result["trace"], 1):
        html += f'<div class="trace-row"><b>{index:02d}</b> &nbsp; {item}</div>'
    st.markdown(html + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title" style="margin-top:12px">Safety & uncertainty</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><span class="badge {"bad" if result["safety"]["status"]=="CAUTION" else "good"}">{result["safety"]["status"]}</span><div class="source-title">{result["safety"]["uncertainty"]}% uncertainty</div><div class="copy">{result["safety"]["reasoning"]}</div><div class="rule"></div><div class="copy muted">{result["safety_note"]}</div></div>', unsafe_allow_html=True)

    if st.button("Open cited filing evidence →", use_container_width=True, on_click=go_to, args=("Filings",)):
        pass


# -----------------------------------------------------------------------------
# FILINGS / RAG
# -----------------------------------------------------------------------------
def render_filings() -> None:
    page_intro("Regulatory Desk", "The Fundamental Agent retrieves source text first, then classifies only what is present in that evidence. If evidence is missing, it abstains.")
    query = st.text_input("Ask the filing corpus", value="revenue margin growth risk uncertainty guidance", key="filing_query")
    evidence = retrieve(st.session_state.stock, query, top_k=2) if not st.session_state.missing_filing else []
    if not evidence:
        st.warning("No filing evidence is available in this run. FININTEL will not generate an uncited financial claim.")
        return
    cols = st.columns(len(evidence))
    for col, item in zip(cols, evidence):
        with col:
            st.markdown(f'<div class="source-card"><span class="badge info">{item["doc_id"]}</span><div class="source-title">{item["title"]}</div><div class="copy">{item["text"]}</div><div class="rule"></div><div class="label">RETRIEVED FOR</div><div class="copy muted">{query}</div></div>', unsafe_allow_html=True)
    st.markdown("#### How the retrieval works")
    st.markdown(
        '<div class="flow-box"><div class="flow-row"><div class="flow-node">Natural-language query</div><div class="flow-node">Token overlap retrieval</div><div class="flow-node">Top evidence chunks</div><div class="flow-node">Fundamental classification</div></div></div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# AI DESK
# -----------------------------------------------------------------------------
def render_ai_desk() -> None:
    page_intro("AI Desk", "Each specialist has one job and returns a structured output. The synthesis layer can only combine those outputs; it cannot quietly rewrite the source data.")
    result = st.session_state.last_result or preview
    names = [a["name"] for a in result["agents"]]
    for start in range(0, len(names), 3):
        cols = st.columns(3)
        for col, name in zip(cols, names[start:start+3]):
            agent = agent_by_name(result, name)
            with col:
                st.markdown(f'<div class="source-card"><div class="label">SPECIALIST</div><div class="source-title">{agent["name"]}</div><span class="badge {signal_class(agent["signal"])}">{agent["signal"]}</span><div class="copy" style="margin-top:9px">{agent["reasoning"]}</div><div class="rule"></div><div class="label">STRUCTURED CONTRACT</div><div class="copy">score = {agent["score"]:+.2f} · confidence = {agent["confidence"]:.0%}</div></div>', unsafe_allow_html=True)

    st.markdown("#### Multi-agent architecture")
    st.markdown(
        '<div class="flow-box"><div class="label">INPUT LAYER</div><div class="flow-row"><div class="flow-node">Market snapshot</div><div class="flow-node">Filing corpus</div><div class="flow-node">Portfolio + profile</div><div class="flow-node">Behavior</div></div></div><div class="flow-arrow">↓</div><div class="flow-box"><div class="label">PARALLEL SPECIALISTS</div><div class="flow-row"><div class="flow-node">Technical</div><div class="flow-node">Volume</div><div class="flow-node">Sentiment</div><div class="flow-node">Fundamental / RAG</div><div class="flow-node">Risk</div><div class="flow-node">Skeptic</div></div></div><div class="flow-arrow">↓</div><div class="flow-box"><b>TRANSPARENT WEIGHTED SYNTHESIS</b></div><div class="flow-arrow">↓</div><div class="flow-box"><b>BEHAVIORAL GUARD + SAFETY / UNCERTAINTY</b></div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# PORTFOLIO
# -----------------------------------------------------------------------------
def render_portfolio() -> None:
    page_intro("Portfolio & Risk", "This page proves personalization: the same stock can produce different risk conclusions for Conservative, Moderate and Aggressive investors.")
    c1, c2, c3 = st.columns(3)
    with c1: st.number_input("RELIANCE holding (₹)", min_value=0.0, step=5000.0, key="holding_RELIANCE")
    with c2: st.number_input("TCS holding (₹)", min_value=0.0, step=5000.0, key="holding_TCS")
    with c3: st.number_input("INFY holding (₹)", min_value=0.0, step=5000.0, key="holding_INFY")
    st.number_input("Planned new investment (₹)", min_value=0.0, step=5000.0, key="new_investment")

    holdings_now, total_now = portfolio_values()
    st.metric("Entered portfolio total", f"₹{total_now:,.0f}")

    rows = []
    for profile in PROFILES:
        r = analysis_for(profile_name=profile, use_demo_failures=False)
        risk = agent_by_name(r, "Risk Agent")
        rows.append({
            "Profile": profile,
            "Limit %": PROFILES[profile]["max_concentration"],
            "Current concentration %": r["portfolio"]["concentration"],
            "Projected concentration %": r["portfolio"]["projected_concentration"],
            "Risk output": risk["signal"],
            "Final signal": r["final_signal"],
            "Confidence %": round(r["confidence"] * 100),
        })
    compare = pd.DataFrame(rows)
    st.dataframe(compare, hide_index=True, use_container_width=True)
    st.info("The market input above is identical across all three rows. Only the stored risk profile changes. That is the personalization requirement in action.")


# -----------------------------------------------------------------------------
# WATCHLIST
# -----------------------------------------------------------------------------
def render_watchlist() -> None:
    page_intro("Watchlist", "A compact paper watchlist for the three demo equities. Toggle which symbols you want to monitor.")
    for symbol in SYMBOLS:
        left, middle, right = st.columns([.32, 2.3, .9])
        with left:
            st.checkbox("Watch", key=f"watch_{symbol}", label_visibility="collapsed")
        r = analysis_for(symbol=symbol, use_demo_failures=False)
        row = refreshed_snapshot(symbol)
        with middle:
            st.markdown(f'<div class="source-card"><div class="label">{symbol}</div><div class="source-title">₹{row["price"]:,.2f} · {row["day_change"]:+.2f}%</div><div class="copy">{r["stance"]} · {r["final_signal"]} · confidence {r["confidence"]:.0%}</div></div>', unsafe_allow_html=True)
        with right:
            st.metric("Signal score", f"{r['signal_score']:.0f}/100")


# -----------------------------------------------------------------------------
# SCENARIO LAB
# -----------------------------------------------------------------------------
def render_scenario_lab() -> None:
    page_intro("Scenario Lab", "Stress-test the selected stock without changing the real demo data. The point is to show how the system reacts, not predict the future.")
    c1, c2, c3 = st.columns(3)
    with c1: price_move = st.slider("Synthetic price move", -15, 15, 0, format="%d%%")
    with c2: volume_ratio = st.slider("Volume vs baseline", .5, 3.0, float(snapshot["volume_anomaly"]), .1, format="%.1f×")
    with c3: sentiment = st.slider("Sentiment", -1.0, 1.0, float(snapshot["sentiment"]), .05)

    scenario = dict(snapshot)
    scenario["price"] = float(snapshot["price"]) * (1 + price_move / 100)
    scenario["day_change"] = price_move
    scenario["momentum"] = float(np.clip(float(snapshot["momentum"]) + price_move * 2.0, 0, 100))
    scenario["volume_anomaly"] = volume_ratio
    scenario["sentiment"] = sentiment
    holdings_now, total_now = portfolio_values()
    result = run_analysis(
        symbol=st.session_state.stock,
        profile=PROFILES[st.session_state.risk_profile],
        snapshot=scenario,
        portfolio={"value": total_now, "selected_holding": holdings_now[st.session_state.stock], "new_investment": st.session_state.new_investment},
        behavior={"reaction": st.session_state.reaction, "decision_style": st.session_state.decision_style},
        question="How does this what-if scenario change the research signal?",
    )
    a, b, c = st.columns(3)
    a.metric("Scenario stance", result["stance"])
    b.metric("Final signal", result["final_signal"])
    c.metric("Confidence", f"{result['confidence']:.0%}")
    st.markdown(f'<div class="card"><div class="label">WHY IT CHANGED</div><div class="copy">{result["advisory"]["action"]}</div></div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# PERFORMANCE + ARCHIVE
# -----------------------------------------------------------------------------
def render_performance() -> None:
    page_intro("Performance", "Each deliberate analysis run persists measurable metrics so judges can inspect latency, confidence and portfolio concentration.")
    logs = load_runs(200)
    if not logs:
        st.info("No logged runs yet. Go to Front Page and click Analyse Stock with All Agents.")
        return
    frame = pd.DataFrame(logs)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Persistent runs", len(frame))
    c2.metric("Average latency", f"{frame['latency_ms'].mean():.1f} ms")
    c3.metric("Average confidence", f"{frame['confidence_pct'].mean():.1f}%")
    c4.metric("Latest concentration", f"{frame.iloc[-1]['concentration_pct']:.1f}%")
    st.dataframe(frame, hide_index=True, use_container_width=True)
    if len(frame) > 1:
        graph = frame[["run", "signal_score", "confidence_pct"]].melt("run", var_name="Metric", value_name="Value")
        chart = alt.Chart(graph).mark_line(point=True).encode(
            x=alt.X("run:Q", axis=alt.Axis(title="Run", labelColor=C["muted"])),
            y=alt.Y("Value:Q", axis=alt.Axis(title=None, labelColor=C["muted"], gridColor=C["softline"])),
            detail="Metric:N", tooltip=["run", "Metric", "Value"]
        ).properties(height=260)
        st.altair_chart(chart, use_container_width=True, theme=None)


def render_archive() -> None:
    page_intro("Archive", "A readable record of prior persisted demo runs. This makes the prototype auditable across app restarts.")
    logs = load_runs(100)
    if not logs:
        st.info("The archive is empty until you run an investigation.")
        return
    for item in reversed(logs[-12:]):
        st.markdown(f'<div class="source-card" style="margin-bottom:7px"><div class="label">{item.get("timestamp", "")}</div><div class="source-title">{item.get("stock")} · {item.get("final_signal")}</div><div class="copy">Profile: {item.get("profile")} · stance: {item.get("stance")} · confidence: {item.get("confidence_pct")}% · latency: {item.get("latency_ms")} ms · concentration: {item.get("concentration_pct")}%</div></div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SETTINGS
# -----------------------------------------------------------------------------
def render_settings() -> None:
    page_intro("Settings", "All settings are intentionally simple and local so the demo remains explainable and safe.")
    st.write("Use the left sidebar to change appearance, investor profile, behavior and failure simulations.")
    st.markdown("#### Current configuration")
    config = {
        "Appearance": st.session_state.theme_mode,
        "User": st.session_state.user_name,
        "Risk profile": st.session_state.risk_profile,
        "Selected stock": st.session_state.stock,
        "Missing feed simulation": st.session_state.missing_feed,
        "Missing filing simulation": st.session_state.missing_filing,
        "Conflict simulation": st.session_state.conflicting_signals,
    }
    st.json(config)
    st.info("Light and Dark modes use the same information architecture. Only the palette, image treatment and contrast change.")


# -----------------------------------------------------------------------------
# ROUTER
# -----------------------------------------------------------------------------
page = st.session_state.nav_page
if page == "Front Page":
    render_front_page()
elif page == "Markets":
    render_markets()
elif page == "Investigations":
    render_investigations()
elif page == "Filings":
    render_filings()
elif page == "AI Desk":
    render_ai_desk()
elif page == "Portfolio":
    render_portfolio()
elif page == "Watchlist":
    render_watchlist()
elif page == "Scenario Lab":
    render_scenario_lab()
elif page == "Performance":
    render_performance()
elif page == "Archive":
    render_archive()
elif page == "Settings":
    render_settings()

st.markdown('<div class="footer">FININTEL · SIMULATED MARKET DATA · SYNTHETIC FILINGS · NO TRADE EXECUTION · EDUCATIONAL HACKATHON PROTOTYPE · NOT FINANCIAL ADVICE</div>', unsafe_allow_html=True)
