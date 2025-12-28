from seed import seed
from calculations import build_tax_statement
from db import fetch_one


def test_build_persists_derived_values(tmp_path, monkeypatch):
    # ensure DB is created in working directory for test
    seed()

    final = build_tax_statement()

    row = fetch_one("SELECT value FROM variables WHERE key='final_income_tax'")
    assert row is not None, "final_income_tax missing from variables"
    stored = row[0]
    assert abs(stored - final) < 1e-6

    # net_cash persisted
    row2 = fetch_one("SELECT value FROM variables WHERE key='net_cash'")
    assert row2 is not None
    assert isinstance(row2[0], float)
