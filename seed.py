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