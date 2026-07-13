"""
Unit tests for the evaluate module.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, balanced_accuracy_score
from pathlib import Path
import tempfile
import os

# Import functions to test
from code.evaluate import calculate_metrics, evaluate_fold, run_evaluation

def test_calculate_metrics_binary():
    """Test metric calculation for binary classification."""
    # Generate synthetic data
    np.random.seed(42)
    y_true = np.array([0, 1, 1, 0, 1, 0, 1, 1, 0, 1])
    y_pred_proba = np.array([0.1, 0.9, 0.8, 0.2, 0.95, 0.15, 0.85, 0.9, 0.1, 0.95])
    y_pred = np.array([0, 1, 1, 0, 1, 0, 1, 1, 0, 1])
    
    metrics = calculate_metrics(y_true, y_pred_proba, y_pred)
    
    # Check that metrics are calculated
    assert "endpoint_0_roc_auc" in metrics
    assert "endpoint_0_pr_auc" in metrics
    assert "endpoint_0_balanced_accuracy" in metrics
    
    # Check that values are reasonable
    assert 0 <= metrics["endpoint_0_roc_auc"] <= 1
    assert 0 <= metrics["endpoint_0_pr_auc"] <= 1
    assert 0 <= metrics["endpoint_0_balanced_accuracy"] <= 1

def test_calculate_metrics_multiclass():
    """Test metric calculation for multiple endpoints."""
    # Generate synthetic data for 2 endpoints
    np.random.seed(42)
    y_true = np.array([
        [0, 1],
        [1, 0],
        [1, 1],
        [0, 0],
        [1, 1]
    ])
    y_pred_proba = np.array([
        [0.1, 0.9],
        [0.9, 0.1],
        [0.8, 0.9],
        [0.2, 0.1],
        [0.95, 0.95]
    ])
    y_pred = np.array([
        [0, 1],
        [1, 0],
        [1, 1],
        [0, 0],
        [1, 1]
    ])
    
    metrics = calculate_metrics(y_true, y_pred_proba, y_pred)
    
    # Check metrics for both endpoints
    assert "endpoint_0_roc_auc" in metrics
    assert "endpoint_1_roc_auc" in metrics
    assert "endpoint_0_pr_auc" in metrics
    assert "endpoint_1_pr_auc" in metrics
    assert "endpoint_0_balanced_accuracy" in metrics
    assert "endpoint_1_balanced_accuracy" in metrics

def test_evaluate_fold():
    """Test evaluation of a single fold."""
    # Create a simple model
    np.random.seed(42)
    X_train = np.random.rand(100, 10)
    y_train = np.random.randint(0, 2, 100)
    
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Create test data
    X_test = np.random.rand(20, 10)
    y_test = np.random.randint(0, 2, 20)
    
    result = evaluate_fold(
        fold=0,
        model=model,
        X_test=X_test,
        y_test=y_test,
        endpoint_name="test_endpoint"
    )
    
    # Check result structure
    assert "fold" in result
    assert "model_type" in result
    assert "endpoint" in result
    assert "roc_auc" in result
    assert "pr_auc" in result
    assert "balanced_accuracy" in result
    
    # Check values
    assert result["fold"] == 0
    assert result["model_type"] == "RandomForestClassifier"
    assert result["endpoint"] == "test_endpoint"
    assert 0 <= result["roc_auc"] <= 1
    assert 0 <= result["pr_auc"] <= 1
    assert 0 <= result["balanced_accuracy"] <= 1
