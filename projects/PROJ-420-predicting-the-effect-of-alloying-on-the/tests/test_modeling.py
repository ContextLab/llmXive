import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor

from code.modeling import (
    apply_ilr_transformation,
    aggregate_model_metrics,
    evaluate_model_on_test,
    load_features_and_target,
    load_split_indices,
    save_model,
    save_model_metrics,
    save_residuals,
    save_methodological_flags,
    split_data,
    train_random_forest_with_cv,
)


@pytest.fixture
def mock_clean_data(tmp_path):
    """Create a mock cleaned parquet file."""
    data = {
        'Cu': [0.05, 0.1, 0.02, 0.08, 0.15, 0.01, 0.05, 0.12, 0.03, 0.07],
        'Mg': [0.02, 0.05, 0.08, 0.01, 0.03, 0.06, 0.04, 0.02, 0.09, 0.05],
        'Si': [0.01, 0.02, 0.05, 0.03, 0.01, 0.04, 0.02, 0.06, 0.01, 0.03],
        'Zn': [0.03, 0.01, 0.02, 0.05, 0.02, 0.01, 0.03, 0.01, 0.04, 0.02],
        'Mn': [0.01, 0.02, 0.01, 0.01, 0.02, 0.01, 0.01, 0.02, 0.01, 0.01],
        'poisson_ratio': [0.33, 0.34, 0.32, 0.35, 0.31, 0.33, 0.34, 0.32, 0.33, 0.34],
    }
    df = pd.DataFrame(data)
    # Ensure sum of composition is ~1.0 (Al balance)
    # For mock, we assume Al fills the rest.
    csv_path = tmp_path / "alloys_clean.parquet"
    df.to_parquet(csv_path)
    return csv_path


@pytest.fixture
def mock_split_indices(tmp_path):
    """Create a mock split indices file."""
    indices = {
        "train_indices": [0, 1, 2, 3, 4, 5, 6, 7],
        "test_indices": [8, 9]
    }
    json_path = tmp_path / "split_indices.json"
    with open(json_path, 'w') as f:
        json.dump(indices, f)
    return json_path


def test_ilr_transform_handles_zero_sum(mock_clean_data):
    """Test that ILR transformation handles edge cases (zeros)."""
    # Create data with a zero
    df = pd.read_parquet(mock_clean_data)
    df.loc[0, 'Cu'] = 0.0
    df.to_parquet(mock_clean_data)

    X = df[['Cu', 'Mg', 'Si', 'Zn', 'Mn']]
    # Should not raise
    X_ilr = apply_ilr_transformation(X)
    assert X_ilr.shape[0] == X.shape[0]
    assert X_ilr.shape[1] == X.shape[1] - 1  # ILR reduces dimension by 1


def test_rf_training_converges(mock_clean_data, mock_split_indices):
    """Test that RF training converges without error."""
    X = pd.read_parquet(mock_clean_data)[['Cu', 'Mg', 'Si', 'Zn', 'Mn']]
    y = pd.read_parquet(mock_clean_data)['poisson_ratio']

    # Load split
    with open(mock_split_indices, 'r') as f:
        indices = json.load(f)
    train_idx = indices['train_indices']
    test_idx = indices['test_indices']

    X_train = X.iloc[train_idx]
    y_train = y.iloc[train_idx]

    # Apply ILR
    X_train_ilr = apply_ilr_transformation(X_train)

    # Train with CV
    best_params, cv_mae, cv_ci_lower, cv_ci_upper = train_random_forest_with_cv(
        X_train_ilr, y_train, n_splits=2, n_repeats=1, random_state=42
    )

    assert isinstance(best_params, dict)
    assert 'n_estimators' in best_params
    assert isinstance(cv_mae, float)
    assert cv_mae > 0


def test_cv_split_reproducibility(mock_clean_data):
    """Test that CV splits are reproducible with the same random state."""
    X = pd.read_parquet(mock_clean_data)[['Cu', 'Mg', 'Si', 'Zn', 'Mn']]
    y = pd.read_parquet(mock_clean_data)['poisson_ratio']
    X_ilr = apply_ilr_transformation(X)

    # Run twice
    params1, mae1, _, _ = train_random_forest_with_cv(
        X_ilr, y, n_splits=2, n_repeats=1, random_state=42
    )
    params2, mae2, _, _ = train_random_forest_with_cv(
        X_ilr, y, n_splits=2, n_repeats=1, random_state=42
    )

    assert params1 == params2
    assert mae1 == mae2