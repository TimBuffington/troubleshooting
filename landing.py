import streamlit as st

# Reuse background + logo CSS
BG_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/AdobeStock_209254754.jpeg"
LOGO_URL = "https://raw.githubusercontent.com/TimBuffington/troubleshooting/refs/heads/main/assets/ANA-ENERGY-LOGO-HORIZONTAL-WHITE-GREEN.png"

st.set_page_config(page_title="EBOSS® Tool", layout="centered")

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
[data-testid="stHeader"], [data-testid="stSidebar"] > div:first-child {{
  background: rgba(0,0,0,0) !important;
}}
.logo-wrap {{
  display:flex; align-items:center; justify-content:center;
  margin:.25rem 0 1rem;
}}
.logo-wrap img {{
  max-width: min(420px, 70vw); height:auto;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,.45));
}}
.btn {{
  display:inline-block;
  padding: 1rem 2rem;
  margin: 1rem;
  font-size: 1.2rem;
  font-weight: bold;
  color: #fff !important;
  background-color: #636569;
  border: 2px solid #D0D4D9;
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.25s ease;
}}
.btn:hover {{
  background-color: #80BD47;
  border-color: #80BD47;
  box-shadow: 0 0 12px rgba(128,189,71,.6);
  color: #fff !important;
}}
</style>
<div class="logo-wrap">
  <img src="{LOGO_URL}" alt="Alliance North America logo">
</div>
""", unsafe_allow_html=True)

st.title("EBOSS® Tool")

# Two buttons side by side
c1, c2 = st.columns(2)
with c1:
    st.markdown('<a href="calculator" target="_self" class="btn">Calculations</a>', unsafe_allow_html=True)
with c2:
    st.markdown('<a href="app" target="_self" class="btn">Fault Codes</a>', unsafe_allow_html=True)
