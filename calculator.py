import streamlit as st
from Calculator import EBOSS, fmt_hours  # reuse your dict + helper if modularized

BG_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/AdobeStock_209254754.jpeg"
LOGO_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"

st.set_page_config(page_title="EBOSS Calculations", layout="centered")

# Background + logo block (reuse same CSS as landing)
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
  background-image: url('{BG_URL}');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
}}
.block-container {{ background: transparent !important; }}
.logo-wrap {{ display:flex; align-items:center; justify-content:center; margin:.25rem 0 1rem; }}
.logo-wrap img {{ max-width: min(420px, 70vw); height:auto; filter: drop-shadow(0 4px 12px rgba(0,0,0,.45)); }}
.btn {{ display:inline-block; padding: .75rem 1.5rem; font-size:1rem; font-weight:bold;
       color:#fff !important; background-color:#636569; border:2px solid #D0D4D9;
       border-radius:10px; text-decoration:none; transition:all 0.25s ease; }}
.btn:hover {{ background-color:#80BD47; border-color:#80BD47;
              box-shadow:0 0 10px rgba(128,189,71,.6); color:#fff !important; }}
</style>
<div class="logo-wrap">
  <img src="{LOGO_URL}" alt="Alliance North America logo">
</div>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>EBOSS Calculations</h1>", unsafe_allow_html=True)

# NAV button to Fault Codes
st.markdown('<div style="text-align:center;"><a href="app" target="_self" class="btn">Fault Codes</a></div>', unsafe_allow_html=True)

# ---- your existing calculation UI goes here ----
# (reuse Calculator.py content below this line)
