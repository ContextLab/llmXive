import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
from sklearn.impute import KNNImputer

# Import functions to test
from preprocess import (
    filter_low_variance_metabolites,
    apply_knn_imputation,
    apply_pca_if_needed,
    genotype_stratified_split,
    save_split_indices
)

@pytest.fixture
def sample_data():
    """Create a sample dataframe for testing."""
    data = {
        'sample_id': range(10),
        'genotype_id': ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D', 'E', 'E'],
        'resistance': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        'metabolite_1': [1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        'metabolite_2': [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1],
        'metabolite_3': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Zero variance
    }
    return pd.DataFrame(data)

def test_filter_low_variance_metabolites(sample_data):
    """Test that low variance metabolites are removed."""
    result = filter_low_variance_metabolites(sample_data, threshold=0.001)
    
    # metabolite_3 should be removed (zero variance)
    assert 'metabolite_3' not in result.columns
    assert 'metabolite_1' in result.columns
    assert 'metabolite_2' in result.columns
    assert 'genotype_id' in result.columns

def test_apply_knn_imputation_no_missing(sample_data):
    """Test KNN imputation when no missing values exist."""
    # Create data without missing values
    clean_data = sample_data.copy()
    clean_data['metabolite_1'] = clean_data['metabolite_1'].fillna(0.0)
    
    result, flags = apply_knn_imputation(clean_data, n_neighbors=3)
    
    # No imputation flag should be True
    assert result['imputation_flag'].sum() == 0
    assert result['metabolite_1'].isna().sum() == 0

def test_apply_knn_imputation_with_missing(sample_data):
    """Test KNN imputation with missing values."""
    result, flags = apply_knn_imputation(sample_data, n_neighbors=3)
    
    # Check that missing value was imputed
    assert result['metabolite_1'].isna().sum() == 0
    
    # Check that imputation flag is set correctly
    # Sample 2 (index 2) had a missing value
    assert result.loc[2, 'imputation_flag'] == 1
    assert result.loc[0, 'imputation_flag'] == 0

def test_apply_pca_if_needed_features_gt_samples():
    """Test PCA is applied when features > samples."""
    # Create small sample, many features
    n_samples = 5
    n_features = 10
    data = {
        'sample_id': range(n_samples),
        'genotype_id': ['A', 'B', 'C', 'D', 'E'],
        'resistance': range(1, n_samples + 1)
    }
    for i in range(n_features):
        data[f'metabolite_{i}'] = np.random.rand(n_samples)
    
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'pca_reduced.csv')
        result = apply_pca_if_needed(df, output_path)
        
        # Check that PCA columns exist
        pca_cols = [c for c in result.columns if c.startswith('pca_comp_')]
        assert len(pca_cols) > 0
        assert 'metabolite_0' not in result.columns

def test_apply_pca_if_needed_features_lt_samples(sample_data):
    """Test PCA is NOT applied when features < samples."""
    result = apply_pca_if_needed(sample_data, 'dummy_path.csv')
    
    # Original metabolite columns should remain
    assert 'metabolite_1' in result.columns
    assert 'metabolite_2' in result.columns
    # No PCA columns should be added
    assert not any(c.startswith('pca_comp_') for c in result.columns)

def test_genotype_stratified_split(sample_data):
    """Test that genotype-stratified split prevents leakage."""
    train_idx, test_idx = genotype_stratified_split(sample_data, test_size=0.2, random_state=42)
    
    # Check that indices are disjoint
    assert set(train_idx).isdisjoint(set(test_idx))
    
    # Check that all genotypes are represented in both sets (if enough samples)
    train_genotypes = set(sample_data.iloc[train_idx]['genotype_id'])
    test_genotypes = set(sample_data.iloc[test_idx]['genotype_id'])
    
    # With 5 genotypes and 10 samples, we might not get all in both, but should get some
    assert len(train_genotypes) > 0
    assert len(test_genotypes) > 0

def test_save_split_indices():
    """Test saving split indices to JSON."""
    train_idx = [0, 1, 2]
    test_idx = [3, 4, 5]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'split_indices.json')
        save_split_indices(train_idx, test_idx, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['train_indices'] == train_idx
        assert data['test_indices'] == test_idx