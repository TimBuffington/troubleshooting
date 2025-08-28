# Calculator.py  (ENTRY)
import streamlit as st
from shared_style import inject_branding

st.set_page_config(page_title="EBOSS Calculations", layout="centered")
inject_branding()

st.markdown("<h1 class='app-title'>EBOSS Calculations</h1>", unsafe_allow_html=True)

# ---- Simple EBOSS dict ----
EBOSS = {
    "FH": {"label": "Full Hybrid", "specs": {
        "EB25": {"ch_rate": 19.5, "kWh": 15},
        "EB70": {"ch_rate": 34.5, "kWh": 25},
        "EB125": {"ch_rate": 54.0, "kWh": 50},
        "EB220": {"ch_rate": 100.0, "kWh": 75},
        "EB400": {"ch_rate": 156.0, "kWh": 125},
    }},
    "PM": {"label": "Power Module", "specs": {
        "EB25": {"ch_rate": 18.5, "kWh": 15},
        "EB70": {"ch_rate": 33.0, "kWh": 25},
        "EB125": {"ch_rate": 50.0, "kWh": 50},
        "EB220": {"ch_rate": 96.0, "kWh": 75},
        "EB400": {"ch_rate": 145.0, "kWh": 125},
    }}
}

def fmt_hours(h):
    if h is None: return "—"
    if h == float("inf"): return "∞"
    hours = int(h); minutes = int(round((h - hours) * 60))
    if hours == 0 and minutes == 0: return "< 1 min"
    if hours == 0: return f"{minutes} min"
    return f"{hours} hr {minutes} min" if minutes else f"{hours} hr"

# ---- UI ----
c1, c2 = st.columns(2)
with c1:
    eb_type = st.selectbox("EB Type_sel", options=list(EBOSS.keys()),
                           format_func=lambda k: f"{k} — {EBOSS[k]['label']}")
with c2:
    models = list(EBOSS[eb_type]["specs"].keys())
    eb_model = st.selectbox("EB Model_sel", options=models)

load_kw = st.number_input("load_kw (kW)", min_value=0.0, step=0.5, value=20.0)

spec = EBOSS[eb_type]["specs"][eb_model]
kwh     = float(spec["kWh"])
ch_rate = float(spec["ch_rate"])

battery_only_hours = (kwh / load_kw) if load_kw > 0 else None
net_kw = load_kw - ch_rate
if load_kw == 0:
    with_charge_hours = float("inf")
elif net_kw <= 0:
    with_charge_hours = float("inf")
else:
    with_charge_hours = kwh / net_kw

st.markdown("---")
st.subheader("Results")
r1, r2 = st.columns(2)
r1.metric("Battery-only runtime", fmt_hours(battery_only_hours))
r2.metric("Runtime w/ charging", fmt_hours(with_charge_hours))

# ---- NAV button to Fault Lookup (no state needed) ----
st.markdown('<div class="center">', unsafe_allow_html=True)
if st.button("Fault Lookup"):
    st.switch_page("pages/Fault_Lookup.py")
st.markdown('</div>', unsafe_allow_html=True)
