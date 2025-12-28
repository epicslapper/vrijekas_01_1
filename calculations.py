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