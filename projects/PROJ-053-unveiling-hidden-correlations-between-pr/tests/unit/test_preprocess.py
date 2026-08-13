import pytest
import numpy as np
import pandas as pd
import json
import os
import tempfile
import logging
from pathlib import Path

# Import from the project's data module
from data.preprocess import (
    load_raw_csv,
    detect_missing_values,
    compute_medians,
    impute_missing_values,
    encode_categorical,
    check_sample_count,
    check_zero_variance,
    split_and_scale,
    save_normalization_bounds
)
from config import get_random_seed

# Setup logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def sample_raw_data():
    """Create a temporary CSV file with sample data for testing."""
    data = {
        'laser_power': [200.0, 250.0, 300.0, 350.0, 400.0, np.nan, 450.0],
        'scan_speed': [500.0, 600.0, 700.0, 800.0, 900.0, 1000.0, np.nan],
        'layer_thickness': [0.03, 0.03, 0.04, 0.04, 0.03, 0.04, 0.03],
        'alloy_type': ['AlSi10Mg', 'Inconel625', 'Ti64', 'AlSi10Mg', 'Inconel625', 'Ti64', 'AlSi10Mg'],
        'yield_strength': [300.0, 450.0, 800.0, 320.0, 470.0, np.nan, 850.0],
        'ductility': [15.0, 25.0, 8.0, 16.0, 24.0, 9.0, np.nan]
    }
    df = pd.DataFrame(data)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    return temp_path

@pytest.fixture
def sample_small_data():
    """Create a small CSV file with less than 50 samples for testing."""
    data = {
        'laser_power': [200.0, 250.0, 300.0],
        'scan_speed': [500.0, 600.0, 700.0],
        'layer_thickness': [0.03, 0.03, 0.04],
        'alloy_type': ['AlSi10Mg', 'Inconel625', 'Ti64'],
        'yield_strength': [300.0, 450.0, 800.0],
        'ductility': [15.0, 25.0, 8.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    return temp_path

@pytest.fixture
def sample_zero_variance_data():
    """Create a CSV file with a zero-variance column."""
    data = {
        'laser_power': [200.0, 250.0, 300.0, 350.0, 400.0],
        'scan_speed': [500.0, 600.0, 700.0, 800.0, 900.0],
        'layer_thickness': [0.04, 0.04, 0.04, 0.04, 0.04],  # Zero variance
        'alloy_type': ['AlSi10Mg', 'Inconel625', 'Ti64', 'AlSi10Mg', 'Inconel625'],
        'yield_strength': [300.0, 450.0, 800.0, 320.0, 470.0],
        'ductility': [15.0, 25.0, 8.0, 16.0, 24.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    return temp_path

def test_load_raw_csv(sample_raw_data):
    """Test loading a raw CSV file."""
    df = load_raw_csv(sample_raw_data)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 7
    assert 'laser_power' in df.columns
    assert 'yield_strength' in df.columns
    
    # Cleanup
    os.unlink(sample_raw_data)

def test_detect_missing_values(sample_raw_data):
    """Test detection of missing values in the dataset."""
    df = load_raw_csv(sample_raw_data)
    missing_info = detect_missing_values(df)
    
    assert 'laser_power' in missing_info
    assert 'scan_speed' in missing_info
    assert 'yield_strength' in missing_info
    assert 'ductility' in missing_info
    
    # Cleanup
    os.unlink(sample_raw_data)

def test_compute_medians(sample_raw_data):
    """Test median computation for imputation."""
    df = load_raw_csv(sample_raw_data)
    medians = compute_medians(df)
    
    assert 'laser_power' in medians
    assert 'scan_speed' in medians
    assert 'yield_strength' in medians
    assert 'ductility' in medians
    
    # Medians should be numeric
    assert isinstance(medians['laser_power'], (int, float))
    assert isinstance(medians['yield_strength'], (int, float))
    
    # Cleanup
    os.unlink(sample_raw_data)

def test_impute_missing_values(sample_raw_data):
    """Test median imputation logic - T010."""
    df = load_raw_csv(sample_raw_data)
    
    # Count original missing values
    original_missing = df.isnull().sum()
    assert original_missing['laser_power'] > 0
    assert original_missing['yield_strength'] > 0
    
    # Compute medians and impute
    medians = compute_medians(df)
    df_imputed = impute_missing_values(df, medians)
    
    # Verify no missing values remain in numeric columns
    assert df_imputed.isnull().sum().sum() == 0
    
    # Verify imputed values are the medians
    expected_laser_median = np.nanmedian([200.0, 250.0, 300.0, 350.0, 400.0, 450.0])
    assert df_imputed['laser_power'].iloc[5] == expected_laser_median
    
    # Cleanup
    os.unlink(sample_raw_data)

def test_encode_categorical(sample_raw_data):
    """Test one-hot encoding of alloy_type - T011."""
    df = load_raw_csv(sample_raw_data)
    medians = compute_medians(df)
    df_imputed = impute_missing_values(df, medians)
    
    # Get unique alloy types before encoding
    unique_alloys_before = df_imputed['alloy_type'].unique()
    assert len(unique_alloys_before) == 3  # AlSi10Mg, Inconel625, Ti64
    
    # Encode
    df_encoded = encode_categorical(df_imputed)
    
    # Verify original column is dropped
    assert 'alloy_type' not in df_encoded.columns
    
    # Verify one-hot columns are created
    assert 'alloy_type_AlSi10Mg' in df_encoded.columns
    assert 'alloy_type_Inconel625' in df_encoded.columns
    assert 'alloy_type_Ti64' in df_encoded.columns
    
    # Verify the encoding is correct (sum of one-hot columns should be 1 for each row)
    one_hot_cols = [col for col in df_encoded.columns if col.startswith('alloy_type_')]
    assert (df_encoded[one_hot_cols].sum(axis=1) == 1).all()
    
    # Cleanup
    os.unlink(sample_raw_data)

def test_check_sample_count_small(sample_small_data):
    """Test sample count check with less than 50 samples."""
    df = load_raw_csv(sample_small_data)
    
    with pytest.raises(ValueError) as exc_info:
        check_sample_count(df, min_samples=50)
    
    assert "insufficient samples" in str(exc_info.value).lower()
    
    # Cleanup
    os.unlink(sample_small_data)

def test_check_sample_count_valid(sample_raw_data):
    """Test sample count check with sufficient samples."""
    # Create a larger dataset
    data = {
        'laser_power': np.random.uniform(200, 400, 100),
        'scan_speed': np.random.uniform(500, 900, 100),
        'layer_thickness': np.random.uniform(0.03, 0.05, 100),
        'alloy_type': np.random.choice(['AlSi10Mg', 'Inconel625', 'Ti64'], 100),
        'yield_strength': np.random.uniform(300, 800, 100),
        'ductility': np.random.uniform(10, 30, 100)
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    df_loaded = load_raw_csv(temp_path)
    # Should not raise
    result = check_sample_count(df_loaded, min_samples=50)
    assert result is True
    
    # Cleanup
    os.unlink(temp_path)

def test_check_zero_variance(sample_zero_variance_data):
    """Test zero-variance detection and dropping - T018."""
    df = load_raw_csv(sample_zero_variance_data)
    
    # Before checking, layer_thickness has zero variance
    assert df['layer_thickness'].var() == 0.0
    
    # Check and drop zero-variance columns
    df_cleaned = check_zero_variance(df)
    
    # Verify layer_thickness is dropped
    assert 'layer_thickness' not in df_cleaned.columns
    
    # Verify other columns remain
    assert 'laser_power' in df_cleaned.columns
    assert 'scan_speed' in df_cleaned.columns
    
    # Cleanup
    os.unlink(sample_zero_variance_data)

def test_split_and_scale():
    """Test train-test split and MinMax scaling."""
    # Create sample data
    np.random.seed(42)
    n_samples = 100
    data = {
        'laser_power': np.random.uniform(200, 400, n_samples),
        'scan_speed': np.random.uniform(500, 900, n_samples),
        'yield_strength_encoded': np.random.uniform(300, 800, n_samples),
        'ductility_encoded': np.random.uniform(10, 30, n_samples)
    }
    df = pd.DataFrame(data)
    
    # Split and scale
    X_train, X_test, y_train, y_test, scaler = split_and_scale(
        df[['laser_power', 'scan_speed']],
        df[['yield_strength_encoded', 'ductility_encoded']],
        random_state=get_random_seed()
    )
    
    # Verify split sizes
    assert len(X_train) + len(X_test) == n_samples
    assert len(y_train) == len(X_train)
    assert len(y_test) == len(X_test)
    
    # Verify scaling (train set should be in [0, 1])
    assert X_train.min().min() >= 0.0
    assert X_train.max().max() <= 1.0
    
    # Verify test set is scaled using train statistics
    # (may be outside [0, 1] if test has different range)
    assert X_test.shape[0] > 0
    assert X_test.shape[1] == X_train.shape[1]
    
    # Verify scaler is fitted
    assert scaler is not None

def test_save_normalization_bounds():
    """Test saving normalization bounds to JSON."""
    bounds = {
        'laser_power': {'min': 200.0, 'max': 400.0},
        'scan_speed': {'min': 500.0, 'max': 900.0},
        'yield_strength': {'min': 300.0, 'max': 800.0}
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'normalization_bounds.json')
        save_normalization_bounds(bounds, output_path)
        
        # Verify file exists and contains correct data
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            loaded_bounds = json.load(f)
        
        assert loaded_bounds == bounds

def test_full_preprocess_pipeline():
    """Test the full preprocessing pipeline end-to-end."""
    # Create a realistic dataset
    np.random.seed(42)
    n_samples = 100
    data = {
        'laser_power': np.random.uniform(200, 400, n_samples),
        'scan_speed': np.random.uniform(500, 900, n_samples),
        'layer_thickness': np.random.choice([0.03, 0.04, 0.05], n_samples),
        'alloy_type': np.random.choice(['AlSi10Mg', 'Inconel625', 'Ti64'], n_samples),
        'yield_strength': np.random.uniform(300, 800, n_samples),
        'ductility': np.random.uniform(10, 30, n_samples)
    }
    
    # Introduce some missing values
    df = pd.DataFrame(data)
    df.loc[np.random.choice(df.index, 5), 'laser_power'] = np.nan
    df.loc[np.random.choice(df.index, 3), 'yield_strength'] = np.nan
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save raw data
        raw_path = os.path.join(tmpdir, 'raw_data.csv')
        df.to_csv(raw_path, index=False)
        
        # Load and preprocess
        df_raw = load_raw_csv(raw_path)
        missing = detect_missing_values(df_raw)
        medians = compute_medians(df_raw)
        df_imputed = impute_missing_values(df_raw, medians)
        df_encoded = encode_categorical(df_imputed)
        df_cleaned = check_zero_variance(df_encoded)
        
        # Split and scale
        feature_cols = [col for col in df_cleaned.columns if col not in ['yield_strength', 'ductility']]
        target_cols = ['yield_strength', 'ductility']
        
        X = df_cleaned[feature_cols]
        y = df_cleaned[target_cols]
        
        X_train, X_test, y_train, y_test, scaler = split_and_scale(
            X, y, random_state=get_random_seed()
        )
        
        # Verify no missing values
        assert X_train.isnull().sum().sum() == 0
        assert X_test.isnull().sum().sum() == 0
        assert y_train.isnull().sum().sum() == 0
        assert y_test.isnull().sum().sum() == 0
        
        # Verify one-hot encoding worked
        assert any(col.startswith('alloy_type_') for col in X_train.columns)
        
        # Verify scaling
        assert X_train.min().min() >= 0.0
        assert X_train.max().max() <= 1.0
        
        # Save normalization bounds
        bounds_path = os.path.join(tmpdir, 'bounds.json')
        bounds = {col: {'min': X_train[col].min(), 'max': X_train[col].max()} 
                 for col in X_train.columns}
        save_normalization_bounds(bounds, bounds_path)
        
        assert os.path.exists(bounds_path)
