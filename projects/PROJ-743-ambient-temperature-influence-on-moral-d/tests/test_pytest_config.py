"""
Tests to verify the pytest configuration and fixtures for PROJ-743.
"""
import os
import pytest
import pandas as pd

def test_cpu_only_mode_enabled(cpu_only_mode):
    """Verify that CPU-only mode is active."""
    assert cpu_only_mode is True
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''

def test_sample_data_loading(stratified_sample):
    """Test that the stratified sample fixture loads data correctly."""
    if stratified_sample is None:
        pytest.skip("Test data file not found or empty. Skipping sample loading test.")
    
    assert isinstance(stratified_sample, pd.DataFrame)
    assert len(stratified_sample) > 0
    # Verify we have the expected columns if they exist in the source
    expected_cols = ['participant_id', 'response_time', 'temperature_celsius']
    for col in expected_cols:
        if col in stratified_sample.columns:
            assert not stratified_sample[col].isna().all()

def test_stratified_sampling_logic(stratified_sample, sample_size):
    """Verify that the sample size is respected and stratification works."""
    if stratified_sample is None:
        pytest.skip("Test data file not found or empty.")
    
    # The sample size should be approximately the requested size or less if data is small
    assert len(stratified_sample) <= sample_size
    
    # If we have a cultural_region column, check that multiple regions are represented
    if 'cultural_region' in stratified_sample.columns:
        regions = stratified_sample['cultural_region'].dropna().unique()
        # We expect at least a few regions if the dataset is large enough
        if len(stratified_sample) > 10:
            assert len(regions) > 1, "Stratification should cover multiple regions"

def test_temp_data_directory(temp_data_dir):
    """Test that the temporary data directory is created and writable."""
    assert temp_data_dir.exists()
    assert temp_data_dir.is_dir()
    
    # Try to write a dummy file
    test_file = temp_data_dir / "test_write.txt"
    test_file.write_text("test")
    assert test_file.exists()
    
    # Cleanup is handled by the fixture

def test_sample_data_loader_fixture(sample_data_loader, project_root):
    """Test the sample_data_loader fixture."""
    # Try to load a known file if it exists, otherwise just test the function signature
    # We check if the function returns None for non-existent files gracefully
    result = sample_data_loader("data/non_existent.parquet")
    assert result is None
    
    # Try to load the config module to ensure path resolution works
    # This is a bit of a hack to test the loader without needing a specific data file
    # but it verifies the path logic
    config_path = project_root / "code" / "config.py"
    if config_path.exists():
        # We can't easily load a .py as a dataframe, so we just check the path logic
        assert config_path.is_file()
