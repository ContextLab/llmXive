import os
import pytest
import yaml
import csv
from pathlib import Path

# Project root relative to test file
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "energy_schema.schema.yaml"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "energy_decay.csv"

@pytest.fixture
def schema():
    if not SCHEMA_PATH.exists():
        pytest.skip("Schema file not found yet (expected if T006b not run)")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), "contracts/energy_schema.schema.yaml must exist"

def test_schema_structure(schema):
    """Verify the schema YAML has the required top-level keys."""
    assert "columns" in schema
    assert "file_type" in schema
    assert "file_path" in schema
    assert schema["file_type"] == "csv"

def test_required_columns_present(schema):
    """Verify all expected columns are defined in the schema."""
    required_cols = ["graph_id", "class", "N", "decay_rate", "r_squared", "status", "seed", "timestamp"]
    schema_cols = [col["name"] for col in schema["columns"]]
    
    for col in required_cols:
        assert col in schema_cols, f"Column '{col}' is missing from schema definition"

def test_column_types_and_constraints(schema):
    """Verify specific column constraints defined in schema."""
    col_map = {col["name"]: col for col in schema["columns"]}

    # Check decay_rate constraints
    assert col_map["decay_rate"]["type"] == "float"
    assert "minimum" in col_map["decay_rate"]
    assert "maximum" in col_map["decay_rate"]

    # Check r_squared constraints (0 to 1)
    assert col_map["r_squared"]["type"] == "float"
    assert col_map["r_squared"]["minimum"] == 0.0
    assert col_map["r_squared"]["maximum"] == 1.0

    # Check status allowed values
    assert set(col_map["status"]["allowed_values"]) == {"dissipative", "resonant"}

def test_data_file_matches_schema_if_exists(schema):
    """If data file exists, validate it against the schema structure."""
    if not DATA_PATH.exists():
        pytest.skip("Data file not found yet. This is expected if simulation hasn't run.")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    schema_headers = [col["name"] for col in schema["columns"]]
    
    # Check that all schema headers are present in the file
    for header in schema_headers:
        assert header in headers, f"Schema requires column '{header}', but it is missing in {DATA_PATH}"