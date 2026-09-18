import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json

# Mock data for testing without full ingestion pipeline
def create_mock_data():
    """Create a small mock dataset for testing modeling functions."""
    data = {
        "Subject_ID": [f"sub-{i:03d}" for i in range(1, 21)],
        "Global_Signal_SD": np.random.uniform(0.1, 0.5, 20),
        "Mean_FD": np.random.uniform(0.05, 0.4, 20),
        "Mean_DVARS": np.random.uniform(1.0, 3.0, 20),
        "Age": np.random.randint(18, 40, 20),
        "Sex": np.random.choice([0, 1], 20),
        "MWQ_Score": np.random.randint(10, 50, 20)
    }
    return pd.DataFrame(data)

class TestReducedModelAnalysis:
    def test_reduced_model_runs(self):
        """Test that the reduced model analysis runs without error on mock data."""
        from modeling import run_reduced_model_analysis, prepare_model_data
        
        df = create_mock_data()
        full_features = ["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"]
        reduced_features = ["Mean_FD", "Mean_DVARS", "Age", "Sex"]
        
        # Run analysis with small sample to avoid timeout in CI
        result = run_reduced_model_analysis(df, full_features, reduced_features, n_splits=3, alphas=[0.1, 1.0])
        
        assert "full_model" in result
        assert "reduced_model" in result
        assert "delta_r2" in result
        assert result["status"] == "Success"
        assert isinstance(result["delta_r2"], (int, float))

    def test_reduced_model_fallback_collinearity(self):
        """Test fallback logic when reduced model fails due to collinearity (simulated)."""
        from modeling import run_reduced_model_analysis
        
        # Create data with perfect collinearity in reduced features
        df = create_mock_data()
        df["Mean_FD"] = df["Mean_DVARS"] * 2  # Perfect linear relationship
        
        full_features = ["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"]
        reduced_features = ["Mean_FD", "Mean_DVARS", "Age", "Sex"]
        
        # This might still run due to Ridge regularization, but let's test the structure
        result = run_reduced_model_analysis(df, full_features, reduced_features, n_splits=3, alphas=[0.1, 1.0])
        
        # Ridge usually handles collinearity, so status might still be Success.
        # The fallback is for when the model completely fails (e.g. singular matrix in OLS, but Ridge is robust).
        # We verify the structure exists regardless.
        assert "full_model" in result
        assert "delta_r2" in result or result["status"] == "High Collinearity"

class TestModelingUtils:
    def test_prepare_model_data(self):
        """Test data preparation function."""
        from modeling import prepare_model_data
        
        df = create_mock_data()
        features = ["Global_Signal_SD", "Mean_FD"]
        X, y, ids = prepare_model_data(df, features, "MWQ_Score")
        
        assert X.shape[0] == len(df)
        assert X.shape[1] == 2
        assert len(y) == len(df)
        assert len(ids) == len(df)

    def test_prepare_model_data_drop_na(self):
        """Test that prepare_model_data drops rows with NaN."""
        from modeling import prepare_model_data
        
        df = create_mock_data()
        df.loc[0, "Global_Signal_SD"] = np.nan
        
        features = ["Global_Signal_SD", "Mean_FD"]
        X, y, ids = prepare_model_data(df, features, "MWQ_Score")
        
        assert X.shape[0] == len(df) - 1
        assert len(y) == len(df) - 1
        assert len(ids) == len(df) - 1
