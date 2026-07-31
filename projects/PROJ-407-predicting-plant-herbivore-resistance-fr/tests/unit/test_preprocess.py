"""
Unit tests for preprocessing module.
"""
import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import (
    filter_low_variance_metabolites,
    apply_knn_imputation,
    apply_pca_if_needed,
    genotype_stratified_split
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'sample_id': range(n_samples),
        'genotype_id': np.random.choice(['G1', 'G2', 'G3'], n_samples),
        'resistance': np.random.uniform(0, 10, n_samples),
        'metabolite_1': np.random.uniform(0, 1, n_samples),
        'metabolite_2': np.random.uniform(0, 1, n_samples),
        'metabolite_3': np.random.uniform(0, 1, n_samples),
        'metabolite_4': np.random.uniform(0, 1, n_samples),
        'metabolite_5': np.random.uniform(0, 1, n_samples),
    }
    
    # Add some missing values
    data['metabolite_1'][10] = np.nan
    data['metabolite_2'][20] = np.nan
    data['metabolite_3'][30] = np.nan
    
    return pd.DataFrame(data)

def test_filter_low_variance_metabolites(sample_data):
    """Test filtering of low variance metabolites."""
    # Add a low variance metabolite
    sample_data['metabolite_low_var'] = 1.0  # Zero variance
    
    df_filtered, removed_cols = filter_low_variance_metabolites(sample_data, threshold=0.001)
    
    assert 'metabolite_low_var' in removed_cols
    assert 'metabolite_low_var' not in df_filtered.columns
    assert len(removed_cols) >= 1

def test_filter_no_metabolite_columns():
    """Test error when no metabolite columns found."""
    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
    
    with pytest.raises(ValueError, match="No metabolite columns found"):
        filter_low_variance_metabolites(df)

def test_apply_knn_imputation(sample_data):
    """Test KNN imputation."""
    df_imputed, imputation_flags = apply_knn_imputation(sample_data, n_neighbors=3)
    
    # Check that imputation flags were created
    assert not imputation_flags.empty
    
    # Check that no missing values remain in metabolite columns
    metabolite_cols = [col for col in df_imputed.columns if col.startswith('metabolite_')]
    assert df_imputed[metabolite_cols].isnull().sum().sum() == 0

def test_apply_knn_imputation_no_missing():
    """Test KNN imputation when no missing values exist."""
    df = pd.DataFrame({
        'metabolite_1': [1.0, 2.0, 3.0],
        'metabolite_2': [4.0, 5.0, 6.0]
    })
    
    df_imputed, imputation_flags = apply_knn_imputation(df)
    
    # Should return original data unchanged
    pd.testing.assert_frame_equal(df_imputed, df)
    assert imputation_flags.empty

def test_apply_pca_if_needed():
    """Test PCA application when features > samples."""
    # Create data with more features than samples
    n_samples = 10
    n_features = 20
    
    data = {
        'sample_id': range(n_samples),
        'genotype_id': ['G1'] * n_samples,
        'resistance': np.random.uniform(0, 10, n_samples),
    }
    
    for i in range(n_features):
        data[f'metabolite_{i}'] = np.random.uniform(0, 1, n_samples)
    
    df = pd.DataFrame(data)
    
    df_pca, pca_obj, pca_applied = apply_pca_if_needed(df)
    
    assert pca_applied is True
    assert pca_obj is not None
    assert 'pca_component_1' in df_pca.columns

def test_apply_pca_not_needed():
    """Test that PCA is not applied when features <= samples."""
    n_samples = 20
    n_features = 5
    
    data = {
        'sample_id': range(n_samples),
        'genotype_id': ['G1'] * n_samples,
        'resistance': np.random.uniform(0, 10, n_samples),
    }
    
    for i in range(n_features):
        data[f'metabolite_{i}'] = np.random.uniform(0, 1, n_samples)
    
    df = pd.DataFrame(data)
    
    df_result, pca_obj, pca_applied = apply_pca_if_needed(df)
    
    assert pca_applied is False
    assert pca_obj is None
    assert 'pca_component_1' not in df_result.columns

def test_genotype_stratified_split(sample_data):
    """Test genotype-stratified split."""
    train_df, test_df, split_info = genotype_stratified_split(sample_data, test_size=0.2)
    
    assert len(train_df) + len(test_df) == len(sample_data)
    assert split_info['train_size'] + split_info['test_size'] == len(sample_data)
    assert split_info['overlap_genotypes'] == 0  # No genotype overlap

def test_genotype_stratified_split_no_genotype_column():
    """Test error when genotype_id column is missing."""
    df = pd.DataFrame({
        'sample_id': [1, 2, 3],
        'resistance': [1.0, 2.0, 3.0],
        'metabolite_1': [4.0, 5.0, 6.0]
    })
    
    with pytest.raises(ValueError, match="Dataset must contain 'genotype_id' column"):
        genotype_stratified_split(df)

def test_genotype_stratified_split_all_same_genotype():
    """Test split when all samples have same genotype."""
    df = pd.DataFrame({
        'sample_id': range(20),
        'genotype_id': ['G1'] * 20,
        'resistance': np.random.uniform(0, 10, 20),
        'metabolite_1': np.random.uniform(0, 1, 20)
    })
    
    # This should work but might raise warning about overlap
    train_df, test_df, split_info = genotype_stratified_split(df, test_size=0.2)
    
    assert len(train_df) + len(test_df) == len(df)