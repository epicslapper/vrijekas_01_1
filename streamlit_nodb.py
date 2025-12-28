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
}


def calculate_revenue(v):
    return v['hrs_home'] * v['rate_home'] + v['hrs_onsite'] * v['rate_onsite']


def calculate_depreciation(v):
    base = v['tesla_price'] - v['vat_recovered']
    return base / v['depr_years']


def build_tax_statement(v):
    revenue = calculate_revenue(v)
    depreciation = calculate_depreciation(v)
    expenses = depreciation
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
        (30, 'Bijtelling (tax only)', v['bijtelling'], 'add', ''),
        (40, 'Zelfstandigenaftrek', -v['zelfstandigenaftrek'], 'subtract', ''),
        (50, 'Startersaftrek', -v['startersaftrek'], 'subtract', ''),
        (60, 'MKB vrijstelling', -mkb, 'subtract', ''),
        (70, 'Taxable profit', taxable, 'result', ''),
        (80, 'Income tax', tax_before_credit, 'tax', ''),
        (90, 'Arbeidskorting', -arbeidskorting, 'credit', ''),
        (100, 'Final income tax', final_tax, 'result', ''),
    ]

    net_cash = revenue - expenses - final_tax

    outputs = {
        'final_income_tax': final_tax,
        'net_cash': net_cash,
        'revenue': revenue,
        'depreciation': depreciation,
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


if __name__ == '__main__':
    main()
