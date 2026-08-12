"""
Unit tests for variable_verification module.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from code.analysis.variable_verification import (
    verify_sample_variables,
    verify_disease_variables,
    run_variable_verification,
    SAMPLE_VARIABLES,
    DISEASE_VARIABLES
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with some required variables."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3'],
        'plant_species': ['Corn', 'Wheat', 'Soy'],
        'gps_latitude': [40.1, 40.2, 40.3],
        'gps_longitude': [-93.1, -93.2, -93.3],
        'soil_type': ['Clay', 'Sandy', 'Loam'],
        'sequencing_depth': [10000, 15000, 12000]
    })

@pytest.fixture
def sample_df_missing_vars():
    """Create a sample DataFrame with missing variables."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2'],
        'plant_species': ['Corn', 'Wheat'],
        # Missing gps_latitude, gps_longitude, soil_type, sequencing_depth
    })

@pytest.fixture
def disease_df():
    """Create a disease DataFrame with required variables."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3'],
        'disease_type': ['Fungal', 'Bacterial', 'Viral'],
        'incidence_rate': [0.15, 0.25, 0.10],
        'measurement_date': ['2023-06-01', '2023-06-02', '2023-06-03']
    })

@pytest.fixture
def disease_df_missing_vars():
    """Create a disease DataFrame with missing variables."""
    return pd.DataFrame({
        'sample_id': ['S1'],
        'disease_type': ['Fungal'],
        # Missing incidence_rate, measurement_date
    })

def test_verify_sample_variables_all_present(sample_df):
    """Test verification when all sample variables are present."""
    results = verify_sample_variables(sample_df, "test.csv")
    
    assert len(results) == len(SAMPLE_VARIABLES) * len(sample_df)
    
    # Check that all variables are marked as present
    variable_statuses = {r['variable_name']: r['status'] for r in results}
    for var in SAMPLE_VARIABLES:
        assert variable_statuses[var] == 'present'

def test_verify_sample_variables_missing(sample_df_missing_vars):
    """Test verification when some sample variables are missing."""
    results = verify_sample_variables(sample_df_missing_vars, "test.csv")
    
    variable_statuses = {}
    for r in results:
        if r['variable_name'] not in variable_statuses:
            variable_statuses[r['variable_name']] = r['status']
    
    # Present variables
    assert variable_statuses.get('sample_id') == 'present'
    assert variable_statuses.get('plant_species') == 'present'
    
    # Missing variables
    assert variable_statuses.get('gps_latitude') == 'missing'
    assert variable_statuses.get('gps_longitude') == 'missing'
    assert variable_statuses.get('soil_type') == 'missing'
    assert variable_statuses.get('sequencing_depth') == 'missing'

def test_verify_disease_variables_all_present(disease_df):
    """Test verification when all disease variables are present."""
    results = verify_disease_variables(disease_df, "test.csv")
    
    assert len(results) == len(DISEASE_VARIABLES) * len(disease_df)
    
    # Check that all variables are marked as present
    variable_statuses = {r['variable_name']: r['status'] for r in results}
    for var in DISEASE_VARIABLES:
        assert variable_statuses[var] == 'present'

def test_verify_disease_variables_missing(disease_df_missing_vars):
    """Test verification when some disease variables are missing."""
    results = verify_disease_variables(disease_df_missing_vars, "test.csv")
    
    variable_statuses = {}
    for r in results:
        if r['variable_name'] not in variable_statuses:
            variable_statuses[r['variable_name']] = r['status']
    
    # Present variables
    assert variable_statuses.get('sample_id') == 'present'
    assert variable_statuses.get('disease_type') == 'present'
    
    # Missing variables
    assert variable_statuses.get('incidence_rate') == 'missing'
    assert variable_statuses.get('measurement_date') == 'missing'

def test_run_variable_verification_creates_file(sample_df, disease_df):
    """Test that run_variable_verification creates the output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_path = os.path.join(tmpdir, "sample.csv")
        disease_path = os.path.join(tmpdir, "disease.csv")
        output_path = os.path.join(tmpdir, "verification_log.csv")
        
        sample_df.to_csv(sample_path, index=False)
        disease_df.to_csv(disease_path, index=False)
        
        result_df = run_variable_verification(
            sample_path=sample_path,
            disease_path=disease_path,
            output_path=output_path
        )
        
        assert os.path.exists(output_path)
        assert len(result_df) > 0
        assert 'sample_id' in result_df.columns
        assert 'variable_name' in result_df.columns
        assert 'status' in result_df.columns

def test_run_variable_verification_empty_input():
    """Test handling of empty input data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "verification_log.csv")
        
        result_df = run_variable_verification(
            sample_path=None,
            disease_path=None,
            output_path=output_path
        )
        
        assert os.path.exists(output_path)
        # Should create empty file with headers
        assert len(result_df) == 0

def test_output_columns_match_requirement():
    """Verify output has required columns: sample_id, variable_name, status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_path = os.path.join(tmpdir, "sample.csv")
        disease_path = os.path.join(tmpdir, "disease.csv")
        output_path = os.path.join(tmpdir, "verification_log.csv")
        
        sample_df = pd.DataFrame({
            'sample_id': ['S1'],
            'plant_species': ['Corn'],
            'gps_latitude': [40.1],
            'gps_longitude': [-93.1],
            'soil_type': ['Clay'],
            'sequencing_depth': [10000]
        })
        disease_df = pd.DataFrame({
            'sample_id': ['S1'],
            'disease_type': ['Fungal'],
            'incidence_rate': [0.15],
            'measurement_date': ['2023-06-01']
        })
        
        sample_df.to_csv(sample_path, index=False)
        disease_df.to_csv(disease_path, index=False)
        
        result_df = run_variable_verification(
            sample_path=sample_path,
            disease_path=disease_path,
            output_path=output_path
        )
        
        assert 'sample_id' in result_df.columns
        assert 'variable_name' in result_df.columns
        assert 'status' in result_df.columns
        assert all(c in result_df.columns for c in ['sample_id', 'variable_name', 'status'])
