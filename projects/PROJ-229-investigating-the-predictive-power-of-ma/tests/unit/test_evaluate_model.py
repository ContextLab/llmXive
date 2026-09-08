"""
Unit test for the ``code/models/evaluate.py`` module.

The test verifies that the ``evaluate_model`` function can successfully
compute an R² score given a simple synthetic model and dataset.  The test
does **not** rely on any external data – it creates a temporary model
(a scikit‑learn ``LinearRegression``) and a tiny pandas DataFrame,
serialises the model with ``joblib`` and then invokes the evaluation logic.
This ensures the core logic works without requiring the full pipeline to be
executed.
"""

import json
import os
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Import the function under test
from models.evaluate import evaluate_model

def test_evaluate_model_basic(tmp_path: Path):
    # Create a tiny dataset
    X = pd.DataFrame({"feat1": [1, 2, 3, 4], "feat2": [4, 3, 2, 1]})
    y = pd.Series([10, 12, 14, 16])  # perfectly linear relationship

    # Train a simple linear regression model
    model = LinearRegression()
    model.fit(X, y)

    # Serialize the model to a temporary file
    model_path = tmp_path / "temp_model.pkl"
    joblib.dump(model, model_path)

    # Evaluate using the function from evaluate.py
    r2 = evaluate_model(model_path, X, y)

    # The R² of a perfect linear fit should be very close to 1.0
    assert np.isclose(r2, 1.0, atol=1e-6)

    # Ensure the function returns a float
    assert isinstance(r2, float)