from db import fetch_all, execute, upsert_variable


def vars_dict():
    rows = fetch_all("SELECT key, value FROM variables")
    return {k: v for k, v in rows}


def calculate_revenue(v):
    return v['hrs_home'] * v['rate_home'] + v['hrs_onsite'] * v['rate_onsite']


def calculate_depreciation(v):
    base = v['tesla_price'] - v['vat_recovered']
    return base / v['depr_years']

def compute_arbeidskorting(arbeidsinkomen: float) -> float:
    """Simple bracketed arbeidskorting for 2026 (AOW-age table provided).

    Brackets (amounts in euros):
    - up to 11,965: 4.156% * y
    - 11,965–25,845: 498 + 15.483% * (y - 11,965)
    - 25,845–45,592: 2,647 + 0.974% * (y - 25,845)
    - 45,592+: 2,840 - 3.250% * (y - 45,592)
    """
    y = max(0.0, float(arbeidsinkomen))
    if y <= 11965:
        return 0.04156 * y
    if y <= 25845:
        return 498 + 0.15483 * (y - 11965)
    if y <= 45592:
        return 2647 + 0.00974 * (y - 25845)
    # above 45,592
    return max(0.0, 2840 - 0.03250 * (y - 45592))


def build_tax_statement():
    v = vars_dict()

    revenue = calculate_revenue(v)
    depreciation = calculate_depreciation(v)
    expenses = depreciation
    profit_before = revenue - expenses + v['bijtelling']
    # --- KIA (kleinschaligheidsinvesteringsaftrek) ---
    # Compute net investment (price excluding VAT recovered)
    net_invest = v.get('tesla_price', 0) - v.get('vat_recovered', 0)
    if net_invest <= 2900:
        kia = 0
    elif net_invest <= 69765:
        kia = net_invest * 0.28
    else:
        # For investments above the second threshold, apply the same 28% rule
        kia = net_invest * 0.28

    after_deductions = (
        profit_before
        - v['zelfstandigenaftrek']
        - v['startersaftrek']
        - kia
    )
    # MKB vrijstelling can be stored as an absolute amount (`mkb_vrijstelling`)
    # or historically as a percentage (`mkb_vrijstelling_pct`). Prefer
    # the absolute value if present; otherwise compute from the percentage.
    if 'mkb_vrijstelling' in v and v['mkb_vrijstelling'] is not None:
        mkb = v['mkb_vrijstelling']
    else:
        mkb = after_deductions * v.get('mkb_vrijstelling_pct', 0)
    taxable = after_deductions - mkb

    # Compute arbeidskorting dynamically from (approximate) arbeidsinkomen.
    # Use `after_deductions` as a proxy for arbeidsinkomen for a ballpark value.
    arbeidskorting = compute_arbeidskorting(after_deductions)
    tax_before_credit = taxable * v['box1_rate']
    final_tax = tax_before_credit - arbeidskorting

    execute("DELETE FROM tax_statement")

    lines = [
        (10, 'Total revenue', revenue, 'add', ''),
        (20, 'Depreciation', -depreciation, 'subtract', ''),
        (25, 'KIA (investment deduction)', -kia, 'subtract', ''),
        (30, 'Bijtelling (tax only)', v['bijtelling'], 'add', ''),
           (40, 'Zelfstandigenaftrek', -v['zelfstandigenaftrek'], 'subtract', ''),
           (50, 'Startersaftrek', -v['startersaftrek'], 'subtract', ''),
           (60, 'KIA (investment deduction)', -kia, 'subtract', ''),
           (70, 'MKB vrijstelling', -mkb, 'subtract', ''),
        (70, 'Taxable profit', taxable, 'result', ''),
           (80, 'Income tax', tax_before_credit, 'tax', ''),
           (90, 'Arbeidskorting', -arbeidskorting, 'credit', ''),
           (100, 'Final income tax', final_tax, 'result', ''),
    ]

    for line in lines:
        execute("INSERT INTO tax_statement VALUES (?, ?, ?, ?, ?)", line)

    # Persist derived values back into the DB so all outputs are stored
    upsert_variable("total_revenue", revenue, unit="€", category="revenue", label_en="Total revenue", is_input=0)
    upsert_variable("depreciation", depreciation, unit="€", category="car", label_en="Depreciation", is_input=0)
    upsert_variable("profit_before", profit_before, unit="€", category="calculation", label_en="Profit before deductions", is_input=0)
    upsert_variable("after_deductions", after_deductions, unit="€", category="calculation", label_en="Profit after deductions", is_input=0)
    upsert_variable("mkb_vrijstelling", mkb, unit="€", category="calculation", label_en="MKB vrijstelling", is_input=0)
    upsert_variable("taxable_profit", taxable, unit="€", category="calculation", label_en="Taxable profit", is_input=0)
    upsert_variable("tax_before_credit", tax_before_credit, unit="€", category="calculation", label_en="Income tax before credits", is_input=0)
    upsert_variable("final_income_tax", final_tax, unit="€", category="calculation", label_en="Final income tax", is_input=0)

    # Simple net cash: revenue - expenses - final income tax
    net_cash = revenue - expenses - final_tax
    upsert_variable("net_cash", net_cash, unit="€", category="calculation", label_en="Net cash", is_input=0)

    return final_tax