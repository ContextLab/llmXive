"""
Tests for T018: Imputation & Bias Check.
"""
import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.impute_and_check import impute_missing, merge_datasets

@pytest.fixture
def sample_similarity_df():
    return pd.DataFrame({
        'ingredient_a': ['A', 'B', 'C', 'D'],
        'ingredient_b': ['X', 'Y', 'Z', 'W'],
        'similarity': [0.8, np.nan, 0.5, np.nan]
    })

@pytest.fixture
def sample_roles_df():
    return pd.DataFrame({
        'ingredient_a': ['A', 'B', 'C', 'D'],
        'ingredient_b': ['X', 'Y', 'Z', 'W'],
        'functional_role': ['primary', np.nan, 'garnish', 'secondary']
    })

@pytest.fixture
def sample_cooc_df():
    return pd.DataFrame({
        'ingredient_a': ['A', 'B', 'C', 'D'],
        'ingredient_b': ['X', 'Y', 'Z', 'W'],
        'log_co_occurrence': [10.0, 5.0, np.nan, 8.0]
    })

def test_impute_similarity_with_zero(sample_similarity_df):
    # Create a minimal df for testing just imputation logic
    df = sample_similarity_df.copy()
    df_imputed, logs = impute_missing(df)
    
    assert df_imputed['similarity'].isna().sum() == 0
    assert df_imputed.loc[df_imputed['ingredient_a'] == 'B', 'similarity'].iloc[0] == 0
    assert df_imputed.loc[df_imputed['ingredient_a'] == 'D', 'similarity'].iloc[0] == 0
    assert 'imputed_similarity' in logs

def test_impute_roles_with_unknown(sample_roles_df):
    df = sample_roles_df.copy()
    df_imputed, logs = impute_missing(df)
    
    assert df_imputed['functional_role'].isna().sum() == 0
    assert df_imputed.loc[df_imputed['ingredient_a'] == 'B', 'functional_role'].iloc[0] == 'unknown'
    assert 'imputed_functional_role' in logs

def test_drop_missing_cooccurrence(sample_cooc_df):
    df = sample_cooc_df.copy()
    df_imputed, logs = impute_missing(df)
    
    # Row C should be dropped because log_co_occurrence is NaN
    assert len(df_imputed) == 3
    assert 'Dropped' in str(logs) or 'dropped' in str(logs)
    
def test_merge_datasets(sample_similarity_df, sample_roles_df, sample_cooc_df):
    df_merged = merge_datasets(sample_similarity_df, sample_roles_df, sample_cooc_df)
    
    assert 'similarity' in df_merged.columns
    assert 'functional_role' in df_merged.columns
    assert 'log_co_occurrence' in df_merged.columns
    assert len(df_merged) == 4