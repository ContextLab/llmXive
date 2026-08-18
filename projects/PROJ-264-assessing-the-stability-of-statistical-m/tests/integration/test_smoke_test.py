"""
Integration test for T050 Smoke Test execution.
This test ensures that the smoke test script runs and produces the expected outputs.
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "results"

def test_smoke_test_execution():
    """
    Runs the smoke test script and verifies it exits successfully.
    This is a heavy integration test, so it is marked as such.
    """
    smoke_script = PROJECT_ROOT / "scripts" / "run_smoke_test.py"
    
    if not smoke_script.exists():
        pytest.skip("Smoke test script not found. T050 implementation missing.")
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(smoke_script)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    
    # Assert exit code
    assert result.returncode == 0, f"Smoke test failed with code {result.returncode}.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    
    # Verify output files exist and are non-empty
    required_files = [
        "raw_evaluations.csv",
        "stability_metrics.csv",
        "correlation_results.csv",
        "permutation_results.csv",
        "final_report.md",
        "regression_coefficients.csv",
        "theoretical_deviation.csv"
    ]
    
    for fname in required_files:
        fpath = RESULTS_DIR / fname
        assert fpath.exists(), f"Missing output file: {fname}"
        assert fpath.stat().st_size > 0, f"Empty output file: {fname}"

def test_smoke_test_data_integrity():
    """
    Verifies that the generated data files contain expected columns and data.
    """
    import pandas as pd
    
    # Check raw evaluations
    raw_path = RESULTS_DIR / "raw_evaluations.csv"
    if raw_path.exists():
        df = pd.read_csv(raw_path)
        assert 'accuracy' in df.columns
        assert 'f1_score' in df.columns
        assert 'dataset_id' in df.columns
        assert len(df) > 0
    
    # Check correlation results
    corr_path = RESULTS_DIR / "correlation_results.csv"
    if corr_path.exists():
        df = pd.read_csv(corr_path)
        assert 'pearson_r' in df.columns
        assert 'adj_p_value_holm' in df.columns
        assert 'significant_holm' in df.columns
        
    # Check permutation results
    perm_path = RESULTS_DIR / "permutation_results.csv"
    if perm_path.exists():
        df = pd.read_csv(perm_path)
        assert 'p_value' in df.columns
        assert 'adj_p_value_holm' in df.columns