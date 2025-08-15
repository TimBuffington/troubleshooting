# app.py
from __future__ import annotations
import json
import re
from pathlib import Path
import streamlit as st

from contextlib import contextmanager
import streamlit as st

def _has(attr: str) -> bool:
    return callable(getattr(st, attr, None))

@contextmanager
def modal_ctx(title: str):
    """Use real modal if available; otherwise fall back to an expander."""
    if _has("modal"):
        with st.modal(title):
            yield
    else:
        with st.expander(f"🔎 {title}", expanded=True):
            yield

def safe_rerun():
    # Works on older and newer Streamlit
    if _has("rerun"):
        safe_rerun()
    else:
        safe_rerun()
# Background image URL (GitHub raw)
BG_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/AdobeStock_209254754.jpeg"
# Company logo (centered near the top)
LOGO_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"

st.markdown(f"""
<style>
.logo-wrap {{
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0.25rem 0 0.75rem 0;   /* tight to the top */
}}
.logo-wrap img {{
  max-width: min(420px, 70vw);
  height: auto;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,.45)); /* legibility over photo */
}}
</style>

<div class="logo-wrap">
  <img src="{LOGO_URL}" alt="Alliance North America logo">
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
  background-image: url('{BG_URL}');
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  background-attachment: fixed;
}}

.block-container {{
  background: transparent !important;
}}

[data-testid="stHeader"] {{
  background: rgba(0,0,0,0) !important;
}}

[data-testid="stSidebar"] > div:first-child {{
  background: rgba(0,0,0,0) !important;
}}

.app-title {{ text-shadow: 0 2px 8px rgba(0,0,0,.45); }}
.muted {{ text-shadow: 0 1px 4px rgba(0,0,0,.35); }}
</style>
""", unsafe_allow_html=True)


st.set_page_config(page_title="Fault Code Finder", page_icon="🛠️", layout="centered")

# ---------------------------------------
# Config / constants
# ---------------------------------------
JSON_FILE = Path(__file__).parent / "inverter_fault_codes_formatted.json"

# Map Inverter_Name -> UI equipment label
EQUIP_NAME_MAP = {
    "AFE Inverter": "AFE",
    "DC-DC Converter": "DC-DC",
    "Grid Inverter": "Grid",
}

UI_EQUIPMENTS = ["AFE", "DC-DC", "Grid"]


# ---------------------------------------
# Load & index data
# ---------------------------------------
def load_faults():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        rows = json.load(f)

    # faults_by_equip[equip]["F91"] = entry dict
    faults_by_equip: dict[str, dict[str, dict]] = {"AFE": {}, "DC-DC": {}, "Grid": {}}

    for r in rows:
        inv_name = r.get("Inverter_Name", "").strip()
        ui_equip = EQUIP_NAME_MAP.get(inv_name)
        fault_code_full = (r.get("Fault_Code") or "").strip()  # e.g., "AFE F91", "Grid Inverter F2", etc.

        # Extract trailing "Fxx" token so user can just type "F91"
        code_only = parse_to_code_only(fault_code_full)  # -> "F91" or None
        if not (ui_equip and code_only):
            continue

        # Store canonical record with nice fields
        entry = {
            "equipment": ui_equip,
            "code": code_only,  # "F91"
            "fault_code_full": fault_code_full,  # original text
            "description": (r.get("Description") or "").strip(),
            "causes": (r.get("Possible_Causes") or "").strip(),
            "fixes": (r.get("Recommended_Fixes") or "").strip(),
        }
        faults_by_equip[ui_equip][code_only] = entry

    return faults_by_equip


def parse_to_code_only(text: str | None) -> str | None:
    """Return the last token that looks like an 'F' code, e.g. 'F1', 'F91'."""
    if not text:
        return None
    # Accept 'F91', 'f91', possibly with punctuation/spaces
    m = re.findall(r"\bF\d+\b", text.upper())
    return m[-1] if m else None


FAULTS = load_faults()


# ---------------------------------------
# Helpers
# ---------------------------------------
def normalize_user_input_code(s: str) -> str | None:
    """Handle inputs like 'F91', ' f 91 ', 'AFE F91', etc -> 'F91'."""
    if not s:
        return None
    s = s.strip().upper()
    # If they typed 'AFE F91' etc, pull just the trailing F-code:
    code = parse_to_code_only(s)
    if code:
        return code
    # Fallback: if they only typed digits, prepend F
    if s.isdigit():
        return f"F{s}"
    return s  # as-is if they typed 'F91' already


def find_fault(selected_equip: str, code: str):
    """Search selected equipment first; if not found, search others."""
    primary = FAULTS.get(selected_equip, {}).get(code)
    alts = []
    if not primary:
        for equip, table in FAULTS.items():
            if equip == selected_equip:
                continue
            if code in table:
                alts.append(table[code])
    return primary, alts


def bullets_from_text(s: str) -> list[str]:
    """Turn a semi-structured sentence string into bullet items."""
    if not s:
        return []
    # Split on periods/semicolons/newlines; keep short/clean items
    parts = re.split(r"[;\.\n]+", s)
    items = []
    for p in parts:
        t = " ".join(p.strip().split())
        if t:
            # De-duplicate accidental doubled words like "Check Check"
            t = re.sub(r"\b(\w+)\s+\1\b", r"\1", t, flags=re.IGNORECASE)
            items.append(t)
    return items


def reset_state():
    for k in list(st.session_state.keys()):
        if k.startswith("fc_"):
            del st.session_state[k]


def show_result(entry: dict):
    st.success(f"Found {entry['code']} in {entry['equipment']}")
    with st.container(border=True):
        if entry.get("description"):
            st.markdown(f"**Description**: {entry['description']}")
        causes = bullets_from_text(entry.get("causes", ""))
        fixes = bullets_from_text(entry.get("fixes", ""))

        if causes:
            st.markdown("**Possible causes:**")
            for c in causes:
                st.markdown(f"- {c}")

        if fixes:
            st.markdown("**Recommended fixes:**")
            for fx in fixes:
                st.markdown(f"- {fx}")


# ---------------------------------------
# UI
# ---------------------------------------
st.markdown(f"""
    <style>
    .app-title 
    font-size: 1.8rem; 
    font-weight: 700; 
    margin-bottom: .25rem;
    )
    (
    .muted
    color: #666;
    )
    (
    .stButton > button
    border-radius: 10px;
    padding: 0.5rem 1rem;
    </style>
    """, unsafe_allow_html=True,
)

st.markdown('<div class="app-title">🛠️ Fault Code Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="muted">Select equipment, enter a code (e.g., F91), then Search.</div>', unsafe_allow_html=True)
st.write("")

with st.form("fc_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    with c1:
        selected = st.selectbox("Equipment", UI_EQUIPMENTS, key="fc_equipment")
    with c2:
        user_code_raw = st.text_input("Fault Code", placeholder="e.g., F91", key="fc_code_raw")

    submitted = st.form_submit_button("Search")

if submitted:
    code = normalize_user_input_code(user_code_raw)
    if not code:
        st.error("Please enter a fault code (e.g., F91).")
    else:
        primary, alts = find_fault(selected, code)
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
            if "fc_result" in st.session_state:
                del st.session_state["fc_result"]
        else:
            reset_state()
            st.warning(f"No results found for {code} in any dictionary.")

# Modal when found in different equipment
if st.session_state.get("fc_show_modal"):
    with modal_ctx("Found in a different equipment"):
    st.info(st.session_state.get("fc_alt_prompt", "Match found elsewhere."))
    options = st.session_state.get("fc_alt_matches", [])
    label_map = {f"{e['equipment']} – {e['fault_code_full']}": i for i, e in enumerate(options)}
    choice_label = st.radio("Choose which one to view:", list(label_map.keys()), index=0)
    cA, cB = st.columns(2)
    if cA.button("Yes, show it"):
        idx = label_map[choice_label]
        st.session_state["fc_result"] = options[idx]
        st.session_state["fc_show_modal"] = False
        safe_rerun()
    if cB.button("Cancel"):
        reset_state()
        safe_rerun()



# Render result if present
if "fc_result" in st.session_state:
    show_result(st.session_state["fc_result"])
    st.write("")
    if st.button("Clear"):
        reset_state()
        safe_rerun()

# Tiny tip
st.caption("Tip: You can type just the number (e.g., 91) or 'F91'. Case-insensitive.")
