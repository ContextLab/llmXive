import pytest
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys
import os

# Add the project root to the path to allow imports from code/
# This ensures the tests run correctly in the project environment
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.scales import load_scale_config, score_cesd, score_gad7, apply_scale_scoring

@pytest.fixture
def scale_config_path():
    """Return the path to the scales.yaml configuration file."""
    return project_root / "code" / "config" / "scales.yaml"

@pytest.fixture
def sample_data():
    """Create a mock dataset with raw items for CES-D and GAD-7."""
    # CES-D items (1-4 scale, 20 items)
    cesd_cols = [f"cesd_item_{i}" for i in range(1, 21)]
    # GAD-7 items (1-4 scale, 7 items)
    gad7_cols = [f"gad7_item_{i}" for i in range(1, 8)]
    
    data = {
        "id": [1, 2, 3, 4, 5],
        **{col: [1, 2, 3, 2, 1] for col in cesd_cols},
        **{col: [1, 1, 2, 3, 1] for col in gad7_cols},
        # Pre-aggregated scores to test fallback logic
        "depression": [20, 40, 60, 40, 20],
        "anxiety": [10, 10, 20, 30, 10]
    }
    return pd.DataFrame(data)

@pytest.fixture
def empty_data():
    """Create a mock dataset with only ID."""
    return pd.DataFrame({"id": [1, 2, 3]})

def test_scale_config_exists(scale_config_path):
    """Test that the scales.yaml configuration file exists."""
    assert scale_config_path.exists(), f"Config file not found: {scale_config_path}"

def test_scale_config_valid_yaml(scale_config_path):
    """Test that the scales.yaml file is valid YAML."""
    try:
        with open(scale_config_path, 'r') as f:
            config = yaml.safe_load(f)
        assert config is not None, "Config file is empty or invalid YAML"
        assert "CES-D" in config, "Missing CES-D configuration"
        assert "GAD-7" in config, "Missing GAD-7 configuration"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in config file: {e}")

def test_scale_variables_match_spec(scale_config_path):
    """Test that the variables in the config match the spec's Data Dictionary."""
    with open(scale_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check for expected variable mappings per spec
    assert config["CES-D"]["variable"] == "depression", "CES-D variable mapping incorrect"
    assert config["GAD-7"]["variable"] == "anxiety", "GAD-7 variable mapping incorrect"

def test_cesd_scoring_logic():
    """Test CES-D scoring logic with raw items."""
    # Create a simple test case where we know the expected sum
    # Assuming 20 items, all scored 1 (minimum) -> sum = 20
    # Assuming 20 items, all scored 4 (maximum) -> sum = 80
    data = {f"cesd_item_{i}": [4] * 5 for i in range(1, 21)}
    df = pd.DataFrame(data)
    
    # Score the CES-D
    result = score_cesd(df)
    
    # Each row should sum to 80 (20 items * 4)
    assert result["depression"].iloc[0] == 80, f"Expected 80, got {result['depression'].iloc[0]}"
    assert len(result) == 5, "Row count mismatch"

def test_gad7_scoring_logic():
    """Test GAD-7 scoring logic with raw items."""
    # 7 items, all scored 4 (maximum) -> sum = 28
    data = {f"gad7_item_{i}": [4] * 5 for i in range(1, 8)}
    df = pd.DataFrame(data)
    
    result = score_gad7(df)
    
    # Each row should sum to 28 (7 items * 4)
    assert result["anxiety"].iloc[0] == 28, f"Expected 28, got {result['anxiety'].iloc[0]}"

def test_apply_scale_scoring_with_raw_items(sample_data):
    """Test apply_scale_scoring when raw items are present."""
    # The function should detect raw items and score them
    result = apply_scale_scoring(sample_data)
    
    # Verify that the scoring was applied (values should be sums, not original 1-4)
    # Since we mixed 1,2,3 in sample_data, the sum should be > 20 for CES-D (20 items)
    # and > 7 for GAD-7 (7 items)
    assert "depression" in result.columns, "Depression score not generated"
    assert "anxiety" in result.columns, "Anxiety score not generated"
    
    # Check that the values are different from the pre-aggregated columns in the input
    # (The function should overwrite pre-aggregated if raw items are found)
    assert result["depression"].iloc[0] != sample_data["depression"].iloc[0], \
        "Scoring should override pre-aggregated values when raw items exist"

def test_apply_scale_scoring_with_aggregate_only(empty_data):
    """Test apply_scale_scoring when only pre-aggregated columns exist."""
    # Add pre-aggregated columns but no raw items
    empty_data["depression"] = [10, 20, 30]
    empty_data["anxiety"] = [5, 10, 15]
    
    result = apply_scale_scoring(empty_data)
    
    # Should use the pre-aggregated columns directly
    assert result["depression"].iloc[0] == 10, "Should use pre-aggregated depression score"
    assert result["anxiety"].iloc[0] == 5, "Should use pre-aggregated anxiety score"

def test_missing_scale_columns():
    """Test behavior when scale columns are missing."""
    df = pd.DataFrame({"id": [1]})
    
    # Should not crash, but might return NaN or original df depending on implementation
    # The key is that it handles the missing data gracefully
    result = apply_scale_scoring(df)
    
    # Verify the function returns a DataFrame
    assert isinstance(result, pd.DataFrame), "Function must return a DataFrame"

def test_scale_config_type_validation(scale_config_path):
    """Test that the scale configuration has valid types."""
    with open(scale_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    for scale_name, scale_config in config.items():
        assert "type" in scale_config, f"Missing 'type' key for {scale_name}"
        assert scale_config["type"] in ["aggregate_score", "raw_items"], \
            f"Invalid type for {scale_name}: {scale_config['type']}"

def test_scale_config_variable_mapping(scale_config_path):
    """Test that scale variable mappings are present and valid."""
    with open(scale_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    for scale_name, scale_config in config.items():
        assert "variable" in scale_config, f"Missing 'variable' key for {scale_name}"
        assert isinstance(scale_config["variable"], str), \
            f"Variable name for {scale_name} must be a string"