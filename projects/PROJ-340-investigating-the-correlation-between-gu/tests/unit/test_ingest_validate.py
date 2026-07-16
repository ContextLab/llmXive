"""
Unit tests for the validate_variables function in code/ingest.py.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.ingest import validate_variables, save_variable_metrics, OUTPUT_METRICS_FILE

@pytest.fixture
def sample_schema():
    return {
        "predictors": {
            "required": ["Phylum_Firmicutes", "Phylum_Bacteroidetes", "Genus_Lactobacillus"]
        },
        "outcomes": {
            "required": ["Sleep_Efficiency", "SWS_duration", "REM_duration"]
        }
    }

@pytest.fixture
def sample_df_complete():
    data = {
        "Phylum_Firmicutes": [100, 120],
        "Phylum_Bacteroidetes": [80, 85],
        "Genus_Lactobacillus": [10, 12],
        "Sleep_Efficiency": [85.0, 90.0],
        "SWS_duration": [2.5, 3.0],
        "REM_duration": [1.5, 1.8]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_missing():
    data = {
        "Phylum_Firmicutes": [100, 120],
        "Phylum_Bacteroidetes": [80, 85],
        "Genus_Lactobacillus": [10, 12],
        "Sleep_Efficiency": [85.0, 90.0],
        "REM_duration": [1.5, 1.8]
        # SWS_duration is missing
    }
    return pd.DataFrame(data)

def test_validate_variables_complete(sample_schema, sample_df_complete, tmp_path):
    """Test validation when all required variables are present."""
    # Temporarily override output path for test isolation
    original_output = validate_variables.__globals__.get('OUTPUT_METRICS_FILE')
    test_output = tmp_path / "test_metrics.json"
    validate_variables.__globals__['OUTPUT_METRICS_FILE'] = test_output

    try:
        metrics = validate_variables(sample_df_complete, sample_schema)
        
        assert metrics['status'] == 'pass'
        assert metrics['total_required'] == 6
        assert metrics['found'] == 6
        assert metrics['missing'] == 0
        assert metrics['percentage_loaded'] == 100.0
        assert len(metrics['missing_variables']) == 0
        assert len(metrics['found_variables']) == 6
        
        assert test_output.exists()
        with open(test_output, 'r') as f:
            saved_metrics = json.load(f)
        assert saved_metrics == metrics
    finally:
        if original_output:
            validate_variables.__globals__['OUTPUT_METRICS_FILE'] = original_output

def test_validate_variables_missing(sample_schema, sample_df_missing, tmp_path):
    """Test validation when some required variables are missing."""
    # Temporarily override output path for test isolation
    original_output = validate_variables.__globals__.get('OUTPUT_METRICS_FILE')
    test_output = tmp_path / "test_metrics.json"
    validate_variables.__globals__['OUTPUT_METRICS_FILE'] = test_output

    try:
        metrics = validate_variables(sample_df_missing, sample_schema)
        
        assert metrics['status'] == 'fail'
        assert metrics['total_required'] == 6
        assert metrics['found'] == 5
        assert metrics['missing'] == 1
        assert metrics['percentage_loaded'] == pytest.approx(83.33, rel=0.1)
        assert "SWS_duration" in metrics['missing_variables']
        assert len(metrics['found_variables']) == 5
        
        assert test_output.exists()
        with open(test_output, 'r') as f:
            saved_metrics = json.load(f)
        assert saved_metrics == metrics
    finally:
        if original_output:
            validate_variables.__globals__['OUTPUT_METRICS_FILE'] = original_output

def test_validate_variables_empty_schema(sample_df_complete, tmp_path):
    """Test validation with an empty schema (no required variables)."""
    empty_schema = {"predictors": {"required": []}, "outcomes": {"required": []}}
    
    original_output = validate_variables.__globals__.get('OUTPUT_METRICS_FILE')
    test_output = tmp_path / "test_metrics.json"
    validate_variables.__globals__['OUTPUT_METRICS_FILE'] = test_output

    try:
        metrics = validate_variables(sample_df_complete, empty_schema)
        
        assert metrics['status'] == 'pass'
        assert metrics['total_required'] == 0
        assert metrics['percentage_loaded'] == 100.0
    finally:
        if original_output:
            validate_variables.__globals__['OUTPUT_METRICS_FILE'] = original_output
