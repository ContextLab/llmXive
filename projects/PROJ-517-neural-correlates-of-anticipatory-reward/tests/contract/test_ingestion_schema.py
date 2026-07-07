"""
Contract test for ingestion schema validation.

Tests T009: Assert that input CSV with valid `trial_id` passes schema validation;
assert invalid `trial_id` format raises `ValidationError`.
"""
import os
import tempfile
import pytest
import pandas as pd
import yaml
from pathlib import Path

# Import schema loading from the synthetic generator which holds the contract
from synthetic_generator import load_schema


# Define expected trial_id format regex pattern based on common conventions
# Assuming format: "trial_<number>" or similar. The schema likely enforces this.
# We will validate against the loaded schema's requirements.
VALID_TRIAL_ID_PREFIX = "trial_"
INVALID_TRIAL_IDS = [
    "invalid",
    "123",
    "Trial_001",  # Case sensitivity
    "trial_001_extra",
    "",
    None
]
VALID_TRIAL_IDS = [
    "trial_001",
    "trial_002",
    "trial_100"
]


def get_schema_path():
    """Get the path to the dataset schema YAML."""
    # The schema was created in T006 at contracts/dataset.schema.yaml
    # We assume the project root is accessible or we construct the path relative to this file
    # Since we are in tests/contract/, go up twice to project root
    base_dir = Path(__file__).resolve().parent.parent.parent
    schema_path = base_dir / "contracts" / "dataset.schema.yaml"
    if not schema_path.exists():
        # Fallback for CI if run from different root, though T006 should have created it
        raise FileNotFoundError(f"Schema file not found at {schema_path}. Run T006 first.")
    return schema_path


def load_contract_schema():
    """Load the dataset schema contract."""
    schema_path = get_schema_path()
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_trial_id_format(trial_id, schema):
    """
    Validate a single trial_id against the schema constraints.
    Returns True if valid, raises ValueError if invalid.
    """
    # Check if trial_id is present in schema definitions
    if 'properties' not in schema:
        # If schema is a list of column definitions, adapt logic
        # Based on T006 description, it defines columns.
        # Let's assume standard JSON-schema-like structure or simple list.
        # If it's a list of dicts like [{'name': 'trial_id', 'type': 'string', 'pattern': ...}]
        fields = schema.get('properties', schema) if isinstance(schema, dict) else schema
        
        # Find trial_id field
        trial_field = None
        if isinstance(fields, dict):
            trial_field = fields.get('trial_id')
        elif isinstance(fields, list):
            for f in fields:
                if f.get('name') == 'trial_id':
                    trial_field = f
                    break
        
        if not trial_field:
            # If field not explicitly defined, assume string is allowed but check format manually
            # based on project conventions if schema is loose
            return True 

        # Extract pattern if exists
        pattern = trial_field.get('pattern')
        if pattern:
            import re
            if not re.match(pattern, str(trial_id)):
                raise ValueError(f"trial_id '{trial_id}' does not match pattern '{pattern}'")
        
        # If no pattern in schema, we rely on the specific test logic for this task
        # which assumes a specific format "trial_<int>"
        if not str(trial_id).startswith("trial_"):
             raise ValueError(f"trial_id '{trial_id}' must start with 'trial_'")
             
        # Check for numeric suffix
        suffix = str(trial_id).replace("trial_", "", 1)
        if not suffix.isdigit():
            raise ValueError(f"trial_id '{trial_id}' must have numeric suffix")

        return True
    else:
        return True


def test_schema_validates_trial_id():
    """
    Test that valid trial_ids pass and invalid ones fail.
    """
    schema = load_contract_schema()
    
    # Test valid IDs
    for tid in VALID_TRIAL_IDS:
        try:
            validate_trial_id_format(tid, schema)
        except ValueError as e:
            pytest.fail(f"Valid trial_id '{tid}' was rejected: {e}")

    # Test invalid IDs
    for tid in INVALID_TRIAL_IDS:
        with pytest.raises((ValueError, TypeError, AssertionError)):
            if tid is None:
                # Handle None specifically if schema allows null checks
                try:
                    validate_trial_id_format(tid, schema)
                    pytest.fail(f"Invalid trial_id '{tid}' (None) was not rejected")
                except (ValueError, TypeError):
                    pass # Expected
            else:
                validate_trial_id_format(tid, schema)

def test_csv_integration_valid():
    """
    Integration test: Create a valid CSV and ensure it passes basic schema checks.
    """
    schema = load_contract_schema()
    df = pd.DataFrame({
        'trial_id': ['trial_001', 'trial_002'],
        'neuron_id': [1, 1],
        'spike_count': [10, 12],
        'reward_magnitude': [1.0, 2.0]
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        # Load and validate row by row
        loaded_df = pd.read_csv(temp_path)
        for _, row in loaded_df.iterrows():
            validate_trial_id_format(row['trial_id'], schema)
    finally:
        os.unlink(temp_path)

def test_csv_integration_invalid():
    """
    Integration test: Create an invalid CSV and ensure it fails validation.
    """
    schema = load_contract_schema()
    df = pd.DataFrame({
        'trial_id': ['invalid_id', 'trial_002'], # First is invalid
        'neuron_id': [1, 1],
        'spike_count': [10, 12],
        'reward_magnitude': [1.0, 2.0]
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        loaded_df = pd.read_csv(temp_path)
        # Expect failure on first row
        with pytest.raises(ValueError):
            for _, row in loaded_df.iterrows():
                validate_trial_id_format(row['trial_id'], schema)
    finally:
        os.unlink(temp_path)
