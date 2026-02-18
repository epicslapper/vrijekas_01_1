import streamlit as st
import pandas as pd


DEFAULTS = {
    'hrs_home': 500,
    'rate_home': 50,
    'hrs_onsite': 500,
    'rate_onsite': 70,
    'tesla_price': 50000,
    'vat_recovered': 8678,
    'depr_years': 5,
    'bijtelling': 9091,
    'zelfstandigenaftrek': 1200,
    'startersaftrek': 2123,
    'mkb_vrijstelling_pct': 0.127,
    'box1_rate': 0.1785,
    'arbeidskorting': 0,
    # car-related operational inputs
    'operational_costs': 3000,
    'interest_payment': 2066,
    'other_expenses': 0,
}


def calculate_revenue(v):
    return v['hrs_home'] * v['rate_home'] + v['hrs_onsite'] * v['rate_onsite']


def calculate_depreciation(v):
    base = v['tesla_price'] - v['vat_recovered']
    return base / v['depr_years']


def compute_arbeidskorting(y: float) -> float:
    y = max(0.0, float(y))
    if y <= 11965:
        return 0.04156 * y
    if y <= 25845:
        return 498 + 0.15483 * (y - 11965)
    if y <= 45592:
        return 2647 + 0.00974 * (y - 25845)
    return max(0.0, 2840 - 0.03250 * (y - 45592))


def build_tax_statement(v):
    revenue = calculate_revenue(v)
    depreciation = calculate_depreciation(v)
    operational = v.get('operational_costs', 0)
    interest = v.get('interest_payment', 0)
    other = v.get('other_expenses', 0)
    expenses = depreciation + operational + interest + other
    profit_before = revenue - expenses + v['bijtelling']

    net_invest = v.get('tesla_price', 0) - v.get('vat_recovered', 0)
    if net_invest <= 2900:
        kia = 0
    else:
        kia = net_invest * 0.28

    after_deductions = (
        profit_before
        - v['zelfstandigenaftrek']
        - v['startersaftrek']
        - kia
    )

    mkb = after_deductions * v['mkb_vrijstelling_pct']
    taxable = after_deductions - mkb

    arbeidskorting = compute_arbeidskorting(after_deductions)

    tax_before_credit = taxable * v['box1_rate']
    final_tax = tax_before_credit - arbeidskorting

    lines = [
        (10, 'Total revenue', revenue, 'add', ''),
        (20, 'Depreciation', -depreciation, 'subtract', ''),
        (21, 'Operational costs (car)', -operational, 'subtract', ''),
        (22, 'Interest payment', -interest, 'subtract', ''),
        (23, 'Other expenses', -other, 'subtract', ''),
        (25, 'KIA (investment deduction)', -kia, 'subtract', ''),
        (30, 'Bijtelling (tax only)', v['bijtelling'], 'add', ''),
        (40, 'Zelfstandigenaftrek', -v['zelfstandigenaftrek'], 'subtract', ''),
        (50, 'Startersaftrek', -v['startersaftrek'], 'subtract', ''),
        (70, 'MKB vrijstelling', -mkb, 'subtract', ''),
        (80, 'Taxable profit', taxable, 'result', ''),
        (90, 'Income tax', tax_before_credit, 'tax', ''),
        (100, 'Arbeidskorting', -arbeidskorting, 'credit', ''),
        (110, 'Final income tax', final_tax, 'result', ''),
    ]

    net_cash = revenue - expenses - final_tax

    outputs = {
        'final_income_tax': final_tax,
        'net_cash': net_cash,
        'revenue': revenue,
        'depreciation': depreciation,
        'expenses': expenses,
        'profit_before': profit_before,
        'kia': kia,
        'after_deductions': after_deductions,
        'mkb': mkb,
        'taxable': taxable,
        'arbeidskorting': arbeidskorting,
        'tax_before_credit': tax_before_credit,
    }

    return lines, outputs


def main():
    st.set_page_config(page_title="VrijeKas — No DB", layout="wide")
    st.warning("BIIIIG NOTE — This calculator uses AOW-age rates: special tax rules for retirees who keep working in the Netherlands.")
    st.title("VrijeKas — Simple (no DB) Streamlit")
    st.caption("Interactive version with prefilled defaults (no persistence)")

    with st.sidebar.expander('Defaults & Inputs', expanded=True):
        st.write('Change values and see outputs update instantly')
        values = {}
        for k, dv in DEFAULTS.items():
            widget_key = f"input_{k}"
            if k in ('box1_rate', 'mkb_vrijstelling_pct'):
                values[k] = st.number_input(k, value=float(dv), format="%.4f", key=widget_key)
            else:
                values[k] = st.number_input(k, value=float(dv), key=widget_key)

        st.markdown('---')
        st.write('Car expense inputs (operational):')
        values['operational_costs'] = st.number_input('operational_costs', value=float(DEFAULTS['operational_costs']), key='input_operational_costs')
        values['interest_payment'] = st.number_input('interest_payment', value=float(DEFAULTS['interest_payment']), key='input_interest_payment')
        values['other_expenses'] = st.number_input('other_expenses', value=float(DEFAULTS['other_expenses']), key='input_other_expenses')

        if st.button('Reset to defaults'):
            st.experimental_rerun()

    lines, outputs = build_tax_statement(values)

    df = pd.DataFrame([(l[1], l[2]) for l in lines], columns=['Label', 'Amount'])

    st.header('Tax statement')
    st.table(df)

    st.header('Key metrics')
    st.metric('Final income tax', f"€ {outputs['final_income_tax']:,.0f}")
    st.metric('Net cash', f"€ {outputs['net_cash']:,.0f}")

    st.header('Derived values')
    st.write(f"Total revenue: € {outputs['revenue']:,.0f}")
    st.write(f"Depreciation (annual): € {outputs['depreciation']:,.0f}")
    
    st.header('Debug — intermediate values')
    st.write(f"Expenses (depr + operational + interest + other): € {outputs['expenses']:,.0f}")
    st.write(f"Profit before deductions (revenue - expenses + bijtelling): € {outputs['profit_before']:,.0f}")
    st.write(f"KIA (investment deduction): € {outputs['kia']:,.0f}")
    st.write(f"After deductions (profit - zelfstandigenaftrek - startersaftrek - kia): € {outputs['after_deductions']:,.0f}")
    st.write(f"MKB vrijstelling (12.7%): € {outputs['mkb']:,.0f}")
    st.write(f"Taxable profit: € {outputs['taxable']:,.0f}")
    st.write(f"Arbeidskorting (credit): € {outputs['arbeidskorting']:,.0f}")
    st.write(f"Income tax before credits: € {outputs['tax_before_credit']:,.0f}")
    st.write(f"Final income tax: € {outputs['final_income_tax']:,.0f}")
    st.write(f"Net cash (revenue - expenses - final tax): € {outputs['net_cash']:,.0f}")


if __name__ == '__main__':
    main()
import streamlit as st
import pandas as pd


DEFAULTS = {
    'hrs_home': 500,
    'rate_home': 50,
    'hrs_onsite': 500,
    'rate_onsite': 70,
    'tesla_price': 50000,
    'vat_recovered': 8678,
    'depr_years': 5,
    'bijtelling': 9091,
    'zelfstandigenaftrek': 1200,
    'startersaftrek': 2123,
    'mkb_vrijstelling_pct': 0.127,
    'box1_rate': 0.1785,
    'arbeidskorting': 0,
    # car-related operational inputs
    'operational_costs': 3000,
    'interest_payment': 2066,
    'other_expenses': 0,
}


def calculate_revenue(v):
    return v['hrs_home'] * v['rate_home'] + v['hrs_onsite'] * v['rate_onsite']


def calculate_depreciation(v):
    base = v['tesla_price'] - v['vat_recovered']
    return base / v['depr_years']


def build_tax_statement(v):
    revenue = calculate_revenue(v)
    depreciation = calculate_depreciation(v)
    # include operational car costs and interest as business expenses
    operational = v.get('operational_costs', 0)
    interest = v.get('interest_payment', 0)
    other = v.get('other_expenses', 0)
    expenses = depreciation + operational + interest + other
    profit_before = revenue - expenses + v['bijtelling']
    # compute KIA like in the DB-backed calculations: net investment = price - vat
    net_invest = v.get('tesla_price', 0) - v.get('vat_recovered', 0)
    if net_invest <= 2900:
        kia = 0
    elif net_invest <= 69765:
        kia = net_invest * 0.28
    else:
        kia = net_invest * 0.28

    after_deductions = (
        profit_before
        - v['zelfstandigenaftrek']
        - v['startersaftrek']
        - kia
    )
    mkb = after_deductions * v['mkb_vrijstelling_pct']

    # Simple arbeidskorting computation (use after_deductions as proxy income)
    def compute_arbeidskorting(y: float) -> float:
        y = max(0.0, float(y))
        if y <= 11965:
            return 0.04156 * y
        if y <= 25845:
            return 498 + 0.15483 * (y - 11965)
        if y <= 45592:
            return 2647 + 0.00974 * (y - 25845)
        return max(0.0, 2840 - 0.03250 * (y - 45592))

    arbeidskorting = compute_arbeidskorting(after_deductions)
    taxable = after_deductions - mkb

    tax_before_credit = taxable * v['box1_rate']
    final_tax = tax_before_credit - arbeidskorting

    lines = [
        (10, 'Total revenue', revenue, 'add', ''),
        (20, 'Depreciation', -depreciation, 'subtract', ''),
        (21, 'Operational costs (car)', -operational, 'subtract', ''),
        (22, 'Interest payment', -interest, 'subtract', ''),
        (23, 'Other expenses', -other, 'subtract', ''),
        (25, 'KIA (investment deduction)', -kia, 'subtract', ''),
        (30, 'Bijtelling (tax only)', v['bijtelling'], 'add', ''),
        (40, 'Zelfstandigenaftrek', -v['zelfstandigenaftrek'], 'subtract', ''),
        (50, 'Startersaftrek', -v['startersaftrek'], 'subtract', ''),
        (70, 'MKB vrijstelling', -mkb, 'subtract', ''),
        (80, 'Taxable profit', taxable, 'result', ''),
        (90, 'Income tax', tax_before_credit, 'tax', ''),
        (100, 'Arbeidskorting', -arbeidskorting, 'credit', ''),
        (110, 'Final income tax', final_tax, 'result', ''),
    ]

    net_cash = revenue - expenses - final_tax

    outputs = {
        'final_income_tax': final_tax,
        'net_cash': net_cash,
        'revenue': revenue,
        'depreciation': depreciation,
        'expenses': expenses,
        'profit_before': profit_before,
        'kia': kia,
        'after_deductions': after_deductions,
        'mkb': mkb,
        'taxable': taxable,
        'arbeidskorting': arbeidskorting,
        'tax_before_credit': tax_before_credit,
    }

    return lines, outputs


def main():
    st.set_page_config(page_title="VrijeKas — No DB", layout="wide")
    st.warning("BIIIIG NOTE — This calculator uses AOW-age rates: special tax rules for retirees who keep working in the Netherlands.")
    st.title("VrijeKas — Simple (no DB) Streamlit")
    st.caption("Interactive version with prefilled defaults (no persistence)")

    with st.sidebar.expander('Defaults & Inputs', expanded=True):
        st.write('Change values and see outputs update instantly')
        values = {}
        for k, dv in DEFAULTS.items():
            # keep rates with a few decimals; others are simple numbers
            if k in ('box1_rate', 'mkb_vrijstelling_pct'):
                values[k] = st.number_input(k, value=float(dv), format="%.4f")
            else:
                values[k] = st.number_input(k, value=float(dv))

        st.markdown('---')
        st.write('Car expense inputs (operational):')
        # show and allow editing of car expense inputs
        values['operational_costs'] = st.number_input('operational_costs', value=float(DEFAULTS['operational_costs']), key='input_operational_costs')
        values['interest_payment'] = st.number_input('interest_payment', value=float(DEFAULTS['interest_payment']), key='input_interest_payment')
        values['other_expenses'] = st.number_input('other_expenses', value=float(DEFAULTS['other_expenses']), key='input_other_expenses')

        if st.button('Reset to defaults'):
            st.experimental_rerun()

    lines, outputs = build_tax_statement(values)

    df = pd.DataFrame([(l[1], l[2]) for l in lines], columns=['Label', 'Amount'])

    st.header('Tax statement')
    st.table(df)

    st.header('Key metrics')
    st.metric('Final income tax', f"€ {outputs['final_income_tax']:,.0f}")
    st.metric('Net cash', f"€ {outputs['net_cash']:,.0f}")

    st.header('Derived values')
    st.write(f"Total revenue: € {outputs['revenue']:,.0f}")
    st.write(f"Depreciation (annual): € {outputs['depreciation']:,.0f}")
    
    st.header('Debug — intermediate values')
    st.write(f"Expenses (depr + operational + interest + other): € {outputs['expenses']:,.0f}")
    st.write(f"Profit before deductions (revenue - expenses + bijtelling): € {outputs['profit_before']:,.0f}")
    st.write(f"KIA (investment deduction): € {outputs['kia']:,.0f}")
    st.write(f"After deductions (profit - zelfstandigenaftrek - startersaftrek - kia): € {outputs['after_deductions']:,.0f}")
    st.write(f"MKB vrijstelling (12.7%): € {outputs['mkb']:,.0f}")
    st.write(f"Taxable profit: € {outputs['taxable']:,.0f}")
    st.write(f"Arbeidskorting (credit): € {outputs['arbeidskorting']:,.0f}")
    st.write(f"Income tax before credits: € {outputs['tax_before_credit']:,.0f}")
    st.write(f"Final income tax: € {outputs['final_income_tax']:,.0f}")
    st.write(f"Net cash (revenue - expenses - final tax): € {outputs['net_cash']:,.0f}")


if __name__ == '__main__':
    main()
