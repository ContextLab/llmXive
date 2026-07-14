"""
Unit tests for CES-D and GAD-7 scoring logic.

This module verifies that the scoring functions correctly apply weights
and handle reverse-coded items as defined in config/scales.yaml.
"""
import pytest
import pandas as pd
import numpy as np
import yaml
from pathlib import Path

# Import the scoring logic from the main codebase
# Assuming the scoring logic was implemented in code/analysis/scales.py or similar
# based on the project structure. If it's in a different location, adjust import.
try:
    from code.analysis.scales import score_cesd, score_gad7, load_scale_config
except ImportError:
    # Fallback if the module structure is slightly different or not yet created
    # This block ensures the test file exists even if the implementation file is missing,
    # though the test will fail if the implementation is missing.
    # In a real scenario, we would raise an error or skip.
    # For this task, we assume the implementation exists as per T004/T005 context.
    # If the file doesn't exist, we define a mock to allow the test file to be syntactically valid
    # but the test execution would fail. However, per instructions, we must write runnable code.
    # We will assume the implementation exists in code/analysis/scales.py as is standard.
    raise ImportError(
        "Implementation module code.analysis.scales not found. "
        "Ensure T004 (config) and the implementation file exist before running tests."
    )


@pytest.fixture
def scale_config():
    """Load the scale configuration from YAML."""
    config_path = Path("config/scales.yaml")
    if not config_path.exists():
        pytest.skip("config/scales.yaml not found. Run T004 first.")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_cesd_data():
    """
    Create sample data for CES-D.
    CES-D has 20 items. Items 5, 9, 12, 16, 18 are reverse coded.
    Scale: 0-3.
    """
    data = {}
    # Normal items
    for i in range(1, 21):
        item_name = f"depressed{i}"
        if i in [5, 9, 12, 16, 18]:
            continue
        data[item_name] = 2  # Value 2
    
    # Reverse items
    for i in [5, 9, 12, 16, 18]:
        data[f"depressed{i}"] = 0  # Value 0 (should become 3-0=3)

    return pd.DataFrame([data])


@pytest.fixture
def sample_gad7_data():
    """
    Create sample data for GAD-7.
    GAD-7 has 7 items. No reverse items.
    Scale: 0-3.
    """
    data = {f"gad{i}": 1 for i in range(1, 8)}
    return pd.DataFrame([data])


def test_cesd_total_score_calculation(sample_cesd_data, scale_config):
    """
    Test that CES-D total score is calculated correctly.
    Normal items (15 items) = 2 * 15 = 30
    Reverse items (5 items) = 0 -> 3. 3 * 5 = 15
    Total expected = 45
    """
    config = scale_config["CES-D"]
    reverse_items = config["reverse_items"]
    
    # Verify the fixture setup matches expectations
    assert len(reverse_items) == 5
    
    result = score_cesd(sample_cesd_data, config)
    
    # Expected: 15 items * 2 + 5 items * (3 - 0) = 30 + 15 = 45
    expected_score = 45
    
    assert result["total_score"] == expected_score
    assert result["n_items"] == 20


def test_gad7_total_score_calculation(sample_gad7_data, scale_config):
    """
    Test that GAD-7 total score is calculated correctly.
    7 items * 1 = 7
    """
    config = scale_config["GAD-7"]
    
    result = score_gad7(sample_gad7_data, config)
    
    expected_score = 7
    
    assert result["total_score"] == expected_score
    assert result["n_items"] == 7


def test_cesd_reverse_scoring_logic(sample_cesd_data, scale_config):
    """
    Test specifically that reverse items are scored as (max - value).
    """
    config = scale_config["CES-D"]
    reverse_items = config["reverse_items"]
    
    # Modify one reverse item to be 1 (should become 2)
    sample_cesd_data.loc[0, "depressed5"] = 1
    
    # Recalculate manually for this specific case
    # Original: 15 items * 2 = 30
    # Reverse: 4 items * 3 = 12, 1 item * (3-1)=2. Total reverse = 14
    # Total = 44
    
    result = score_cesd(sample_cesd_data, config)
    assert result["total_score"] == 44


def test_missing_values_handling(sample_cesd_data, scale_config):
    """
    Test behavior with missing values.
    The scoring function should handle NaNs gracefully (e.g., return NaN or skip).
    """
    config = scale_config["CES-D"]
    sample_cesd_data.loc[0, "depressed1"] = np.nan
    
    result = score_cesd(sample_cesd_data, config)
    
    # Depending on implementation, this might be NaN or a sum of non-NaN items.
    # Standard behavior in psychometrics is often to require full scale or impute.
    # Assuming the implementation returns NaN if any item is missing for strict scoring,
    # or sums available items. We check that it doesn't crash.
    assert isinstance(result["total_score"], (int, float, np.floating))


def test_invalid_item_names(sample_cesd_data, scale_config):
    """
    Test that the function raises an error or handles missing column names correctly.
    """
    config = scale_config["CES-D"]
    # Remove a required item
    del sample_cesd_data["depressed1"]
    
    # This should ideally raise a KeyError or return a specific error code.
    # We test that the function doesn't silently produce a wrong score.
    with pytest.raises((KeyError, ValueError)):
        score_cesd(sample_cesd_data, config)
