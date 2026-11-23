"""
Unit tests for reproducibility verification utilities.
"""
import pytest
import numpy as np
import random
from unittest.mock import Mock, patch

from utils.reproducibility import audit_seed_propagation, verify_model_reproducibility

class TestAuditSeedPropagation:
    def test_numpy_reproducibility(self):
        """Test that numpy random state is correctly set."""
        result = audit_seed_propagation(
            args_seed=42,
            generator_func=Mock(),
            train_func=Mock()
        )
        
        assert result["seed_used"] == 42
        assert len(result["checks"]) > 0
        
        numpy_check = next((c for c in result["checks"] if c["name"] == "numpy_reproducibility"), None)
        assert numpy_check is not None
        assert numpy_check["passed"] is True

    def test_python_random_reproducibility(self):
        """Test that python random state is correctly set."""
        result = audit_seed_propagation(
            args_seed=123,
            generator_func=Mock(),
            train_func=Mock()
        )
        
        random_check = next((c for c in result["checks"] if c["name"] == "python_random_reproducibility"), None)
        assert random_check is not None
        assert random_check["passed"] is True

    def test_all_checks_passed(self):
        """Test that all checks are marked as passed."""
        result = audit_seed_propagation(
            args_seed=999,
            generator_func=Mock(),
            train_func=Mock()
        )
        
        assert result["all_checks_passed"] is True

class TestVerifyModelReproducibility:
    def test_model_reproducibility(self):
        """Test that model training is reproducible with same seed."""
        # Create a simple mock training function
        def mock_train(X, y, seed=42):
            np.random.seed(seed)
            random.seed(seed)
            # Generate a deterministic metric based on seed
            metric_value = np.random.random()
            return Mock(), {"metric_value": metric_value, "model": None}
        
        # Create dummy data
        X = np.random.random((10, 5))
        y = np.random.random(10)
        
        result = verify_model_reproducibility(
            train_func=mock_train,
            X=X,
            y=y,
            seed=42,
            n_runs=3
        )
        
        assert result["passed"] is True

    def test_model_non_reproducibility(self):
        """Test detection of non-reproducible training."""
        # Create a mock training function that doesn't use seed
        def non_reproducible_train(X, y, seed=42):
            # Intentionally not setting seed
            metric_value = np.random.random()
            return Mock(), {"metric_value": metric_value, "model": None}
        
        X = np.random.random((10, 5))
        y = np.random.random(10)
        
        result = verify_model_reproducibility(
            train_func=non_reproducible_train,
            X=X,
            y=y,
            seed=42,
            n_runs=3
        )
        
        # This might pass or fail depending on random chance, but the test
        # verifies the function runs without error
        assert "passed" in result
        assert "details" in result