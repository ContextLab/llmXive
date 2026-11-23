"""
Integration test for the full modeling pipeline on the unified dataset.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Import modeling functions
from modeling import split_data, train_baseline_rf, generate_oof_predictions, calculate_residuals, train_augmented_rf, run_permutation_test

@pytest.fixture
def mock_unified_dataset(tmp_path):
    """Create a synthetic unified dataset for modeling tests."""
    n_samples = 100
    data = {
        "lesion_area_ratio": np.random.rand(n_samples),
        "necrosis_color_index": np.random.rand(n_samples) * 100,
        "texture_entropy": np.random.rand(n_samples) * 10,
        "mean_temp": np.random.rand(n_samples) * 15 + 15,
        "mean_humidity": np.random.rand(n_samples) * 40 + 40,
        "total_precipitation": np.random.rand(n_samples) * 10,
        # Target variable (simulated severity)
        "severity_target": np.random.rand(n_samples) * 100
    }
    df = pd.DataFrame(data)
    path = tmp_path / "unified_analysis.csv"
    df.to_csv(path, index=False)
    return path

def test_modeling_pipeline(mock_unified_dataset):
    """
    Run the baseline -> residual -> augmented -> permutation test flow.
    """
    df = pd.read_csv(mock_unified_dataset)
    
    # 1. Split
    train_df, test_df = split_data(df, test_size=0.2)
    assert len(train_df) + len(test_df) == len(df)
    
    # 2. Baseline RF
    # We need to define features and target explicitly for the test
    feature_cols = ["lesion_area_ratio", "necrosis_color_index", "texture_entropy"]
    target_col = "severity_target"
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    # Train baseline
    baseline_model, oof_preds, oof_y = generate_oof_predictions(train_df, feature_cols, target_col)
    
    # 3. Calculate Residuals
    residuals = calculate_residuals(oof_y, oof_preds)
    assert len(residuals) == len(oof_y)
    
    # 4. Augmented Model (using weather features to predict residuals)
    weather_cols = ["mean_temp", "mean_humidity", "total_precipitation"]
    # Combine weather and residuals for augmented training
    # Note: The actual modeling.py logic might handle this internally, 
    # here we test the high-level flow.
    
    # For this integration test, we assume the `run_permutation_test` function
    # orchestrates the specific logic defined in T028.
    # We pass a small subset to ensure it runs quickly.
    
    result = run_permutation_test(
        train_data=train_df,
        feature_cols=feature_cols,
        weather_cols=weather_cols,
        target_col=target_col,
        n_iterations=10 # Small number for speed
    )
    
    assert "p_value" in result
    assert "R2_aug" in result
    assert "R2_null" in result
    assert 0.0 <= result["p_value"] <= 1.0
