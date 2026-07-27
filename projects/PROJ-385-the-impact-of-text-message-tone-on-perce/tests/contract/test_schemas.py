"""
Contract tests to ensure generated data artifacts match the defined schemas.
"""
import json
import csv
import pytest
from pathlib import Path
import yaml
import re

from config import get_contracts_dir, get_raw_data_dir, get_processed_data_dir
from validate_schemas import load_schema, validate_json_against_schema, validate_csv_against_schema

@pytest.fixture
def contracts_dir():
    return get_contracts_dir()

@pytest.fixture
def raw_dir():
    return get_raw_data_dir()

@pytest.fixture
def processed_dir():
    return get_processed_data_dir()

def test_stimulus_schema_exists(contracts_dir):
    """Test that the stimulus schema file exists."""
    schema_path = contracts_dir / "stimulus.schema.yaml"
    assert schema_path.exists(), "stimulus.schema.yaml not found"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert schema['title'] == "Stimulus Schema"
    assert "stimulus_id" in schema['required']

def test_rating_schema_exists(contracts_dir):
    """Test that the rating schema file exists."""
    schema_path = contracts_dir / "rating.schema.yaml"
    assert schema_path.exists(), "rating.schema.yaml not found"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert schema['title'] == "Rating Schema"
    assert "participant_id" in schema['required']

def test_analysis_result_schema_exists(contracts_dir):
    """Test that the analysis result schema file exists."""
    schema_path = contracts_dir / "analysis_result.schema.yaml"
    assert schema_path.exists(), "analysis_result.schema.yaml not found"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert schema['title'] == "Analysis Result Schema"
    assert "model_summary" in schema['required']

def test_stimuli_csv_validation(raw_dir):
    """Validate the generated stimuli.csv against the schema."""
    file_path = raw_dir / "stimuli.csv"
    if not file_path.exists():
        pytest.skip("stimuli.csv not generated yet")
    
    errors = validate_csv_against_schema(file_path, "stimulus.schema.yaml")
    assert not errors, f"Stimuli schema validation failed: {errors}"

def test_ratings_csv_validation(raw_dir):
    """Validate the generated ratings.csv against the schema."""
    file_path = raw_dir / "ratings.csv"
    if not file_path.exists():
        pytest.skip("ratings.csv not generated yet")
    
    errors = validate_csv_against_schema(file_path, "rating.schema.yaml")
    assert not errors, f"Rating schema validation failed: {errors}"

def test_analysis_results_json_validation(processed_dir):
    """Validate the generated analysis_results.json against the schema."""
    file_path = processed_dir / "analysis_results.json"
    if not file_path.exists():
        pytest.skip("analysis_results.json not generated yet")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    schema = load_schema("analysis_result.schema.yaml")
    errors = validate_json_against_schema(data, schema)
    assert not errors, f"Analysis result schema validation failed: {errors}"