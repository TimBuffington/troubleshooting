
import json, re
import streamlit as st

st.markdown(
    """
    <style>
    .stApp {
      background-image: url('https://raw.githubusercontent.com/timbuffington/troubleshoot/main/assets/AdobeStock_209254754.jpeg');
      background-size: cover;
      background-position: center center;
      background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)
LOGO_URL = "https://raw.githubusercontent.com/timbuffington/troubleshoot/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"

st.markdown(
    f"""
    <style>
    /* Container to center the logo */
    .logo-container {{
        display: flex;
        justify-content: center; /* horizontal center */
        align-items: center;     /* vertical center */
        margin-bottom: 20px;
        background-color: rgba(0, 0, 0, 0.4); /* optional backdrop to make white logo visible */
        padding: 10px;
        border-radius: 8px;
    }}
    /* Style for the logo image */
    .logo-container img {{
        max-width: 300px;   /* scale down if large */
        height: auto;
    }}
    </style>

    <div class="logo-container">
        <img src="{LOGO_URL}" alt="ANA Energy Logo">
    </div>
    """,
    unsafe_allow_html=True
)

st.set_page_config(page_title="EBOSS® Inverter Fault Lookup", layout="centered")

@st.cache_data
def load_data(path: str):
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    # Normalize: add 'Device' from prefix, build index
    for r in rows:
        code = r.get("Fault Code", "").strip()
        dev = "Any"
        up = code.upper()
        if up.startswith("AFE"): dev = "AFE"
        elif up.startswith("DC-DC") or up.startswith("DCDC"): dev = "DC-DC"
        elif up.startswith("GRID INVERTER"): dev = "Grid Inverter"
        r["Device"] = dev
        r["_UCODE"] = up  # cached uppercase
    idx = {r["_UCODE"]: r for r in rows}
    return rows, idx

rows, idx = load_data("inverter_fault_codes.json")

st.title("EBOSS® Inverter Fault Lookup")
st.caption("Quick search for **AFE**, **DC-DC**, and **Grid Inverter** fault descriptions.")

# ---- Filters & Inputs
col1, col2 = st.columns([1, 2])
with col1:
    device = st.selectbox("Device", ["Any", "AFE", "DC-DC", "Grid Inverter"])
with col2:
    code_input = st.text_input("Fault Code (e.g., AFE F1, DC-DC F80, Grid Inverter F92)").strip()

# Optional selectable list of codes based on device filter
with st.expander("Browse known fault codes"):
    if device == "Any":
        codes = [r["Fault Code"] for r in rows]
    else:
        codes = [r["Fault Code"] for r in rows if r["Device"] == device]
    sel = st.selectbox("Select a code", ["--"] + codes, key="browse_select")
    if sel != "--":
        code_input = sel

def normalize(code: str) -> str:
    """
    Normalize minor variants:
    - collapse multiple spaces
    - allow 'DCDC' to match 'DC-DC'
    - allow AFEF1 -> AFE F1, etc.
    """
    c = code.upper().strip()
    if not c:
        return c
    c = c.replace("DCDC", "DC-DC")
    # Insert space before F if missing (e.g., AFEF1 -> AFE F1)
    c = re.sub(r"^(AFE|GRID INVERTER|DC-DC)\s*F", r"\1 F", c)
    # Collapse spaces
    c = re.sub(r"\s+", " ", c)
    return c

def search(code: str, device_filter: str):
    key = normalize(code)
    # Direct hit
    rec = idx.get(key)
    if rec and (device_filter == "Any" or rec["Device"] == device_filter):
        return rec, []
    # Suggestions: prefix/contains matches inside device
    pool = rows if device_filter == "Any" else [r for r in rows if r["Device"] == device_filter]
    sugg = [r for r in pool if key and (key in r["_UCODE"] or r["_UCODE"].startswith(key))]
    # fallback: suggest same F-number regardless of device
    m = re.search(r"F\s*\d+", key)
    if not sugg and m:
        fnum = m.group(0)  # e.g., F 80
        sugg = [r for r in pool if fnum.replace(" ", "") in r["_UCODE"].replace(" ", "")]
    return None, sugg[:10]

def render_record(r: dict):
    st.success(f"**{r.get('Fault Code','')}** — *{r.get('Device','')}*")
    desc = r.get("Description","").strip()
    # Light formatting: split at 'Possible cause and solution:' if present
    parts = re.split(r"(?i)Possible\s*cause\s*and\s*solution\s*:", desc, maxsplit=1)
    st.markdown(parts[0].strip())
    if len(parts) > 1:
        st.markdown("**Possible cause and solution:**")
        # Try to bulletize lines that look like steps
        bullets = [ln.strip(" \t-•") for ln in parts[1].splitlines() if ln.strip()]
        for b in bullets:
            st.markdown(f"- {b}")

# ---- Action
do_search = st.button("Search") or (code_input and st.session_state.get("_entered_once") != code_input)
if code_input:
    st.session_state["_entered_once"] = code_input

if do_search and code_input:
    rec, suggestions = search(code_input, device)
    if rec:
        render_record(rec)
    else:
        st.warning("No exact match found.")
        if suggestions:
            st.markdown("**Did you mean:**")
            for s in suggestions:
                if st.button(s["Fault Code"], key=f"sugg_{s['_UCODE']}"):
                    render_record(s)
        else:
            st.info("Try loosening the device filter or checking the code format.")
else:
    st.caption("Enter a code above or open **Browse known fault codes** to pick one.")
