"""
Contract test for phylogenetic permutation test output schema (US3).

Verifies that data/processed/permutation_results.json contains the 
required structure for significance testing results.

Expected schema:
- p_value (float)
- significance (bool or string flag)
- permutation_count (int)
- observed_statistic (float)
"""
import os
import sys
import pytest
import json
from pathlib import Path

# Add code directory to path for imports if needed
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.logging import get_logger

logger = get_logger(__name__)

PERMUTATION_RESULTS_PATH = Path("data/processed/permutation_results.json")
REQUIRED_KEYS = [
    "p_value",
    "significance",
    "permutation_count",
    "observed_statistic"
]

def check_file_exists():
    """Verify the permutation results file exists."""
    assert PERMUTATION_RESULTS_PATH.exists(), \
        f"Permutation results file not found at {PERMUTATION_RESULTS_PATH}"

def load_permutation_results():
    """Load the permutation results JSON."""
    check_file_exists()
    try:
        with open(PERMUTATION_RESULTS_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in permutation results: {e}")
    except Exception as e:
        pytest.fail(f"Failed to load permutation results: {e}")

def test_required_keys_present():
    """Test that all required keys are present in the results."""
    results = load_permutation_results()
    missing_keys = set(REQUIRED_KEYS) - set(results.keys())
    assert not missing_keys, f"Missing required keys: {missing_keys}"
    logger.info("All required keys present in permutation results.")

def test_p_value_valid_range():
    """Test that p_value is a valid probability."""
    results = load_permutation_results()
    p_val = results["p_value"]
    assert isinstance(p_val, (int, float)), "p_value must be numeric"
    assert 0 <= p_val <= 1, f"p_value {p_val} is not in range [0, 1]"
    logger.info(f"P-value validated: {p_val}")

def test_significance_flag_consistent():
    """Test that significance flag is consistent with p_value."""
    results = load_permutation_results()
    p_val = results["p_value"]
    sig_flag = results["significance"]
    
    # Handle both boolean and string representations
    if isinstance(sig_flag, bool):
        expected_sig = p_val < 0.05
        assert sig_flag == expected_sig, \
            f"Significance flag {sig_flag} inconsistent with p_value {p_val}"
    elif isinstance(sig_flag, str):
        # Accept common string representations
        assert sig_flag in ["significant", "not significant", "True", "False", "1", "0"], \
            f"Invalid significance string: {sig_flag}"
        if sig_flag in ["significant", "True", "1"]:
            assert p_val < 0.05, f"Significant flag set but p_value {p_val} >= 0.05"
        else:
            assert p_val >= 0.05, f"Not significant flag set but p_value {p_val} < 0.05"
    
    logger.info(f"Significance flag validated: {sig_flag} (p={p_val})")

def test_permutation_count_positive():
    """Test that permutation count is a positive integer."""
    results = load_permutation_results()
    count = results["permutation_count"]
    assert isinstance(count, int), "permutation_count must be integer"
    assert count > 0, "permutation_count must be positive"
    logger.info(f"Permutation count validated: {count}")

def test_observed_statistic_numeric():
    """Test that observed statistic is numeric."""
    results = load_permutation_results()
    stat = results["observed_statistic"]
    assert isinstance(stat, (int, float)), "observed_statistic must be numeric"
    logger.info(f"Observed statistic validated: {stat}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])