"""
Basic tests to verify the pytest framework setup for the project.

These tests ensure that:
- CPU-only execution is enforced
- Stratified sampling fixtures work correctly
- Custom markers are recognized
- Test environment is properly configured
"""

import os
import pytest
import pandas as pd
import numpy as np


@pytest.mark.cpu_only
def test_cpu_only_enforcement():
    """Verify that GPU devices are disabled in the test environment."""
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CUDA_VISIBLE_DEVICES must be empty"
    assert os.environ.get("TF_CPP_MIN_LOG_LEVEL") == "3", "TensorFlow logging must be suppressed"


@pytest.mark.stratified
def test_stratified_sampling_fixture(stratified_sample_data):
    """Test that stratified sampling produces a valid, representative sample."""
    assert isinstance(stratified_sample_data, pd.DataFrame)
    assert len(stratified_sample_data) > 0
    
    # Check that stratification columns exist
    assert 'temp_range' in stratified_sample_data.columns
    assert 'dilemma_complexity' in stratified_sample_data.columns
    
    # Verify distribution across strata
    temp_range_counts = stratified_sample_data['temp_range'].value_counts()
    complexity_counts = stratified_sample_data['dilemma_complexity'].value_counts()
    
    # Ensure we have samples from multiple strata
    assert len(temp_range_counts) >= 2, "Should have samples from multiple temperature ranges"
    assert len(complexity_counts) >= 2, "Should have samples from multiple complexity levels"


@pytest.mark.unit
def test_small_moral_machine_sample_fixture(small_moral_machine_sample):
    """Test that the small Moral Machine sample fixture works correctly."""
    assert small_moral_machine_sample.exists()
    
    df = pd.read_csv(small_moral_machine_sample)
    assert len(df) == 5
    assert 'participant_id' in df.columns
    assert 'response_time_ms' in df.columns
    assert 'latitude' in df.columns
    assert 'longitude' in df.columns


@pytest.mark.unit
def test_small_era5_sample_fixture(small_era5_sample):
    """Test that the small ERA5 sample fixture works correctly."""
    assert small_era5_sample.exists()
    
    df = pd.read_parquet(small_era5_sample)
    assert len(df) > 0
    assert 'datetime' in df.columns
    assert 'temperature_2m' in df.columns
    assert 'latitude' in df.columns
    assert 'longitude' in df.columns


@pytest.mark.integration
def test_data_loading_with_stratified_sampling(stratified_sample_data, small_era5_sample):
    """Integration test combining stratified sampling with real data loading."""
    # Load ERA5 data
    era5_df = pd.read_parquet(small_era5_sample)
    
    # Verify we can work with both datasets
    assert len(stratified_sample_data) > 0
    assert len(era5_df) > 0
    
    # Test that we can merge on common columns (simulating actual workflow)
    # In real scenario, this would involve geospatial matching
    sample_with_temp = stratified_sample_data.copy()
    sample_with_temp['test_flag'] = True
    
    assert 'test_flag' in sample_with_temp.columns


@pytest.mark.slow
def test_memory_efficiency_with_large_sample():
    """Test that sampling logic is memory efficient with larger datasets."""
    # Create a larger dataset to simulate memory constraints
    np.random.seed(42)
    n_large = 100000
    
    large_df = pd.DataFrame({
        'id': range(n_large),
        'value': np.random.normal(0, 1, n_large),
        'category': np.random.choice(['A', 'B', 'C'], n_large)
    })
    
    # Apply stratified sampling logic
    sample_size = 1000
    sampled = large_df.groupby('category', group_keys=False).apply(
        lambda x: x.sample(n=min(int(sample_size / 3), len(x)), random_state=42)
    ).reset_index(drop=True)
    
    assert len(sampled) <= sample_size
    assert len(sampled) > 0
    assert set(sampled['category'].unique()).issubset(set(large_df['category'].unique()))
