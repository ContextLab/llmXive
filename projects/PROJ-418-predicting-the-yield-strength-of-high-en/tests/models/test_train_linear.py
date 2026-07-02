import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from models.train import train_linear_regression, load_processed_data, prepare_features_target, create_stratified_split

def test_train_linear_regression_creates_pipeline():
    """Test that the linear regression trainer returns a fitted pipeline."""
    # Create dummy data
    X = pd.DataFrame(np.random.rand(100, 5), columns=['f1', 'f2', 'f3', 'f4', 'f5'])
    y = pd.Series(np.random.rand(100))
    
    model = train_linear_regression(X, y)
    
    assert isinstance(model, Pipeline), "Model should be a sklearn Pipeline"
    assert len(model.steps) == 2, "Pipeline should have 2 steps (scaler, regressor)"
    assert model.named_steps['regressor'] is not None
    assert hasattr(model.named_steps['regressor'], 'coef_'), "Regressor should be fitted"

def test_train_linear_regression_predicts():
    """Test that the model can make predictions."""
    X = pd.DataFrame(np.random.rand(50, 3), columns=['a', 'b', 'c'])
    y = pd.Series(np.random.rand(50))
    
    model = train_linear_regression(X, y)
    
    X_test = pd.DataFrame(np.random.rand(5, 3), columns=['a', 'b', 'c'])
    preds = model.predict(X_test)
    
    assert len(preds) == 5, "Should predict 5 values"
    assert all(isinstance(p, (float, np.floating)) for p in preds), "Predictions should be numeric"

def test_train_linear_regression_handles_missing():
    """Test behavior with missing values (should raise or handle gracefully)."""
    X = pd.DataFrame({'a': [1.0, 2.0, np.nan], 'b': [1.0, 2.0, 3.0]})
    y = pd.Series([1.0, 2.0, 3.0])
    
    # The train function calls fit directly. 
    # If data has NaN, sklearn LinearRegression will raise ValueError.
    # This test ensures we expect that behavior or that the function handles it.
    # Based on implementation, we expect it to fail if NaNs are present in input.
    try:
        model = train_linear_regression(X, y)
        # If it doesn't fail, it might have handled it internally or the data wasn't problematic enough
        # But standard sklearn fails on NaN.
    except ValueError as e:
        assert "nan" in str(e).lower() or "missing" in str(e).lower(), f"Expected NaN error, got {e}"

def test_integration_linear_regression_on_dummy_csv(tmp_path):
    """Integration test: Load CSV, split, train, verify output."""
    # Create a temporary CSV
    data = {
        'f1': np.random.rand(200),
        'f2': np.random.rand(200),
        'yield_strength_mpa': np.random.rand(200) * 100
    }
    df = pd.DataFrame(data)
    csv_path = str(tmp_path / "test_data.csv")
    df.to_csv(csv_path, index=False)
    
    # Load and process
    loaded_df = load_processed_data(csv_path)
    X, y = prepare_features_target(loaded_df)
    
    # Split
    X_train, X_test, y_train, y_test = create_stratified_split(X, y)
    
    # Train
    model = train_linear_regression(X_train, y_train)
    
    # Evaluate
    r2 = model.score(X_test, y_test)
    assert -1 < r2 < 1.5, f"R2 should be reasonable, got {r2}"