"""
Unit tests for code/analysis/modeling.py
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from analysis.modeling import prepare_model_features


@pytest.fixture
def sample_data():
    """Create a small synthetic dataset for testing feature preparation."""
    data = {
        'SampleID': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'Tissue': ['Liver', 'Liver', 'Adipose', 'Liver', 'Adipose'],
        'Sex': ['M', 'F', 'M', 'F', 'M'],
        'Age': [45, 52, 38, 60, 41],
        'Gene_PER1': [1.2, 0.9, 1.5, 0.8, 1.1],
        'Gene_CRY1': [2.1, 1.8, 2.5, 1.9, 2.0],
        'MetS_Status': [0, 1, 0, 1, 0]
    }
    return pd.DataFrame(data)


def test_prepare_model_features_encoding(sample_data):
    """Test that categorical variables are one-hot encoded correctly."""
    X, metadata = prepare_model_features(
        sample_data,
        target_col='MetS_Status',
        categorical_cols=['Tissue', 'Sex'],
        numerical_cols=['Age'],
        gene_cols=['Gene_PER1', 'Gene_CRY1']
    )
    
    # Check that categorical columns are removed from X
    assert 'Tissue' not in X.columns
    assert 'Sex' not in X.columns
    
    # Check that one-hot encoded columns exist
    # OneHotEncoder with drop='first' on 2 categories -> 1 column per cat
    # Liver, Adipose -> 'Tissue_Adipose' (Liver is base)
    # M, F -> 'Sex_F' (M is base)
    assert 'Tissue_Adipose' in X.columns
    assert 'Sex_F' in X.columns
    
    # Check that numerical columns exist
    assert 'Age' in X.columns
    assert 'Gene_PER1' in X.columns
    assert 'Gene_CRY1' in X.columns
    
    # Verify metadata
    assert 'preprocessor' in metadata
    assert 'feature_names' in metadata
    assert len(metadata['feature_names']) == len(X.columns)


def test_prepare_model_features_scaling(sample_data):
    """Test that numerical variables are scaled (mean=0, std=1)."""
    X, metadata = prepare_model_features(
        sample_data,
        target_col='MetS_Status',
        categorical_cols=['Tissue', 'Sex'],
        numerical_cols=['Age'],
        gene_cols=['Gene_PER1', 'Gene_CRY1']
    )
    
    # Check scaling of Age
    # Original Ages: 45, 52, 38, 60, 41
    # Mean: 47.2, Std: ~7.9
    # Scaled values should have mean ~0 and std ~1
    age_col = X['Age']
    np.testing.assert_almost_equal(age_col.mean(), 0.0, decimal=5)
    np.testing.assert_almost_equal(age_col.std(), 1.0, decimal=5)
    
    # Check scaling of Gene_PER1
    gene_col = X['Gene_PER1']
    np.testing.assert_almost_equal(gene_col.mean(), 0.0, decimal=5)
    np.testing.assert_almost_equal(gene_col.std(), 1.0, decimal=5)


def test_prepare_model_features_missing_columns(sample_data):
    """Test that the function raises an error if required columns are missing."""
    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_model_features(
            sample_data,
            target_col='MetS_Status',
            categorical_cols=['Tissue', 'Sex', 'NonExistent']
        )


def test_prepare_model_features_target_separation(sample_data):
    """Test that the target column is separated from features."""
    X, metadata = prepare_model_features(
        sample_data,
        target_col='MetS_Status'
    )
    
    assert 'MetS_Status' not in X.columns
    assert 'target' in metadata
    pd.testing.assert_series_equal(metadata['target'], sample_data['MetS_Status'])