"""
Unit tests for statistical utilities:
* Benjamini‑Hochberg false discovery rate correction.
* Application of the correction to a DataFrame of correlation results.
"""

import pandas as pd
import pytest
import numpy as np

from code.feature_analysis import benjamini_hochberg, apply_bh_correction_to_df

def test_bh_correction():
    # Known p-values for testing BH
    p_vals = [0.01, 0.04, 0.03, 0.20]
    # Sorted: 0.01, 0.03, 0.04, 0.20
    # Adjusted: 
    # 0.01 * 4 / 1 = 0.04
    # 0.03 * 4 / 2 = 0.06
    # 0.04 * 4 / 3 = 0.0533
    # 0.20 * 4 / 4 = 0.20
    adj, reject = benjamini_hochberg(p_vals, alpha=0.05)
    
    assert len(adj) == len(p_vals)
    assert all(0.0 <= a <= 1.0 for a in adj)
    # The most significant p-value should remain the most significant
    assert np.argmin(adj) == np.argmin(p_vals)

def test_apply_bh_to_df():
    results = [
        ("feature1", 0.5, 0.001), # Very significant
        ("feature2", -0.2, 0.5)    # Not significant
    ]
    df = apply_bh_correction_to_df(results, alpha=0.05)
    
    assert "adjusted_p_value" in df.columns
    assert "is_significant" in df.columns
    
    # Check specific values
    f1_sig = df.loc[df["feature"] == "feature1", "is_significant"].iloc[0]
    f2_sig = df.loc[df["feature"] == "feature2", "is_significant"].iloc[0]
    
    assert f1_sig is True
    assert f2_sig is False
