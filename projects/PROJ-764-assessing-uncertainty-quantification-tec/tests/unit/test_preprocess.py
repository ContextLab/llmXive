import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure code root is in path
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from data.preprocess import load_config, apply_quantile_binning, stratified_split, perform_pca_and_exclusion

def test_load_config():
    """Test that config loads correctly from the expected path."""
    config = load_config("code/config.yaml")
    assert "seed" in config
    assert "split_ratio" in config
    assert "split_type" in config
    assert config["split_type"] == "stratified"

def test_apply_quantile_binning():
    """Test quantile binning creates the target_bin column."""
    # Create a synthetic dataframe with a target column
    df = pd.DataFrame({
        "feature1": np.random.randn(100),
        "formation_energy": np.random.randn(100)
    })
    
    result = apply_quantile_binning(df, "formation_energy", n_bins=10)
    
    assert "target_bin" in result.columns
    assert len(result) == len(df)
    # Check that bins are integers
    assert result["target_bin"].dtype in [np.int64, np.int32, np.int8]
    # Check that we have at most 10 bins (could be fewer if duplicates='drop')
    assert result["target_bin"].nunique() <= 10

def test_stratified_split_structure():
    """Test that stratified split returns three dataframes."""
    # Create a synthetic dataframe
    n_samples = 200
    df = pd.DataFrame({
        "feature1": np.random.randn(n_samples),
        "formation_energy": np.random.randn(n_samples)
    })
    
    config = {
        "seed": 42,
        "split_ratio": [0.8, 0.1, 0.1],
        "split_type": "stratified"
    }
    
    train_df, val_df, test_df = stratified_split(df, config)
    
    assert len(train_df) + len(val_df) + len(test_df) == n_samples
    assert "target_bin" in train_df.columns
    assert "target_bin" in val_df.columns
    assert "target_bin" in test_df.columns

def test_stratified_split_ratios():
    """Test that stratified split respects approximate ratios."""
    n_samples = 1000
    df = pd.DataFrame({
        "feature1": np.random.randn(n_samples),
        "formation_energy": np.random.randn(n_samples)
    })
    
    config = {
        "seed": 42,
        "split_ratio": [0.8, 0.1, 0.1],
        "split_type": "stratified"
    }
    
    train_df, val_df, test_df = stratified_split(df, config)
    
    # Allow for small rounding differences
    assert abs(len(train_df) / n_samples - 0.8) < 0.02
    assert abs(len(val_df) / n_samples - 0.1) < 0.02
    assert abs(len(test_df) / n_samples - 0.1) < 0.02

def test_stratified_split_invalid_type():
    """Test that non-stratified split raises an error."""
    df = pd.DataFrame({
        "feature1": np.random.randn(100),
        "formation_energy": np.random.randn(100)
    })
    
    config = {
        "seed": 42,
        "split_ratio": [0.8, 0.1, 0.1],
        "split_type": "random"  # Invalid
    }
    
    with pytest.raises(ValueError, match="stratified"):
        stratified_split(df, config)

def test_stratified_split_missing_target():
    """Test that missing target column raises an error."""
    df = pd.DataFrame({
        "feature1": np.random.randn(100),
        "other_column": np.random.randn(100)
    })
    
    config = {
        "seed": 42,
        "split_ratio": [0.8, 0.1, 0.1],
        "split_type": "stratified"
    }
    
    with pytest.raises(KeyError, match="formation_energy"):
        stratified_split(df, config)

def test_pca_and_exclusion():
    """Test PCA transformation and missing data exclusion logic."""
    # Create a synthetic dataset with some missing values
    n_samples = 200
    n_features = 10
    
    np.random.seed(42)
    data = np.random.randn(n_samples, n_features)
    # Introduce some missing values
    data[0:5, 0] = np.nan
    data[10:15, 1] = np.nan
    
    df = pd.DataFrame(data, columns=[f"feature_{i}" for i in range(n_features)])
    df["formation_energy"] = np.random.randn(n_samples)
    
    # Define target column
    target_col = "formation_energy"
    
    # Perform PCA and exclusion
    pca_result, excluded_count, missing_columns = perform_pca_and_exclusion(
        df, target_col, n_components=5
    )
    
    # Verify exclusion count matches introduced missing rows
    assert excluded_count == 10  # 5 + 5 rows with missing values
    
    # Verify remaining data has no missing values
    assert not pca_result.isnull().any().any()
    
    # Verify PCA reduced dimensions
    expected_features = n_features - 1  # -1 for target column
    assert pca_result.shape[1] == expected_features - 5 + 5  # Original - target + 5 PCs
    
    # Verify target_bin is preserved if it existed
    # (In this test it doesn't, but the function should handle it)
    
    # Verify missing columns are reported correctly
    assert "feature_0" in missing_columns
    assert "feature_1" in missing_columns
    assert len(missing_columns) == 2

def test_pca_and_exclusion_all_missing():
    """Test behavior when all rows have missing values."""
    # Create a dataset where all rows have at least one missing value
    n_samples = 50
    n_features = 5
    
    df = pd.DataFrame(np.random.randn(n_samples, n_features), 
                     columns=[f"feature_{i}" for i in range(n_features)])
    df["formation_energy"] = np.random.randn(n_samples)
    
    # Make every row have a missing value
    for i in range(n_samples):
        df.iloc[i, i % n_features] = np.nan
    
    target_col = "formation_energy"
    
    # This should exclude all rows
    pca_result, excluded_count, missing_columns = perform_pca_and_exclusion(
        df, target_col, n_components=2
    )
    
    assert excluded_count == n_samples
    assert len(pca_result) == 0  # No rows remaining

def test_pca_and_exclusion_no_missing():
    """Test PCA when there are no missing values."""
    n_samples = 100
    n_features = 8
    
    np.random.seed(42)
    df = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    df["formation_energy"] = np.random.randn(n_samples)
    
    target_col = "formation_energy"
    
    pca_result, excluded_count, missing_columns = perform_pca_and_exclusion(
        df, target_col, n_components=3
    )
    
    assert excluded_count == 0
    assert len(missing_columns) == 0
    assert len(pca_result) == n_samples