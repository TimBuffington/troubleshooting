# app.py — EBOSS® Inverter Fault Lookup (fixed & consolidated)
# -----------------------------------------------------------
# Streamlit app with robust background/logo loading and a safe
# data loader so `rows` is always defined.
#
# Requirements (install locally):
#   pip install streamlit pandas pillow requests
#
# Run:
#   streamlit run app.py

# ---- Imports
import base64
import re
import requests
from io import BytesIO
from typing import Tuple
from PIL import Image, UnidentifiedImageError
import pandas as pd
import streamlit as st

# ---- MUST be first Streamlit call
st.set_page_config(page_title="EBOSS® Inverter Fault Lookup", layout="centered")

# ---- GitHub RAW URLs (update if you move files)
BG_URL   = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/main/assets/AdobeStock_209254754.jpeg"
LOGO_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"

# Optional CSV that holds fault codes. Expected columns include at least:
# "Device", "Fault Code" and optionally "Title"/"Description"/"Cause"/"Resolution"
DATA_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/main/assets/fault_codes.csv"

# ---- Utility: fetch image safely
def fetch_image(url: str) -> Tuple[bytes, str]:
    """Return (content_bytes, mime) after validating it's an image/* response."""
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            raise ValueError(f"URL returned non-image content-type: {ctype or 'unknown'}")
        return r.content, ctype.split(";")[0]  # e.g. 'image/png'
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching image from URL: {e}")

def set_background_from_bytes(img_bytes: bytes, mime: str):
    if img_bytes and mime:
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        st.markdown(
            f"""
            <style>
            .stApp {{
              background-image: url("data:{mime};base64,{b64}");
              background-size: cover;
              background-position: center center;
              background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("Unable to set background image due to missing or invalid data.")

def show_logo_from_bytes(img_bytes: bytes, mime: str, width: int = 360, on_dark_bg: bool = True):
    if img_bytes and mime:
        try:
            _ = Image.open(BytesIO(img_bytes))
        except UnidentifiedImageError:
            raise ValueError("Downloaded logo bytes are not a valid image file.")
       # backdrop = "background: rgba(0,0,0,.35);" if on_dark_bg else ""
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        st.markdown(
            f"""
            <style>
            .logo-wrap {{
              display:flex; justify-content:center; align-items:center;
              margin: 8px 0 18px;
            }}
            .logo-wrap img {{ max-width:{width}px; height:auto; }}
            </style>
            <div class="logo-wrap">
              <img src="data:{mime};base64,{b64}" alt="Company Logo" />
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("Unable to display logo due to missing or invalid image data.")

# ---- Data loader so `rows` always exists
@st.cache_data(show_spinner=False)
def load_rows(url: str):
    try:
        df = pd.read_csv(url, dtype=str).fillna("")
        # Normalize expected column names to a consistent case for lookups
        df.columns = [c.strip() for c in df.columns]
        return df.to_dict(orient="records"), df
    except Exception as e:
        st.warning(f"Could not load fault code data: {e}")
        return [], pd.DataFrame()

rows, df = load_rows(DATA_URL)

# ---- Background and logo (safe, with errors surfaced to user)
try:
    bg_bytes, bg_mime = fetch_image(BG_URL)
    set_background_from_bytes(bg_bytes, bg_mime)
except Exception as e:
    st.error(f"Background failed to load: {e}")

try:
    logo_bytes, logo_mime = fetch_image(LOGO_URL)
    show_logo_from_bytes(logo_bytes, logo_mime, width=360, on_dark_bg=True)
except Exception as e:
    st.error(f"Logo failed to load: {e}")

st.markdown("<h2 style='text-align:center;margin-top:0;'>EBOSS® Inverter Fault Lookup</h2>", unsafe_allow_html=True)

# ---- Filters & Inputs
col1, col2 = st.columns([1, 2])
with col1:
    device = st.selectbox("Device", ["Any", "AFE", "DC-DC", "Grid Inverter"])
with col2:
    code_input = st.text_input("Fault Code (e.g., AFE F1, DC-DC F80, Grid Inverter F92)").strip()

# ---- Optional: Browse known fault codes
with st.expander("Browse known fault codes"):
    if device == "Any":
        codes = [r.get("Fault Code", "") for r in rows]
    else:
        codes = [r.get("Fault Code", "") for r in rows if r.get("Device", "") == device]
    # dedupe + sort; filter blanks
    codes = sorted({c for c in codes if c})
    sel = st.selectbox("Select a code", ["--"] + codes, key="browse_select")
    if sel != "--":
        code_input = sel

# ---- Normalize helper
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
    c = re.sub(r"^(AFE|GRID INVERTER|DC-DC)\s*F", r"\\1 F", c)
    # Collapse spaces
    c = re.sub(r"\\s+", " ", c)
    return c

# ---- Search + display results
def find_matches(rows, code_text: str, device_filter: str):
    if not code_text:
        return []
    target = normalize(code_text)
    out = []
    for r in rows:
        dev = r.get("Device", "").upper()
        code = normalize(r.get("Fault Code", ""))
        if not code:
            continue
        if device_filter != "Any" and dev != device_filter.upper():
            continue
        if code == target:
            out.append(r)
    return out

st.markdown("---")
btn = st.button("Lookup Fault Details", use_container_width=True)

matches = []
if btn:
    matches = find_matches(rows, code_input, device)

if not btn and code_input:
    # Live preview without clicking button
    matches = find_matches(rows, code_input, device)

if matches:
    for m in matches:
        title = m.get("Title") or m.get("Description") or m.get("Summary") or ""
        st.subheader(m.get("Fault Code", "Code"))
        if m.get("Device"):
            st.caption(m["Device"])
        if title:
            st.write(title)

        c1, c2 = st.columns(2)
        with c1:
            cause = m.get("Cause") or m.get("Possible Cause") or m.get("Details") or ""
            if cause:
                st.markdown("**Cause**")
                st.write(cause)
        with c2:
            res = m.get("Resolution") or m.get("Recommended Action") or m.get("Fix") or ""
            if res:
                st.markdown("**Resolution**")
                st.write(res)

        # Show full row if user wants
        with st.expander("Show raw record"):
            st.json(m)
        st.markdown("---")
else:
    if code_input:
        st.info("No exact match found. Try adjusting the code or device, e.g., 'AFE F1', 'DC-DC F80', 'Grid Inverter F92'.")
    else:
        st.caption("Enter a fault code or browse known codes above.")
