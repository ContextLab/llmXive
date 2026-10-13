"""Unit tests for the T002 thin-slice Hedges' g calculation."""
import importlib.util
import math
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "code" / "data" / "thin_slice.py"

spec = importlib.util.spec_from_file_location("thin_slice", SCRIPT)
thin_slice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thin_slice)


def test_hedges_g_manual_calculation():
    # Hand-computed: n=20/22, means 75/70, sds 10/11
    n1, n2, m1, m2, s1, s2 = 20, 22, 75.0, 70.0, 10.0, 11.0
    pooled_var = ((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2)
    pooled_sd = math.sqrt(pooled_var)
    d = (m1 - m2) / pooled_sd
    j = 1 - 3.0 / (4.0 * (n1 + n2 - 2) - 1.0)
    expected_g = d * j

    g, se, ci_lo, ci_hi, p_sd, corr = thin_slice.calculate_hedges_g(
        n1, n2, m1, m2, s1, s2
    )
    assert abs(g - expected_g) < 1e-12
    assert abs(p_sd - pooled_sd) < 1e-12
    assert abs(corr - j) < 1e-12
    assert ci_lo < g < ci_hi
    expected_se = math.sqrt(
        (n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2))
    )
    assert abs(se - expected_se) < 1e-12


def test_hedges_g_rejects_invalid_inputs():
    for bad in (
        (0, 10, 1.0, 0.0, 1.0, 1.0),
        (10, 0, 1.0, 0.0, 1.0, 1.0),
        (10, 10, 1.0, 0.0, 0.0, 1.0),
        (10, 10, 1.0, 0.0, 1.0, 0.0),
    ):
        try:
          thin_slice.calculate_hedges_g(*bad)
        except ValueError:
          continue
        raise AssertionError(f"expected ValueError for {bad}")


def test_group_stat_extraction():
    om = {
        "groups": [{"id": "1", "title": "Tx"}, {"id": "2", "title": "Ctl"}],
        "statistics": [
            {"groupId": "1", "paramType": "Mean", "value": 12.5,
             "dispersionType": "Standard Deviation", "dispersionValue": 3.2},
            {"groupId": "2", "paramType": "Mean", "value": 10.1,
             "dispersionType": "Standard Deviation", "dispersionValue": 2.8},
        ],
        "denoms": [
            {"denomCount": {"counts": [
                {"groupId": "1", "value": 30},
                {"groupId": "2", "value": 28},
            ]}}
        ],
    }
    assert thin_slice._group_stat(om, "1") == (12.5, 3.2)
    assert thin_slice._group_stat(om, "2") == (10.1, 2.8)
    assert thin_slice._group_n(om, "1") == 30
    assert thin_slice._group_n(om, "2") == 28
    assert thin_slice._group_n(om, "9") is None
