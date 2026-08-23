import os
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path

# Mock the config to use a temporary directory for testing
import code.config as config_module

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_path):
    """
    Sets up a temporary directory structure for testing the consolidate module.
    """
    # Create a temporary data directory structure
    test_data_root = tmp_path / "data"
    test_processed = test_data_root / "processed"
    test_processed.mkdir(parents=True)
    
    # Mock get_data_path to return our temp root
    def mock_get_data_path():
        return str(test_data_root)
    
    monkeypatch.setattr(config_module, "get_data_path", mock_get_data_path)
    
    # Also need to ensure the module reloads to pick up the new config
    # In a real scenario, this would be handled by a better config injection strategy
    # For now, we rely on the fact that the consolidate module imports get_data_path at runtime
    
    return test_data_root

def test_load_and_consolidate(setup_test_environment):
    """
    Test that the consolidate module correctly loads multiple processed files
    and writes them to a single Parquet file.
    """
    test_processed = setup_test_environment
    
    # Create mock processed files
    df1 = pd.DataFrame({
        'material': ['Al', 'Al'],
        'reduction': [10, 20],
        'confidence': [0.9, 0.8],
        'phi1': [0.0, 10.0],
        'Phi': [0.0, 10.0],
        'phi2': [0.0, 10.0],
        'sample_id': ['s1', 's2']
    })
    
    df2 = pd.DataFrame({
        'material': ['Cu', 'Cu'],
        'reduction': [30, 40],
        'confidence': [0.85, 0.95],
        'phi1': [5.0, 15.0],
        'Phi': [5.0, 15.0],
        'phi2': [5.0, 15.0],
        'sample_id': ['s3', 's4']
    })
    
    file1 = test_processed / "al_processed.parquet"
    file2 = test_processed / "cu_processed.parquet"
    
    df1.to_parquet(file1, index=False)
    df2.to_parquet(file2, index=False)
    
    # Import the module functions (they will use the mocked config)
    from code.data.consolidate import load_all_processed_datasets, write_consolidated_parquet
    
    # Load data
    combined_df = load_all_processed_datasets()
    
    assert len(combined_df) == 4
    assert set(combined_df['material'].unique()) == {'Al', 'Cu'}
    assert 'reduction' in combined_df.columns
    assert 'confidence' in combined_df.columns
    
    # Write consolidated file
    output_path = write_consolidated_parquet(combined_df)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Verify the written file
    written_df = pd.read_parquet(output_path)
    assert len(written_df) == 4
    assert 'material' in written_df.columns
    assert 'reduction' in written_df.columns
    assert 'confidence' in written_df.columns

def test_empty_directory(setup_test_environment):
    """
    Test behavior when no processed files are found.
    """
    # Ensure directory is empty
    test_processed = setup_test_environment / "processed"
    # It's already empty from fixture setup if no files were created
    
    from code.data.consolidate import load_all_processed_datasets, write_consolidated_parquet
    
    combined_df = load_all_processed_datasets()
    assert combined_df.empty
    
    # Should still write an empty file
    output_path = write_consolidated_parquet(combined_df)
    assert output_path.exists()
    
    # Verify it's empty
    written_df = pd.read_parquet(output_path)
    assert written_df.empty
