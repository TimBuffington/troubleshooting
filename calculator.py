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

st.set_page_config(page_title="Battery Life", layout="centered")
# NAV button to Fault Codes
st.markdown('<div style="text-align:center;"><a href="app" target="_self" class="btn">Fault Codes</a></div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center;'>EBOSS Calculations</h1>", unsafe_allow_html=True)

# ---------- Data (EBOSS dictionary) ----------
FH_specs = {
    "EB25":  {"ch_rate": 19.5, "kWh": 15},
    "EB70":  {"ch_rate": 34.5, "kWh": 25},
    "EB125": {"ch_rate": 54.0, "kWh": 50},
    "EB220": {"ch_rate": 100.0, "kWh": 75},
    "EB400": {"ch_rate": 156.0, "kWh": 125},
}

PM_specs = {
    "EB25":  {"ch_rate": 18.5, "kWh": 15},
    "EB70":  {"ch_rate": 33.0, "kWh": 25},
    "EB125": {"ch_rate": 50.0, "kWh": 50},
    "EB220": {"ch_rate": 96.0, "kWh": 75},
    "EB400": {"ch_rate": 145.0, "kWh": 125},
}

EBOSS = {
    "FH": {"label": "Full Hybrid", "specs": FH_specs},
    "PM": {"label": "Power Module", "specs": PM_specs},
}

# ---------- Helpers ----------
def fmt_hours(h):
    if h is None:
        return "—"
    if h == float("inf"):
        return "∞"
    # Show hours and minutes for readability
    hours = int(h)
    minutes = int(round((h - hours) * 60))
    if hours == 0 and minutes == 0:
        return "< 1 min"
    if hours == 0:
        return f"{minutes} min"
    return f"{hours} hr {minutes} min" if minutes else f"{hours} hr"

# ---------- UI ----------
st.title("Battery Life")

col1, col2 = st.columns(2)
with col1:
    eb_type = st.selectbox("EB Type_sel", options=list(EBOSS.keys()), format_func=lambda k: f"{k} — {EBOSS[k]['label']}")
with col2:
    models = list(EBOSS[eb_type]["specs"].keys())
    eb_model = st.selectbox("EB Model_sel", options=models)

load_kw = st.number_input("load_kw (kW)", min_value=0.0, step=0.5, value=20.0)

# ---------- Calculation ----------
spec = EBOSS[eb_type]["specs"][eb_model]
kwh     = float(spec["kWh"])
ch_rate = float(spec["ch_rate"])

battery_only_hours = None
with_charge_hours = None
note = ""

if load_kw > 0:
    battery_only_hours = kwh / load_kw

# Net load accounting for charge rate (generator/inverter charging effect)
net_kw = load_kw - ch_rate  # positive => battery draining; negative/zero => sustained/charging
if load_kw == 0:
    with_charge_hours = float("inf")
elif net_kw <= 0:
    with_charge_hours = float("inf")
    note = "Net load ≤ 0 kW: charge rate covers or exceeds the load (battery sustains/charges)."
else:
    with_charge_hours = kwh / net_kw

# ---------- Output ----------
st.subheader("Selected Specs")
c1, c2, c3 = st.columns(3)
c1.metric("Type", f"{eb_type} ({EBOSS[eb_type]['label']})")
c2.metric("Model", eb_model)
c3.metric("Battery", f"{kwh:.0f} kWh")

c4, c5 = st.columns(2)
c4.metric("Charge Rate (ch_rate)", f"{ch_rate:.1f} kW")
c5.metric("Load", f"{load_kw:.1f} kW")

st.markdown("---")
st.subheader("Results")
r1, r2 = st.columns(2)
r1.metric("Battery-only runtime", fmt_hours(battery_only_hours))
r2.metric("Runtime w/ charging", fmt_hours(with_charge_hours))

if note:
    st.info(note)

st.caption("Formulae: Battery-only = kWh / load_kW. With-charging = kWh / max(load_kW − ch_rate, ε); if (load_kW − ch_rate) ≤ 0 ⇒ ∞.")
