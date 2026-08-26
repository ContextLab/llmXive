"""
Contract tests for the Caco-2 dataset schema compliance.
Validates data against the schema defined in T007.
"""
import json
import os
import sys
import pytest
from pathlib import Path
import yaml

# Add project root to path for imports if necessary, though this test is standalone
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-molecular-flexibility-permeability" / "contracts" / "dataset.schema.yaml"
DATA_PATH_RAW = PROJECT_ROOT / "data" / "raw" / "chembl_raw.csv"
DATA_PATH_PROCESSED = PROJECT_ROOT / "data" / "processed" / "filtered_data.csv"

def load_schema():
    """Load the JSON schema from the yaml file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}. "
                                "Ensure T007 has been completed and the schema file exists.")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_record(record: dict, schema: dict):
    """
    Validates a single record dictionary against the schema.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    # Type checking for top-level fields
    type_checks = {
        'smiles': str,
        'logPapp': (int, float),
        'mw': (int, float),
        'psa': (int, float),
        'assay_id': str,
        'protocol_metadata': dict
    }

    for field, expected_type in type_checks.items():
        if field in record:
            if not isinstance(record[field], expected_type):
                errors.append(f"Field '{field}' has type {type(record[field]).__name__}, expected {expected_type}")

    # Specific validation for protocol_metadata
    if 'protocol_metadata' in record and isinstance(record['protocol_metadata'], dict):
        meta = record['protocol_metadata']
        meta_required = ['lab_id', 'temperature', 'passage']
        for meta_field in meta_required:
            if meta_field not in meta:
                errors.append(f"Missing required field in protocol_metadata: {meta_field}")
        
        if 'temperature' in meta and not isinstance(meta['temperature'], (int, float)):
            errors.append("protocol_metadata.temperature must be a number")
    
    # Check for empty strings where not allowed
    if 'smiles' in record and (not record['smiles'] or not record['smiles'].strip()):
        errors.append("smiles cannot be empty")

    return errors

def load_csv_data(filepath: Path):
    """Load CSV data and return a list of dictionaries."""
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found at {filepath}")
    
    import pandas as pd
    df = pd.read_csv(filepath)
    
    # If protocol_metadata is a JSON string (as per T009 requirement), parse it
    if 'protocol_metadata' in df.columns:
        # Check if it's stringified JSON
        sample = df['protocol_metadata'].iloc[0] if len(df) > 0 else None
        if isinstance(sample, str):
            try:
                df['protocol_metadata'] = df['protocol_metadata'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            except json.JSONDecodeError as e:
                # If parsing fails, we might have raw strings or mixed types, 
                # but for strict schema validation we expect the parsed object
                # If it fails, we'll let the validator catch the type error
                pass
        
    return df.to_dict(orient='records')

@pytest.mark.contract
def test_schema_compliance():
    """
    Validates the dataset against the schema defined in T007.
    Checks both raw and processed data files if they exist.
    """
    schema = load_schema()
    all_passed = True
    total_records = 0
    failed_records = 0
    error_log = []

    # Test Raw Data
    if DATA_PATH_RAW.exists():
        try:
            raw_records = load_csv_data(DATA_PATH_RAW)
            total_records += len(raw_records)
            for i, record in enumerate(raw_records):
                errors = validate_record(record, schema)
                if errors:
                    failed_records += 1
                    if len(error_log) < 5: # Limit log size
                        error_log.append(f"Raw data record {i}: {errors}")
        except Exception as e:
            pytest.fail(f"Failed to load or validate raw data: {e}")

    # Test Processed Data
    if DATA_PATH_PROCESSED.exists():
        try:
            processed_records = load_csv_data(DATA_PATH_PROCESSED)
            total_records += len(processed_records)
            for i, record in enumerate(processed_records):
                errors = validate_record(record, schema)
                if errors:
                    failed_records += 1
                    if len(error_log) < 5:
                        error_log.append(f"Processed data record {i}: {errors}")
        except Exception as e:
            pytest.fail(f"Failed to load or validate processed data: {e}")

    if total_records == 0:
        pytest.fail("No data files found to validate. Ensure T009 and T010 have produced output files.")

    if failed_records > 0:
        pytest.fail(f"Schema validation failed for {failed_records} out of {total_records} records.\n" + 
                    "Sample errors:\n" + "\n".join(error_log))

    assert failed_records == 0, "Schema validation failed."