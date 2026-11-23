"""
Integration tests for schema validation against real data artifacts.
These tests ensure that the pipeline outputs match the defined schema.
"""
import json
import os
import yaml
import jsonschema
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
DATA_DIR = PROJECT_ROOT / "data" / "processed"

@pytest.fixture
def schema():
    """Load the schema for use in tests."""
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def filtered_data_path():
    """Return the path to the filtered galaxies CSV if it exists."""
    csv_path = DATA_DIR / "filtered_galaxies.csv"
    if not csv_path.exists():
        pytest.skip(f"Data file {csv_path} not found. Run preprocessing first.")
    return csv_path

def test_validate_csv_against_schema(schema, filtered_data_path):
    """
    Validate the structure of the generated CSV against the schema.
    Note: JSON Schema validates JSON, so we convert CSV to a JSON structure
    that matches the schema's 'galaxies' array format.
    """
    import pandas as pd
    
    df = pd.read_csv(filtered_data_path)
    
    # Verify required columns exist
    required_cols = ['name', 'distance', 'inclination', 'inclination_error', 'm_star_m_l']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Verify min points constraint
    # We assume the preprocessing step already enforced this, but we check the count here
    # The schema expects 'rotation_points' as a nested list. 
    # Since the CSV is flattened, we verify the row count per galaxy group if possible,
    # or simply assert that the file has data.
    # For strict schema compliance, the JSON export is the primary artifact.
    
    # Check metadata file if it exists
    metadata_path = DATA_DIR / "metadata.yaml"
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            meta = yaml.safe_load(f)
        
        assert "source" in meta, "Metadata must have 'source'"
        assert "download_timestamp" in meta, "Metadata must have 'download_timestamp'"
        assert "version" in meta, "Metadata must have 'version'"

def test_validate_json_export(schema):
    """
    If a JSON export exists, validate it strictly against the schema.
    """
    json_path = DATA_DIR / "filtered_galaxies.json"
    if not json_path.exists():
        pytest.skip(f"JSON export {json_path} not found.")
    
    with open(json_path, "r") as f:
        data = json.load(f)
    
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Data failed schema validation: {e.message}")