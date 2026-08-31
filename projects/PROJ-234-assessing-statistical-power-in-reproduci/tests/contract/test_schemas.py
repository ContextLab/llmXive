"""
Contract test for T011 and T014: Validates data/raw/openml_metadata_filtered.json
against the dataset_metadata schema.
"""
import json
import pytest
from pathlib import Path
import sys

# Load schema validator
try:
    import yaml
    from jsonschema import validate, ValidationError
except ImportError:
    pytest.skip("jsonschema or pyyaml not installed", allow_module_level=True)

# Import schema loading logic from utils if available, or load directly
from utils.verify_schema import load_and_validate_schema

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "openml_metadata_filtered.json"
SCHEMA_FILE = PROJECT_ROOT / "contracts" / "dataset_metadata.schema.yaml"

@pytest.mark.skipif(not DATA_FILE.exists(), reason="Data file not generated yet. Run T012/T013 first.")
def test_dataset_metadata_schema():
    """
    T011: Validates the filtered JSON against the schema.
    """
    if not SCHEMA_FILE.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_FILE}")
    
    # Load data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure it's a list
    assert isinstance(data, list), "Top level must be a list of datasets"
    
    # Load schema
    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    # Validate each item
    errors = []
    for i, item in enumerate(data):
        try:
            validate(instance=item, schema=schema)
        except ValidationError as e:
            errors.append(f"Item {i}: {e.message}")
    
    if errors:
        pytest.fail(f"Schema validation failed:\n" + "\n".join(errors))
    
    assert True, "Schema validation passed"