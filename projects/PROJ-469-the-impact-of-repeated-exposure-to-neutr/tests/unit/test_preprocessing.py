"""
Unit tests for preprocessing module (MICE Imputation).
"""
import pytest
import pandas as pd
import numpy as np
from preprocessing import impute_mice, load_data, derive_variables
from config import ensure_dirs
import os
import tempfile

@pytest.fixture
def sample_data_with_missing():
    """Create a sample dataframe with missing values."""
    data = {
        'id': range(100),
        'IAT_D_score': np.random.normal(0, 0.5, 100),
        'political_ideology': np.random.normal(5, 2, 100),
        'news_exposure_freq': np.random.normal(3, 1, 100),
    }
    df = pd.DataFrame(data)
    
    # Introduce missing values (approx 10% missing)
    mask = np.random.choice([0, 1], size=(100, 3), p=[0.1, 0.9]).astype(bool)
    df.iloc[mask[:, 0], 1] = np.nan # IAT_D_score
    df.iloc[mask[:, 1], 2] = np.nan # political_ideology
    df.iloc[mask[:, 2], 3] = np.nan # news_exposure_freq
    
    return df

@pytest.fixture
def sample_data_high_missing():
    """Create a sample dataframe with >50% missing values."""
    data = {
        'IAT_D_score': np.random.normal(0, 0.5, 100),
        'political_ideology': np.random.normal(5, 2, 100),
        'news_exposure_freq': np.random.normal(3, 1, 100),
    }
    df = pd.DataFrame(data)
    
    # Introduce >50% missing values
    mask = np.random.choice([0, 1], size=(100, 3), p=[0.6, 0.4]).astype(bool)
    df.iloc[mask[:, 0], 0] = np.nan
    df.iloc[mask[:, 1], 1] = np.nan
    df.iloc[mask[:, 2], 2] = np.nan
    
    return df

def test_impute_mice_no_missing():
    """Test that impute_mice returns a copy if no missing values."""
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    imputed, diag = impute_mice(df)
    
    assert imputed.equals(df)
    assert len(diag) == 0 or diag['missing_rate'].sum() == 0

def test_impute_mice_with_missing(sample_data_with_missing):
    """Test MICE imputation on data with <50% missing."""
    imputed_df, diag_df = impute_mice(sample_data_with_missing)
    
    # Check shape is preserved
    assert imputed_df.shape == sample_data_with_missing.shape
    
    # Check no missing values remain in numeric columns
    numeric_cols = imputed_df.select_dtypes(include=[np.number]).columns
    assert imputed_df[numeric_cols].isnull().sum().sum() == 0
    
    # Check diagnostics
    assert 'column' in diag_df.columns
    assert 'missing_rate' in diag_df.columns
    assert len(diag_df) > 0

def test_impute_mice_high_missing_raises(sample_data_high_missing):
    """Test that impute_mice raises ValueError if missingness > 50%."""
    with pytest.raises(ValueError, match="exceeds threshold"):
        impute_mice(sample_data_high_missing)

def test_derive_variables(sample_data_with_missing):
    """Test derivation of z-scored and binary variables."""
    # Run imputation first to ensure no missing values
    imputed_df, _ = impute_mice(sample_data_with_missing)
    
    derived_df = derive_variables(imputed_df)
    
    # Check new columns exist
    assert 'news_exposure_z' in derived_df.columns
    assert 'ideology_binary' in derived_df.columns
    
    # Check z-score properties (approx mean 0, std 1)
    # Note: due to floating point and imputation noise, exact 0/1 is unlikely, but close
    z_mean = derived_df['news_exposure_z'].mean()
    z_std = derived_df['news_exposure_z'].std()
    assert np.isclose(z_mean, 0, atol=1e-5)
    assert np.isclose(z_std, 1, atol=1e-5)
    
    # Check binary values are 0 or 1
    assert set(derived_df['ideology_binary'].unique()).issubset({0, 1})

def test_impute_mice_output_file_creation(tmp_path):
    """Test that the imputation logic can be run and output written to disk."""
    # Create a temporary CSV for testing
    data = {
        'id': range(50),
        'IAT_D_score': np.random.normal(0, 0.5, 50),
        'political_ideology': np.random.normal(5, 2, 50),
        'news_exposure_freq': np.random.normal(3, 1, 50),
    }
    df = pd.DataFrame(data)
    # Add some missing
    df.loc[0:4, 'IAT_D_score'] = np.nan
    
    # Save to temp
    temp_csv = tmp_path / "test_input.csv"
    df.to_csv(temp_csv, index=False)
    
    # Load and process
    from data_loader import load_csv
    loaded_df = load_csv(str(temp_csv))
    imputed_df, _ = impute_mice(loaded_df)
    
    # Write output
    output_csv = tmp_path / "test_output.csv"
    imputed_df.to_csv(output_csv, index=False)
    
    assert output_csv.exists()
    output_loaded = pd.read_csv(output_csv)
    assert output_loaded.shape == df.shape
    assert output_loaded['IAT_D_score'].isnull().sum() == 0
