import streamlit as st

BG_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/AdobeStock_209254754.jpeg"
LOGO_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"

def inject_branding():
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
      background-image: url('{BG_URL}');
      background-size: cover;
      background-position: center center;
      background-repeat: no-repeat;
      background-attachment: fixed;
    }}
    .block-container {{ background: transparent !important; }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
    .logo-wrap {{ display:flex; align-items:center; justify-content:center; margin:.25rem 0 .75rem; }}
    .logo-wrap img {{ max-width: min(420px, 70vw); height:auto; filter: drop-shadow(0 4px 12px rgba(0,0,0,.45)); }}
    .app-title {{ font-size: 1.8rem; font-weight: 700; text-align:center; color:#fff; text-shadow:0 2px 8px rgba(0,0,0,.7); }}
    .btn {{ display:inline-block; padding:.8rem 1.6rem; font-weight:700; border-radius:12px; border:2px solid #D0D4D9; color:#fff; background:#636569; text-decoration:none; }}
    .btn:hover {{ background:#80BD47; border-color:#80BD47; box-shadow:0 0 12px rgba(128,189,71,.6); }}
    .center {{ text-align:center; }}
    </style>
    <div class="logo-wrap"><img src="{LOGO_URL}" alt="ANA Energy"></div>
    """, unsafe_allow_html=True)