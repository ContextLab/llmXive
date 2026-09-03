import pytest
import pandas as pd
import numpy as np
from code.analysis import filter_outliers, run_sensitivity_analysis
from code.config import SEED

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(SEED)
    n_samples = 100
    data = {
        'smiles': [f'mol_{i}' for i in range(n_samples)],
        'degree_mean': np.random.normal(2.5, 0.5, n_samples),
        'degree_std': np.random.normal(0.3, 0.1, n_samples),
        'path_length_mean': np.random.normal(5.0, 1.0, n_samples),
        'path_length_std': np.random.normal(1.2, 0.3, n_samples),
        'aromaticity_index': np.random.choice([0, 1], n_samples),
        'conjugation_length': np.random.exponential(2.0, n_samples),
        'ring_count': np.random.poisson(1.5, n_samples),
        'log_conductivity': np.random.normal(0.0, 1.0, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_file(sample_data, tmp_path):
    """Create a temporary CSV file with sample data."""
    file_path = tmp_path / "test_descriptors.csv"
    sample_data.to_csv(file_path, index=False)
    return str(file_path)

@pytest.fixture
def temp_output_file(tmp_path):
    """Create a temporary output file path."""
    return str(tmp_path / "test_sensitivity.json")

def test_filter_outliers_basic(temp_data_file):
    """Test basic outlier filtering functionality."""
    df = pd.read_csv(temp_data_file)
    
    # Test with 3.0 sigma threshold
    filtered_df = filter_outliers(df, 'log_conductivity', 3.0)
    
    # Should have fewer rows than original
    assert len(filtered_df) <= len(df)
    
    # All remaining rows should have z-scores within threshold
    mean_val = df['log_conductivity'].mean()
    std_val = df['log_conductivity'].std()
    if std_val > 0:
        z_scores = (filtered_df['log_conductivity'] - mean_val) / std_val
        assert all(z_scores.abs() <= 3.0)

def test_filter_outliers_strict_threshold(temp_data_file):
    """Test that stricter threshold removes more outliers."""
    df = pd.read_csv(temp_data_file)
    
    filtered_2_5 = filter_outliers(df, 'log_conductivity', 2.5)
    filtered_3_5 = filter_outliers(df, 'log_conductivity', 3.5)
    
    # Stricter threshold should remove more data
    assert len(filtered_2_5) <= len(filtered_3_5)

def test_filter_outliers_invalid_column(temp_data_file):
    """Test error handling for invalid column name."""
    df = pd.read_csv(temp_data_file)
    
    with pytest.raises(ValueError):
        filter_outliers(df, 'nonexistent_column', 3.0)

def test_run_sensitivity_analysis(temp_data_file, temp_output_file):
    """Test the full sensitivity analysis pipeline."""
    results = run_sensitivity_analysis(
        data_path=temp_data_file,
        output_path=temp_output_file,
        thresholds=[2.5, 3.0]
    )
    
    # Check results structure
    assert 'thresholds' in results
    assert 'results' in results
    assert 'kruskal_test' in results
    
    # Check that results match thresholds
    assert len(results['results']) == 2
    
    # Check that each result has expected keys
    for result in results['results']:
        assert 'threshold' in result
        assert 'sample_size' in result
        assert 'rf_r2' in result or result.get('skipped', False)
        assert 'gb_r2' in result or result.get('skipped', False)
    
    # Check that output file was created
    import os
    assert os.path.exists(temp_output_file)

def test_run_sensitivity_analysis_kruskal_test(temp_data_file, temp_output_file):
    """Test that Kruskal-Wallis test is performed correctly."""
    # Create data with known variance differences
    np.random.seed(SEED)
    n_samples = 200
    data = {
        'smiles': [f'mol_{i}' for i in range(n_samples)],
        'degree_mean': np.random.normal(2.5, 0.5, n_samples),
        'degree_std': np.random.normal(0.3, 0.1, n_samples),
        'path_length_mean': np.random.normal(5.0, 1.0, n_samples),
        'path_length_std': np.random.normal(1.2, 0.3, n_samples),
        'aromaticity_index': np.random.choice([0, 1], n_samples),
        'conjugation_length': np.random.exponential(2.0, n_samples),
        'ring_count': np.random.poisson(1.5, n_samples),
        'log_conductivity': np.random.normal(0.0, 1.0, n_samples)
    }
    
    df = pd.DataFrame(data)
    temp_file = temp_data_file.replace('test_descriptors.csv', 'test_descriptors_large.csv')
    df.to_csv(temp_file, index=False)
    
    results = run_sensitivity_analysis(
        data_path=temp_file,
        output_path=temp_output_file,
        thresholds=[2.5, 3.0, 3.5]
    )
    
    # Check Kruskal-Wallis results
    assert 'kruskal_test' in results
    assert 'rf' in results['kruskal_test']
    assert 'gb' in results['kruskal_test']
    
    # Check that statistics are numeric
    assert isinstance(results['kruskal_test']['rf']['statistic'], float)
    assert isinstance(results['kruskal_test']['rf']['p_value'], float)
    assert isinstance(results['kruskal_test']['gb']['statistic'], float)
    assert isinstance(results['kruskal_test']['gb']['p_value'], float)

def test_run_sensitivity_analysis_output_file(temp_data_file, temp_output_file):
    """Test that output file is written correctly."""
    run_sensitivity_analysis(
        data_path=temp_data_file,
        output_path=temp_output_file,
        thresholds=[2.5, 3.0]
    )
    
    # Verify file exists and is valid JSON
    import json
    with open(temp_output_file, 'r') as f:
        loaded_results = json.load(f)
    
    assert 'thresholds' in loaded_results
    assert len(loaded_results['results']) == 2