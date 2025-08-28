# pages/Fault_Lookup.py
import streamlit as st
from shared_style import inject_branding

st.set_page_config(page_title="EBOSS Fault Codes", layout="centered")
inject_branding()

st.markdown("<h1 class='app-title'>EBOSS Fault Codes</h1>", unsafe_allow_html=True)
st.write("Enter your fault lookup UI here...")  # placeholder for your existing logic

# ---- NAV button back to Calculator (no state needed) ----
st.markdown('<div class="center">', unsafe_allow_html=True)
if st.button("Calculator"):
    st.switch_page("Calculator.py")
st.markdown('</div>', unsafe_allow_html=True)