Excellent. Then we do this **properly and cleanly**, but still **version-1 pragmatic**.

Below is **a complete, minimal but solid v0.1.0 implementation**, split exactly as promised:

* `db.py` – SQLite plumbing
* `seed.py` – one-time initialization
* `calculations.py` – all financial & tax logic
* `app.py` – Streamlit UI, sectioned exactly like *your mental model*

No over-engineering, no classes, no magic.

---

# 📁 Project structure (final)

```
vrijekas/
│
├── app.py
├── db.py
├── seed.py
├── calculations.py
├── vrijekas.db          # created automatically
└── README.md            # optional later
```

---

# 1️⃣ `db.py` — SQLite helpers (boring on purpose)

```python
import sqlite3
from pathlib import Path

DB_PATH = Path("vrijekas.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def fetch_all(query, params=()):
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def fetch_one(query, params=()):
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchone()


def execute(query, params=()):
    with get_conn() as conn:
        conn.execute(query, params)
        conn.commit()
```

---

# 2️⃣ `seed.py` — schema + defaults (run once)

```python
from db import execute, DB_PATH
import os


def seed():
    if DB_PATH.exists():
        return

    # ---- tables ----
    execute("""
    CREATE TABLE variables (
        key TEXT PRIMARY KEY,
        value REAL NOT NULL,
        unit TEXT,
        category TEXT,
        label_nl TEXT,
        label_en TEXT,
        editable INTEGER DEFAULT 1,
        notes TEXT
    )
    """)

    execute("""
    CREATE TABLE derived_values (
        key TEXT PRIMARY KEY,
        value REAL,
        unit TEXT,
        formula TEXT,
        notes TEXT
    )
    """)

    execute("""
    CREATE TABLE tax_statement (
        line_no INTEGER PRIMARY KEY,
        label TEXT,
        amount REAL,
        kind TEXT,
        notes TEXT
    )
    """)

    execute("""
    CREATE TABLE balance_sheet (
        item TEXT PRIMARY KEY,
        category TEXT,
        before_start REAL,
        after_1y REAL,
        notes TEXT
    )
    """)

    execute("""
    CREATE TABLE meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # ---- meta ----
    execute("INSERT INTO meta VALUES ('app_name', 'VrijeKas')")
    execute("INSERT INTO meta VALUES ('version', '0.1.0')")
    execute("INSERT INTO meta VALUES ('tax_year', '2026')")

    # ---- variables ----
    variables = [
        ('hrs_home', 600, 'hrs', 'revenue', 'Uren thuis', 'Hours home', 1, ''),
        ('rate_home', 50, '€/hr', 'revenue', 'Tarief thuis', 'Rate home', 1, ''),
        ('hrs_onsite', 600, 'hrs', 'revenue', 'Uren locatie', 'Hours onsite', 1, ''),
        ('rate_onsite', 75, '€/hr', 'revenue', 'Tarief locatie', 'Rate onsite', 1, ''),

        ('tesla_price', 50000, '€', 'car', 'Tesla prijs', 'Tesla price', 1, ''),
        ('vat_recovered', 8678, '€', 'car', 'BTW terug', 'VAT recovered', 1, ''),
        ('depr_years', 5, 'yrs', 'car', 'Afschrijving', 'Depreciation years', 1, ''),
        ('bijtelling', 7291, '€', 'tax', 'Bijtelling', 'Bijtelling', 1, 'Pure tax'),

        ('kia', 14000, '€', 'tax', 'KIA', 'KIA deduction', 1, ''),
        ('zelfstandigenaftrek', 7280, '€', 'tax', 'Zelfstandigenaftrek', 'Self-employed deduction', 1, ''),
        ('startersaftrek', 2123, '€', 'tax', 'Startersaftrek', 'Starter deduction', 1, ''),
        ('mkb_vrijstelling_pct', 0.14, '%', 'tax', 'MKB %', 'MKB %', 1, ''),
        ('box1_rate', 0.178, '%', 'tax', 'Box 1 tarief', 'Box 1 rate', 1, ''),
        ('arbeidskorting', 3540, '€', 'tax', 'Arbeidskorting', 'Labour tax credit', 1, '')
    ]

    for v in variables:
        execute("INSERT INTO variables VALUES (?, ?, ?, ?, ?, ?, ?, ?)", v)


if __name__ == "__main__":
    seed()
    print("Database initialized.")
```

---

# 3️⃣ `calculations.py` — **all logic, no UI**

```python
from db import fetch_all, execute


def vars_dict():
    rows = fetch_all("SELECT key, value FROM variables")
    return {k: v for k, v in rows}


def calculate_revenue(v):
    return v['hrs_home'] * v['rate_home'] + v['hrs_onsite'] * v['rate_onsite']


def calculate_depreciation(v):
    base = v['tesla_price'] - v['vat_recovered']
    return base / v['depr_years']


def build_tax_statement():
    v = vars_dict()

    revenue = calculate_revenue(v)
    depreciation = calculate_depreciation(v)
    expenses = depreciation
    profit_before = revenue - expenses + v['bijtelling']

    after_deductions = (
        profit_before
        - v['zelfstandigenaftrek']
        - v['startersaftrek']
    )

    mkb = after_deductions * v['mkb_vrijstelling_pct']
    taxable = after_deductions - mkb

    tax_before_credit = taxable * v['box1_rate']
    final_tax = tax_before_credit - v['arbeidskorting']

    execute("DELETE FROM tax_statement")

    lines = [
        (10, 'Total revenue', revenue, 'add', ''),
        (20, 'Depreciation', -depreciation, 'subtract', ''),
        (30, 'Bijtelling (tax only)', v['bijtelling'], 'add', ''),
        (40, 'Zelfstandigenaftrek', -v['zelfstandigenaftrek'], 'subtract', ''),
        (50, 'Startersaftrek', -v['startersaftrek'], 'subtract', ''),
        (60, 'MKB vrijstelling', -mkb, 'subtract', ''),
        (70, 'Taxable profit', taxable, 'result', ''),
        (80, 'Income tax', tax_before_credit, 'tax', ''),
        (90, 'Arbeidskorting', -v['arbeidskorting'], 'credit', ''),
        (100, 'Final income tax', final_tax, 'result', ''),
    ]

    for line in lines:
        execute("INSERT INTO tax_statement VALUES (?, ?, ?, ?, ?)", line)

    return final_tax
```

---

# 4️⃣ `app.py` — Streamlit UI (clean & calm)

```python
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
```

---

# ✅ What you now have

* Persistent data ✅
* One source of truth ✅
* Logical Dutch tax flow ✅
* Bijtelling treated as **pure tax fiction** ✅
* Easy refactor path ✅

And most importantly:

> **This is no longer a spreadsheet with lipstick.
> This is a small financial system.**

---

## Next ideas (when *you* feel like it)

* Revenue slider (40k–80k)
* Scenario table (A / B / C)
* Export to CSV / PDF
* Multi-year depreciation
* Toggle buy vs lease
* Real Box-1 brackets instead of flat rate

Say the word — we evolve it calmly.

