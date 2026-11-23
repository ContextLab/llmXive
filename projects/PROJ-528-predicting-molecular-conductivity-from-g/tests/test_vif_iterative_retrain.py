"""
Unit tests for iterative VIF retraining logic (T039).
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import json

from code.vif_iterative_retrain import (
    calculate_vif_scores,
    iterative_vif_retrain,
    prepare_features_and_target
)


@pytest.fixture
def sample_data():
    """Create a sample dataframe with known VIF properties."""
    # Create features with some correlation to trigger VIF > 10
    np.random.seed(42)
    n = 100
    X1 = np.random.randn(n)
    X2 = X1 * 5 + np.random.randn(n) * 0.1  # Highly correlated with X1
    X3 = np.random.randn(n)
    X4 = np.random.randn(n)
    y = X1 + X2 + X3 + np.random.randn(n) * 0.5

    df = pd.DataFrame({
        'smiles': ['SMILES' + str(i) for i in range(n)],
        'status': ['valid'] * n,
        'feature_1': X1,
        'feature_2': X2,
        'feature_3': X3,
        'feature_4': X4,
        'log_conductivity': y
    })
    return df


def test_calculate_vif_scores_basic(sample_data):
    """Test that VIF scores are calculated correctly."""
    exclude_cols = ['smiles', 'status', 'log_conductivity']
    X, y, feature_names = prepare_features_and_target(sample_data, 'log_conductivity', exclude_cols)

    vif_scores = calculate_vif_scores(X, feature_names)

    assert isinstance(vif_scores, dict)
    assert len(vif_scores) == 4
    assert all(isinstance(v, float) for v in vif_scores.values())
    # feature_2 should have high VIF due to correlation with feature_1
    assert vif_scores['feature_2'] > 10.0


def test_iterative_vif_retrain_excludes_high_vif(sample_data):
    """Test that the loop excludes features with VIF > 10."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "vif_results.json")
        csv_path = os.path.join(tmpdir, "data.csv")
        sample_data.to_csv(csv_path, index=False)

        # Reload to ensure clean state
        df = pd.read_csv(csv_path)

        results = iterative_vif_retrain(
            df=df,
            target_col='log_conductivity',
            output_path=output_path,
            vif_threshold=10.0,
            model_type='rf',
            cv_folds=2  # Use fewer folds for speed in test
        )

        # Check that feature_2 (highly correlated) was excluded
        assert 'feature_2' in results['excluded_features']
        # Check that final VIFs are all <= 10
        for vif in results['final_vif_scores'].values():
            assert vif <= 10.0
        # Check that results were saved
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
            assert saved_results['excluded_features'] == results['excluded_features']


def test_iterative_vif_retrain_stops_when_all_vif_ok(sample_data):
    """Test that the loop stops when no VIF > threshold."""
    # Create data with low correlation
    np.random.seed(42)
    n = 100
    X1 = np.random.randn(n)
    X2 = np.random.randn(n)
    X3 = np.random.randn(n)
    y = X1 + X2 + X3 + np.random.randn(n) * 0.5

    df = pd.DataFrame({
        'smiles': ['SMILES' + str(i) for i in range(n)],
        'status': ['valid'] * n,
        'f1': X1,
        'f2': X2,
        'f3': X3,
        'log_conductivity': y
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "vif_results.json")

        results = iterative_vif_retrain(
            df=df,
            target_col='log_conductivity',
            output_path=output_path,
            vif_threshold=10.0,
            model_type='rf',
            cv_folds=2
        )

        # No features should be excluded
        assert len(results['excluded_features']) == 0
        # All final VIFs should be <= 10
        for vif in results['final_vif_scores'].values():
            assert vif <= 10.0