"""
Unit tests for the data ingestion and schema validation logic.
"""
import pytest
import pandas as pd
import json
import os
import sys
from pathlib import Path
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingest import validate_variables, load_schema, save_variable_metrics

# Mock Schema for testing
MOCK_SCHEMA = {
    "outcomes": [
        {"name": "total_sleep_duration", "type": "float", "required": True},
        {"name": "sws_duration", "type": "float", "required": True},
        {"name": "rem_duration", "type": "float", "required": True}
    ],
    "identifiers": [
        {"name": "subject_id", "type": "string", "required": True},
        {"name": "age", "type": "integer", "required": True}
    ]
}

def test_validate_variables_complete():
    """Test validation when all required variables are present."""
    df = pd.DataFrame({
        "total_sleep_duration": [400, 450],
        "sws_duration": [100, 120],
        "rem_duration": [90, 100],
        "subject_id": ["S1", "S2"],
        "age": [25, 30]
    })
    
    is_complete, metrics = validate_variables(df, MOCK_SCHEMA)
    
    assert is_complete is True
    assert metrics['percentage_loaded'] == 100.0
    assert len(metrics['missing_variables']) == 0

def test_validate_variables_missing_one():
    """Test validation when one required variable is missing."""
    df = pd.DataFrame({
        "total_sleep_duration": [400, 450],
        "sws_duration": [100, 120],
        # rem_duration is missing
        "subject_id": ["S1", "S2"],
        "age": [25, 30]
    })
    
    is_complete, metrics = validate_variables(df, MOCK_SCHEMA)
    
    assert is_complete is False
    assert metrics['percentage_loaded'] == 80.0
    assert "rem_duration" in metrics['missing_variables']

def test_validate_variables_missing_multiple():
    """Test validation when multiple required variables are missing."""
    df = pd.DataFrame({
        "total_sleep_duration": [400, 450],
        # sws_duration missing
        # rem_duration missing
        "subject_id": ["S1", "S2"],
        # age missing
    })
    
    is_complete, metrics = validate_variables(df, MOCK_SCHEMA)
    
    assert is_complete is False
    assert metrics['percentage_loaded'] == 40.0
    assert len(metrics['missing_variables']) == 3

def test_save_variable_metrics(tmp_path):
    """Test saving metrics to JSON."""
    metrics = {
        "total_required_variables": 5,
        "total_present_variables": 3,
        "missing_variables": ["a", "b"],
        "percentage_loaded": 60.0,
        "is_complete": False
    }
    
    output_file = tmp_path / "metrics.json"
    save_variable_metrics(metrics, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        saved_metrics = json.load(f)
    
    assert saved_metrics == metrics
