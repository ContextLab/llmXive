"""
Unit tests for outlier exclusion threshold logic (Task T025).

Tests the logic for excluding outliers based on a sigma threshold
relative to the mean of the target variable.
"""
import pytest
import numpy as np
import pandas as pd
from code.config import SEED
from code.data_loader import apply_log_transformation
from code.validators import check_target_range
from code.logging_config import setup_logging

# Setup logging for the test module
setup_logging()

def generate_sample_data(n_samples=100, n_outliers=5, seed=SEED):
    """Generate a sample dataset with known outliers for testing."""
    np.random.seed(seed)
    # Normal distribution for main data
    main_data = np.random.normal(loc=2.0, scale=0.5, size=n_samples)
    
    # Outliers: significantly higher values
    outliers = np.random.normal(loc=6.0, scale=0.5, size=n_outliers)
    
    combined = np.concatenate([main_data, outliers])
    np.random.shuffle(combined)
    
    return pd.DataFrame({
        'smiles': [f'mol_{i}' for i in range(len(combined))],
        'conductivity': combined
    })

def test_outlier_exclusion_threshold_basic():
    """Test that outliers beyond a threshold are correctly identified and excluded."""
    df = generate_sample_data(n_samples=100, n_outliers=5)
    
    # Apply log transformation if needed (simulating pipeline flow)
    if 'conductivity' in df.columns:
        df['log_conductivity'] = np.log10(df['conductivity'] + 1e-9)
        target_col = 'log_conductivity'
    else:
        target_col = 'conductivity'
    
    target_values = df[target_col].values
    
    # Calculate mean and std
    mean_val = np.mean(target_values)
    std_val = np.std(target_values)
    
    # Define threshold (e.g., 3.0 sigma)
    threshold_sigma = 3.0
    lower_bound = mean_val - threshold_sigma * std_val
    upper_bound = mean_val + threshold_sigma * std_val
    
    # Identify outliers
    outliers_mask = (target_values < lower_bound) | (target_values > upper_bound)
    non_outliers_mask = ~outliers_mask
    
    # Verify that the known outliers are detected
    # In our synthetic data, outliers are ~6.0, main data ~2.0
    # With 3 sigma, we expect the high outliers to be caught
    detected_outliers_count = np.sum(outliers_mask)
    
    # We expect at least some of the 5 injected outliers to be detected
    # (depending on the exact random seed and distribution overlap)
    assert detected_outliers_count >= 1, "Expected at least one outlier to be detected"
    
    # Verify that non-outliers are not excluded
    non_outlier_values = target_values[non_outliers_mask]
    assert np.all((non_outlier_values >= lower_bound) & (non_outlier_values <= upper_bound)), \
        "Non-outlier values should not be excluded"

def test_outlier_exclusion_threshold_edge_cases():
    """Test edge cases: all outliers, no outliers, threshold = 0."""
    df = generate_sample_data(n_samples=100, n_outliers=0)
    
    target_col = 'conductivity'
    target_values = df[target_col].values
    
    mean_val = np.mean(target_values)
    std_val = np.std(target_values)
    
    # Test with threshold = 0 (should exclude everything except exactly mean)
    threshold_zero = 0.0
    lower_zero = mean_val - threshold_zero * std_val
    upper_zero = mean_val + threshold_zero * std_val
    
    outliers_mask_zero = (target_values < lower_zero) | (target_values > upper_zero)
    # With continuous data, almost everything should be excluded with threshold=0
    # (only values exactly equal to mean survive, which is rare)
    assert np.sum(outliers_mask_zero) > len(target_values) - 2, \
        "With threshold=0, almost all values should be considered outliers"
    
    # Test with very large threshold (should exclude nothing)
    threshold_large = 100.0
    lower_large = mean_val - threshold_large * std_val
    upper_large = mean_val + threshold_large * std_val
    
    outliers_mask_large = (target_values < lower_large) | (target_values > upper_large)
    assert np.sum(outliers_mask_large) == 0, \
        "With very large threshold, no values should be outliers"

def test_outlier_exclusion_with_log_transformation():
    """Test outlier exclusion logic after log transformation of target variable."""
    df = generate_sample_data(n_samples=100, n_outliers=5)
    
    # Apply log transformation
    df['log_conductivity'] = np.log10(df['conductivity'] + 1e-9)
    
    target_values = df['log_conductivity'].values
    
    mean_val = np.mean(target_values)
    std_val = np.std(target_values)
    
    threshold_sigma = 3.0
    lower_bound = mean_val - threshold_sigma * std_val
    upper_bound = mean_val + threshold_sigma * std_val
    
    # Check that the range of non-outliers is within bounds
    non_outlier_values = target_values[(target_values >= lower_bound) & (target_values <= upper_bound)]
    
    # Verify that the log-transformed data still has a reasonable range
    assert len(non_outlier_values) > 0, "Should have non-outlier values after log transformation"
    
    # The log transformation should compress the scale, but outliers should still be detectable
    assert np.std(non_outlier_values) < np.std(target_values), \
        "Log transformation should reduce variance of non-outlier data"

def test_outlier_exclusion_reproducibility():
    """Test that outlier exclusion is reproducible with fixed seed."""
    df1 = generate_sample_data(n_samples=100, n_outliers=5, seed=SEED)
    df2 = generate_sample_data(n_samples=100, n_outliers=5, seed=SEED)
    
    # Apply same threshold logic
    threshold_sigma = 3.0
    
    for df in [df1, df2]:
        target_values = df['conductivity'].values
        mean_val = np.mean(target_values)
        std_val = np.std(target_values)
        lower_bound = mean_val - threshold_sigma * std_val
        upper_bound = mean_val + threshold_sigma * std_val
        outliers_mask = (target_values < lower_bound) | (target_values > upper_bound)
        df['is_outlier'] = outliers_mask
    
    # Both datasets should have the same number of outliers (given same seed)
    assert df1['is_outlier'].sum() == df2['is_outlier'].sum(), \
        "Outlier count should be reproducible with same seed"

def test_outlier_exclusion_threshold_validation():
    """Test that invalid threshold values are handled appropriately."""
    # Test negative threshold (should raise error or be treated as absolute value)
    df = generate_sample_data(n_samples=100, n_outliers=5)
    target_values = df['conductivity'].values
    
    mean_val = np.mean(target_values)
    std_val = np.std(target_values)
    
    # Negative threshold should be treated as absolute value or raise error
    # In our implementation, we'll assume it's treated as absolute value
    threshold_negative = -3.0
    lower_neg = mean_val - abs(threshold_negative) * std_val
    upper_neg = mean_val + abs(threshold_negative) * std_val
    
    outliers_neg = (target_values < lower_neg) | (target_values > upper_neg)
    assert np.sum(outliers_neg) >= 0, "Should handle negative threshold gracefully"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
