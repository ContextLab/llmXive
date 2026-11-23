"""
Integration test for the Quickstart Validation script (T037).
This test ensures the validation script runs successfully and produces expected artifacts.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'code'))

from config import RESULTS_DIR

@pytest.mark.integration
def test_quickstart_script_execution():
    """
    Test that the quickstart_validator.py script runs without errors
    and generates the expected output files.
    """
    script_path = PROJECT_ROOT / 'code' / 'scripts' / 'quickstart_validator.py'
    
    if not script_path.exists():
        pytest.skip("Quickstart validator script not found.")

    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    # Assert success
    assert result.returncode == 0, f"Script failed with error:\n{result.stderr}"

    # Assert output files exist
    expected_files = [
        RESULTS_DIR / 'quickstart_coverage.csv',
        RESULTS_DIR / 'quickstart_pit.csv',
        RESULTS_DIR / 'quickstart_crps.csv'
    ]

    for f in expected_files:
        assert f.exists(), f"Expected output file missing: {f}"
        assert f.stat().st_size > 0, f"Output file is empty: {f}"

    # Assert content validity (basic check)
    import pandas as pd
    for f in expected_files:
        df = pd.read_csv(f)
        assert len(df) > 0, f"Output file has no data rows: {f}"
        # Check for expected columns based on the script logic
        if 'coverage' in str(f):
            assert 'empirical_coverage' in df.columns or 'coverage' in df.columns

@pytest.mark.integration
def test_quickstart_reproducibility():
    """
    Run the quickstart twice and verify that results are consistent
    (within a small tolerance for stochastic elements if any, though ARIMA is deterministic here).
    """
    script_path = PROJECT_ROOT / 'code' / 'scripts' / 'quickstart_validator.py'
    
    if not script_path.exists():
        pytest.skip("Quickstart validator script not found.")

    # First run
    result1 = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result1.returncode == 0, f"First run failed: {result1.stderr}"

    # Capture first run results
    import pandas as pd
    df1 = pd.read_csv(RESULTS_DIR / 'quickstart_coverage.csv')
    
    # Second run
    result2 = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result2.returncode == 0, f"Second run failed: {result2.stderr}"

    # Compare results
    df2 = pd.read_csv(RESULTS_DIR / 'quickstart_coverage.csv')
    
    # Since ARIMA is deterministic on the same data, results should be identical
    pd.testing.assert_frame_equal(df1, df2)