# app.py
from __future__ import annotations
import io
import json
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import base64
import requests
import streamlit as st

st.set_page_config(page_title="EBOSS® Falt Code Lookup", layout="centered")



def to_data_uri(url: str) -> str:
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    mime = r.headers.get("Content-Type", "image/png").split(";")[0]
    b64 = base64.b64encode(r.content).decode("utf-8")
    return f"data:{mime};base64,{b64}"

BG_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/AdobeStock_209254754.jpeg"
LOGO_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"

BG_DATA = to_data_uri(BG_URL)
LOGO_DATA = to_data_uri(LOGO_URL)

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
  background-image: url('{BG_DATA}');
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  background-attachment: fixed;
}}
.block-container {{ background: none !important; }}
[data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
[data-testid="stSidebar"] > div:first-child {{ background: rgba(0,0,0,0) !important; }}

.app-title {{ font-size: 1.8rem; font-weight: 700; margin-bottom: .25rem; text-shadow: 0 2px 8px rgba(0,0,0,.45); }}
.muted {{ color: #eaeaea; text-shadow: 0 1px 4px rgba(0,0,0,.35); }}

.logo-wrap {{
  display: flex; align-items: center; justify-content: center;
  margin: 0.25rem 0 0.75rem 0;
}}
.logo-wrap img {{
  max-width: min(420px, 70vw);
  height: auto;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,.45));
}}
</style>

<div class="logo-wrap">
  <img src="{LOGO_DATA}" alt="Alliance North America logo">
</div>
""", unsafe_allow_html=True)

#
# st.markdown("""
 #   <style>
 #   /* Remove border from the outer container of your form section */
 #   div[data-testid="stForm"] {
 #       border: none !important;      /* Remove any border */
 #       box-shadow: none !important;  /* Remove any shadow if applied */
 #       background-color: #000000 !important; /* Optional: make background transparent */
 #       padding: 0 !important;        /* Reset container padding */
 #       margin: 0 !important;         /* Reset container margin */
 #   }
 #   </style>
# """, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* Main selectbox container */
    div[data-baseweb="select"] > div {
        background-color: #000000; /* Black background */
        border: 2px solid #939598; /* Light grey border */
        color: #FFFFFF; /* Alpine white text */
        Height: Auto;
        font-family: Arial, sans-serif;
        font-weight: bold;
        border-radius: 6px;
        padding: 1px;
    }
    
    /* Hover effect on selectbox */
    div[data-baseweb="select"] > div:hover {
        border-color: #80BD47; /* Energy green border */
        box-shadow: 0 0 12px #80BD47; /* Glow effect */
    }

    /* Dropdown arrow icon */
    div[data-baseweb="select"] svg {
        fill: #FFFFFF; /* Alpine white arrow */
    }

    /* Dropdown menu background */
    div[data-baseweb="select"] ul {
        background-color: #000000; /* Black menu */
        color: #FFFFFF; /* Alpine white text */
    }

    /* Option hover effect */
    div[data-baseweb="select"] li:hover {
        background-color: #000000;
        color: #FFFFFF;
        box-shadow: 0 0 30px #80BD47; /* Energy green glow */
   }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    /* Base style for text input */
    input[type="text"] {
        background-color: #000000; /* Black background */
        color: #FFFFFF;           /* White text */
        font-family: Arial, sans-serif;
        font-weight: bold;
        border: 2px solid #939598, !important;
        border-radius: 6px;
        padding: 1px, !important;
        height: 42px, !important;
        box-sizing: border-box; /* Include padding/border in height */
    }

    /* Placeholder text */
    input[type="text"]::placeholder {
        color: #CCCCCC; /* Light grey placeholder */
        font-weight: normal;
    }

    /* Hover effect */
    input[type="text"]:hover {
        box-shadow: 0 0 30px #80BD47; /* Energy green glow */
    }
    </style>
""", unsafe_allow_html=True)



# -------------------- Compat helpers --------------------
def _has(attr: str) -> bool:
    return callable(getattr(st, attr, None))

def safe_rerun():
    """Use st.rerun() if available, else st.experimental_rerun()."""
    if _has("rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

@contextmanager
def modal_ctx(title: str):
    """Real modal on newer Streamlit; expander fallback on older."""
    if _has("modal"):
        with st.modal(title):
            yield
    else:
        with st.expander(f"🔎 {title}", expanded=True):
            yield

# -------------------- Data sources / constants --------------------
UI_EQUIPMENTS = ["AFE", "DC-DC", "Grid"]
EQUIP_NAME_MAP = {  # formatted JSON -> UI label
    "AFE Inverter": "AFE",
    "DC-DC Converter": "DC-DC",
    "Grid Inverter": "Grid",
}

LOCAL_CANDIDATES = [
    Path.cwd() / "inverter_fault_codes_formatted.json",
    Path(__file__).parent / "inverter_fault_codes_formatted.json",
    Path.cwd() / "data" / "inverter_fault_codes_formatted.json",
    Path.cwd() / "inverter_fault_codes.json",
    Path(__file__).parent / "inverter_fault_codes.json",
    Path.cwd() / "data" / "inverter_fault_codes.json",
]

REMOTE_CANDIDATES = [
    # formatted preferred
    "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/inverter_fault_codes_formatted.json",
    "https://raw.githubusercontent.com/TimBuffington/troubleshooting/main/inverter_fault_codes_formatted.json",
    # original fallback
    "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/inverter_fault_codes.json",
    "https://raw.githubusercontent.com/TimBuffington/troubleshooting/main/inverter_fault_codes.json",
]

# -------------------- Utilities --------------------
def parse_to_code_only(text: Optional[str]) -> Optional[str]:
    """Pull 'Fxx' from strings like 'AFE F91'."""
    if not text:
        return None
    m = re.findall(r"\bF\d+\b", text.upper())
    return m[-1] if m else None

def normalize_user_input_code(s: str) -> Optional[str]:
    """Accept 'F91', '  f 91', or '91' -> 'F91'."""
    if not s:
        return None
    s = s.strip().upper()
    code = parse_to_code_only(s)
    if code:
        return code
    if s.isdigit():
        return f"F{s}"
    return s

def bullets_from_text(s: str) -> List[str]:
    """Turn semi-structured text into bullets."""
    if not s:
        return []
    parts = re.split(r"[;\.\n]+", s)
    items = []
    for p in parts:
        t = " ".join(p.strip().split())
        if t:
            t = re.sub(r"\b(\w+)\s+\1\b", r"\1", t, flags=re.IGNORECASE)
            items.append(t)
    return items

def try_load_local() -> Optional[List[dict]]:
    for p in LOCAL_CANDIDATES:
        try:
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            continue
    return None

def try_load_remote() -> Optional[List[dict]]:
    for url in REMOTE_CANDIDATES:
        try:
            r = requests.get(url, timeout=10)
            if r.ok:
                return r.json()
        except Exception:
            continue
    return None

def parse_rows_to_faults(rows: List[dict]) -> Dict[str, Dict[str, dict]]:
    """
    Supports:
      - formatted schema: Inverter_Name, Fault_Code, Description, Possible_Causes, Recommended_Fixes
      - original schema:  "Fault Code", "Description" (combined narrative)
    """
    faults: Dict[str, Dict[str, dict]] = {"AFE": {}, "DC-DC": {}, "Grid": {}}

    for r in rows:
        # formatted?
        inv_name = (r.get("Inverter_Name") or "").strip()
        fault_code_full = (r.get("Fault_Code") or "").strip()

        if inv_name and fault_code_full:
            ui_equip = EQUIP_NAME_MAP.get(inv_name)
            code = parse_to_code_only(fault_code_full)
            if not (ui_equip and code):
                continue
            entry = {
                "equipment": ui_equip,
                "code": code,
                "fault_code_full": fault_code_full,
                "description": (r.get("Description") or "").strip(),
                "causes": (r.get("Possible_Causes") or "").strip(),
                "fixes": (r.get("Recommended_Fixes") or "").strip(),
            }
            faults[ui_equip][code] = entry
            continue

        # original?
        fault_code_full = (r.get("Fault Code") or "").strip()
        if fault_code_full:
            code = parse_to_code_only(fault_code_full)
            if not code:
                continue
            if fault_code_full.startswith("AFE"):
                ui_equip = "AFE"
            elif fault_code_full.startswith("DC-DC"):
                ui_equip = "DC-DC"
            elif fault_code_full.startswith("Grid Inverter"):
                ui_equip = "Grid"
            else:
                continue

            desc = (r.get("Description") or "").strip()
            entry = {
                "equipment": ui_equip,
                "code": code,
                "fault_code_full": fault_code_full,
                "description": desc,  # may contain causes/fixes in prose
                "causes": "",
                "fixes": "",
            }
            faults[ui_equip][code] = entry

    return faults

def load_faults_with_fallback() -> Tuple[Optional[Dict[str, Dict[str, dict]]], str]:
    # 1) local
    rows = try_load_local()
    if rows is not None:
        return parse_rows_to_faults(rows), "local"
    # 2) remote
    rows = try_load_remote()
    if rows is not None:
        return parse_rows_to_faults(rows), "remote"
    # 3) ask user to upload
    return None, "missing"

def find_fault(faults: Dict[str, Dict[str, dict]], selected_equip: str, code: str):
    """Search selected equipment first; then others."""
    primary = faults.get(selected_equip, {}).get(code)
    alts = []
    if not primary:
        for equip, table in faults.items():
            if equip == selected_equip:
                continue
            if code in table:
                alts.append(table[code])
    return primary, alts

def show_result(entry: dict):
    st.success(f"Found {entry['code']} in {entry['equipment']}")
    if entry.get("description"):
        st.markdown(f"**Description**: {entry['description']}")
    causes = bullets_from_text(entry.get("causes", ""))
    fixes  = bullets_from_text(entry.get("fixes", ""))

    if causes:
        st.markdown("**Possible causes:**")
        for c in causes:
            st.markdown(f"- {c}")
    if fixes:
        st.markdown("**Recommended fixes:**")
        for fx in fixes:
            st.markdown(f"- {fx}")

def reset_state():
    for k in list(st.session_state.keys()):
        if k.startswith("fc_"):
            del st.session_state[k]

# -------------------- Load data --------------------
FAULTS, data_origin = load_faults_with_fallback()

if FAULTS is None:
    st.error("Fault code data file not found locally or remotely.")
    up = st.file_uploader("Upload inverter fault JSON", type=["json"])
    if up:
        try:
            rows = json.load(io.StringIO(up.getvalue().decode("utf-8")))
            FAULTS = parse_rows_to_faults(rows)
            data_origin = "uploaded"
            st.success("Loaded data from uploaded file.")
        except Exception as e:
            st.exception(e)

# -------------------- UI --------------------
st.markdown('<div class="app-title">EBOSS&reg Fault Code Lookup</div>', unsafe_allow_html=True)
st.markdown('<div class="muted">Select equipment, enter a code (e.g., F91), then Search.</div>', unsafe_allow_html=True)
st.write("")

if FAULTS:
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
            primary, alts = find_fault(FAULTS, selected, code)
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

    # --- Modal / fallback expander ---
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

    # Render result
    if "fc_result" in st.session_state:
        show_result(st.session_state["fc_result"])
        st.write("")
        if st.button("Clear"):
            reset_state()
            safe_rerun()
        st.caption("Tip: you can type just the number (e.g., 91) or 'F91'.")


# --- Mobile-first responsive tweaks ---
st.markdown("""
<style>
/* 1) General mobile layout improvements */
@media (max-width: 700px) {
  /* Make the app content breathe on small screens */
  .block-container { padding: 0.75rem 0.75rem !important; }

  /* Stack Streamlit columns vertically and ensure full width */
  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    flex: 1 1 100% !important;
    width: 100% !important;
    min-width: 100% !important;
  }

  /* Full-width inputs/buttons for easier tapping */
  .stButton > button,
  input[type="text"],
  div[data-baseweb="select"] > div {
    width: 100% !important;
  }

  /* Slightly smaller title to prevent wrapping */
  .app-title { font-size: 1.4rem !important; line-height: 1.25 !important; }
}

/* 2) Improve tap targets across devices */
.stButton > button,
input[type="text"],
div[data-baseweb="select"] > div {
  min-height: 44px; /* iOS/Android recommended minimum */
}

/* 3) Avoid dropdown going off-screen; make it scrollable */
@media (max-width: 700px) {
  div[data-baseweb="select"] ul {
    max-height: 50vh !important;
    overflow-y: auto !important;
  }
}

/* 4) Better radio/selectable items for touch */
[role="radiogroup"] label, [role="menuitem"] {
  padding: 6px 8px;
  border-radius: 8px;
}

/* 5) Prevent background jank on mobile (fixed -> scroll) */
@media (max-width: 700px) {
  [data-testid="stAppViewContainer"] {
    background-attachment: scroll !important;
    background-position: center top !important;
  }
}
</style>
""", unsafe_allow_html=True)
