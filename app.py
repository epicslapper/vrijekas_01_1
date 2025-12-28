import streamlit as st
from seed import seed
from db import fetch_all, execute
from calculations import build_tax_statement

seed()

st.set_page_config(page_title="VrijeKas", layout="wide")

app_name = fetch_all("SELECT value FROM meta WHERE key='app_name'")[0][0]
version = fetch_all("SELECT value FROM meta WHERE key='version'")[0][0]

st.title(f"{app_name} — Freelance Reality Check")
st.caption(f"Version {version}")

# -------- Section 1: Revenue --------
st.header("1. Revenue")

vars_rev = fetch_all(
    "SELECT key, value, label_en FROM variables WHERE category='revenue'"
)

for k, v, label in vars_rev:
    new = st.number_input(label, value=float(v))
    execute("UPDATE variables SET value=? WHERE key=?", (new, k))

# -------- Section 2: Expenses --------
st.header("2. Business Expenses")

vars_exp = fetch_all(
    "SELECT key, value, label_en FROM variables WHERE category IN ('car')"
)

for k, v, label in vars_exp:
    new = st.number_input(label, value=float(v))
    execute("UPDATE variables SET value=? WHERE key=?", (new, k))

# -------- Section 3: Tax --------
st.header("3. Tax parameters")

vars_tax = fetch_all(
    "SELECT key, value, label_en FROM variables WHERE category='tax'"
)

for k, v, label in vars_tax:
    new = st.number_input(label, value=float(v))
    execute("UPDATE variables SET value=? WHERE key=?", (new, k))

# -------- Calculate --------
st.header("4. Simplified Tax Statement")

final_tax = build_tax_statement()
rows = fetch_all("SELECT label, amount FROM tax_statement ORDER BY line_no")

st.table(rows)

st.metric("Final income tax", f"€ {final_tax:,.0f}")