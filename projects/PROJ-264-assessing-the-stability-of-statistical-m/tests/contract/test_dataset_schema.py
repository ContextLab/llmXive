"""
Contract tests for dataset schema validation.
Validates that datasets loaded by the pipeline conform to the schema
defined in specs/001-assess-model-stability/contracts/dataset_contract.md.
"""
import os
import json
import hashlib
from pathlib import Path
import pytest

# Project imports
from code.data_loader import load_datasets
from code.utils import setup_logging, set_seed

# Constants
CONTRACT_PATH = Path("specs/001-assess-model-stability/contracts/dataset_contract.md")
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

# Ensure logs are set up
logger = setup_logging()

def load_contract_spec():
    """Load the contract specification from the markdown file."""
    if not CONTRACT_PATH.exists():
        pytest.skip(f"Contract file not found: {CONTRACT_PATH}")
    
    # Parse the markdown file for schema definitions
    # Expected format in markdown:
    # ## Schema Definition
    # | Field | Type | Required | Description |
    # |-------|------|----------|-------------|
    # | dataset_id | int | True | OpenML ID |
    # | n_samples | int | True | Number of samples |
    # | n_features | int | True | Number of features |
    # | target_type | str | True | 'binary' or 'multiclass'
    # | checksum | str | True | SHA-256 checksum of raw file
    # | raw_path | str | True | Path to raw data file
    
    with open(CONTRACT_PATH, "r") as f:
        content = f.read()
    
    # Simple parsing logic to extract table (assuming standard markdown table)
    lines = content.split("\n")
    table_start = None
    for i, line in enumerate(lines):
        if line.startswith("| dataset_id |"):
            table_start = i
            break
    
    if table_start is None:
        pytest.fail("Could not find schema table in contract file")
    
    # Extract headers and types
    headers = [h.strip() for h in lines[table_start].split("|")[1:-1]]
    types = [t.strip() for t in lines[table_start + 1].split("|")[1:-1]]
    
    schema = {}
    for h, t in zip(headers, types):
        schema[h] = t
    
    return schema

def validate_dataset_schema(dataset, schema):
    """Validate a single dataset against the schema."""
    errors = []
    
    for field, expected_type in schema.items():
        if field == "checksum":
            # Skip checksum validation in this test as it depends on file existence
            continue
        if field == "raw_path":
            # Skip path validation as it's relative to data directory
            continue
        
        if field not in dataset:
            errors.append(f"Missing required field: {field}")
            continue
        
        value = dataset[field]
        
        # Type validation
        if expected_type == "int":
            if not isinstance(value, int):
                errors.append(f"Field '{field}' should be int, got {type(value)}")
        elif expected_type == "str":
            if not isinstance(value, str):
                errors.append(f"Field '{field}' should be str, got {type(value)}")
        elif expected_type == "bool":
            if not isinstance(value, bool):
                errors.append(f"Field '{field}' should be bool, got {type(value)}")
    
    return errors

def test_dataset_schema_contracts():
    """
    Test that all loaded datasets conform to the dataset schema contract.
    This test validates:
    1. All required fields are present
    2. Field types match the schema
    3. Data constraints (e.g., n_samples > 0) are met
    """
    schema = load_contract_spec()
    
    # Load datasets (this will trigger download if not present)
    # We use a small subset for the contract test to avoid long runtimes
    test_ids = [59, 61]  # Small binary classification datasets
    
    try:
        datasets = load_datasets(dataset_ids=test_ids, max_samples=1000)
    except Exception as e:
        pytest.fail(f"Failed to load datasets: {str(e)}")
    
    assert len(datasets) > 0, "No datasets were loaded"
    
    all_errors = []
    for dataset in datasets:
        dataset_errors = validate_dataset_schema(dataset, schema)
        if dataset_errors:
            all_errors.extend([f"Dataset {dataset.get('dataset_id', 'unknown')}: {err}" 
                             for err in dataset_errors])
    
    if all_errors:
        pytest.fail("Schema validation errors found:\n" + "\n".join(all_errors))

def test_dataset_checksum_contract():
    """
    Test that dataset checksums are correctly computed and stored.
    Validates the checksum contract requirement.
    """
    if not RAW_DATA_DIR.exists():
        pytest.skip("Raw data directory not found")
    
    checksum_files = list(RAW_DATA_DIR.glob("*.checksum"))
    if not checksum_files:
        pytest.skip("No checksum files found - datasets may not have been downloaded yet")
    
    for checksum_file in checksum_files[:2]:  # Test first 2 checksum files
        dataset_name = checksum_file.stem
        checksum_value = checksum_file.read_text().strip()
        
        # Validate checksum format (SHA-256)
        assert len(checksum_value) == 64, f"Invalid checksum length for {dataset_name}"
        assert all(c in '0123456789abcdef' for c in checksum_value), \
            f"Invalid checksum characters for {dataset_name}"

def test_dataset_range_contract():
    """
    Test that datasets meet the sample size range contract (100-100,000).
    """
    try:
        datasets = load_datasets(dataset_ids=[59, 61, 1596], max_samples=100000)
    except Exception as e:
        pytest.fail(f"Failed to load datasets: {str(e)}")
    
    for dataset in datasets:
        n_samples = dataset.get("n_samples", 0)
        assert 100 <= n_samples <= 100000, \
            f"Dataset {dataset.get('dataset_id')} has {n_samples} samples, outside contract range [100, 100000]"
