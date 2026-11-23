"""
Integration test for T016: feature_save.py

This test verifies that the feature saving pipeline correctly merges
raw features and validation flags, and writes the final CSV.
"""
import os
import tempfile
import pandas as pd
from pathlib import Path
import pytest
import shutil

# Mock the config and dependencies for the test
from unittest.mock import patch, MagicMock
import sys

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    data_raw = tmp_path / "data" / "raw"
    data_processed = tmp_path / "data" / "processed"
    data_interim = tmp_path / "data" / "interim"
    code_dir = tmp_path / "code"
    
    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    data_interim.mkdir(parents=True)
    code_dir.mkdir(parents=True)
    
    # Create dummy raw features
    features_data = {
        'prompt_id': ['p1', 'p2', 'p3'],
        'modal_verb_freq': [0.1, 0.2, 0.3],
        'imperative_ratio': [0.5, 0.0, 0.8], # p2 has 0 total sentences?
        'citation_density': [1.0, 2.0, 3.0]
    }
    features_df = pd.DataFrame(features_data)
    raw_features_path = data_interim / "features_raw.csv"
    features_df.to_csv(raw_features_path, index=False)
    
    # Create dummy validation flags
    validation_data = {
        'prompt_id': ['p1', 'p2', 'p3'],
        'has_undefined_imperative_ratio': [False, True, False],
        'imperative_ratio': [0.5, float('nan'), 0.8] # NaN for p2
    }
    validation_df = pd.DataFrame(validation_data)
    validation_path = data_interim / "validation_flags.csv"
    validation_df.to_csv(validation_path, index=False)
    
    return {
        'root': tmp_path,
        'processed_dir': data_processed,
        'interim_dir': data_interim
    }

def test_merge_and_save_features(temp_project_root):
    """Test that merge_and_save_features produces the correct output."""
    from feature_save import merge_and_save_features
    
    config = {
        'project_root': str(temp_project_root['root']),
        'paths': {
            'raw_features': str(temp_project_root['interim_dir'] / "features_raw.csv"),
            'validation_flags': str(temp_project_root['interim_dir'] / "validation_flags.csv"),
            'processed_features': str(temp_project_root['processed_dir'] / "features.csv")
        }
    }
    
    # Run the function
    output_path = merge_and_save_features(config)
    
    # Assertions
    assert output_path.exists(), "Output file was not created."
    
    df_output = pd.read_csv(output_path)
    
    # Check row count
    assert len(df_output) == 3, "Row count mismatch."
    
    # Check columns
    expected_cols = ['prompt_id', 'modal_verb_freq', 'imperative_ratio', 'citation_density', 
                     'has_undefined_imperative_ratio']
    for col in expected_cols:
        assert col in df_output.columns, f"Missing column: {col}"
    
    # Check specific values
    # p2 should have NaN for imperative_ratio and True for has_undefined
    p2_row = df_output[df_output['prompt_id'] == 'p2'].iloc[0]
    assert pd.isna(p2_row['imperative_ratio']), "p2 imperative_ratio should be NaN."
    assert p2_row['has_undefined_imperative_ratio'] == True, "p2 should be flagged."
    
    # p1 should be normal
    p1_row = df_output[df_output['prompt_id'] == 'p1'].iloc[0]
    assert p1_row['imperative_ratio'] == 0.5
    assert p1_row['has_undefined_imperative_ratio'] == False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
