import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import (
    load_config,
    load_data,
    exclude_missing_data,
    stratified_split,
    apply_pca,
    main
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'material_id': [f'mat_{i}' for i in range(n_samples)],
        'formula': [f'A{i}B{i}' for i in range(n_samples)],
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.randn(n_samples),
        'feature_4': np.random.randn(n_samples),
        'formation_energy': np.random.randn(n_samples) * 0.5
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_data_with_missing(sample_data):
    """Create sample data with some missing values."""
    df = sample_data.copy()
    # Add some missing values
    df.loc[5:10, 'feature_1'] = np.nan
    df.loc[15:20, 'feature_2'] = np.nan
    return df

@pytest.fixture
def config_file(tmp_path):
    """Create a temporary config file."""
    config_path = tmp_path / "config.yaml"
    config_content = """
    seed: 42
    split_ratio: [0.8, 0.1, 0.1]
    split_type: "stratified"
    timeout_hours: 5.0
    """
    config_path.write_text(config_content)
    return str(config_path)

@pytest.fixture
def parquet_file(tmp_path, sample_data):
    """Create a temporary parquet file."""
    parquet_path = tmp_path / "test_data.parquet"
    sample_data.to_parquet(parquet_path)
    return str(parquet_path)

def test_load_config(config_file):
    """Test loading configuration from YAML."""
    config = load_config(config_file)
    assert config['seed'] == 42
    assert config['split_ratio'] == [0.8, 0.1, 0.1]
    assert config['split_type'] == "stratified"
    assert config['timeout_hours'] == 5.0

def test_load_data(parquet_file):
    """Test loading data from parquet file."""
    df = load_data(parquet_file)
    assert len(df) == 100
    assert 'formation_energy' in df.columns

def test_exclude_missing_data(sample_data_with_missing):
    """Test exclusion of rows with missing data."""
    cleaned_df, exclusion_log = exclude_missing_data(sample_data_with_missing)
    
    # Check that rows with missing values were excluded
    assert len(cleaned_df) < len(sample_data_with_missing)
    assert exclusion_log['excluded_count'] > 0
    assert 'feature_1' in exclusion_log['missing_columns'] or 'feature_2' in exclusion_log['missing_columns']

def test_stratified_split(sample_data):
    """Test stratified splitting of data."""
    train_df, val_df, test_df = stratified_split(
        sample_data, 
        target_col='formation_energy',
        split_ratio=[0.8, 0.1, 0.1],
        seed=42
    )
    
    # Check split ratios (allowing for small variations due to binning)
    total = len(train_df) + len(val_df) + len(test_df)
    assert abs(len(train_df) / total - 0.8) < 0.05
    assert abs(len(val_df) / total - 0.1) < 0.05
    assert abs(len(test_df) / total - 0.1) < 0.05
    
    # Check that no duplicates across splits
    train_ids = set(train_df['material_id'])
    val_ids = set(val_df['material_id'])
    test_ids = set(test_df['material_id'])
    
    assert len(train_ids & val_ids) == 0
    assert len(train_ids & test_ids) == 0
    assert len(val_ids & test_ids) == 0

def test_apply_pca(sample_data):
    """Test PCA application."""
    pca_df, pca_model = apply_pca(sample_data, n_components=3, seed=42)
    
    # Check that PCA components are created
    assert 'pca_0' in pca_df.columns
    assert 'pca_1' in pca_df.columns
    assert 'pca_2' in pca_df.columns
    assert len(pca_df.columns) >= 4  # 3 PCA + target
    
    # Check that number of rows is preserved
    assert len(pca_df) == len(sample_data)
    
    # Check that target column is preserved
    assert 'formation_energy' in pca_df.columns

def test_apply_pca_with_fewer_components(sample_data):
    """Test PCA with fewer components than features."""
    pca_df, pca_model = apply_pca(sample_data, n_components=2, seed=42)
    
    assert 'pca_0' in pca_df.columns
    assert 'pca_1' in pca_df.columns
    assert 'pca_2' not in pca_df.columns  # Should not exist
    assert len(pca_df.columns) == 4  # 2 PCA + target + material_id or formula

def test_exclude_missing_data_empty_list(sample_data):
    """Test exclusion when no critical columns specified."""
    cleaned_df, exclusion_log = exclude_missing_data(sample_data, critical_columns=[])
    assert len(cleaned_df) == len(sample_data)
    assert exclusion_log['excluded_count'] == 0
    assert len(exclusion_log['missing_columns']) == 0

def test_main_integration(tmp_path, sample_data_with_missing, config_file):
    """Test the main function integration."""
    # Create temporary directories
    data_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Save sample data
    parquet_path = data_dir / "oqmd.parquet"
    sample_data_with_missing.to_parquet(parquet_path)
    
    # Temporarily override paths for testing
    original_load_data = load_data
    original_load_config = load_config
    
    def mock_load_data(data_path="data/raw/oqmd.parquet"):
        return pd.read_parquet(str(parquet_path))
    
    def mock_load_config(config_path="code/config.yaml"):
        return load_config(config_file)
    
    # Monkey patch for test
    import data.preprocess as preprocess_module
    preprocess_module.load_data = mock_load_data
    preprocess_module.load_config = mock_load_config
    
    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run main
        main()
        
        # Check outputs
        assert (processed_dir / "exclusion_log.json").exists()
        assert (processed_dir / "features_20pca.csv").exists()
        
        # Verify exclusion log content
        with open(processed_dir / "exclusion_log.json", 'r') as f:
            exclusion_log = json.load(f)
        assert 'excluded_count' in exclusion_log
        assert 'missing_columns' in exclusion_log
        
        # Verify features file
        features_df = pd.read_csv(processed_dir / "features_20pca.csv")
        assert 'pca_0' in features_df.columns
        assert 'formation_energy' in features_df.columns
        
    finally:
        # Restore original functions and directory
        preprocess_module.load_data = original_load_data
        preprocess_module.load_config = original_load_config
        os.chdir(original_cwd)