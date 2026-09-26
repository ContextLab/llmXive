"""
Unit tests for schema validation logic.
"""
import pytest
import json
import yaml
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_validator import SchemaValidator, load_schema
from config import get_project_root

@pytest.fixture
def validator():
    return SchemaValidator()

@pytest.fixture
def valid_dataset_record():
    return {
        "age": 35,
        "sex": "M",
        "bmi": 24.5,
        "alpha_power": 12.3,
        "taxon_abundances": {"Bacteroides": 0.45, "Faecalibacterium": 0.15},
        "diet": "Omnivore"
    }

@pytest.fixture
def invalid_dataset_record_missing_field():
    return {
        "age": 35,
        "sex": "M",
        # bmi missing
        "alpha_power": 12.3,
        "taxon_abundances": {"Bacteroides": 0.45},
        "diet": "Omnivore"
    }

@pytest.fixture
def invalid_dataset_record_bad_type():
    return {
        "age": "thirty-five", # Should be int
        "sex": "M",
        "bmi": 24.5,
        "alpha_power": 12.3,
        "taxon_abundances": {"Bacteroides": 0.45},
        "diet": "Omnivore"
    }

@pytest.fixture
def valid_output_record():
    return {
        "stratum_id": "20-30_M_<25_Omnivore",
        "stratum_mean_alpha_power": 11.5,
        "stratum_taxa_means": {"Bacteroides": 0.42, "Faecalibacterium": 0.18},
        "valid_strata_count": 12
    }

def test_validate_dataset_record_valid(validator, valid_dataset_record):
    is_valid, error = validator.validate_dataset_record(valid_dataset_record)
    assert is_valid is True
    assert error is None

def test_validate_dataset_record_missing_field(validator, invalid_dataset_record_missing_field):
    is_valid, error = validator.validate_dataset_record(invalid_dataset_record_missing_field)
    assert is_valid is False
    assert "bmi" in error

def test_validate_dataset_record_bad_type(validator, invalid_dataset_record_bad_type):
    is_valid, error = validator.validate_dataset_record(invalid_dataset_record_bad_type)
    assert is_valid is False
    assert "age" in error

def test_validate_output_record_valid(validator, valid_output_record):
    is_valid, error = validator.validate_output_record(valid_output_record)
    assert is_valid is True
    assert error is None

def test_validate_output_record_missing_stratum_id(validator):
    record = {
        "stratum_mean_alpha_power": 11.5,
        "stratum_taxa_means": {},
        "valid_strata_count": 12
    }
    is_valid, error = validator.validate_output_record(record)
    assert is_valid is False
    assert "stratum_id" in error

def test_validate_output_record_null_diet(validator):
    # Diet is not in output schema, but test that optional fields in dataset schema work
    # We are testing output schema here, so diet shouldn't matter unless we add it
    record = {
        "stratum_id": "test",
        "stratum_mean_alpha_power": 11.5,
        "stratum_taxa_means": {},
        "valid_strata_count": 12
    }
    is_valid, error = validator.validate_output_record(record)
    assert is_valid is True

def test_load_schema_invalid_path():
    with pytest.raises(FileNotFoundError):
        load_schema(Path("/non/existent/path.yaml"))

def test_validate_artifacts_file_not_found(validator):
    result = validator.validate_artifacts(Path("/non/existent/file.json"), "output")
    assert result is False

def test_validate_artifacts_invalid_json(validator):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = Path(f.name)
    
    try:
        result = validator.validate_artifacts(temp_path, "output")
        assert result is False
    finally:
        os.unlink(temp_path)