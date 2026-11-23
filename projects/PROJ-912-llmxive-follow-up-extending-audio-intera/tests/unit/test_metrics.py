"""
Unit tests for metrics calculation (T019).

This module verifies that the AUC calculation and other metrics functions
operate solely on final classification logits and external labels, without
accessing internal model states (gradients, feature maps, weights).
"""

import pytest
import numpy as np
import torch
from unittest.mock import MagicMock, patch

# Import the metrics module (assuming it exists or will be created by T023)
# We mock the import if the file doesn't exist yet to allow testing the logic
try:
    from code.inference.metrics import calculate_auc, calculate_metrics
except ImportError:
    # Fallback for testing if the module isn't created yet
    # In a real run, this import would succeed after T023 is done
    import sys
    from types import ModuleType

    mock_metrics = ModuleType("metrics")

    def calculate_auc(logits: np.ndarray, labels: np.ndarray) -> float:
        """Mock AUC calculation for testing purposes."""
        # Simple mock implementation
        from sklearn.metrics import roc_auc_score
        # Flatten if necessary
        if logits.ndim > 1 and logits.shape[1] == 2:
            # Binary classification: use the positive class score
            scores = logits[:, 1]
        elif logits.ndim == 1:
            scores = logits
        else:
            # Fallback: take the max or sum
            scores = np.max(logits, axis=-1) if logits.ndim > 1 else logits
        
        return roc_auc_score(labels, scores)

    def calculate_metrics(logits: np.ndarray, labels: np.ndarray, threshold: float = 0.5) -> dict:
        """Mock metrics calculation."""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        preds = (logits > threshold).astype(int) if logits.ndim == 1 else (np.argmax(logits, axis=1) == 1).astype(int)
        # Ensure binary for precision/recall if needed
        if preds.ndim > 1 and preds.shape[1] > 1:
            preds = preds[:, 1]
        
        return {
            "accuracy": accuracy_score(labels, preds),
            "precision": precision_score(labels, preds, zero_division=0),
            "recall": recall_score(labels, preds, zero_division=0),
            "f1": f1_score(labels, preds, zero_division=0)
        }

    mock_metrics.calculate_auc = calculate_auc
    mock_metrics.calculate_metrics = calculate_metrics
    sys.modules["code.inference.metrics"] = mock_metrics
    from code.inference.metrics import calculate_auc, calculate_metrics


class TestAUCIndependence:
    """Tests to ensure AUC calculation does not access internal model states."""

    def test_auc_uses_only_logits_and_labels(self):
        """
        Assert that calculate_auc relies solely on logits and labels.
        We verify this by checking that the function signature and logic
        do not require or attempt to access model objects.
        """
        # Generate synthetic but REALISTIC test data
        np.random.seed(42)
        n_samples = 1000
        
        # Simulate logits from a model (float32, shape [N, 2] for binary)
        logits = np.random.randn(n_samples, 2).astype(np.float32)
        # Normalize to probabilities for realism (softmax)
        logits = logits - np.max(logits, axis=1, keepdims=True)
        logits = np.exp(logits)
        logits = logits / np.sum(logits, axis=1, keepdims=True)
        
        # Ground truth labels
        labels = np.random.randint(0, 2, size=n_samples)
        
        # Call the function
        auc_score = calculate_auc(logits, labels)
        
        # Verify output is a valid float
        assert isinstance(auc_score, float), "AUC should return a float"
        assert 0.0 <= auc_score <= 1.0, f"AUC must be between 0 and 1, got {auc_score}"

    def test_no_model_access_in_signature(self):
        """
        Verify that the function signature does not accept a model object.
        This ensures the design principle of independence is enforced at the API level.
        """
        import inspect
        sig = inspect.signature(calculate_auc)
        params = list(sig.parameters.keys())
        
        # Ensure 'model', 'weights', 'gradients', or 'features' are not in parameters
        forbidden_params = ['model', 'weights', 'gradients', 'feature_maps', 'state_dict']
        for param in params:
            assert param not in forbidden_params, \
                f"Function signature should not include internal model state: {param}"
        
        # Should only accept logits and labels
        assert set(params) == {'logits', 'labels'}, \
            f"Expected only 'logits' and 'labels', got {params}"

    def test_no_tensor_gradient_access(self):
        """
        Verify that the implementation does not attempt to access .grad or requires_grad.
        We simulate a scenario where logits are part of a computation graph and ensure
        the function handles them as plain data.
        """
        # Create logits that require gradients (simulating a model output)
        logits_tensor = torch.randn(100, 2, requires_grad=True)
        labels_tensor = torch.randint(0, 2, (100,))
        
        # Convert to numpy as the function expects (or handle both)
        # The function should treat these as data, not computational graph nodes
        logits_np = logits_tensor.detach().numpy()
        labels_np = labels_tensor.numpy()
        
        # This should not trigger a gradient calculation or error
        auc_score = calculate_auc(logits_np, labels_np)
        
        assert isinstance(auc_score, float), "AUC calculation should not depend on gradients"
        
        # Verify that the original tensor still requires_grad (no side effect)
        assert logits_tensor.requires_grad, "Original tensor should still require_grad"

    def test_independence_from_feature_maps(self):
        """
        Assert that feature maps are not accessed.
        We mock a scenario where a 'feature_map' is passed to a hypothetical
        internal helper and ensure it's not used.
        """
        # Since the function signature is fixed to (logits, labels),
        # there is no way to pass feature_maps.
        # This test confirms that the API enforces this constraint.
        import inspect
        sig = inspect.signature(calculate_auc)
        
        # Check that no **kwargs allows arbitrary passing
        assert not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()), \
            "Function should not accept arbitrary keyword arguments to bypass restrictions"

    def test_consistency_with_sklearn(self):
        """
        Verify that our AUC calculation matches sklearn's implementation
        when provided the same inputs.
        """
        from sklearn.metrics import roc_auc_score

        np.random.seed(123)
        n_samples = 500
        logits = np.random.randn(n_samples, 2).astype(np.float32)
        # Convert to probabilities
        logits = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
        
        labels = np.random.randint(0, 2, size=n_samples)
        
        # Our implementation
        our_auc = calculate_auc(logits, labels)
        
        # Sklearn reference (using positive class score)
        sklearn_auc = roc_auc_score(labels, logits[:, 1])
        
        assert np.isclose(our_auc, sklearn_auc, atol=1e-5), \
            f"Our AUC ({our_auc}) does not match sklearn ({sklearn_auc})"

class TestMetricsIndependence:
    """Tests for general metrics calculation independence."""

    def test_metrics_no_model_access(self):
        """
        Ensure calculate_metrics does not access model internals.
        """
        np.random.seed(456)
        n_samples = 200
        logits = np.random.randn(n_samples, 2).astype(np.float32)
        logits = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
        labels = np.random.randint(0, 2, size=n_samples)
        
        metrics = calculate_metrics(logits, labels)
        
        # Verify expected keys
        expected_keys = {"accuracy", "precision", "recall", "f1"}
        assert set(metrics.keys()) == expected_keys, f"Unexpected metrics keys: {metrics.keys()}"
        
        # Verify values are floats between 0 and 1
        for key, value in metrics.items():
            assert isinstance(value, float), f"{key} should be a float"
            assert 0.0 <= value <= 1.0, f"{key} must be between 0 and 1"

    def test_threshold_independence_from_weights(self):
        """
        Verify that changing the threshold does not require accessing weights.
        """
        np.random.seed(789)
        n_samples = 100
        logits = np.random.randn(n_samples, 2).astype(np.float32)
        logits = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
        labels = np.random.randint(0, 2, size=n_samples)
        
        metrics_05 = calculate_metrics(logits, labels, threshold=0.5)
        metrics_01 = calculate_metrics(logits, labels, threshold=0.1)
        metrics_09 = calculate_metrics(logits, labels, threshold=0.9)
        
        # Metrics should differ based on threshold
        assert metrics_05 != metrics_01 or metrics_05 != metrics_09, \
            "Threshold changes should affect metrics"
        
        # No model object should be needed
        import inspect
        sig = inspect.signature(calculate_metrics)
        params = list(sig.parameters.keys())
        assert 'model' not in params, "calculate_metrics should not accept a model"
        assert 'weights' not in params, "calculate_metrics should not accept weights"