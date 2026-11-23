"""
Unit tests for code/analysis/modeling.py
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from analysis.modeling import (
    prepare_model_features,
    run_cross_validation,
    train_logistic_regression,
    extract_odds_ratios,
    check_collinearity,
)


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


def test_logistic_regression_training_auc(sample_data):
    """Test that logistic regression training yields an AUC >= 0.5."""
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score
    from analysis.modeling import train_logistic_regression, prepare_model_features

    # Prepare features and target
    X, metadata = prepare_model_features(
        sample_data,
        target_col='MetS_Status',
        categorical_cols=['Tissue', 'Sex'],
        numerical_cols=['Age'],
        gene_cols=['Gene_PER1', 'Gene_CRY1']
    )
    y = metadata['target']

    # Simple train‑test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.4, random_state=42, stratify=y
    )

    # Train logistic regression
    model = train_logistic_regression(X_train, y_train)

    # Predict probabilities for the positive class
    probs = model.predict_proba(X_test)[:, 1]

    # Compute AUC
    auc = roc_auc_score(y_test, probs)

    # The model should achieve at least random performance
    assert auc >= 0.5


def test_cross_validation_loop(sample_data):
    """Test that cross‑validation returns a valid AUC mean and confidence interval."""
    X, metadata = prepare_model_features(
        sample_data,
        target_col='MetS_Status',
        categorical_cols=['Tissue', 'Sex'],
        numerical_cols=['Age'],
        gene_cols=['Gene_PER1', 'Gene_CRY1']
    )
    y = metadata['target']

    cv_result = run_cross_validation(X, y, n_splits=3, random_state=0)

    # Ensure result contains expected keys
    assert 'mean_auc' in cv_result
    assert 'ci_lower' in cv_result
    assert 'ci_upper' in cv_result
    assert 'auc_scores' in cv_result

    # AUC values should be between 0 and 1
    for auc in cv_result['auc_scores']:
        assert 0.0 <= auc <= 1.0

    # Confidence interval should enclose the mean
    assert cv_result['ci_lower'] <= cv_result['mean_auc'] <= cv_result['ci_upper']


def test_odds_ratio_extraction_collinearity(sample_data):
    """Verify that odds‑ratio extraction works and that collinearity detection flags high VIF."""
    # Introduce a perfectly collinear predictor (Age duplicated)
    df = sample_data.copy()
    df['Age_dup'] = df['Age'] * 2  # linear combination of Age
    
    X, metadata = prepare_model_features(
        df,
        target_col='MetS_Status',
        categorical_cols=['Tissue', 'Sex'],
        numerical_cols=['Age', 'Age_dup'],
        gene_cols=['Gene_PER1', 'Gene_CRY1']
    )

    # Train logistic regression model
    model = train_logistic_regression(X, metadata['target'])

    # Run collinearity check – expect a dict containing VIF values
    col_report = check_collinearity(X)
    assert isinstance(col_report, dict), "Collinearity report should be a dict"

    # The report should contain a mapping of feature names to VIF scores
    vif_dict = col_report.get('vif')
    assert isinstance(vif_dict, dict), "VIF values should be provided in a dict under the key 'vif'"

    # At least one VIF should exceed the threshold of 5 due to the duplicated column
    high_vif_exists = any(v > 5 for v in vif_dict.values())
    assert high_vif_exists, "Expected at least one feature with VIF > 5 indicating collinearity"

    # Extract odds ratios – expect a DataFrame with an odds_ratio column
    odds_df = extract_odds_ratios(model, metadata['feature_names'])
    assert isinstance(odds_df, pd.DataFrame), "Odds ratio extraction should return a pandas DataFrame"
    assert 'odds_ratio' in odds_df.columns, "Returned DataFrame must contain an 'odds_ratio' column"
    # The number of rows should match the number of features used in the model
    assert len(odds_df) == len(metadata['feature_names']), "Odds ratio DataFrame should have one row per feature"