import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

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
    p_vals = {'a': 0.01, 'b': 0.04, 'c': 0.06}
    corrected = apply_benjamini_hochberg(p_vals)
    assert len(corrected) == 3
    assert all(0 <= v <= 1 for v in corrected.values())

def test_run_shapiro_wilk():
    df = pd.DataFrame({'residuals': np.random.normal(0, 1, 100)})
    res = run_shapiro_wilk(df)
    assert 'statistic' in res
    assert 'pvalue' in res
    assert 0 <= res['statistic'] <= 1

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