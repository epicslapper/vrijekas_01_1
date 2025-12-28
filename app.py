import streamlit as st
from seed import seed
from db import fetch_all, fetch_one, upsert_variable
from calculations import build_tax_statement

seed()

st.set_page_config(page_title="VrijeKas", layout="wide")

# Prominent notice: this app uses AOW-age rates (for retirees working in NL)
st.warning("BIIIIG NOTE — This calculator uses AOW-age rates: special tax rules for retirees who keep working in the Netherlands.")

app_name = fetch_all("SELECT value FROM meta WHERE key='app_name'")[0][0]
version = fetch_all("SELECT value FROM meta WHERE key='version'")[0][0]

st.title(f"{app_name} — Freelance Reality Check")
st.caption(f"Version {version}")

# Fetch editable variables and display in a single form
st.header("1–3. Inputs: Revenue, Expenses & Tax parameters")

rev_inputs = fetch_all("SELECT key, value, label_en FROM variables WHERE editable=1 AND category='revenue' ORDER BY key")
car_inputs = fetch_all("SELECT key, value, label_en FROM variables WHERE editable=1 AND category='car' ORDER BY key")
general_inputs = fetch_all("SELECT key, value, label_en FROM variables WHERE editable=1 AND category IN ('expenses','general','operational') ORDER BY key")
# split tax-category into deductions vs rates (simple heuristic)
rate_keys = ('box1_rate', 'mkb_vrijstelling_pct')
ded_inputs = fetch_all(
    "SELECT key, value, label_en FROM variables WHERE editable=1 AND category='tax' AND key NOT IN ('box1_rate','mkb_vrijstelling_pct') ORDER BY key"
)
taxrate_inputs = fetch_all(
    "SELECT key, value, label_en FROM variables WHERE editable=1 AND category='tax' AND key IN ('box1_rate','mkb_vrijstelling_pct') ORDER BY key"
)

inputs = {}
with st.form("inputs_form"):
    st.subheader("Revenue")
    cols = st.columns(2)
    for i, (k, v, label) in enumerate(rev_inputs):
        col = cols[i % 2]
        inputs[k] = col.number_input(label, value=float(v))

    st.subheader("Car expenses")
    cols = st.columns(2)
    for i, (k, v, label) in enumerate(car_inputs):
        col = cols[i % 2]
        inputs[k] = col.number_input(label, value=float(v))

    st.subheader("General expenses")
    cols = st.columns(2)
    for i, (k, v, label) in enumerate(general_inputs):
        col = cols[i % 2]
        inputs[k] = col.number_input(label, value=float(v))

    st.subheader("Deductions")
    cols = st.columns(2)
    for i, (k, v, label) in enumerate(ded_inputs):
        col = cols[i % 2]
        inputs[k] = col.number_input(label, value=float(v))

    st.subheader("Tax rates")
    cols = st.columns(2)
    for i, (k, v, label) in enumerate(taxrate_inputs):
        col = cols[i % 2]
        inputs[k] = col.number_input(label, value=float(v))

    submit = st.form_submit_button("Save & Calculate")

if submit:
    for k, val in inputs.items():
        # persist user inputs (mark as editable/source)
        upsert_variable(k, float(val), is_input=1)

    # run calculations and persist derived values
    build_tax_statement()

# -------- Calculate / Display --------
st.header("4. Simplified Tax Statement")

# Show tax statement rows persisted in DB (may be empty until first calculation)
rows = fetch_all("SELECT label, amount FROM tax_statement ORDER BY line_no")
if rows:
    st.table(rows)
else:
    st.info("No calculation yet — press 'Save & Calculate' to compute." )

# Show key final metrics from persisted variables
final_tax_row = fetch_one("SELECT value FROM variables WHERE key='final_income_tax'")
net_cash_row = fetch_one("SELECT value FROM variables WHERE key='net_cash'")

final_tax = final_tax_row[0] if final_tax_row else None
net_cash = net_cash_row[0] if net_cash_row else None

if final_tax is not None:
    st.metric("Final income tax", f"€ {final_tax:,.0f}")
if net_cash is not None:
    st.metric("Net cash", f"€ {net_cash:,.0f}")