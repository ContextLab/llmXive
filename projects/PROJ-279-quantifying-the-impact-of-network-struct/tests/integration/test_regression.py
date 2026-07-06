"""
Integration test for the full regression pipeline on synthetic data.

This test verifies that the statistical correlation and visualization pipeline
(User Story 3) functions correctly end-to-end using generated synthetic data
that mimics the structure of the real descriptor dataset.

It validates:
1. Data loading and aggregation (mocked for synthetic)
2. Cross-validation logic (LOOCV vs 5-fold switch)
3. Ridge Regression execution
4. Feature importance and p-value calculation
5. Result aggregation and logging
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score, LeaveOneOut, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

# Project imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models import (
    get_cross_validation_split,
    run_ridge_regression,
    calculate_feature_pvalues,
    extract_feature_importance,
    get_top_features
)
from logging_config import setup_logging, get_logger

# Configure logging for the test
logger = get_logger(__name__)
setup_logging()

def _generate_synthetic_descriptors(n_samples: int = 50, n_features: int = 10, noise: float = 0.1) -> pd.DataFrame:
    """
    Generate a synthetic dataset mimicking the structure of data/processed/descriptors.csv.
    
    Creates a DataFrame with:
    - config_id: unique identifiers
    - ring_3, ring_4, ... ring_10: topological features
    - q6: steinhardt parameter
    - clustering_coeff: clustering coefficient
    - thermal_conductivity: target variable (generated with a known linear relationship)
    """
    np.random.seed(42)
    
    # Generate topological features (random but realistic ranges)
    data = {
        "config_id": [f"cfg_{i:03d}" for i in range(n_samples)],
    }
    
    # Add ring statistics
    for i in range(3, 11):
        data[f"ring_{i}"] = np.random.uniform(0.0, 1.0, n_samples)
    
    # Add other descriptors
    data["q6"] = np.random.uniform(0.0, 1.0, n_samples)
    data["clustering_coeff"] = np.random.uniform(0.0, 1.0, n_samples)
    
    df = pd.DataFrame(data)
    
    # Create a target variable with a known relationship to features
    # k = 2.0 * ring_3 + 1.5 * ring_4 - 0.5 * q6 + noise
    true_coeffs = {
        "ring_3": 2.0,
        "ring_4": 1.5,
        "q6": -0.5
    }
    
    target = np.zeros(n_samples)
    for feat, coeff in true_coeffs.items():
        target += coeff * df[feat].values
    
    target += np.random.normal(0, noise, n_samples)
    df["thermal_conductivity"] = target
    
    return df

@pytest.fixture
def synthetic_data():
    """Fixture to generate and return synthetic descriptor data."""
    return _generate_synthetic_descriptors(n_samples=50, n_features=10, noise=0.1)

@pytest.fixture
def small_synthetic_data():
    """Fixture to generate small dataset (< 30 samples) to trigger LOOCV."""
    return _generate_synthetic_descriptors(n_samples=15, n_features=10, noise=0.1)

def test_full_regression_pipeline_synthetic(synthetic_data):
    """
    Integration test: Run the full regression pipeline on synthetic data (N >= 30).
    
    Verifies:
    - Correct CV split selection (5-fold for N >= 30)
    - Ridge regression execution
    - R^2 calculation
    - Feature importance extraction
    """
    logger.info("Running full regression pipeline integration test (N >= 30)...")
    
    # Prepare features and target
    feature_cols = [col for col in synthetic_data.columns if col not in ["config_id", "thermal_conductivity"]]
    X = synthetic_data[feature_cols].values
    y = synthetic_data["thermal_conductivity"].values
    
    # 1. Test Cross-Validation Split Selection
    # Since N=50, it should select 5-fold
    cv_splitter = get_cross_validation_split(X)
    assert isinstance(cv_splitter, KFold), "Expected KFold for N >= 30"
    assert cv_splitter.n_splits == 5, "Expected 5 splits"
    
    # 2. Test Ridge Regression
    # Scale features first
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = Ridge(alpha=1.0)
    scores = cross_val_score(model, X_scaled, y, cv=cv_splitter, scoring='r2')
    
    logger.info(f"Cross-validation R² scores: {scores}")
    assert len(scores) == 5, "Expected 5 CV scores"
    assert np.all(scores > -1.0), "R² scores should be > -1.0"
    
    # 3. Test Feature Importance and P-values
    # Train on full data for feature importance extraction
    model.fit(X_scaled, y)
    
    importance = extract_feature_importance(model, feature_cols)
    assert len(importance) == len(feature_cols), "Importance vector length mismatch"
    
    # Calculate p-values (using linear regression approximation for p-values as Ridge doesn't provide them directly)
    # We use the helper which fits a LinearRegression on the scaled data for p-value estimation
    p_values = calculate_feature_pvalues(X_scaled, y, feature_cols)
    assert len(p_values) == len(feature_cols), "P-values vector length mismatch"
    
    # 4. Test Top Features Extraction
    top_features = get_top_features(importance, p_values, top_n=3)
    assert len(top_features) == 3, "Expected top 3 features"
    
    # Verify that the top features include the ones we injected in the synthetic data
    # We injected ring_3, ring_4, q6. One of them should be in top 3.
    top_feature_names = [f[0] for f in top_features]
    injected_features = ["ring_3", "ring_4", "q6"]
    found_injected = any(f in top_feature_names for f in injected_features)
    assert found_injected, f"Expected at least one injected feature in top 3, got {top_feature_names}"
    
    logger.info("Full regression pipeline test passed.")

def test_loocv_trigger_small_dataset(small_synthetic_data):
    """
    Integration test: Verify LOOCV is triggered for small datasets (N < 30).
    """
    logger.info("Testing LOOCV trigger for small dataset (N < 30)...")
    
    feature_cols = [col for col in small_synthetic_data.columns if col not in ["config_id", "thermal_conductivity"]]
    X = small_synthetic_data[feature_cols].values
    y = small_synthetic_data["thermal_conductivity"].values
    
    cv_splitter = get_cross_validation_split(X)
    assert isinstance(cv_splitter, LeaveOneOut), "Expected LeaveOneOut for N < 30"
    
    logger.info("LOOCV trigger test passed.")

def test_end_to_end_metrics_aggregation(synthetic_data):
    """
    Integration test: Verify the aggregation of metrics into a result dictionary.
    """
    logger.info("Testing metrics aggregation...")
    
    feature_cols = [col for col in synthetic_data.columns if col not in ["config_id", "thermal_conductivity"]]
    X = synthetic_data[feature_cols].values
    y = synthetic_data["thermal_conductivity"].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Run regression
    cv_splitter = get_cross_cv_split(X) # Using the internal logic
    model = Ridge(alpha=1.0)
    scores = cross_val_score(model, X_scaled, y, cv=cv_splitter, scoring='r2')
    
    mean_r2 = np.mean(scores)
    std_r2 = np.std(scores)
    
    # Train on full data for feature analysis
    model.fit(X_scaled, y)
    importance = extract_feature_importance(model, feature_cols)
    p_values = calculate_feature_pvalues(X_scaled, y, feature_cols)
    top_features = get_top_features(importance, p_values, top_n=3)
    
    # Construct result dict (simulating what main.py might do)
    results = {
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "n_samples": len(y),
        "cv_method": "5-fold" if len(y) >= 30 else "LOOCV",
        "top_features": [
            {"name": name, "importance": float(imp), "p_value": float(pv)}
            for name, imp, pv in top_features
        ]
    }
    
    # Assertions on results structure
    assert "mean_r2" in results
    assert "std_r2" in results
    assert "top_features" in results
    assert len(results["top_features"]) == 3
    assert results["cv_method"] == "5-fold"
    
    logger.info(f"Aggregated results: {json.dumps(results, indent=2)}")
    logger.info("Metrics aggregation test passed.")

if __name__ == "__main__":
    # Allow running this file directly for quick manual verification
    pytest.main([__file__, "-v"])
