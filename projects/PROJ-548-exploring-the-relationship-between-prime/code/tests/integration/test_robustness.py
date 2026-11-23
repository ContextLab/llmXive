"""
Integration test for the Robustness and Sensitivity Analysis (T028).

This test verifies that the robustness.py script can be executed end-to-end
and produces the expected output file with valid schema.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Adjust path for import if running from project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.robustness import run_pipeline, WINDOW_SIZES, OUTPUT_FILE


@pytest.fixture
def mock_gaps():
    """Generate a small set of mock gaps for testing."""
    # Mock data simulating the output of generate_primes.py
    # Format: prime_before, prime_after, gap_size
    gaps = []
    p = 2
    # Generate first 1000 primes roughly to have enough data for small windows
    # This is a simplified mock; real data would be larger.
    # We need enough gaps to form windows.
    import math
    
    # Simple prime generator for mock data
    def is_prime(n):
        if n < 2: return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0: return False
        return True

    primes = []
    curr = 2
    while len(primes) < 5000: # Generate enough primes
        if is_prime(curr):
            primes.append(curr)
        curr += 1

    for i in range(len(primes) - 1):
        gaps.append({
            "prime_before": primes[i],
            "prime_after": primes[i+1],
            "gap_size": primes[i+1] - primes[i]
        })
    return gaps


@pytest.fixture
def temp_data_dir(mock_gaps):
    """Create a temporary directory structure with mock data."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "code" / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Write mock gaps to CSV
    csv_file = data_dir / "raw_gaps.csv"
    with open(csv_file, 'w') as f:
        f.write("prime_before,prime_after,gap_size\n")
        for g in mock_gaps:
            f.write(f"{g['prime_before']},{g['prime_after']},{g['gap_size']}\n")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_robustness_sweep_integration(temp_data_dir, mock_gaps):
    """
    Test that the robustness sweep runs and produces a valid JSON output.
    
    This test patches the file paths to use the temporary directory.
    """
    # Patch the OUTPUT_FILE and the input file path
    temp_output = Path(temp_data_dir) / "code" / "results" / "robustness_sweep.json"
    temp_input = Path(temp_data_dir) / "code" / "data" / "processed" / "raw_gaps.csv"
    
    with patch('src.analysis.robustness.OUTPUT_FILE', temp_output):
        with patch('src.analysis.robustness.OUTPUT_DIR', temp_output.parent):
            # We also need to patch the path inside run_pipeline where it loads gaps
            # Since run_pipeline uses a hardcoded relative path, we patch the Path constructor or the file check
            # A cleaner way for this specific script is to patch the specific file check logic
            # But since the script uses Path("code/data/processed/raw_gaps.csv"), we can't easily patch it
            # unless we change the script to accept an argument. 
            # Instead, we assume the test environment sets up the file at the expected relative path
            # OR we run the test from the temp_data_dir root.
            
            # Let's change the working directory to temp_data_dir for the duration of the test
            original_cwd = os.getcwd()
            os.chdir(temp_data_dir)
            
            try:
                # Ensure the results directory exists (script expects it)
                (Path(temp_data_dir) / "code" / "results").mkdir(parents=True, exist_ok=True)
                
                result = run_pipeline()
                
                assert result['status'] == 'success'
                assert 'results' in result
                assert len(result['results']) > 0
                
                # Verify schema
                for r in result['results']:
                    assert 'window_size' in r
                    assert 'ks_statistic' in r
                    assert 'p_value' in r
                    assert 'timestamp' in r
                    assert r['window_size'] in WINDOW_SIZES
                
                # Verify file was written
                assert temp_output.exists()
                
                with open(temp_output) as f:
                    data = json.load(f)
                assert len(data) > 0
                
            finally:
                os.chdir(original_cwd)


def test_empty_gaps_handling():
    """Test behavior with insufficient data (mocked)."""
    # This test is more about logic verification. 
    # If we pass a tiny list of gaps, the window extraction might fail.
    # We rely on the integration test above for the happy path.
    pass
