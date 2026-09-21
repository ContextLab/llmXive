import os
import subprocess
import pytest
import pandas as pd
from pathlib import Path

# Test for T032: Summit Match Verification
# This test verifies that the script code/09_summit_match.R runs successfully
# and produces the expected output file with the correct schema.

@pytest.mark.integration
def test_summit_match_script_execution():
    """
    Integration test for T032: Summit Match Verification.
    
    Input:
      - results/CRE_ranked_heatshock.md (must exist from T018)
      - tracks/heatshock_CRE_signal.bw (must exist from T031)
    
    Output:
      - results/summit_match_stats.txt
    
    Assertions:
      - File exists.
      - File contains headers: correlation_rho, match_percentage, exit_code.
      - exit_code is 0.
      - correlation_rho and match_percentage are numeric.
    """
    # Ensure input files exist (mock data might be needed if real data is not present)
    # For this test, we assume the pipeline has been run up to T031 and T018.
    # If running in isolation, we might need to create mock files.
    
    report_path = Path("results/CRE_ranked_heatshock.md")
    bw_path = Path("tracks/heatshock_CRE_signal.bw")
    output_path = Path("results/summit_match_stats.txt")
    
    # Skip if input files are missing (not a failure of the script, but of the environment)
    if not report_path.exists() or not bw_path.exists():
        pytest.skip("Input files for summit match test are missing. Ensure T018 and T031 have run.")
    
    # Run the R script
    result = subprocess.run(
        ["Rscript", "code/09_summit_match.R", "heatshock", "5"],
        capture_output=True,
        text=True
    )
    
    # Check exit code
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # Check output file exists
    assert output_path.exists(), "Output file results/summit_match_stats.txt was not created."
    
    # Read and validate output
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) >= 2, "Output file should have at least a header and one data row."
    
    header = lines[0].strip().split('\t')
    expected_headers = ['correlation_rho', 'match_percentage', 'exit_code']
    assert header == expected_headers, f"Unexpected headers: {header}"
    
    data_row = lines[1].strip().split('\t')
    assert len(data_row) == 3, f"Data row should have 3 columns: {data_row}"
    
    rho, match_pct, exit_code = data_row
    
    # Validate types
    try:
        rho_val = float(rho)
        match_pct_val = float(match_pct)
        exit_code_val = int(exit_code)
    except ValueError:
        pytest.fail("Output values are not numeric.")
    
    assert exit_code_val == 0, f"Expected exit_code 0, got {exit_code_val}"
    
    # Validate ranges (optional, but good practice)
    # rho should be between -1 and 1
    assert -1 <= rho_val <= 1, f"rho {rho_val} is out of range [-1, 1]"
    # match_pct should be between 0 and 100
    assert 0 <= match_pct_val <= 100, f"match_percentage {match_pct_val} is out of range [0, 100]"

@pytest.mark.integration
def test_summit_match_content_validation():
    """
    Additional validation for T032 output content.
    Checks that the warning logic is triggered if match_percentage < 90.
    This is harder to test without mocking, so we just check the output format.
    """
    output_path = Path("results/summit_match_stats.txt")
    
    if not output_path.exists():
        pytest.skip("Output file not found. Run the script first.")
    
    with open(output_path, 'r') as f:
        content = f.read()
    
    # Basic check that the file is not empty and has the expected structure
    assert 'correlation_rho' in content
    assert 'match_percentage' in content
    assert 'exit_code' in content