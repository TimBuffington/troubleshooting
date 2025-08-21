# app.py
from __future__ import annotations

# ----------------------------
# Setup & Imports
# ----------------------------
import json
import re
from pathlib import Path
from contextlib import contextmanager
import streamlit as st

st.set_page_config(page_title="EBOSS® Fault Code Lookup", layout="centered")

# ----------------------------
# Utilities
# ----------------------------
def _has(attr: str) -> bool:
    return callable(getattr(st, attr, None))
def safe_rerun() -> None:
    """Version-agnostic rerun (no recursion, no contextmanager)."""
    rerun_fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if callable(rerun_fn):
        rerun_fn()

@contextmanager
def modal_ctx(title: str):
    """Use real modal if available; otherwise an expander."""
    if _has("modal"):
        with st.modal(title):
            yield
    else:
        with st.expander(f"🔎 {title}", expanded=True):
            yield

# ----------------------------
# Branding / Global CSS
# ----------------------------
BG_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/AdobeStock_209254754.jpeg"
LOGO_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"

css = """
<style>
/* =================== FOUNDATION =================== */
:root {
  --alpine-white: #FFFFFF;
  --energy-green: #80BD47;  /* ANA Energy Green */
  --light-grey:  #D0D4D9;
  --charcoal:    #636569;   /* ANA Charcoal (99,101,105) */
}

/* Background (kept active) */
[data-testid="stAppViewContainer"] {
  background-image: url('%s');
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  background-attachment: fixed;
}
/* iOS/mobile: avoid fixed-bg repaint jank */
@media (max-width: 480px) {
  [data-testid="stAppViewContainer"] { background-attachment: scroll; }
}

/* Shell chrome — make sure nothing blocks bg/logo */
.block-container { background: transparent !important; }
[data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }
[data-testid="stSidebar"] > div:first-child { background: rgba(0,0,0,0) !important; }

/* Logo (kept active) */
.logo-wrap {
  display:flex; align-items:center; justify-content:center;
  margin: .25rem 0 .75rem 0;
}
.logo-wrap img {
  max-width: min(420px, 70vw); height:auto;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,.45));
}

/* =================== GLOBAL TYPOGRAPHY =================== */
/* Force Arial Bold Alpine White + subtle shadow across app */
html, body, [class*="stMarkdown"], [class*="stText"],
[data-testid="stMarkdownContainer"], [data-testid="stCaption"] p,
[data-testid="stAlert"] p, .stRadio label, .stCheckbox label,
.stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label {
  font-family: Arial, Helvetica, sans-serif !important;
  font-weight: 700 !important;
  color: var(--alpine-white) !important;
  -webkit-text-fill-color: var(--alpine-white) !important; /* iOS Safari */
  text-shadow: 0 1px 2px rgba(0,0,0,.85);
}
.stMarkdown strong, .stMarkdown b { color: var(--alpine-white) !important; }

/* Optional heading helper if you use .app-title / .muted */
.app-title {
  font-size: 1.8rem; font-weight: 700; margin-bottom: .25rem;
  color: var(--alpine-white) !important; text-shadow: 0 2px 8px rgba(0,0,0,.7);
}
.muted { color: #eef2f6 !important; }

/* =================== FORM CONTROLS (UNIFIED LOOK) =================== */
/* SELECT visible control */
[data-testid="stSelectbox"] > div[data-baseweb="select"] > div,
/* TEXT / NUMBER inputs */
[data-testid="stTextInput"]  input,
[data-testid="stNumberInput"] input,
/* TEXTAREA */
textarea[data-baseweb="textarea"] {
  background: var(--charcoal) !important;
  color: var(--alpine-white) !important;
  -webkit-text-fill-color: var(--alpine-white) !important;
  font-family: Arial, Helvetica, sans-serif !important;
  font-weight: 700 !important;
  border: 1px solid var(--light-grey) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  caret-color: var(--alpine-white) !important;
}

/* Placeholders */
[data-testid="stTextInput"]  input::placeholder,
[data-testid="stNumberInput"] input::placeholder,
textarea[data-baseweb="textarea"]::placeholder {
  color: var(--alpine-white) !important;
  opacity: .65 !important;
}

/* Hover/Focus = Energy-Green glow */
[data-testid="stSelectbox"] > div[data-baseweb="select"] > div:hover,
[data-testid="stSelectbox"] > div[data-baseweb="select"] > div:focus,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within,
[data-testid="stTextInput"]  input:hover,
[data-testid="stTextInput"]  input:focus,
[data-testid="stNumberInput"] input:hover,
[data-testid="stNumberInput"] input:focus,
textarea[data-baseweb="tex]()


# ----------------------------
# Data Load / Index
# ----------------------------
JSON_FILE = Path(__file__).parent / "inverter_fault_codes_formatted.json"
EQUIP_NAME_MAP = {"AFE Inverter": "AFE", "DC-DC Converter": "DC-DC", "Grid Inverter": "Grid"}
UI_EQUIPMENTS = ["AFE", "DC-DC", "Grid"]

def parse_to_code_only(text: str | None) -> str | None:
    if not text: return None
    m = re.findall(r"\bF\d+\b", text.upper())
    return m[-1] if m else None

def load_faults() -> dict[str, dict[str, dict]]:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        rows = json.load(f)
    faults: dict[str, dict[str, dict]] = {"AFE": {}, "DC-DC": {}, "Grid": {}}
    for r in rows:
        inv = (r.get("Inverter_Name") or "").strip()
        equip = EQUIP_NAME_MAP.get(inv)
        full = (r.get("Fault_Code") or "").strip()
        code = parse_to_code_only(full)
        if not (equip and code): continue
        faults[equip][code] = {
            "equipment": equip, "code": code, "fault_code_full": full,
            "description": (r.get("Description") or "").strip(),
            "causes": (r.get("Possible_Causes") or "").strip(),
            "fixes": (r.get("Recommended_Fixes") or "").strip(),
        }
    return faults

FAULTS = load_faults()

# ----------------------------
# Helpers
# ----------------------------
def normalize_user_input_code(s: str) -> str | None:
    if not s: return None
    s = s.strip().upper()
    code = parse_to_code_only(s)
    return code or (f"F{s}" if s.isdigit() else s)

def bullets_from_text(s: str) -> list[str]:
    if not s: return []
    parts = re.split(r"[;\.\n]+", s)
    out = []
    for p in parts:
        t = " ".join(p.strip().split())
        if t:
            t = re.sub(r"\b(\w+)\s+\1\b", r"\1", t, flags=re.IGNORECASE)
            out.append(t)
    return out

def reset_state():
    for k in list(st.session_state.keys()):
        if k.startswith("fc_"):
            del st.session_state[k]

def show_result(entry: dict):
    st.success(f"Found {entry['code']} in {entry['equipment']}")
    # Glass panel for guaranteed readability
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    if entry.get("description"):
        st.markdown(f"**Description**: {entry['description']}")
    causes = bullets_from_text(entry.get("causes", ""))
    fixes  = bullets_from_text(entry.get("fixes",  ""))
    if causes:
        st.markdown("**Possible causes:**")
        for c in causes: st.markdown(f"- {c}")
    if fixes:
        st.markdown("**Recommended fixes:**")
        for fx in fixes: st.markdown(f"- {fx}")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# Header
# ----------------------------
st.markdown('<div class="app-title">EBOSS® Fault Code Lookup</div>', unsafe_allow_html=True)
st.markdown('<div class="muted">Select equipment, enter a code (e.g., F91), then Search.</div>', unsafe_allow_html=True)
st.write("")

# ============================================================
# 🟦 BLUE — Equipment / Fault Code / Search
# ============================================================
with st.form("fc_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1:
        selected = st.selectbox("Equipment", UI_EQUIPMENTS, key="fc_equipment")
    with c2:
        user_code_raw = st.text_input("Fault Code", placeholder="e.g., F91", key="fc_code_raw")
    submitted = st.form_submit_button("Search")

# Search behavior
if submitted:
    code = normalize_user_input_code(user_code_raw)
    if not code:
        st.error("Please enter a fault code (e.g., F91).")
    else:
        primary = FAULTS.get(selected, {}).get(code)
        alts = []
        if not primary:
            for equip, table in FAULTS.items():
                if equip != selected and code in table:
                    alts.append(table[code])
        if primary:
            st.session_state["fc_result"] = primary
            st.session_state["fc_show_modal"] = False
        elif alts:
            st.session_state["fc_alt_matches"] = alts
            st.session_state["fc_alt_prompt"] = (
                f"Fault code {code} was not found in {selected}, "
                f"but it exists in: {', '.join(sorted({a['equipment'] for a in alts}))}."
            )
            st.session_state["fc_show_modal"] = True
            st.session_state.pop("fc_result", None)
        else:
            reset_state()
            st.warning(f"No results found for {code} in any dictionary.")

# ============================================================
# 🟥 RED — Modal/Expander header
#      contains:
#        🟨 YELLOW — info message
#        🟩 GREEN  — radio & buttons
# ============================================================
if st.session_state.get("fc_show_modal"):
    with modal_ctx("Found in a different equipment"):
        # 🟨 YELLOW — info
        st.info(st.session_state.get("fc_alt_prompt", "Match found elsewhere."))
        # 🟩 GREEN — radio + actions
        options = st.session_state.get("fc_alt_matches", [])
        label_map = {f"{e['equipment']} – {e['fault_code_full']}": i for i, e in enumerate(options)}
        choice_label = st.radio("Choose which one to view:", list(label_map.keys()), index=0)
        cA, cB = st.columns(2)
        if cA.button("Yes, show it"):
            st.session_state["fc_result"] = options[idx]
            st.session_state["fc_show_modal"] = False
            safe_rerun()

        if cB.button("Cancel"):
            reset_state()  # clears fc_* including fc_show_modal
            safe_rerun()

# ----------------------------
# Result rendering
# ----------------------------
if st.session_state.get("fc_result"):
    show_result(st.session_state["fc_result"])

# Tip
st.caption("Tip: You can type just the number (e.g., 91) or 'F91'. Case-insensitive.")
