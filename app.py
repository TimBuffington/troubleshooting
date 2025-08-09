import json, re
from PIL import Image
import requests
import base64
from io import BytesIO
from typing import Tuple
import streamlit as st
from PIL import Image, UnidentifiedImageError

LOGO_URL = "https://raw.githubusercontent.com/timbuffington/troubleshoot/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"
BG_URL   = "https://raw.githubusercontent.com/timbuffington/troubleshoot/main/assets/AdobeStock_209254754.jpeg"  # use main, not master

def fetch_image(url: str) -> Tuple[bytes, str]:
    """Return (content_bytes, mime) after validating it's an image/* response."""
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            # Helpful detail for debugging
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
        # Optional: validate with PIL so we can downscale/convert if desired
        try:
            _ = Image.open(BytesIO(img_bytes))
        except UnidentifiedImageError:
            raise ValueError("Downloaded logo bytes are not a valid image file.")
        backdrop = "background: rgba(0,0,0,.35);" if on_dark_bg else ""
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        st.markdown(
            f"""
            <style>
            .logo-wrap {{
              display:flex; justify-content:center; align-items:center;
              padding:10px; border-radius:10px; {backdrop}
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

# ---- Use them (with clear error messages) ----
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

st.set_page_config(page_title="EBOSS® Inverter Fault Lookup", layout="centered")
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
