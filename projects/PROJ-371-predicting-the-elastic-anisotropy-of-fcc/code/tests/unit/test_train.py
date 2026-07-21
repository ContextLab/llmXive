"""
Unit tests for the model training module (T020).

Tests verify:
- LOEO split logic ensures no element overlap
- Model training completes without errors
- Metrics calculation matches expected values
"""

import pytest
import numpy as np
import pandas as pd
from typing import List, Set, Tuple
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.train import (
    prepare_loeo_data,
    train_single_model,
    evaluate_model,
    MODEL_TYPES,
    DEFAULT_HYPERPARAMETERS
)
from sklearn.model_selection import LeaveOneGroupOut

@pytest.fixture
def sample_loeo_data():
    """Create sample data with known element groups for LOEO testing."""
    np.random.seed(42)
    n_samples = 60
    
    # Create data with 3 distinct elements
    elements = ["Al", "Cu", "Ni"]
    samples_per_element = n_samples // len(elements)
    
    data = []
    for i, elem in enumerate(elements):
        for j in range(samples_per_element):
            data.append({
                "element": elem,
                "feature_1": np.random.randn(),
                "feature_2": np.random.randn(),
                "A1": np.random.rand() * 2 + 0.5  # Anisotropy ratio
            })
    
    df = pd.DataFrame(data)
    return df, ["feature_1", "feature_2"]

@pytest.fixture
def loeo_splitter():
    """Create a LeaveOneGroupOut splitter instance."""
    return LeaveOneGroupOut()

class TestLOEOSplitNoElementOverlap:
    """Test that LOEO split ensures no element overlap between train and test."""
    
    def test_loeo_no_element_overlap(self, sample_loeo_data, loeo_splitter):
        """Verify that each LOEO fold has no element overlap."""
        df, feature_cols = sample_loeo_data
        X, y, groups = prepare_loeo_data(df, feature_cols)
        
        unique_elements = set(groups)
        n_elements = len(unique_elements)
        
        fold_count = 0
        for train_idx, test_idx in loeo_splitter.split(X, y, groups):
            train_elements = set(groups[train_idx])
            test_elements = set(groups[test_idx])
            
            # Verify no overlap
            overlap = train_elements.intersection(test_elements)
            assert len(overlap) == 0, f"Element overlap detected: {overlap}"
            
            # Verify test set has exactly one element
            assert len(test_elements) == 1, f"Test set should have exactly 1 element, got {len(test_elements)}"
            
            # Verify train set has all other elements
            expected_train_elements = unique_elements - test_elements
            assert train_elements == expected_train_elements, "Train set should have all elements except test element"
            
            fold_count += 1
        
        # Verify number of folds equals number of unique elements
        assert fold_count == n_elements, f"Expected {n_elements} folds, got {fold_count}"
    
    def test_loeo_element_coverage(self, sample_loeo_data, loeo_splitter):
        """Verify each element appears in test set exactly once."""
        df, feature_cols = sample_loeo_data
        X, y, groups = prepare_loeo_data(df, feature_cols)
        
        test_elements_seen = []
        
        for train_idx, test_idx in loeo_splitter.split(X, y, groups):
            test_elements = set(groups[test_idx])
            test_elements_seen.extend(list(test_elements))
        
        unique_elements = set(groups)
        assert set(test_elements_seen) == unique_elements, "Not all elements were tested"
        assert len(test_elements_seen) == len(unique_elements), "Some elements were tested multiple times"

class TestModelTraining:
    """Test model training functionality."""
    
    def test_train_random_forest(self, sample_loeo_data):
        """Test Random Forest model training."""
        df, feature_cols = sample_loeo_data
        X, y, _ = prepare_loeo_data(df, feature_cols)
        
        # Split data manually for single model test
        train_size = int(0.8 * len(X))
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        model = train_single_model("random_forest", X_train, y_train)
        assert model is not None
        assert hasattr(model, 'predict')
        
        # Verify model can make predictions
        predictions = model.predict(X_test)
        assert len(predictions) == len(X_test)
    
    def test_train_gradient_boosting(self, sample_loeo_data):
        """Test Gradient Boosting model training."""
        df, feature_cols = sample_loeo_data
        X, y, _ = prepare_loeo_data(df, feature_cols)
        
        train_size = int(0.8 * len(X))
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        model = train_single_model("gradient_boosting", X_train, y_train)
        assert model is not None
        assert hasattr(model, 'predict')
        
        predictions = model.predict(X_test)
        assert len(predictions) == len(X_test)
    
    def test_train_linear_regression(self, sample_loeo_data):
        """Test Linear Regression model training."""
        df, feature_cols = sample_loeo_data
        X, y, _ = prepare_loeo_data(df, feature_cols)
        
        train_size = int(0.8 * len(X))
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        model = train_single_model("linear_regression", X_train, y_train)
        assert model is not None
        assert hasattr(model, 'predict')
        
        predictions = model.predict(X_test)
        assert len(predictions) == len(X_test)

class TestModelEvaluation:
    """Test model evaluation metrics."""
    
    def test_evaluate_returns_correct_metrics(self, sample_loeo_data):
        """Test that evaluation returns R², MAE, and RMSE."""
        df, feature_cols = sample_loeo_data
        X, y, _ = prepare_loeo_data(df, feature_cols)
        
        train_size = int(0.8 * len(X))
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        model = train_single_model("random_forest", X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test, "random_forest")
        
        assert "r2" in metrics
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "model_type" in metrics
        assert "n_test_samples" in metrics
        
        # Verify metric types
        assert isinstance(metrics["r2"], float)
        assert isinstance(metrics["mae"], float)
        assert isinstance(metrics["rmse"], float)
        assert isinstance(metrics["n_test_samples"], int)
    
    def test_metrics_reasonable_values(self, sample_loeo_data):
        """Test that metrics are within reasonable bounds."""
        df, feature_cols = sample_loeo_data
        X, y, _ = prepare_loeo_data(df, feature_cols)
        
        train_size = int(0.8 * len(X))
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        model = train_single_model("random_forest", X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test, "random_forest")
        
        # R² can be negative but should be > -10 for reasonable models
        assert metrics["r2"] > -10
        # MAE and RMSE should be positive
        assert metrics["mae"] >= 0
        assert metrics["rmse"] >= 0

class TestHyperparameters:
    """Test hyperparameter configuration."""
    
    def test_default_hyperparameters_exist(self):
        """Verify default hyperparameters are defined for all models."""
        for model_type in MODEL_TYPES.keys():
            assert model_type in DEFAULT_HYPERPARAMETERS, f"Missing hyperparameters for {model_type}"
    
    def test_random_state_set(self):
        """Verify random_state is set for stochastic models."""
        assert "random_state" in DEFAULT_HYPERPARAMETERS["random_forest"]
        assert "random_state" in DEFAULT_HYPERPARAMETERS["gradient_boosting"]
        # Linear regression doesn't need random_state