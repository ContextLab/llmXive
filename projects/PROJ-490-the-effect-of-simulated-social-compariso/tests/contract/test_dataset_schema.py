import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.validators import load_schema, validate_dataframe_schema, assert_valid

CONTRACTS_DIR = project_root / "contracts"

@pytest.fixture
def dataset_schema():
    """Load the dataset schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / "dataset.schema.yaml"
    if not schema_path.exists():
        pytest.fail(f"Schema file not found at {schema_path}. Ensure T002 is complete.")
    return load_schema(schema_path)

@pytest.fixture
def valid_dataframe():
    """Create a minimal valid dataframe matching the schema requirements."""
    data = {
        "participant_id": ["P001", "P002", "P003"],
        "avatar_condition": [0.0, 1.0, 1.0],
        "pre_self_esteem": [22.0, 18.0, 25.0],
        "post_self_esteem": [23.0, 16.0, 26.0],
        "comparison_tendency": [3.5, 4.0, 2.0],
        "data_source_type": ["synthetic", "synthetic", "synthetic"]
    }
    return pd.DataFrame(data)

def test_dataset_schema_validation(dataset_schema, valid_dataframe):
    """Test that a valid dataframe passes the dataset schema."""
    result = validate_dataframe_schema(valid_dataframe, dataset_schema)
    assert result["valid"], f"Schema validation failed: {result.get('errors')}"
    assert_valid(result)

def test_dataset_schema_missing_column(dataset_schema):
    """Test that a dataframe missing a required column fails validation."""
    data = {
        "participant_id": ["P001"],
        "pre_self_esteem": [22.0],
        # Missing avatar_condition, post_self_esteem, comparison_tendency
    }
    df = pd.DataFrame(data)
    result = validate_dataframe_schema(df, dataset_schema)
    assert not result["valid"], "Validation should fail for missing required columns"

def test_dataset_schema_invalid_type(dataset_schema):
    """Test that a dataframe with invalid types fails validation."""
    data = {
        "participant_id": ["P001"],
        "avatar_condition": ["invalid"], # Should be number
        "pre_self_esteem": [22.0],
        "post_self_esteem": [23.0],
        "comparison_tendency": [3.5],
        "data_source_type": ["synthetic"]
    }
    df = pd.DataFrame(data)
    result = validate_dataframe_schema(df, dataset_schema)
    # Depending on strictness of validator, this might fail on type coercion or explicit check
    # We expect it to be flagged as invalid or have errors
    assert not result["valid"] or len(result.get("errors", [])) > 0, "Validation should fail for invalid types"