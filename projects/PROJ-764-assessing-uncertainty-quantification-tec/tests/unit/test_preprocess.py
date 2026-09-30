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

from data.preprocess import load_config, apply_quantile_binning, stratified_split

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
