"""
Unit tests for PCA dimensionality reduction logic in preprocess.py
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from preprocess import apply_pca_if_needed, save_pca_reduced_data

def test_pca_applied_when_features_greater_than_samples():
    """Test that PCA is applied when features > samples."""
    # Create a dataset with 5 samples and 10 metabolite features
    np.random.seed(42)
    data = {
        'sample_id': [f's{i}' for i in range(5)],
        'genotype_id': [f'g{i%2}' for i in range(5)],
        'resistance': np.random.rand(5),
        **{f'metabolite_{i}': np.random.rand(5) for i in range(10)}
    }
    df = pd.DataFrame(data)
    
    pca_df, pca_model = apply_pca_if_needed(df)
    
    assert pca_model is not None, "PCA model should be created when features > samples"
    assert 'pca_component_1' in pca_df.columns, "PCA components should be added to dataframe"
    assert len(pca_df.columns) < len(df.columns), "Number of columns should decrease after PCA"

def test_pca_skipped_when_features_less_than_samples():
    """Test that PCA is skipped when features <= samples."""
    # Create a dataset with 10 samples and 5 metabolite features
    np.random.seed(42)
    data = {
        'sample_id': [f's{i}' for i in range(10)],
        'genotype_id': [f'g{i%2}' for i in range(10)],
        'resistance': np.random.rand(10),
        **{f'metabolite_{i}': np.random.rand(10) for i in range(5)}
    }
    df = pd.DataFrame(data)
    
    pca_df, pca_model = apply_pca_if_needed(df)
    
    assert pca_model is None, "PCA model should be None when features <= samples"
    assert 'pca_component_1' not in pca_df.columns, "PCA components should not be added"

def test_save_pca_reduced_data():
    """Test saving PCA reduced data to CSV."""
    np.random.seed(42)
    data = {
        'sample_id': [f's{i}' for i in range(5)],
        'genotype_id': [f'g{i%2}' for i in range(5)],
        'resistance': np.random.rand(5),
        'pca_component_1': np.random.rand(5),
        'pca_component_2': np.random.rand(5)
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "pca_reduced.csv")
        save_pca_reduced_data(df, output_path)
        
        assert os.path.exists(output_path), "Output file should be created"
        
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 5, "Number of rows should match"
        assert 'pca_component_1' in loaded_df.columns, "PCA components should be in saved file"