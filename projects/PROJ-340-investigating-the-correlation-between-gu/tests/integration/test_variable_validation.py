"""
Integration tests for variable validation (T012).
Tests that validate_variables correctly identifies missing variables
and writes the metrics file to disk.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from code.ingest import validate_variables, load_required_variables

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe with some missing variables."""
    # Required: Taxon_0..Taxon_19, total_sleep_time, sws_duration, rem_duration, sleep_efficiency
    # Present: Taxon_0..Taxon_18 (missing Taxon_19), total_sleep_time, sws_duration (missing rem_duration, sleep_efficiency)
    data = {
        'Taxon_0': [1, 2, 3],
        'Taxon_1': [4, 5, 6],
        'Taxon_2': [7, 8, 9],
        'Taxon_3': [10, 11, 12],
        'Taxon_4': [13, 14, 15],
        'Taxon_5': [16, 17, 18],
        'Taxon_6': [19, 20, 21],
        'Taxon_7': [22, 23, 24],
        'Taxon_8': [25, 26, 27],
        'Taxon_9': [28, 29, 30],
        'Taxon_10': [31, 32, 33],
        'Taxon_11': [34, 35, 36],
        'Taxon_12': [37, 38, 39],
        'Taxon_13': [40, 41, 42],
        'Taxon_14': [43, 44, 45],
        'Taxon_15': [46, 47, 48],
        'Taxon_16': [49, 50, 51],
        'Taxon_17': [52, 53, 54],
        'Taxon_18': [55, 56, 57],
        # Missing Taxon_19
        'total_sleep_time': [400, 420, 380],
        'sws_duration': [100, 110, 90],
        # Missing rem_duration, sleep_efficiency
    }
    return pd.DataFrame(data)

def test_validate_variables_partial_missing(sample_dataframe, temp_output_dir):
    """
    Test that validate_variables correctly identifies missing variables
    and writes the metrics file to disk.
    """
    # Load required variables
    required_vars = load_required_variables("data/config/required_variables.yaml")
    
    # Define output path in temp directory
    output_path = os.path.join(temp_output_dir, "variable_load_metrics.json")
    
    # Run validation
    metrics = validate_variables(sample_dataframe, required_vars, output_path)
    
    # Assertions on metrics
    assert 'percentage_loaded' in metrics
    assert 'missing_variables' in metrics
    assert 'total_required' in metrics
    
    # Calculate expected missing
    # Predictors: 20 (Taxon_0 to Taxon_19) -> Missing Taxon_19 (1)
    # Outcomes: 4 (total_sleep_time, sws_duration, rem_duration, sleep_efficiency) -> Missing rem_duration, sleep_efficiency (2)
    # Total missing: 3
    # Total required: 24
    # Percentage: (21/24) * 100 = 87.5
    
    assert metrics['total_required'] == 24
    assert len(metrics['missing_variables']) == 3
    assert 'Taxon_19' in metrics['missing_variables']
    assert 'rem_duration' in metrics['missing_variables']
    assert 'sleep_efficiency' in metrics['missing_variables']
    assert metrics['percentage_loaded'] == 87.5
    
    # CRITICAL: Verify the file was written to disk
    assert os.path.exists(output_path), "Metrics file was not written to disk"
    
    # Verify file content matches metrics
    with open(output_path, 'r') as f:
        saved_metrics = json.load(f)
    
    assert saved_metrics == metrics

def test_validate_variables_all_present(temp_output_dir):
    """
    Test validation when all required variables are present.
    """
    # Create a dataframe with all required variables
    required_vars = load_required_variables("data/config/required_variables.yaml")
    all_vars = required_vars['predictors'] + required_vars['outcomes']
    
    data = {var: [1, 2, 3] for var in all_vars}
    df = pd.DataFrame(data)
    
    output_path = os.path.join(temp_output_dir, "variable_load_metrics.json")
    metrics = validate_variables(df, required_vars, output_path)
    
    assert metrics['percentage_loaded'] == 100.0
    assert metrics['missing_variables'] == []
    assert metrics['total_required'] == len(all_vars)
    
    assert os.path.exists(output_path)

def test_validate_variables_empty_dataframe(temp_output_dir):
    """
    Test validation on an empty dataframe (no columns).
    """
    df = pd.DataFrame()
    required_vars = load_required_variables("data/config/required_variables.yaml")
    
    output_path = os.path.join(temp_output_dir, "variable_load_metrics.json")
    metrics = validate_variables(df, required_vars, output_path)
    
    assert metrics['percentage_loaded'] == 0.0
    assert len(metrics['missing_variables']) == 24
    assert metrics['total_required'] == 24
    
    assert os.path.exists(output_path)
