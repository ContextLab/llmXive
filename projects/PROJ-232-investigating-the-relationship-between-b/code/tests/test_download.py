import pytest
import pandas as pd
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError
from llmxive_toolkit import paths
from code.src.data.download import calculate_file_checksum, verify_bmrq_column

def test_calculate_checksum(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    sha = calculate_file_checksum(f)
    assert len(sha) == 64  # SHA-256 length

def test_verify_bmrq_column(tmp_path):
    csv_path = tmp_path / "beh.csv"
    df = pd.DataFrame({
        "subject_id": ["s1"],
        "BMRQ_Total": [50],
        "age": [25],
        "sex": ["M"]
    })
    df.to_csv(csv_path, index=False)
    
    # Test success
    all_present, missing = verify_bmrq_column(csv_path, required_columns={"subject_id", "BMRQ_Total"})
    assert all_present is True
    assert len(missing) == 0
    
    # Test failure
    all_present, missing = verify_bmrq_column(csv_path, required_columns={"NON_EXISTENT"})
    assert all_present is False
    assert "NON_EXISTENT" in missing

def test_schema_validation():
    # Load schema
    schema_path = paths.path("specs/001-investigating-the-relationship-between-b/contracts/dataset.schema.yaml")
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Mock a downloaded record (mapped from CSV names to schema names)
    # Note: BMRQ_Total in CSV -> bmrq_total in schema
    record = {
        "subject_id": "sub-01",
        "age": 25,
        "sex": "M",
        "bmrq_total": 50.5,
        "fd_mean": 0.2,
        "motion_excluded": False
    }
    
    try:
        validate(instance=record, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e}")

def test_schema_validation_invalid():
    schema_path = paths.path("specs/001-investigating-the-relationship-between-b/contracts/dataset.schema.yaml")
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Invalid record: age is a string
    record = {
        "subject_id": "sub-01",
        "age": "twenty-five",
        "sex": "M",
        "bmrq_total": 50.5,
        "fd_mean": 0.2,
        "motion_excluded": False
    }
    
    with pytest.raises(ValidationError):
        validate(instance=record, schema=schema)