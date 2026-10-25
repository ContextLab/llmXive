"""
test_wilcoxon.py
-----------------
Unit tests for the wilcoxon_compare module (task T006).

The tests construct a tiny synthetic predictions DataFrame where the
expected outcome of the statistical tests is known in advance.
"""

import pandas as pd
import numpy as np
import pytest

from src.wilcoxon_compare import _compute_group_stats, run_wilcoxon_analysis

@pytest.fixture
def simple_predictions(tmp_path):
    """
    Create a minimal predictions CSV with two material classes and a single
    algorithm (“rf”).  The data are crafted so that Model B is uniformly
    better than Model A, yielding a >10 % MAPE reduction and very small
    p‑values for both Wilcoxon and paired‑t tests.
    """
    data = {
        "material_class": ["steel"] * 5 + ["aluminum"] * 5,
        "algorithm": ["rf"] * 10,
        "y_true": [100, 200, 150, 120, 180, 80, 160, 140, 110, 190],
        # Model A predictions are deliberately noisy
        "pred_A": [110, 190, 160, 130, 170, 90, 150, 130, 120, 200],
        # Model B predictions are closer to truth (≈5 % error)
        "pred_B": [102, 202, 148, 118, 182, 82, 158, 138, 112, 188],
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "model_predictions.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

def test_compute_group_stats_known_values():
    """
    Directly test the private helper on a handcrafted group where we can
    compute the expected metrics analytically.
    """
    # Five rows – small enough to enumerate manually
    y_true = np.array([100.0, 200.0, 150.0, 120.0, 180.0])
    pred_A = np.array([110.0, 190.0, 160.0, 130.0, 170.0])
    pred_B = np.array([102.0, 202.0, 148.0, 118.0, 182.0])

    grp = pd.DataFrame(
        {
            "y_true": y_true,
            "pred_A": pred_A,
            "pred_B": pred_B,
            "material_class": ["steel"] * 5,
            "algorithm": ["rf"] * 5,
        }
    )

    wilcoxon_p, ttest_p, mape_red, claim = _compute_group_stats(grp)

    # Expected MAPE values (rounded to 2 dp)
    #   A: mean(|(y‑pred)/y|) = (0.10+0.05+0.0667+0.0833+0.0556)/5 ≈ 0.0711 → 7.11 %
    #   B: mean(|(y‑pred)/y|) = (0.02+0.01+0.0133+0.0167+0.0111)/5 ≈ 0.0142 → 1.42 %
    # Reduction ≈ (7.11‑1.42)/7.11 ≈ 80 %
    assert mape_red > 10.0

    # With the synthetic data the paired differences are all non‑zero,
    # leading to very small p‑values (well below the Bonferroni‑corrected
    # α = 0.05/3 ≈ 0.0167).  The exact numeric values are not asserted,
    # only that they are below the corrected threshold.
    assert wilcoxon_p < 0.0167
    assert ttest_p < 0.0167

    # Because both conditions are satisfied, the claim flag must be True.
    assert claim is True

def test_end_to_end_wilcoxon_file(tmp_path, simple_predictions):
    """
    Run the public ``run_wilcoxon_analysis`` function on a temporary CSV
    and verify that the output file exists and contains the expected
    columns and a True claim for both material classes.
    """
    out_path = tmp_path / "wilcoxon_results.csv"
    df_out = run_wilcoxon_analysis(
        predictions_path=simple_predictions,
        output_path=out_path,
    )

    # Basic shape checks
    assert out_path.is_file()
    assert set(df_out.columns) == {
        "material_class",
        "algorithm",
        "wilcoxon_p",
        "ttest_p",
        "mape_reduction_pct",
        "improvement_claim_supported",
    }

    # There should be two rows (steel & aluminum)
    assert df_out.shape[0] == 2

    # Both rows should have claim == True
    assert df_out["improvement_claim_supported"].all()