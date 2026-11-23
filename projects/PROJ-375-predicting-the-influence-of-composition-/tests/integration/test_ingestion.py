"""
Integration tests for the data ingestion pipeline.
"""
import os
import sys
import pytest
import yaml
import pandas as pd
from pathlib import Path
from typing import List

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from ingestion.fetch_data import setup_logging
from utils.io import compute_sha256

# Constants
SCHEMA_PATH = project_root / "contracts" / "mg_dataset.schema.yaml"
EXPECTED_COLUMNS = [
    "composition",
    "cte",
    "weighted_mean_atomic_radius",
    "electronegativity_variance",
    "vec",
    "atomic_size_mismatch",
    "amorphous_state_flag",
    "alloy_family",
    "source"
]

def load_schema(schema_path: Path) -> dict:
    """Load the YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def get_required_fields(schema: dict) -> List[str]:
    """Extract required field names from the schema."""
    return schema.get('required', [])

def validate_dataframe_columns(df: pd.DataFrame, schema: dict) -> None:
    """
    Validate that a DataFrame's columns match the schema's required fields.
    
    Args:
        df: The DataFrame to validate.
        schema: The loaded schema dictionary.
        
    Raises:
        AssertionError: If columns do not match or are missing.
    """
    required_fields = get_required_fields(schema)
    df_columns = list(df.columns)
    
    missing = set(required_fields) - set(df_columns)
    extra = set(df_columns) - set(required_fields)
    
    assert len(missing) == 0, f"Missing required columns: {missing}"
    # Note: We allow extra columns for future extensibility, but strict schema
    # validation usually checks exact match. Here we focus on required fields.
    if extra:
        print(f"Warning: Extra columns found (allowed): {extra}")

class TestSchemaValidation:
    """Tests to verify output schema matches the defined contract."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure logging is configured for tests."""
        setup_logging()
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_validation(self):
        """
        Verify output schema matches contracts/mg_dataset.schema.yaml.
        
        This test loads the schema definition and asserts that the expected
        columns defined in the schema match the required fields.
        It also validates the logic against a mock DataFrame to ensure
        the validation function works correctly.
        """
        schema = load_schema(SCHEMA_PATH)
        required_fields = get_required_fields(schema)
        
        # Assert the schema has the required structure
        assert "properties" in schema, "Schema must define 'properties'"
        assert "required" in schema, "Schema must define 'required' fields"
        
        # Assert the list of columns we expect to validate against matches the schema
        assert sorted(EXPECTED_COLUMNS) == sorted(required_fields), (
            f"Expected columns {EXPECTED_COLUMNS} do not match schema required fields {required_fields}"
        )

        # Verify specific critical fields exist in schema definition
        critical_fields = ["composition", "cte", "amorphous_state_flag"]
        for field in critical_fields:
            assert field in schema["properties"], f"Critical field '{field}' missing from schema properties"
            assert field in schema["required"], f"Critical field '{field}' missing from schema required list"

        # Create a mock DataFrame with the correct columns to test the validation logic
        mock_data = {col: [] for col in EXPECTED_COLUMNS}
        mock_df = pd.DataFrame(mock_data)
        
        # This should pass without error
        validate_dataframe_columns(mock_df, schema)

        # Test that it fails with missing columns
        incomplete_data = {col: [] for col in EXPECTED_COLUMNS if col != "cte"}
        incomplete_df = pd.DataFrame(incomplete_data)
        
        with pytest.raises(AssertionError) as exc_info:
            validate_dataframe_columns(incomplete_df, schema)
        assert "Missing required columns" in str(exc_info.value)
        assert "cte" in str(exc_info.value)

    def test_schema_type_constraints(self):
        """Verify that specific fields have expected type constraints in the schema."""
        schema = load_schema(SCHEMA_PATH)
        props = schema["properties"]
        
        # Check 'cte' is a number
        assert props["cte"]["type"] == "number", "CTE must be a number"
        
        # Check 'amorphous_state_flag' is an integer with enum constraints
        assert props["amorphous_state_flag"]["type"] == "integer", "Amorphous flag must be integer"
        assert set(props["amorphous_state_flag"]["enum"]) == {0, 1}, "Amorphous flag must be 0 or 1"
        
        # Check 'alloy_family' enum
        assert set(props["alloy_family"]["enum"]) == {"Zr", "Pd", "Fe", "Other"}, "Invalid alloy families"