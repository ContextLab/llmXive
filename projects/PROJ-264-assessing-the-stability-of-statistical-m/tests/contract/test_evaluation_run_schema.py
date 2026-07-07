"""
Contract tests for evaluation run schema validation.
Validates that evaluation runs conform to the schema defined in
specs/001-assess-model-stability/contracts/evaluation_run_contract.md.
"""
import os
import json
import pandas as pd
import pytest
from pathlib import Path

from code.utils import setup_logging

# Constants
CONTRACT_PATH = Path("specs/001-assess-model-stability/contracts/evaluation_run_contract.md")
RESULTS_DIR = Path("results")
RAW_EVALUATIONS_FILE = RESULTS_DIR / "raw_evaluations.csv"

# Ensure logs are set up
logger = setup_logging()

def load_contract_spec():
    """Load the evaluation run contract specification from the markdown file."""
    if not CONTRACT_PATH.exists():
        pytest.skip(f"Contract file not found: {CONTRACT_PATH}")
    
    with open(CONTRACT_PATH, "r") as f:
        content = f.read()
    
    # Parse the markdown file for schema definitions
    # Expected format in markdown:
    # ## Schema Definition
    # | Field | Type | Required | Description |
    # |-------|------|----------|-------------|
    # | dataset_id | int | True | OpenML ID of the dataset |
    # | model_name | str | True | Name of the model (e.g., 'LogisticRegression') |
    # | fold_id | int | True | Fold number (0 to n_splits-1) |
    # | repeat_id | int | True | Repeat number (0 to n_repeats-1) |
    # | accuracy | float | True | Accuracy score (0.0 to 1.0) |
    # | f1_score | float | True | F1 score (0.0 to 1.0) |
    
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

def validate_evaluation_run_schema(df, schema):
    """Validate an evaluation run dataframe against the schema."""
    errors = []
    
    # Check required columns
    for field in schema:
        if field not in df.columns:
            errors.append(f"Missing required column: {field}")
    
    if errors:
        return errors
    
    # Validate each row
    for idx, row in df.iterrows():
        row_errors = []
        
        for field, expected_type in schema.items():
            value = row[field]
            
            # Type validation
            if expected_type == "int":
                if not isinstance(value, (int, np.integer)):
                    row_errors.append(f"Row {idx}: Field '{field}' should be int, got {type(value)}")
            elif expected_type == "float":
                if not isinstance(value, (float, np.floating)):
                    row_errors.append(f"Row {idx}: Field '{field}' should be float, got {type(value)}")
                # Range validation for scores
                if field in ["accuracy", "f1_score"]:
                    if not (0.0 <= value <= 1.0):
                        row_errors.append(f"Row {idx}: Field '{field}' should be in [0.0, 1.0], got {value}")
            elif expected_type == "str":
                if not isinstance(value, str):
                    row_errors.append(f"Row {idx}: Field '{field}' should be str, got {type(value)}")
        
        errors.extend(row_errors)
    
    return errors

def test_evaluation_run_schema_contract():
    """
    Test that evaluation run data conforms to the evaluation run schema contract.
    This test validates:
    1. All required columns are present
    2. Column types match the schema
    3. Value constraints (e.g., accuracy in [0,1]) are met
    """
    schema = load_contract_spec()
    
    # Check if raw evaluations file exists
    if not RAW_EVALUATIONS_FILE.exists():
        pytest.skip(f"Raw evaluations file not found: {RAW_EVALUATIONS_FILE}. "
                   "Run the evaluation pipeline first.")
    
    # Load the data
    try:
        df = pd.read_csv(RAW_EVALUATIONS_FILE)
    except Exception as e:
        pytest.fail(f"Failed to load raw evaluations: {str(e)}")
    
    if len(df) == 0:
        pytest.skip("Raw evaluations file is empty")
    
    errors = validate_evaluation_run_schema(df, schema)
    
    if errors:
        pytest.fail("Schema validation errors found:\n" + "\n".join(errors))

def test_evaluation_run_structure_contract():
    """
    Test the structural requirements of evaluation runs:
    - Each dataset should have multiple repeats
    - Each repeat should have multiple folds
    - Each fold should have exactly one record per model
    """
    if not RAW_EVALUATIONS_FILE.exists():
        pytest.skip(f"Raw evaluations file not found: {RAW_EVALUATIONS_FILE}")
    
    df = pd.read_csv(RAW_EVALUATIONS_FILE)
    
    if len(df) == 0:
        pytest.skip("Raw evaluations file is empty")
    
    # Check that we have multiple repeats
    n_repeats = df['repeat_id'].nunique()
    assert n_repeats >= 1, "Expected at least 1 repeat in evaluation runs"
    
    # Check that we have multiple folds
    n_folds = df['fold_id'].nunique()
    assert n_folds >= 1, "Expected at least 1 fold in evaluation runs"
    
    # Check that we have multiple models
    n_models = df['model_name'].nunique()
    assert n_models >= 1, "Expected at least 1 model in evaluation runs"
    
    # Verify structure: each (dataset, repeat, fold) should have one row per model
    grouped = df.groupby(['dataset_id', 'repeat_id', 'fold_id'])
    for name, group in grouped:
        n_models_per_fold = group['model_name'].nunique()
        assert n_models_per_fold >= 1, \
            f"Group {name} should have at least 1 model, got {n_models_per_fold}"

def test_evaluation_run_data_integrity():
    """
    Test data integrity constraints:
    - No duplicate (dataset_id, model_name, fold_id, repeat_id) combinations
    - All metric values are non-negative
    """
    if not RAW_EVALUATIONS_FILE.exists():
        pytest.skip(f"Raw evaluations file not found: {RAW_EVALUATIONS_FILE}")
    
    df = pd.read_csv(RAW_EVALUATIONS_FILE)
    
    if len(df) == 0:
        pytest.skip("Raw evaluations file is empty")
    
    # Check for duplicates
    duplicates = df.duplicated(subset=['dataset_id', 'model_name', 'fold_id', 'repeat_id'], keep=False)
    if duplicates.any():
        dup_count = duplicates.sum()
        pytest.fail(f"Found {dup_count} duplicate evaluation records")
    
    # Check metric ranges
    for metric in ['accuracy', 'f1_score']:
        if metric in df.columns:
            invalid = (df[metric] < 0) | (df[metric] > 1)
            if invalid.any():
                pytest.fail(f"Found {invalid.sum()} records with {metric} outside [0, 1] range")
