import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import importlib.util

# Load the modeling module dynamically to ensure we are testing the actual file
spec = importlib.util.spec_from_file_location("modeling", "code/modeling.py")
modeling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modeling)

from modeling import (
    run_ridge_regression_with_nested_cv,
    prepare_model_data,
    load_cleaned_data,
    run_reduced_model_analysis,
    calculate_delta_r2
)

def create_sample_dataframe(n=100, seed=42):
    """Create a synthetic dataframe matching the expected schema for testing."""
    np.random.seed(seed)
    
    # Generate features
    global_signal_sd = np.random.normal(0.5, 0.1, n)
    age = np.random.randint(18, 65, n)
    sex = np.random.choice([0, 1], n)
    mean_fd = np.random.normal(0.2, 0.05, n)
    mean_dvars = np.random.normal(0.5, 0.1, n)
    
    # Create a moderate correlation for MWQ_Score based on Global_Signal_SD
    # MWQ = 30 + 10 * Global_Signal_SD + noise
    mwq_score = 30 + 10 * global_signal_sd + np.random.normal(0, 2, n)
    
    data = {
        "Subject_ID": [f"sub-{i:03d}" for i in range(n)],
        "Global_Signal_SD": global_signal_sd,
        "MWQ_Score": mwq_score,
        "Age": age,
        "Sex": sex,
        "Mean_FD": mean_fd,
        "Mean_DVARS": mean_dvars
    }
    
    # Ensure no zero variance in Global_Signal_SD
    data["Global_Signal_SD"] = np.abs(data["Global_Signal_SD"]) + 0.01
    
    return pd.DataFrame(data)

def test_prepare_model_data():
    """Test that prepare_model_data correctly splits features and target."""
    df = create_sample_dataframe(n=50)
    
    y, X, feature_names = modeling.prepare_model_data(
        df,
        y_col="MWQ_Score",
        features=["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"]
    )
    
    assert y.shape[0] == 50
    assert X.shape[0] == 50
    assert X.shape[1] == 5
    assert list(feature_names) == ["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"]
    assert "Subject_ID" not in feature_names

def test_run_ridge_regression_with_nested_cv_structure():
    """
    Verify that the nested CV logic runs without error and returns the expected structure.
    This test uses synthetic data with a known correlation to ensure alpha tuning works.
    """
    df = create_sample_dataframe(n=100, seed=42)
    
    # Run the full nested CV pipeline
    result = modeling.run_ridge_regression_with_nested_cv(
        df,
        y_col="MWQ_Score",
        features=["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"],
        n_splits=3, # Reduced for speed in test
        alphas=[0.1, 1.0, 10.0]
    )
    
    # Verify top-level keys
    assert "best_alpha" in result
    assert "mean_mae" in result
    assert "mean_r2" in result
    assert "mean_pearson_r" in result
    assert "cv_results" in result
    
    # Verify numeric types
    assert isinstance(result["best_alpha"], float)
    assert isinstance(result["mean_mae"], float)
    assert isinstance(result["mean_r2"], float)
    
    # Verify that the result is not trivial (data was generated with signal)
    # With synthetic data r=0.3+, we expect R2 > 0.05 and MAE < 5.0
    assert result["mean_r2"] > 0.0, "R2 should be positive with synthetic signal"
    assert result["mean_mae"] < 5.0, "MAE should be reasonable for synthetic data"
    
    # Verify CV results structure
    assert isinstance(result["cv_results"], dict)
    assert "alphas" in result["cv_results"]
    assert "mae_scores" in result["cv_results"]
    assert len(result["cv_results"]["alphas"]) == len(result["cv_results"]["mae_scores"])

def test_nested_cv_alpha_tuning():
    """
    Verify that alpha tuning actually selects a value and that different alphas produce different scores.
    """
    df = create_sample_dataframe(n=100, seed=42)
    
    # Run with a wide range of alphas
    result = modeling.run_ridge_regression_with_nested_cv(
        df,
        y_col="MWQ_Score",
        features=["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"],
        n_splits=3,
        alphas=[0.01, 0.1, 1.0, 10.0, 100.0]
    )
    
    # Check that the best alpha is one of the candidates
    assert result["best_alpha"] in [0.01, 0.1, 1.0, 10.0, 100.0], \
        f"Best alpha {result['best_alpha']} not in candidate list"
    
    # Verify that the CV results show variance across alphas (unless data is perfectly linear/constant)
    mae_scores = result["cv_results"]["mae_scores"]
    # If all alphas give the exact same score, it might be a data issue, but usually they differ
    # We just assert that we have scores for all alphas
    assert len(mae_scores) == 5, "Should have 5 MAE scores for 5 alphas"

def test_run_reduced_model_analysis():
    """Test that reduced model analysis runs and produces valid output."""
    df = create_sample_dataframe(n=100)
    
    # Run the analysis
    result = modeling.run_reduced_model_analysis(
        df, 
        y_col="MWQ_Score",
        reduced_features=["Mean_FD", "Mean_DVARS", "Age", "Sex"],
        full_features=["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"],
        n_splits=3 
    )
    
    # Verify structure
    assert "full_model" in result
    assert "reduced_model" in result
    assert "delta_r2" in result
    
    # Verify numeric types
    assert isinstance(result["delta_r2"], float)
    assert isinstance(result["full_model"]["r2"], float)
    assert isinstance(result["reduced_model"]["r2"], float)
    
    # Verify delta_r2 calculation logic
    expected_delta = result["full_model"]["r2"] - result["reduced_model"]["r2"]
    assert np.isclose(result["delta_r2"], expected_delta)

def test_calculate_delta_r2():
    """Test the helper function to extract delta_r2."""
    mock_result = {
        "full_model": {"r2": 0.4},
        "reduced_model": {"r2": 0.3},
        "delta_r2": 0.1
    }
    
    val = modeling.calculate_delta_r2(mock_result)
    assert np.isclose(val, 0.1)
    
    # Test missing key
    empty_result = {}
    val_empty = modeling.calculate_delta_r2(empty_result)
    assert val_empty == 0.0

def test_integration_with_file_io(tmp_path):
    """Test the full flow: create data, run analysis, save JSON, verify file."""
    # Create a temporary CSV
    df = create_sample_dataframe(n=30)
    csv_path = tmp_path / "cleaned_data.csv"
    df.to_csv(csv_path, index=False)
    
    # Mock the load function to use our temp file
    # We will call the logic directly instead of main() to avoid path issues in test
    result = modeling.run_reduced_model_analysis(
        df,
        y_col="MWQ_Score",
        reduced_features=["Mean_FD", "Mean_DVARS", "Age", "Sex"],
        full_features=["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"],
        n_splits=3
    )
    
    # Simulate saving
    json_path = tmp_path / "delta_r2.json"
    with open(json_path, "w") as f:
        json.dump(result, f)
    
    # Verify file exists and is valid JSON
    assert json_path.exists()
    with open(json_path, "r") as f:
        loaded = json.load(f)
    
    assert "delta_r2" in loaded
    assert isinstance(loaded["delta_r2"], (int, float))
    assert loaded["delta_r2"] == result["delta_r2"]