import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
import shutil
from preprocess import (
    load_interim_dataset, 
    filter_low_variance_metabolites, 
    apply_knn_imputation, 
    apply_pca_if_needed, 
    genotype_stratified_split, 
    save_split_indices
)

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    data = {
        'sample_id': ['s1', 's2', 's3', 's4', 's5', 's6'],
        'genotype_id': ['G1', 'G1', 'G2', 'G2', 'G3', 'G3'],
        'resistance': [1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
        'metabolite_A': [10.0, 10.0, 20.0, 20.0, 30.0, 30.0], # Low variance
        'metabolite_B': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],     # High variance
        'metabolite_C': [np.nan, 2.0, 3.0, np.nan, 5.0, 6.0] # Missing values
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file output tests."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

def test_filter_low_variance_metabolites(sample_df):
    """Test that metabolites with variance < 0.001 are removed."""
    # metabolite_A has variance 0 (constant within groups, but let's check global)
    # Global variance of A: [10, 10, 20, 20, 30, 30] -> var > 0.001
    # Let's create a truly low variance column
    sample_df['metabolite_D'] = 5.0 # Variance = 0
    
    df_filtered = filter_low_variance_metabolites(sample_df, variance_threshold=0.001)
    
    assert 'metabolite_D' not in df_filtered.columns
    assert 'metabolite_B' in df_filtered.columns
    assert 'genotype_id' in df_filtered.columns # Non-numeric should remain

def test_apply_knn_imputation(sample_df):
    """Test KNN imputation fills missing values and sets flag."""
    # Ensure we have missing values
    df_imputed = apply_knn_imputation(sample_df)
    
    # Check that imputation_flag column exists
    assert 'imputation_flag' in df_imputed.columns
    
    # Check that NaNs in numeric columns are filled
    # Note: The original df had NaNs in metabolite_C
    # We expect no NaNs in the numeric columns of the result
    numeric_cols = df_imputed.select_dtypes(include=[np.number]).columns
    # Exclude the flag column for this check if it's numeric
    feature_cols = [c for c in numeric_cols if c != 'imputation_flag']
    
    for col in feature_cols:
        assert df_imputed[col].isnull().sum() == 0

def test_apply_pca_if_needed(sample_df):
    """Test PCA is applied when features > samples."""
    # Current sample_df: 6 samples, ~4 numeric features (resistance, A, B, C)
    # 4 < 6, so PCA should NOT be applied by default logic in function
    df_pca = apply_pca_if_needed(sample_df)
    
    # If features < samples, it returns original df (or similar structure)
    # We check that it doesn't crash
    assert df_pca is not None
    
    # Force PCA by adding more features
    for i in range(10):
        sample_df[f'metabolite_extra_{i}'] = np.random.rand(6)
    
    df_pca_forced = apply_pca_if_needed(sample_df)
    
    # Should now have PCA components
    assert any('pca_comp' in col for col in df_pca_forced.columns)

def test_genotype_stratified_split_no_leakage(sample_df):
    """Test that genotype-stratified split prevents genotype leakage."""
    train_indices, test_indices = genotype_stratified_split(sample_df, train_size=0.8)
    
    train_genotypes = set(sample_df.loc[train_indices, 'genotype_id'])
    test_genotypes = set(sample_df.loc[test_indices, 'genotype_id'])
    
    # Intersection must be empty
    assert len(train_genotypes.intersection(test_genotypes)) == 0
    
    # Union must be all genotypes
    all_genotypes = set(sample_df['genotype_id'])
    assert train_genotypes.union(test_genotypes) == all_genotypes

def test_save_split_indices(sample_df, temp_dir):
    """Test saving split indices to JSON."""
    train_indices, test_indices = genotype_stratified_split(sample_df, train_size=0.8)
    filepath = os.path.join(temp_dir, 'split_indices.json')
    
    save_split_indices(train_indices, test_indices, filepath)
    
    assert os.path.exists(filepath)
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    assert 'train' in data
    assert 'test' in data
    assert len(data['train']) > 0
    assert len(data['test']) > 0
    assert set(data['train']) == set(train_indices)
    assert set(data['test']) == set(test_indices)