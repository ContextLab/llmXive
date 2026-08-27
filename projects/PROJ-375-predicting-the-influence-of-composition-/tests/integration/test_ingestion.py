"""
Integration tests for the data ingestion pipeline.
"""
import os
import sys
import pytest
import yaml
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
        Since the ingestion pipeline (T013, T016) is not fully implemented
        in this task scope, we validate the contract definition itself
        and the logic that would check the DataFrame columns.
        
        In a full integration run, this would:
        1. Run the ingestion script to produce a temporary CSV/Parquet.
        2. Load the DataFrame.
        3. Assert df.columns matches get_required_fields(schema).
        
        Here, we assert the schema is well-formed and the expected columns
        list matches the schema's required fields exactly.
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

        # Simulate the check logic that would happen on a DataFrame
        # If we had a dataframe 'df', the check would be:
        # missing = set(required_fields) - set(df.columns)
        # assert len(missing) == 0, f"Missing columns: {missing}"
        
        # Verify specific critical fields exist in schema definition
        critical_fields = ["composition", "cte", "amorphous_state_flag"]
        for field in critical_fields:
            assert field in schema["properties"], f"Critical field '{field}' missing from schema properties"
            assert field in schema["required"], f"Critical field '{field}' missing from schema required list"

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