import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
import tempfile
import json

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.preprocessing import (
    calculate_energy_density,
    verify_column_integrity,
    calculate_vif,
    perform_vif_analysis,
    perform_loafo_split,
    perform_stratified_split,
    split_data,
    save_split_artifacts
)

@pytest.fixture
def sample_curated_data():
    """Create a sample curated dataset for testing."""
    data = {
        'laser_power': [200, 300, 250, 350, 200, 300, 250, 350],
        'scan_speed': [800, 1000, 900, 1100, 800, 1000, 900, 1100],
        'hatch_spacing': [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        'layer_thickness': [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05],
        'ductility': [15.5, 12.3, 14.2, 10.8, 16.1, 11.9, 13.7, 11.2],
        'alloy_family': ['Inconel-718', 'Inconel-718', 'Inconel-718', 'Inconel-718',
                        'Hastelloy-X', 'Hastelloy-X', 'Hastelloy-X', 'Hastelloy-X'],
        'alloy_composition': ['Ni-19Cr', 'Ni-19Cr', 'Ni-19Cr', 'Ni-19Cr',
                             'Ni-16Cr', 'Ni-16Cr', 'Ni-16Cr', 'Ni-16Cr']
    }
    return pd.DataFrame(data)

@pytest.fixture
def large_curated_data():
    """Create a larger dataset (>=100 rows) for stratified split testing."""
    np.random.seed(42)
    n_samples = 150
    
    data = {
        'laser_power': np.random.uniform(150, 400, n_samples),
        'scan_speed': np.random.uniform(500, 1200, n_samples),
        'hatch_spacing': np.random.uniform(0.08, 0.12, n_samples),
        'layer_thickness': np.random.uniform(0.03, 0.07, n_samples),
        'ductility': np.random.uniform(8, 20, n_samples),
        'alloy_family': np.random.choice(['Inconel-718', 'Hastelloy-X', 'Mar-M-247', 'CMX-4'], n_samples),
        'alloy_composition': np.random.choice(['Ni-19Cr', 'Ni-16Cr', 'Ni-20Cr', 'Ni-18Cr'], n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_placeholder_preprocessing():
    """Placeholder test to ensure the test file is valid."""
    assert True

def test_calculate_energy_density(sample_curated_data):
    """Test energy density calculation."""
    df = calculate_energy_density(sample_curated_data)
    
    assert 'energy_density' in df.columns
    assert len(df) == len(sample_curated_data)
    
    # Verify calculation for first row
    # E_v = P / (v * h * t) = 200 / (800 * 0.1 * 0.05) = 200 / 4 = 50
    expected_ev = 200 / (800 * 0.1 * 0.05)
    assert abs(df.iloc[0]['energy_density'] - expected_ev) < 0.01

def test_verify_column_integrity(sample_curated_data):
    """Test column integrity verification."""
    required_cols = ['laser_power', 'scan_speed', 'ductility']
    all_present, missing = verify_column_integrity(sample_curated_data, required_cols)
    
    assert all_present
    assert len(missing) == 0
    
    # Test with missing column
    required_cols_missing = ['laser_power', 'nonexistent_col']
    all_present, missing = verify_column_integrity(sample_curated_data, required_cols_missing)
    
    assert not all_present
    assert 'nonexistent_col' in missing

def test_calculate_vif(sample_curated_data):
    """Test VIF calculation."""
    features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    vif_df = calculate_vif(sample_curated_data, features)
    
    assert 'feature' in vif_df.columns
    assert 'VIF' in vif_df.columns
    assert len(vif_df) == len(features)
    
    # VIF should be >= 1 for all features (or NaN if insufficient data)
    valid_vifs = vif_df['VIF'].dropna()
    if len(valid_vifs) > 0:
        assert all(valid_vifs >= 1.0)

def test_perform_vif_analysis(sample_curated_data):
    """Test VIF analysis and feature selection."""
    features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density']
    
    # Add energy density to dataframe first
    df = calculate_energy_density(sample_curated_data)
    
    filtered_df, selected_features = perform_vif_analysis(df, features, threshold=5.0)
    
    assert 'energy_density' in selected_features or len(selected_features) < len(features)
    assert len(filtered_df) > 0

def test_perform_loafo_split(sample_curated_data):
    """Test LOAFO split logic."""
    result = perform_loafo_split(sample_curated_data, 'ductility', ['laser_power', 'scan_speed'])
    
    assert 'folds' in result
    assert 'strategy' in result
    assert result['strategy'] == 'LOAFO'
    
    # Should have one fold per unique alloy family
    assert len(result['folds']) == len(sample_curated_data['alloy_family'].unique())
    
    # Check each fold
    for fold in result['folds']:
        assert 'train' in fold
        assert 'test' in fold
        assert 'left_out_family' in fold
        
        # Test set should only contain the left-out family
        test_families = fold['test']['alloy_family'].unique()
        assert len(test_families) == 1
        assert test_families[0] == fold['left_out_family']
        
        # Train set should not contain the left-out family
        train_families = fold['train']['alloy_family'].unique()
        assert fold['left_out_family'] not in train_families

def test_perform_stratified_split(large_curated_data):
    """Test stratified split logic."""
    result = perform_stratified_split(large_curated_data, 'ductility', ['laser_power', 'scan_speed'])
    
    assert 'train' in result
    assert 'val' in result
    assert 'test' in result
    assert result['strategy'] == 'stratified'
    
    # Check that all sets are non-empty
    assert len(result['train']) > 0
    assert len(result['val']) > 0
    assert len(result['test']) > 0
    
    # Check stratification (alloy families should be represented in all sets)
    train_families = set(result['train']['alloy_family'].unique())
    val_families = set(result['val']['alloy_family'].unique())
    test_families = set(result['test']['alloy_family'].unique())
    
    # All sets should have similar family representation
    assert len(train_families.intersection(val_families)) > 0
    assert len(train_families.intersection(test_families)) > 0

def test_split_data_small_dataset(sample_curated_data):
    """Test split_data with small dataset (<100 rows) uses LOAFO."""
    result = split_data(sample_curated_data, 'ductility', ['laser_power', 'scan_speed'])
    
    assert result['strategy'] == 'LOAFO'
    assert 'folds' in result

def test_split_data_large_dataset(large_curated_data):
    """Test split_data with large dataset (>=100 rows) uses stratified split."""
    result = split_data(large_curated_data, 'ductility', ['laser_power', 'scan_speed'])
    
    assert result['strategy'] == 'stratified'
    assert 'train' in result
    assert 'val' in result
    assert 'test' in result

def test_split_deterministic(sample_curated_data):
    """Test that stratified split is deterministic with random_state."""
    result1 = perform_stratified_split(sample_curated_data, 'ductility', ['laser_power'])
    result2 = perform_stratified_split(sample_curated_data, 'ductility', ['laser_power'])
    
    # For LOAFO, order might differ but content should be same
    # For stratified, with random_state=42, results should be identical
    if sample_curated_data['alloy_family'].nunique() > 1:
        # Check that splits are consistent
        assert len(result1['train']) == len(result2['train'])
        assert len(result1['test']) == len(result2['test'])

def test_save_split_artifacts_loafo(sample_curated_data, temp_output_dir):
    """Test saving LOAFO split artifacts."""
    splits = perform_loafo_split(sample_curated_data, 'ductility', ['laser_power'])
    splits['n_samples'] = len(sample_curated_data)
    splits['strategy_description'] = 'Test LOAFO'
    
    saved_paths = save_split_artifacts(splits, temp_output_dir)
    
    assert len(saved_paths) > 0
    assert any('metadata.json' in str(p) for p in saved_paths)
    
    # Check that fold files were created
    fold_files = [p for p in saved_paths if 'fold_' in str(p)]
    assert len(fold_files) > 0

def test_save_split_artifacts_stratified(large_curated_data, temp_output_dir):
    """Test saving stratified split artifacts."""
    splits = perform_stratified_split(large_curated_data, 'ductility', ['laser_power'])
    
    saved_paths = save_split_artifacts(splits, temp_output_dir)
    
    assert len(saved_paths) > 0
    assert any('train.csv' in str(p) for p in saved_paths)
    assert any('val.csv' in str(p) for p in saved_paths)
    assert any('test.csv' in str(p) for p in saved_paths)

def test_save_split_artifacts_metadata(temp_output_dir):
    """Test that metadata is saved correctly."""
    sample_data = {
        'train': pd.DataFrame({'a': [1, 2]}),
        'test': pd.DataFrame({'a': [3, 4]}),
        'strategy': 'test_strategy',
        'n_samples': 4
    }
    
    save_split_artifacts(sample_data, temp_output_dir)
    
    metadata_path = temp_output_dir / 'split_metadata.json'
    assert metadata_path.exists()
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert metadata['strategy'] == 'test_strategy'
    assert metadata['n_samples'] == 4
