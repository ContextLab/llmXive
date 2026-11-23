"""
Integration test for T020: Verify learners_raw.csv generation.

This test ensures that:
1. The script runs without error.
2. The output file exists and is not empty.
3. The file contains >= 10,000 records.
4. Required columns are present.
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from generate_learners_raw import main as t020_main
from schema import load_schema_from_file, validate_schema

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "learners_raw.csv"
SCHEMA_FILE = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

@pytest.fixture(scope="module")
def generated_data():
    """Run T020 and return the loaded DataFrame."""
    # Only run if file doesn't exist to avoid re-running every test
    if not OUTPUT_FILE.exists():
        try:
            t020_main()
        except Exception as e:
            pytest.fail(f"T020 main failed: {e}")
    
    return pd.read_csv(OUTPUT_FILE)

def test_output_file_exists():
    """Test that the output file was created."""
    assert OUTPUT_FILE.exists(), "learners_raw.csv was not created"
    assert OUTPUT_FILE.stat().st_size > 0, "learners_raw.csv is empty"

def test_record_count(generated_data):
    """Test that we have at least 10,000 records."""
    count = len(generated_data)
    assert count >= 10000, f"Record count {count} is less than 10,000"

def test_required_columns(generated_data):
    """Test that all required columns are present."""
    required_columns = [
        "student_id", "code_module", "num_assessments", "num_forum_posts",
        "first_feedback_interval", "final_grade", "is_complete", "has_forum_interaction"
    ]
    missing = [col for col in required_columns if col not in generated_data.columns]
    assert not missing, f"Missing required columns: {missing}"

def test_no_null_required_fields(generated_data):
    """Test that required fields have no null values."""
    required_columns = [
        "student_id", "code_module", "num_assessments", "num_forum_posts",
        "first_feedback_interval", "final_grade", "is_complete", "has_forum_interaction"
    ]
    for col in required_columns:
        null_count = generated_data[col].isnull().sum()
        assert null_count == 0, f"Column {col} has {null_count} null values"

def test_schema_validation(generated_data):
    """Test that data conforms to the schema."""
    if not SCHEMA_FILE.exists():
        pytest.skip("Schema file not found, skipping validation")
    
    schema = load_schema_from_file(SCHEMA_FILE)
    is_valid, errors = validate_schema(generated_data, schema)
    assert is_valid, f"Schema validation failed: {errors}"

def test_data_types(generated_data):
    """Test that data types are correct."""
    # Check numeric types
    assert generated_data['num_assessments'].dtype in ['int64', 'float64']
    assert generated_data['num_forum_posts'].dtype in ['int64', 'float64']
    assert generated_data['first_feedback_interval'].dtype in ['int64', 'float64']
    assert generated_data['final_grade'].dtype in ['int64', 'float64']
    
    # Check boolean types
    assert generated_data['is_complete'].dtype == 'bool'
    assert generated_data['has_forum_interaction'].dtype == 'bool'

def test_range_constraints(generated_data):
    """Test that values are within expected ranges."""
    assert (generated_data['num_assessments'] >= 0).all()
    assert (generated_data['num_forum_posts'] >= 1).all()  # T018 exclusion
    assert (generated_data['first_feedback_interval'] >= 0).all()
    assert (generated_data['final_grade'] >= 0).all()
    assert (generated_data['final_grade'] <= 100).all()
    assert (generated_data['has_forum_interaction'] == True).all()  # All should be True