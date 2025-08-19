import streamlit as st
import requests
import base64
import json
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from contextlib import contextmanager

# Set page configuration
st.set_page_config(page_title="EBOSS® Fault Code Lookup", layout="centered")

# -------------------- Helper Functions --------------------
def to_data_uri(url: str) -> str:
    """Convert an image URL to a data URI."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        mime = response.headers.get("Content-Type", "image/png").split(";")[0]
        b64 = base64.b64encode(response.content).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""

# Load images
BG_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/AdobeStock_209254754.jpeg"
LOGO_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"
BG_DATA = to_data_uri(BG_URL)
LOGO_DATA = to_data_uri(LOGO_URL)

# Apply CSS styling
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
.logo-wrap {{ display: flex; align-items: center; justify-content: center; margin: 0.25rem 0 0.75rem 0; }}
.logo-wrap img {{ max-width: min(420px, 70vw); height: auto; filter: drop-shadow(0 4px 12px rgba(0,0,0,.45)); }}

div[data-testid="stForm"] {{ border: none !important; box-shadow: none !important; background-color: transparent; padding: 0 !important; margin: 0 !important; }}

div[data-baseweb="select"] > div {{
    background-color: #000000; border: 2px solid #939598; color: #FFFFFF; font-family: Arial, sans-serif; font-weight: bold; border-radius: 6px; padding: 1px;
}}
div[data-baseweb="select"] > div:hover {{ border-color: #80BD47; box-shadow: 0 0 12px #80BD47; }}
div[data-baseweb="select"] svg {{ fill: #FFFFFF; }}
div[data-baseweb="select"] ul {{ background-color: #000000; color: #FFFFFF; }}
div[data-baseweb="select"] li:hover {{ background-color: #000000; color: #FFFFFF; box-shadow: 0 0 30px #80BD47; }}

input[type="text"] {{
    background-color: #000000; color: #FFFFFF; font-family: Arial, sans-serif; font-weight: bold; border: 2px solid #939598 !important; border-radius: 6px; padding: 1px !important; height: 42px !important; box-sizing: border-box;
}}
input[type="text"]::placeholder {{ color: #CCCCCC; font-weight: normal; }}
input[type="text"]:hover {{ box-shadow: 0 0 30px #80BD47; }}

@media (max-width: 700px) {{
    .block-container {{ padding: 0.75rem 0.75rem !important; }}
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{ flex: 1 1 100% !important; width: 100% !important; min-width: 100% !important; }}
    .stButton > button, input[type="text"], div[data-baseweb="select"] > div {{ width: 100% !important; }}
    .app-title {{ font-size: 1.4rem !important; line-height: 1.25 !important; }}
    div[data-baseweb="select"] ul {{ max-height: 50vh !important; overflow-y: auto !important; }}
    [data-testid="stAppViewContainer"] {{ background-attachment: scroll !important; background-position: center top !important; }}
}}

.stButton > button, input[type="text"], div[data-baseweb="select"] > div {{ min-height: 44px; }}
[role="radiogroup"] label, [role="menuitem"] {{ padding: 6px 8px; border-radius: 8px; }}
</style>
<div class="logo-wrap"><img src="{LOGO_DATA}" alt="Alliance North America logo"></div>
""", unsafe_allow_html=True)

# -------------------- Compatibility Helpers --------------------
def safe_rerun():
    """Use st.rerun() if available, else st.experimental_rerun()."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

@contextmanager
def modal_ctx(title: str):
    """Use modal if available, else fallback to expander."""
    if hasattr(st, "modal"):
        with st.modal(title):
            yield
    else:
        with st.expander(f"🔎 {title}", expanded=True):
            yield

# -------------------- Data Handling --------------------
UI_EQUIPMENTS = ["AFE", "DC-DC", "Grid"]
EQUIP_NAME_MAP = {
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
    "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/inverter_fault_codes_formatted.json",
    "https://raw.githubusercontent.com/TimBuffington/troubleshooting/main/inverter_fault_codes_formatted.json",
    "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/inverter_fault_codes.json",
    "https://raw.githubusercontent.com/TimBuffington/troubleshooting/main/inverter_fault_codes.json",
]

def parse_to_code_only(text: Optional[str]) -> Optional[str]:
    """Extract 'Fxx' from strings like 'AFE F91'."""
    if not text:
        return None
    matches = re.findall(r"\bF\d+\b", text.upper())
    return matches[-1] if matches else None

def normalize_user_input_code(s: str) -> Optional[str]:
    """Normalize input to 'Fxx' format."""
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
    """Convert text into bullet points."""
    if not s:
        return []
    parts = re.split(r"[;\.\n]+", s)
    items = []
    for part in parts:
        text = " ".join(part.strip().split())
        if text:
            text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
            items.append(text)
    return items

def try_load_local() -> Optional[List[dict]]:
    """Attempt to load fault data from local files."""
    for path in LOCAL_CANDIDATES:
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            continue
    return None

def try_load_remote() -> Optional[List[dict]]:
    """Attempt to load fault data from remote URLs."""
    for url in REMOTE_CANDIDATES:
        try:
            response = requests.get(url, timeout=10)
            if response.ok:
                return response.json()
        except Exception:
            continue
    return None

def parse_rows_to_faults(rows: List[dict]) -> Dict[str, Dict[str, dict]]:
    """Parse JSON rows into fault dictionary."""
    faults: Dict[str, Dict[str, dict]] = {"AFE": {}, "DC-DC": {}, "Grid": {}}
    for row in rows:
        inv_name = (row.get("Inverter_Name") or "").strip()
        fault_code_full = (row.get("Fault_Code") or "").strip()
        if inv_name and fault_code_full:
            ui_equip = EQUIP_NAME_MAP.get(inv_name)
            code = parse_to_code_only(fault_code_full)
            if not (ui_equip and code):
                continue
            faults[ui_equip][code] = {
                "equipment": ui_equip,
                "code": code,
                "fault_code_full": fault_code_full,
                "description": (row.get("Description") or "").strip(),
                "causes": (row.get("Possible_Causes") or "").strip(),
                "fixes": (row.get("Recommended_Fixes") or "").strip(),
            }
        else:
            fault_code_full = (row.get("Fault Code") or "").strip()
            if fault_code_full:
                code = parse_to_code_only(fault_code_full)
                if not code:
                    continue
                ui_equip = None
                if fault_code_full.startswith("AFE"):
                    ui_equip = "AFE"
                elif fault_code_full.startswith("DC-DC"):
                    ui_equip = "DC-DC"
                elif fault_code_full.startswith("Grid Inverter"):
                    ui_equip = "Grid"
                if ui_equip:
                    faults[ui_equip][code] = {
                        "equipment": ui_equip,
                        "code": code,
                        "fault_code_full": fault_code_full,
                        "description": (row.get("Description") or "").strip(),
                        "causes": "",
                        "fixes": "",
                    }
    return faults

def load_faults_with_fallback() -> Tuple[Optional[Dict[str, Dict[str, dict]]], str]:
    """Load fault data with local, remote, or upload fallback."""
    if rows := try_load_local():
        return parse_rows_to_faults(rows), "local"
    if rows := try_load_remote():
        return parse_rows_to_faults(rows), "remote"
    return None, "missing"

def find_fault(faults: Dict[str, Dict[str, dict]], equipment: str, code: str) -> Tuple[Optional[dict], List[dict]]:
    """Find fault in selected equipment, then others."""
    primary = faults.get(equipment, {}).get(code)
    alternatives = []
    if not primary:
        for equip, table in faults.items():
            if equip != equipment and code in table:
                alternatives.append(table[code])
    return primary, alternatives

def show_result(entry: dict):
    """Display fault code details."""
    st.success(f"Found {entry['code']} in {entry['equipment']}")
    if entry.get("description"):
        st.markdown(f"**Description**: {entry['description']}")
    causes = bullets_from_text(entry.get("causes", ""))
    fixes = bullets_from_text(entry.get("fixes", ""))
    if causes:
        st.markdown("**Possible causes:**")
        for cause in causes:
            st.markdown(f"- {cause}")
    if fixes:
        st.markdown("**Recommended fixes:**")
        for fix in fixes:
            st.markdown(f"- {fix}")

def reset_state():
    """Clear session state keys related to fault codes."""
    for key in list(st.session_state.keys()):
        if key.startswith("fc_"):
            del st.session_state[key]

# -------------------- Main App Logic --------------------
faults, data_origin = load_faults_with_fallback()

if faults is None:
    st.error("Fault code data file not found locally or remotely.")
    uploaded_file = st.file_uploader("Upload inverter fault JSON", type=["json"])
    if uploaded_file:
        try:
            rows = json.load(uploaded_file)
            faults = parse_rows_to_faults(rows)
            data_origin = "uploaded"
            st.success("Loaded data from uploaded file.")
        except Exception as e:
            st.error(f"Error loading file: {e}")

if faults:
    st.markdown('<div class="app-title">EBOSS&reg Fault Code Lookup</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Select equipment, enter a code (e.g., F91), then Search.</div>', unsafe_allow_html=True)
    st.write("")

    with st.form("fc_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            selected_equipment = st.selectbox("Equipment", UI_EQUIPMENTS, key="fc_equipment")
        with col2:
            user_code_raw = st.text_input("Fault Code", placeholder="e.g., F91", key="fc_code_raw")
        submitted = st.form_submit_button("Search")

    if submitted:
        code = normalize_user_input_code(user_code_raw)
        if not code:
            st.error("Please enter a fault code (e.g., F91).")
        else:
            primary, alternatives = find_fault(faults, selected_equipment, code)
            if primary:
                st.session_state["fc_result"] = primary
                st.session_state["fc_show_modal"] = False
            elif alternatives:
                st.session_state["fc_alt_matches"] = alternatives
                st.session_state["fc_alt_prompt"] = (
                    f"Fault code {code} was not found in {selected_equipment}, "
                    f"but it exists in: {', '.join(sorted({a['equipment'] for a in alternatives}))}."
                )
                st.session_state["fc_show_modal"] = True
                if "fc_result" in st.session_state:
                    del st.session_state["fc_result"]
            else:
                reset_state()
                st.warning(f"No results found for {code} in any dictionary.")

    if st.session_state.get("fc_show_modal"):
        with modal_ctx("Found in a different equipment"):
            st.info(st.session_state.get("fc_alt_prompt", "Match found elsewhere."))
            options = st.session_state.get("fc_alt_matches", [])
            label_map = {f"{e['equipment']} – {e['fault_code_full']}": i for i, e in enumerate(options)}
            choice_label = st.radio("Choose which one to view:", list(label_map.keys()), index=0)

            col_a, col_b = st.columns(2)
            if col_a.button("Yes, show it"):
                idx = label_map[choice_label]
                st.session_state["fc_result"] = options[idx]
                st.session_state["fc_show_modal"] = False
                safe_rerun()
            if col_b.button("Cancel"):
                reset_state()
                safe_rerun()

    if "fc_result" in st.session_state:
        show_result(st.session_state["fc_result"])
        st.write("")
        if st.button("Clear"):
            reset_state()
            safe_rerun()
        st.caption("Tip: you can type just the number (e.g., 91) or 'F91'.")
```

