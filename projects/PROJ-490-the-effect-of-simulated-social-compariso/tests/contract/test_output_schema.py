import pytest
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.validators import load_schema, validate_dataframe_schema, assert_valid

CONTRACTS_DIR = project_root / "contracts"

@pytest.fixture
def output_schema():
    return load_schema(CONTRACTS_DIR / "output.schema.yaml")

@pytest.fixture
def valid_output_df():
    data = {
        "term": ["Intercept", "avatar_condition", "pre_self_esteem"],
        "coefficient": [10.0, 2.5, 0.8],
        "std_error": [1.0, 0.5, 0.1],
        "p_value": [0.0, 0.01, 0.001],
        "ci_lower": [8.0, 1.5, 0.6],
        "ci_upper": [12.0, 3.5, 1.0]
    }
    return pd.DataFrame(data)

def test_output_schema_validation(output_schema, valid_output_df):
    """Test that a valid output dataframe passes the output schema."""
    result = validate_dataframe_schema(valid_output_df, output_schema)
    assert result["valid"], f"Schema validation failed: {result.get('errors')}"
    assert_valid(result)

def test_output_schema_missing_column(output_schema):
    """Test that a dataframe missing a required column fails validation."""
    data = {
        "term": ["Intercept"],
        "coefficient": [10.0],
        # Missing std_error, p_value, etc.
    }
    df = pd.DataFrame(data)
    result = validate_dataframe_schema(df, output_schema)
    assert not result["valid"]
