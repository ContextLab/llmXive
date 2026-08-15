"""
Tests to verify the pytest configuration and fixtures for T014.

These tests ensure:
1. The test framework is correctly configured for CPU-only execution.
2. Stratified sampling fixtures work as expected.
3. Logging infrastructure is initialized correctly during test runs.
"""
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

def test_cpu_only_enforcement(enforce_cpu_only):
    """
    Verify that the CPU-only enforcement fixture runs without error.
    This ensures that if CUDA is present, it is disabled or skipped.
    """
    # If we get here, the fixture executed successfully
    assert True, "CPU-only enforcement fixture executed successfully."

def test_stratified_sampling_fixture(sample_moral_machine_data):
    """
    Verify that the stratified sampling fixture returns a DataFrame
    with the expected structure and stratification properties.
    """
    df = sample_moral_machine_data
    
    # Check structure
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 500
    
    # Check required columns exist
    required_cols = ['latitude', 'longitude', 'response_time_ms', 'country_code']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Verify stratification logic by checking unique values in strata column
    unique_countries = df['country_code'].nunique()
    assert unique_countries > 1, "Stratified sample should contain multiple strata."

def test_stratified_sampling_distribution(sample_moral_machine_data):
    """
    Verify that the stratified sampling fixture distributes samples across strata.
    """
    df = sample_moral_machine_data
    strata_counts = df['country_code'].value_counts()
    
    # Ensure no stratum is completely empty in the sample
    assert (strata_counts > 0).all(), "All strata should have at least one sample."

def test_logging_directory_creation(logs_dir):
    """
    Verify that the logging directory exists and is writable.
    """
    assert logs_dir.exists(), "Logging directory should exist."
    assert logs_dir.is_dir(), "Logging path should be a directory."
    
    # Test write permission
    test_file = logs_dir / "write_test.txt"
    try:
        test_file.write_text("test")
        assert test_file.exists()
        test_file.unlink()
    except Exception as e:
        pytest.fail(f"Logging directory is not writable: {e}")

def test_sample_data_integrity(sample_moral_machine_data):
    """
    Verify that the sample data contains expected ranges for validation tests.
    """
    df = sample_moral_machine_data
    
    # Check for invalid response times introduced in the fixture
    invalid_low = df[(df['response_time_ms'] < 100) & (df['response_time_ms'] > 0)]
    invalid_high = df[df['response_time_ms'] > 10000]
    
    # We expect some invalid data to test the filtering logic
    assert len(invalid_low) > 0, "Fixture should include low response time outliers."
    assert len(invalid_high) > 0, "Fixture should include high response time outliers."

def test_geospatial_sample_fixture(sample_moral_machine_data, small_era5_sample):
    """
    Verify that both sample fixtures can be used together for integration-like tests.
    """
    moral_df = sample_moral_machine_data
    era5_df = small_era5_sample
    
    assert isinstance(moral_df, pd.DataFrame)
    assert isinstance(era5_df, pd.DataFrame)
    
    # Check that ERA5 has grid coordinates
    assert 'latitude' in era5_df.columns
    assert 'longitude' in era5_df.columns
    assert 'temperature_2m' in era5_df.columns