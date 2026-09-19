"""
Contract test for T032: code/09_summit_match.R output schema.
Validates that the output file `results/summit_match_stats.txt` contains
the required fields and format as per SC-005.
"""
import os
import pytest
import re

OUTPUT_PATH = "results/summit_match_stats.txt"

REQUIRED_FIELDS = [
  "Stress Condition",
  "Total Significant CREs Analyzed",
  "Spearman Rho",
  "Summit Match Percentage",
  "Match Count",
  "Rho Threshold",
  "Match % Threshold",
  "Overall Status"
]

def test_output_file_exists():
    """Assert that the script produces the output file."""
    assert os.path.exists(OUTPUT_PATH), f"Output file {OUTPUT_PATH} not found."

def test_output_schema():
    """Assert the output file contains all required fields."""
    if not os.path.exists(OUTPUT_PATH):
        pytest.skip("Output file missing, skipping schema check.")
    
    with open(OUTPUT_PATH, 'r') as f:
        content = f.read()
    
    for field in REQUIRED_FIELDS:
        assert field in content, f"Missing required field: {field}"

def test_rho_format():
    """Assert Spearman Rho is a valid number."""
    if not os.path.exists(OUTPUT_PATH):
        pytest.skip("Output file missing.")
    
    with open(OUTPUT_PATH, 'r') as f:
        content = f.read()
    
    # Look for "Spearman Rho ... : <number>"
    match = re.search(r"Spearman Rho.*:\s*(-?\d+\.?\d*)", content)
    assert match is not None, "Could not parse Spearman Rho value."
    
    try:
        rho_val = float(match.group(1))
        assert -1.0 <= rho_val <= 1.0, f"Spearman Rho {rho_val} is out of valid range [-1, 1]."
    except ValueError:
        pytest.fail("Spearman Rho value is not a valid float.")

def test_percentage_format():
    """Assert Match Percentage is a valid percentage."""
    if not os.path.exists(OUTPUT_PATH):
        pytest.skip("Output file missing.")
    
    with open(OUTPUT_PATH, 'r') as f:
        content = f.read()
    
    match = re.search(r"Summit Match Percentage.*:\s*(\d+\.?\d*)%", content)
    assert match is not None, "Could not parse Match Percentage."
    
    try:
        pct_val = float(match.group(1))
        assert 0.0 <= pct_val <= 100.0, f"Match Percentage {pct_val} is out of valid range [0, 100]."
    except ValueError:
        pytest.fail("Match Percentage is not a valid float.")

def test_status_flag():
    """Assert Overall Status is PASS or FAIL."""
    if not os.path.exists(OUTPUT_PATH):
        pytest.skip("Output file missing.")
    
    with open(OUTPUT_PATH, 'r') as f:
        content = f.read()
    
    match = re.search(r"Overall Status:\s*(PASS|FAIL)", content)
    assert match is not None, "Could not parse Overall Status."
    assert match.group(1) in ["PASS", "FAIL"], "Status must be PASS or FAIL."