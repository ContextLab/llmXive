import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from src.validation.stratified_analysis import (
    load_features_data,
    get_strata_groups,
    train_model_on_stratum,
    run_stratified_analysis,
    MIN_STRATUM_SAMPLES
)

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    data = {
        'composition': [
            '{"Co": 0.5, "Mn": 0.5}',
            '{"Ni": 0.5, "Mn": 0.5}',
            '{"Co": 0.5, "Mn": 0.5}',
            '{"Ni": 0.5, "Mn": 0.5}',
            '{"Co": 0.5, "Mn": 0.5}',
            '{"Ni": 0.5, "Mn": 0.5}',
            '{"Co": 0.5, "Mn": 0.5}',
            '{"Ni": 0.5, "Mn": 0.5}',
            '{"Co": 0.5, "Mn": 0.5}',
            '{"Ni": 0.5, "Mn": 0.5}',
            '{"Co": 0.5, "Mn": 0.5}',
            '{"Ni": 0.5, "Mn": 0.5}',
            '{"Co": 0.5, "Mn": 0.5}',
            '{"Ni": 0.5, "Mn": 0.5}',
            '{"Co": 0.5, "Mn": 0.5}',
        ],
        'synthesis_method': [
            'Arc Melting', 'Arc Melting', 'Arc Melting', 'Arc Melting', 'Arc Melting',
            'Sputtering', 'Sputtering', 'Sputtering', 'Sputtering', 'Sputtering',
            'Arc Melting', 'Arc Melting', 'Arc Melting', 'Arc Melting', 'Arc Melting',
        ],
        'coercivity_oe': [
            100.0, 110.0, 105.0, 115.0, 102.0,
            50.0, 55.0, 52.0, 58.0, 51.0,
            108.0, 106.0, 104.0, 109.0, 107.0,
        ],
        'saturation_magnetization_emu_g': [
            120.0, 125.0, 122.0, 128.0, 121.0,
            90.0, 95.0, 92.0, 98.0, 91.0,
            123.0, 121.0, 119.0, 124.0, 122.0,
        ],
        'avg_electronegativity': [1.7, 1.8, 1.7, 1.8, 1.7, 1.8, 1.8, 1.8, 1.7, 1.8, 1.7, 1.7, 1.7, 1.7, 1.7],
        'VEC': [8.0, 9.0, 8.0, 9.0, 8.0, 9.0, 9.0, 9.0, 8.0, 9.0, 8.0, 8.0, 8.0, 8.0, 8.0],
        'atomic_radii_variance': [0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.02, 0.02, 0.01, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01]
    }
    return pd.DataFrame(data)

@pytest.fixture
def small_dataframe():
    """Create a dataframe with a stratum that has too few samples."""
    data = {
        'composition': ['{"A": 0.5, "B": 0.5}'] * 3,
        'synthesis_method': ['Rare_Method'] * 3,
        'coercivity_oe': [100.0, 110.0, 105.0],
        'avg_electronegativity': [1.5, 1.6, 1.5],
        'VEC': [8.0, 8.0, 8.0],
        'atomic_radii_variance': [0.01, 0.01, 0.01]
    }
    return pd.DataFrame(data)

def test_load_features_data(sample_dataframe, tmp_path):
    """Test loading data from a CSV file."""
    file_path = tmp_path / "test.csv"
    sample_dataframe.to_csv(file_path, index=False)
    
    loaded_df = load_features_data(str(file_path))
    
    assert len(loaded_df) == len(sample_dataframe)
    assert 'coercivity_oe' in loaded_df.columns
    assert 'synthesis_method' in loaded_df.columns

def test_get_strata_groups(sample_dataframe):
    """Test grouping by synthesis method."""
    groups = get_strata_groups(sample_dataframe, 'synthesis_method')
    
    assert 'Arc Melting' in groups
    assert 'Sputtering' in groups
    assert len(groups['Arc Melting']) == 10
    assert len(groups['Sputtering']) == 5

def test_train_model_on_stratum_insufficient_data(small_dataframe, tmp_path):
    """Test that training skips strata with insufficient data."""
    # Ensure we have fewer than MIN_STRATUM_SAMPLES
    assert len(small_dataframe) < MIN_STRATUM_SAMPLES
    
    model, metrics, status = train_model_on_stratum(
        small_dataframe, 
        target_col='coercivity_oe',
        feature_cols=['avg_electronegativity', 'VEC']
    )
    
    assert model is None
    assert metrics == {}
    assert status == 'skipped_insufficient_data'

def test_train_model_on_stratum_success(sample_dataframe):
    """Test that training succeeds on a valid stratum."""
    arc_melting_df = sample_dataframe[sample_dataframe['synthesis_method'] == 'Arc Melting']
    
    model, metrics, status = train_model_on_stratum(
        arc_melting_df,
        target_col='coercivity_oe',
        feature_cols=['avg_electronegativity', 'VEC', 'atomic_radii_variance']
    )
    
    assert model is not None
    assert status == 'trained'
    assert 'r2' in metrics
    assert 'mae' in metrics
    assert isinstance(metrics['r2'], float)
    assert isinstance(metrics['mae'], float)

def test_run_stratified_analysis_skips_small_strata(sample_dataframe, small_dataframe, tmp_path):
    """Test that run_stratified_analysis skips small strata and trains on large ones."""
    # Combine dataframes
    combined_df = pd.concat([sample_dataframe, small_dataframe], ignore_index=True)
    file_path = tmp_path / "combined.csv"
    combined_df.to_csv(file_path, index=False)
    
    output_path = tmp_path / "results.json"
    
    results = run_stratified_analysis(
        str(file_path),
        str(output_path),
        stratify_col='synthesis_method',
        target_col='coercivity_oe'
    )
    
    # Check that output file was created
    assert output_path.exists()
    
    # Check results structure
    assert 'strata' in results
    assert 'Arc Melting' in results['strata']
    assert 'Sputtering' in results['strata']
    assert 'Rare_Method' in results['strata']
    
    # Arc Melting should be trained (has 10 samples)
    assert results['strata']['Arc Melting']['status'] == 'trained'
    
    # Rare_Method should be skipped (has 3 samples)
    assert results['strata']['Rare_Method']['status'] == 'skipped_insufficient_data'
    
    # Sputtering should be trained (has 5 samples, equal to threshold)
    # Note: Our threshold is 5, so 5 samples should train
    assert results['strata']['Sputtering']['status'] == 'trained'

def test_run_stratified_analysis_file_not_found():
    """Test handling of missing input file."""
    with pytest.raises(FileNotFoundError):
        run_stratified_analysis(
            "non_existent_file.csv",
            "output.json"
        )