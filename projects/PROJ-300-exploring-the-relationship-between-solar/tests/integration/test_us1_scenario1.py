"""
Specific integration test for US-1 Acceptance Scenario 1.
Exercises the pipeline on a 1-minute Vsw and Ey series (simulated or real subset)
and asserts that Pearson, Spearman, and empirical p-values are returned.
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.main import run_analysis_pipeline

def test_us1_scenario_1_detailed():
    """
    Detailed check for US-1 Scenario 1:
    - Runs pipeline on a short interval.
    - Checks specific keys: pearson, spearman, p_val_permutation.
    - Asserts they are numeric and within valid ranges.
    """
    start = datetime(2023, 1, 1, 0, 0)
    end = datetime(2023, 1, 1, 2, 0)  # 2 hours of data

    try:
        result = run_analysis_pipeline(start_date=start, end_date=end)
        
        # Check keys
        assert 'pearson' in result, "Missing 'pearson'"
        assert 'spearman' in result, "Missing 'spearman'"
        assert 'p_val_permutation' in result, "Missing 'p_val_permutation'"
        
        # Check types and ranges
        p_pearson = result['pearson']
        p_spearman = result['spearman']
        p_pval = result['p_val_permutation']
        
        assert isinstance(p_pearson, (int, float)), "Pearson is not numeric"
        assert isinstance(p_spearman, (int, float)), "Spearman is not numeric"
        assert isinstance(p_pval, (int, float)), "P-value is not numeric"
        
        assert -1.0 <= p_pearson <= 1.0, f"Pearson out of range: {p_pearson}"
        assert -1.0 <= p_spearman <= 1.0, f"Spearman out of range: {p_spearman}"
        assert 0.0 <= p_pval <= 1.0, f"P-value out of range: {p_pval}"
        
    except Exception as e:
        pytest.fail(f"Scenario 1 test failed: {str(e)}")
