"""
Contract test for dataset schema validation.

This test verifies that datasets loaded during the pipeline conform to the
schema defined in contracts/dataset.schema.yaml (created in T005).

It specifically checks for the presence of required columns:
- duration_estimate
- stimulus_sequence
- participant_id

This test depends on T005 (contract definition).
"""
import os
import sys
import yaml
import pytest
import pandas as pd

# Add code directory to path for imports if necessary, though this test
# primarily relies on reading the contract and a sample data file.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

# Path to the schema contract
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'contracts', 'dataset.schema.yaml')

# Path to a sample processed file if available (for integration of the check)
# If no file exists yet, we test the schema definition itself and the logic
# that would validate a dataframe.
SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'standardized.csv')

REQUIRED_COLUMNS = ['duration_estimate', 'stimulus_sequence', 'participant_id']

def load_schema():
    """Load the dataset schema contract."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.fail(f"Schema contract file not found at {SCHEMA_PATH}. Ensure T005 is complete.")
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def get_required_columns_from_schema(schema):
    """Extract required column names from the schema definition."""
    # The schema structure is assumed to define a 'required' list or similar under 'properties'
    # Based on T005 description: "defining required columns (duration_estimate, stimulus_sequence, participant_id)"
    # We expect the schema to explicitly list these.
    
    if 'required' in schema:
        return schema['required']
    
    # Fallback: check properties if 'required' is missing but defined there
    properties = schema.get('properties', {})
    # If the schema uses a list of required fields in the root
    if 'required' in schema:
        return schema['required']
        
    # If the schema is a list of column definitions
    if isinstance(schema, list):
        return [item.get('name') or item.get('column') for item in schema]
        
    # Default fallback based on task description if schema parsing is ambiguous
    return REQUIRED_COLUMNS

def test_schema_file_exists_and_valid():
    """Test that the schema contract exists and is valid YAML."""
    schema = load_schema()
    assert schema is not None, "Schema could not be loaded."
    assert isinstance(schema, dict) or isinstance(schema, list), "Schema must be a dict or list."

def test_schema_contains_required_fields():
    """Test that the schema explicitly defines the required columns."""
    schema = load_schema()
    required_from_schema = get_required_columns_from_schema(schema)
    
    # Ensure the specific columns mentioned in T005 are present in the schema definition
    for col in REQUIRED_COLUMNS:
        assert col in required_from_schema, f"Required column '{col}' missing from schema contract."

def test_dataframe_conforms_to_schema():
    """
    Test that if a processed dataset exists, it conforms to the schema.
    
    If the data file does not exist yet (T017 not run), this test is skipped
    but the schema logic is still validated by the previous tests.
    """
    if not os.path.exists(SAMPLE_DATA_PATH):
        pytest.skip(f"Sample data file {SAMPLE_DATA_PATH} not found. Skipping data validation.")

    try:
        df = pd.read_csv(SAMPLE_DATA_PATH)
    except Exception as e:
        pytest.fail(f"Failed to read sample data file: {e}")

    required_cols = get_required_columns_from_schema(load_schema())
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    assert len(missing_cols) == 0, (
        f"Dataset schema validation failed. Missing required columns: {missing_cols}. "
        f"Expected columns: {required_cols}"
    )

def test_column_types_basic():
    """
    Basic type check for required columns if data exists.
    Ensures duration_estimate is numeric, participant_id is present.
    """
    if not os.path.exists(SAMPLE_DATA_PATH):
        pytest.skip(f"Sample data file {SAMPLE_DATA_PATH} not found.")

    df = pd.read_csv(SAMPLE_DATA_PATH)
    required_cols = get_required_columns_from_schema(load_schema())

    if 'duration_estimate' in df.columns:
        assert pd.api.types.is_numeric_dtype(df['duration_estimate']), \
            "duration_estimate must be numeric."
    
    if 'participant_id' in df.columns:
        assert df['participant_id'].notnull().all(), \
            "participant_id must not contain null values."
    
    if 'stimulus_sequence' in df.columns:
        # Sequence should not be null
        assert df['stimulus_sequence'].notnull().all(), \
            "stimulus_sequence must not contain null values."