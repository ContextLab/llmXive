"""
Unit tests for PCA reduction logic in preprocess.py
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from preprocess import apply_pca_if_needed, save_pca_reduced_data

def test_pca_skipped_when_features_le_samples():
    """Test that PCA is skipped when features <= samples."""
    # Create a small dataset with more samples than features
    np.random.seed(42)
    data = {
        'sample_id': range(10),
        'genotype_id': ['G1', 'G2'] * 5,
        'resistance': np.random.randint(1, 4, 10),
        'metabolite_1': np.random.rand(10),
        'metabolite_2': np.random.rand(10)
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'pca_reduced.csv')
        
        result = apply_pca_if_needed(df, output_path)
        
        # PCA should be skipped
        assert result is False, "PCA should be skipped when features <= samples"
        assert not os.path.exists(output_path), "PCA file should not be created when skipped"

def test_pca_applied_when_features_gt_samples():
    """Test that PCA is applied when features > samples."""
    # Create a dataset with more features than samples
    np.random.seed(42)
    n_samples = 5
    n_features = 10
    
    data = {
        'sample_id': range(n_samples),
        'genotype_id': ['G1'] * n_samples,
        'resistance': np.random.randint(1, 4, n_samples)
    }
    
    # Add many metabolite columns
    for i in range(n_features):
        data[f'metabolite_{i+1}'] = np.random.rand(n_samples)
    
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'pca_reduced.csv')
        
        result = apply_pca_if_needed(df, output_path)
        
        # PCA should be applied
        assert result is True, "PCA should be applied when features > samples"
        assert os.path.exists(output_path), "PCA file should be created"
        
        # Load and verify the output
        df_pca = pd.read_csv(output_path)
        
        # Check that PCA components are present
        pca_cols = [col for col in df_pca.columns if col.startswith('pca_component_')]
        assert len(pca_cols) > 0, "PCA components should be present in output"
        
        # Check that non-metabolite columns are preserved
        assert 'sample_id' in df_pca.columns, "Non-metabolite columns should be preserved"
        assert 'genotype_id' in df_pca.columns, "Non-metabolite columns should be preserved"
        assert 'resistance' in df_pca.columns, "Non-metabolite columns should be preserved"

def test_pca_reduced_shape():
    """Test that PCA reduces dimensions correctly."""
    np.random.seed(42)
    n_samples = 3
    n_features = 8
    
    data = {
        'sample_id': range(n_samples),
        'genotype_id': ['G1'] * n_samples,
        'resistance': [1, 2, 3]
    }
    
    for i in range(n_features):
        data[f'metabolite_{i+1}'] = np.random.rand(n_samples)
    
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'pca_reduced.csv')
        
        apply_pca_if_needed(df, output_path)
        df_pca = pd.read_csv(output_path)
        
        # Number of PCA components should be min(n_samples - 1, n_features)
        expected_components = min(n_samples - 1, n_features)
        pca_cols = [col for col in df_pca.columns if col.startswith('pca_component_')]
        
        assert len(pca_cols) == expected_components, f"Expected {expected_components} PCA components, got {len(pca_cols)}"

def test_save_pca_reduced_data():
    """Test the save function directly."""
    np.random.seed(42)
    df_pca = pd.DataFrame({
        'pca_component_1': np.random.rand(5),
        'pca_component_2': np.random.rand(5),
        'sample_id': range(5),
        'genotype_id': ['G1'] * 5
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'pca_reduced.csv')
        
        save_pca_reduced_data(df_pca, output_path)
        
        assert os.path.exists(output_path), "Output file should be created"
        
        df_loaded = pd.read_csv(output_path)
        assert len(df_loaded) == 5, "Should have 5 rows"
        assert 'pca_component_1' in df_loaded.columns, "PCA components should be present"