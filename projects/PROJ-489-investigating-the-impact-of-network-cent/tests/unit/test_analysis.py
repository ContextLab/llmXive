import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import (
    check_subject_count,
    calculate_cohens_d,
    calculate_effect_sizes,
    run_lme_analysis,
    run_shapiro_wilk,
    apply_benjamini_hochberg,
    generate_analysis_report
)

def test_check_subject_count():
    data = {'subject_id': [1, 2, 3], 'val': [1, 2, 3]}
    df = pd.DataFrame(data)
    assert check_subject_count(df, min_count=3) is True
    assert check_subject_count(df, min_count=4) is False

def test_calculate_cohens_d():
    g1 = np.array([1.0, 2.0, 3.0])
    g2 = np.array([4.0, 5.0, 6.0])
    d = calculate_cohens_d(g1, g2)
    assert isinstance(d, float)

def test_apply_benjamini_hochberg():
    """
    Unit test for FDR correction logic (Benjamini-Hochberg procedure).
    
    Tests the core algorithm:
    1. Sorts p-values
    2. Calculates rank-based thresholds
    3. Ensures monotonicity (corrected p-values do not decrease as rank increases)
    4. Validates output bounds (0-1)
    """
    # Test Case 1: Mixed p-values
    p_vals = {'a': 0.01, 'b': 0.04, 'c': 0.06}
    corrected = apply_benjamini_hochberg(p_vals)
    
    assert len(corrected) == 3
    assert all(0 <= v <= 1 for v in corrected.values())
    
    # Verify monotonicity logic:
    # Sorted p-values: 0.01 (rank 1), 0.04 (rank 2), 0.06 (rank 3)
    # Thresholds: 0.01 * 3/3 = 0.01, 0.04 * 3/2 = 0.06, 0.06 * 3/1 = 0.18
    # The BH procedure ensures that if p_(i) > threshold, we don't necessarily reject,
    # but the corrected values must be monotonically non-decreasing with respect to sorted rank.
    
    # Convert to sorted list to check monotonicity
    sorted_items = sorted(corrected.items(), key=lambda x: p_vals[x[0]])
    sorted_corrected = [v for _, v in sorted_items]
    
    # Check that corrected values are non-decreasing
    for i in range(1, len(sorted_corrected)):
        assert sorted_corrected[i] >= sorted_corrected[i-1], \
            f"BH correction violated monotonicity: {sorted_corrected}"

    # Test Case 2: All significant p-values
    p_vals_sig = {'x': 0.001, 'y': 0.002}
    corrected_sig = apply_benjamini_hochberg(p_vals_sig)
    assert all(v <= 0.05 for v in corrected_sig.values())

    # Test Case 3: All non-significant p-values
    p_vals_ns = {'u': 0.5, 'v': 0.8, 'w': 0.9}
    corrected_ns = apply_benjamini_hochberg(p_vals_ns)
    # Even if raw p is high, corrected might be > 1, but we clamp to 1.0
    assert all(v <= 1.0 for v in corrected_ns.values())

def test_run_shapiro_wilk():
    """
    Unit test for residual diagnostics JSON generation.
    
    Verifies that run_shapiro_wilk returns a dictionary compatible with JSON
    serialization, containing 'statistic' and 'pvalue' keys with valid numeric values.
    This ensures the diagnostic output can be correctly written to 
    data/results/residuals_diagnostics.json as required by T036.
    """
    # Generate synthetic residuals for testing the diagnostic function
    # In real usage, these would come from the LME model residuals
    np.random.seed(42)
    residuals = np.random.normal(0, 1, 100)
    df = pd.DataFrame({'residuals': residuals})
    
    # Execute the function
    res = run_shapiro_wilk(df)
    
    # Verify structure
    assert 'statistic' in res, "Result missing 'statistic' key"
    assert 'pvalue' in res, "Result missing 'pvalue' key"
    
    # Verify value constraints for Shapiro-Wilk
    # Statistic should be between 0 and 1
    assert 0 <= res['statistic'] <= 1, f"Statistic {res['statistic']} out of range [0, 1]"
    
    # P-value should be between 0 and 1
    assert 0 <= res['pvalue'] <= 1, f"P-value {res['pvalue']} out of range [0, 1]"
    
    # Verify types are JSON serializable (float/int)
    assert isinstance(res['statistic'], (float, int)), "Statistic must be numeric"
    assert isinstance(res['pvalue'], (float, int)), "P-value must be numeric"
    
    # Verify JSON serializability explicitly
    json_str = json.dumps(res)
    parsed_back = json.loads(json_str)
    assert parsed_back['statistic'] == res['statistic']
    assert parsed_back['pvalue'] == res['pvalue']

def test_generate_analysis_report():
    # Mock LME result object is complex, so we test the dict generation logic
    mock_result = type('MockModel', (), {
        'fe_params': {'x1': 0.5, 'x2': -0.2},
        'summary': lambda: "Mock Summary"
    })()
    raw_p = {'x1': 0.01, 'x2': 0.05}
    fdr_p = {'x1': 0.01, 'x2': 0.05}
    shapiro = {'statistic': 0.98, 'pvalue': 0.5}
    
    report = generate_analysis_report(mock_result, raw_p, fdr_p, shapiro, n_subjects=30)
    assert 'metadata' in report
    assert 'lme_results' in report
    assert report['metadata']['n_subjects'] == 30
    # Verify the report structure matches what is expected for JSON serialization
    assert 'diagnostics' in report
    assert 'shapiro_wilk' in report['diagnostics']
    assert report['diagnostics']['shapiro_wilk']['statistic'] == 0.98