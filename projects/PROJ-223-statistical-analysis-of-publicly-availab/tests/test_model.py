"""
Very light model tests.

The model module (`code/model.py`) wraps statsmodels' OrderedModel.
These tests construct a tiny synthetic dataset, fit the model and verify
that the result object exposes the expected attributes without raising
exceptions.
"""

import pandas as pd
import pytest

from code.model import prepare_model_data, fit_ordinal_model

@pytest.fixture
def tiny_dataset():
    """Create a minimal dataset with an ordinal target and three predictors."""
    df = pd.DataFrame({
        "precipitation": [0.0, 0.1, 0.0, 0.2],
        "visibility": [10, 8, 9, 7],
        "temperature": [30, 28, 29, 27],
        "hour": [8, 14, 20, 2],
        "severity": [0, 1, 0, 2],  # ordinal target
    })
    return df

def test_prepare_model_data(tiny_dataset):
    X, y = prepare_model_data(tiny_dataset)
    # Expect a DataFrame for X and a Series for y.
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert list(y.unique()) == [0, 1, 2]

def test_fit_ordinal_model(tiny_dataset):
    X, y = prepare_model_data(tiny_dataset)
    result = fit_ordinal_model(X, y)
    # The fitted result should be an instance of statsmodels' OrderedModel
    from statsmodels.miscmodels.ordinal_model import OrderedModel
    assert isinstance(result, OrderedModel)
    # Basic sanity: the model should have a `params` attribute after fitting.
    assert hasattr(result, "params")
