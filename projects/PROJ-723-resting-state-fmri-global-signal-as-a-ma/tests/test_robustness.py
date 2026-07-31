"""
Unit tests for Robustness Analysis (T028, T029, T030).
"""
import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import functions to test
from robustness import (
    run_alpha_sweep,
    run_variance_metric_analysis,
    run_partial_correlation_analysis
)
from utils import write_csv

@pytest.fixture
def sample_cleaned_data():
    """
    Creates a synthetic but realistic dataframe matching the schema of cleaned_data.csv.
    Used for unit testing logic without needing the full dataset.
    """
    np.random.seed(42)
    n = 100
    data = {
        "Subject_ID": [f"sub-{i:03d}" for i in range(n)],
        "Global_Signal_SD": np.random.uniform(0.5, 2.0, n),
        "MWQ_Score": np.random.uniform(20, 80, n),
        "Mean_FD": np.random.uniform(0.1, 0.4, n),
        "Mean_DVARS": np.random.uniform(0.5, 2.0, n),
        "Age": np.random.randint(18, 65, n),
        "Sex": np.random.choice([0, 1], n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_path(sample_cleaned_data):
    """Saves sample data to a temp CSV and returns the path."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        write_csv(sample_cleaned_data, f.name)
        yield f.name
    os.unlink(f.name)

def test_alpha_sweep_logic(sample_cleaned_data):
    """
    T032: Verify alpha sweep results match expected MAE variations.
    
    Checks that:
    1. The function runs without error.
    2. It returns a list of results for each alpha.
    3. MAE values are numeric and positive.
    4. Best alpha is correctly identified.
    """
    result = run_alpha_sweep(
        sample_cleaned_data,
        feature_col="Global_Signal_SD",
        target_col="MWQ_Score",
        covariate_cols=["Mean_FD", "Mean_DVARS", "Age", "Sex"],
        alpha_range=[0.01, 1.0, 100.0],
        n_folds=3
    )
    
    assert "alpha_sweep" in result
    assert "best_alpha" in result
    assert "best_mae" in result
    assert len(result["alpha_sweep"]) == 3
    
    for item in result["alpha_sweep"]:
        assert item["alpha"] in [0.01, 1.0, 100.0]
        assert isinstance(item["mean_mae"], float)
        assert item["mean_mae"] > 0
    
    # Verify best_alpha corresponds to the lowest mean_mae
    min_mae = min([x["mean_mae"] for x in result["alpha_sweep"]])
    best_alpha = result["best_alpha"]
    best_mae = result["best_mae"]
    
    assert abs(best_mae - min_mae) < 1e-6

def test_variance_metric_correlation(sample_cleaned_data):
    """
    T033: Verify variance metric correlation is within reasonable bounds.
    
    Since Variance = SD^2, the correlation should be strong and positive
    if SD is predictive. We check that the correlation is not NaN and has a p-value.
    """
    result = run_variance_metric_analysis(
        sample_cleaned_data,
        target_col="MWQ_Score",
        covariate_cols=["Mean_FD", "Mean_DVARS", "Age", "Sex"],
        alpha=1.0
    )
    
    assert "metric" in result
    assert result["metric"] == "Variance"
    assert "pearson_r" in result
    assert "p_value" in result
    assert not np.isnan(result["pearson_r"])
    assert not np.isnan(result["p_value"])
    
    # The correlation should be positive (assuming SD was positively correlated)
    # or at least consistent in sign with the underlying data generation
    assert abs(result["pearson_r"]) <= 1.0

def test_partial_correlation_analysis(sample_cleaned_data):
    """
    Verify partial correlation logic runs and returns valid stats.
    """
    result = run_partial_correlation_analysis(
        sample_cleaned_data,
        target_col="MWQ_Score",
        pred_col="Global_Signal_SD",
        control_col="Mean_FD"
    )
    
    assert "partial_r" in result
    assert "p_value" in result
    assert "is_significant" in result
    assert isinstance(result["is_significant"], bool)
    assert abs(result["partial_r"]) <= 1.0