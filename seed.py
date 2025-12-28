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
        ('hrs_home', 500, 'hrs', 'revenue', 'Uren thuis', 'Hours home', 1, ''),
        ('rate_home', 50, '€/hr', 'revenue', 'Tarief thuis', 'Rate home', 1, ''),
        ('hrs_onsite', 500, 'hrs', 'revenue', 'Uren locatie', 'Hours onsite', 1, ''),
        ('rate_onsite', 70, '€/hr', 'revenue', 'Tarief locatie', 'Rate onsite', 1, ''),

        ('tesla_price', 50000, '€', 'car', 'Tesla prijs', 'Tesla price', 1, ''),
        ('vat_recovered', 8678, '€', 'car', 'BTW terug', 'VAT recovered', 1, ''),
        ('depr_years', 5, 'yrs', 'car', 'Afschrijving', 'Depreciation years', 1, ''),
        ('bijtelling', 9091, '€', 'tax', 'Bijtelling', 'Bijtelling', 1, 'Pure tax'),

        ('kia', 0, '€', 'tax', 'KIA', 'KIA deduction', 1, ''),
        ('zelfstandigenaftrek', 1200, '€', 'tax', 'Zelfstandigenaftrek', 'Self-employed deduction', 1, ''),
        ('startersaftrek', 2123, '€', 'tax', 'Startersaftrek', 'Starter deduction', 1, ''),
        # MKB vrijstelling is applied as a percentage of profit after deductions
        ('mkb_vrijstelling_pct', 0.127, '%', 'tax', 'MKB %', 'MKB %', 1, ''),
        ('box1_rate', 0.1785, '%', 'tax', 'Box 1 tarief', 'Box 1 rate', 1, ''),
        # arbeidskorting will be computed dynamically; default to 0
        ('arbeidskorting', 0, '€', 'tax', 'Arbeidskorting', 'Labour tax credit', 1, '')
    ]

    # Derived / output variables (persisted as non-editable by default)
    derived = [
        ('total_revenue', 60000, '€', 'revenue', 'Omzet totaal', 'Total revenue', 0, ''),
        ('depreciation', 8264, '€', 'calculation', 'Afschrijving', 'Depreciation', 0, ''),
        ('profit_before', 35099, '€', 'calculation', 'Winst voor aftrek', 'Profit before deductions', 0, ''),
        ('after_deductions', 31776, '€', 'calculation', 'Winst na aftrek', 'Profit after deductions', 0, ''),
        ('mkb_vrijstelling', 7620, '€', 'calculation', 'MKB vrijstelling', 'MKB exemption', 0, ''),
        ('taxable_profit', 24156, '€', 'calculation', 'Belastbare winst', 'Taxable profit', 0, ''),
        ('tax_before_credit', 4312, '€', 'calculation', 'Belasting voor korting', 'Tax before credit', 0, ''),
        ('final_income_tax', 1462, '€', 'calculation', 'Eindbelasting', 'Final income tax', 0, ''),
        ('net_cash', 53472, '€', 'calculation', 'Netto kas', 'Net cash', 0, ''),
    ]

    for v in derived:
        variables.append(v)

    for v in variables:
        execute("INSERT INTO variables VALUES (?, ?, ?, ?, ?, ?, ?, ?)", v)


if __name__ == "__main__":
    seed()
    print("Database initialized.")