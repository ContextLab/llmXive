import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from analysis.statistical_test import select_and_run_test, run_full_analysis

def test_select_and_run_test_significance_flag():
    """
    Integration test for statistical test selection and SC-002 significance flagging.
    Verifies that 'is_statistically_significant' is True ONLY when p < 0.05.
    """
    # Generate synthetic data with a known significant difference
    # Group 1 (LLM-like): mean=10, std=2
    # Group 2 (Human): mean=20, std=2
    # This should yield a very low p-value (< 0.05)
    np.random.seed(42)
    group1 = np.random.normal(10, 2, 100)
    group2 = np.random.normal(20, 2, 100)
    
    result = select_and_run_test(group1, group2, alpha=0.05)
    
    assert result["p_value"] is not None, "P-value should be calculated"
    assert result["p_value"] < 0.05, "P-value should be < 0.05 for these groups"
    assert result["is_statistically_significant"] is True, "Flag should be True when p < 0.05"
    
def test_select_and_run_test_non_significance_flag():
    """
    Integration test verifying 'is_statistically_significant' is False when p >= 0.05.
    """
    # Generate synthetic data with NO significant difference
    # Both groups from same distribution
    np.random.seed(42)
    group1 = np.random.normal(10, 2, 100)
    group2 = np.random.normal(10, 2, 100)
    
    result = select_and_run_test(group1, group2, alpha=0.05)
    
    assert result["p_value"] is not None, "P-value should be calculated"
    # While it might occasionally be < 0.05 by chance, it's likely >= 0.05
    # We assert the flag logic matches the p-value logic
    expected_significant = result["p_value"] < 0.05
    assert result["is_statistically_significant"] == expected_significant, \
        f"Flag mismatch: p={result['p_value']}, flag={result['is_statistically_significant']}"

def test_run_full_analysis_file_io():
    """
    Integration test for full pipeline: loading data, running analysis, saving JSON.
    """
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_file = tmpdir_path / "input.parquet"
        output_file = tmpdir_path / "output.json"
        
        # Create dummy data
        data = {
            'classification_label': ['LLM-like'] * 50 + ['Human'] * 50,
            'review_duration': list(np.random.normal(10, 2, 50)) + list(np.random.normal(20, 2, 50))
        }
        df = pd.DataFrame(data)
        df.to_parquet(input_file)
        
        # Run analysis
        results = run_full_analysis(str(input_file), str(output_file))
        
        # Verify output file exists
        assert output_file.exists(), "Output JSON file should be created"
        
        # Verify content
        with open(output_file, 'r') as f:
            saved_results = json.load(f)
            
        assert saved_results["is_statistically_significant"] is True, \
            "Should detect significant difference in this test data"
        assert "p_value" in saved_results
        assert saved_results["p_value"] < 0.05