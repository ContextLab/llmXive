"""
Unit tests for the Forward Stepwise Selection implementation.
"""
import pytest
import numpy as np
from code.analysis.selectors import forward_stepwise_selection, select_variables_forward_stepwise


class TestForwardStepwiseSelection:
    """Tests for the forward_stepwise_selection function."""

    def setup_method(self):
        """Setup test fixtures."""
        np.random.seed(42)
        self.n_samples = 100
        self.n_features = 5
        
        # Create a dataset where we know the true structure
        self.X = np.random.randn(self.n_samples, self.n_features)
        self.true_coef = np.array([3.0, -2.0, 1.5, 0.0, 0.0])
        self.y = self.X @ self.true_coef + np.random.randn(self.n_samples) * 0.5
        self.feature_names = [f"feat_{i}" for i in range(self.n_features)]

    def test_selects_correct_features(self):
        """Test that the algorithm selects the known non-zero features."""
        selected, stats = forward_stepwise_selection(
            self.X, self.y, feature_names=self.feature_names, max_features=3
        )
        
        # Should select the first 3 features (non-zero coefficients)
        # Note: Order may vary, but these should be in the selected set
        assert len(selected) <= 3
        # The top 3 features by coefficient magnitude should be selected
        expected_features = {"feat_0", "feat_1", "feat_2"}
        selected_set = set(selected)
        
        # At least 2 of the 3 true features should be selected
        assert len(selected_set.intersection(expected_features)) >= 2

    def test_aic_improves(self):
        """Test that AIC improves with each step (or stops when no improvement)."""
        selected, stats = forward_stepwise_selection(
            self.X, self.y, feature_names=self.feature_names, max_features=3
        )
        
        history = stats.get("history", [])
        if len(history) > 1:
            # Check that AIC generally decreases (or stays same if no improvement)
            aic_values = [h["aic"] for h in history if h["aic"] != float('inf')]
            if len(aic_values) > 1:
                # The last AIC should be <= the first AIC
                assert aic_values[-1] <= aic_values[0] + 1e-6

    def test_handles_empty_initial(self):
        """Test selection starting from empty model."""
        selected, stats = forward_stepwise_selection(
            self.X, self.y, feature_names=self.feature_names, initial_features=[], max_features=2
        )
        
        assert len(selected) >= 0
        assert len(selected) <= 2

    def test_handles_max_features(self):
        """Test that max_features constraint is respected."""
        selected, stats = forward_stepwise_selection(
            self.X, self.y, feature_names=self.feature_names, max_features=2
        )
        
        assert len(selected) <= 2

    def test_returns_stats(self):
        """Test that the function returns comprehensive statistics."""
        selected, stats = forward_stepwise_selection(
            self.X, self.y, feature_names=self.feature_names, max_features=3
        )
        
        assert "history" in stats
        assert "final_aic" in stats
        assert "final_stats" in stats
        assert "n_selected" in stats

    def test_feature_names_mapping(self):
        """Test that feature names are correctly mapped and returned."""
        custom_names = [f"custom_{i}" for i in range(self.n_features)]
        selected, stats = forward_stepwise_selection(
            self.X, self.y, feature_names=custom_names, max_features=2
        )
        
        # All selected names should be from the custom list
        assert all(name in custom_names for name in selected)

    def test_singular_matrix_handling(self):
        """Test handling of singular matrices (collinear features)."""
        # Create perfectly collinear features
        X_collinear = np.column_stack([
            np.random.randn(self.n_samples),
            np.random.randn(self.n_samples),
            np.random.randn(self.n_samples)
        ])
        # Make columns 0 and 1 identical
        X_collinear[:, 1] = X_collinear[:, 0]
        
        y_collinear = X_collinear[:, 0] + np.random.randn(self.n_samples) * 0.1
        names = ["f0", "f1", "f2"]
        
        # Should not raise an exception
        selected, stats = forward_stepwise_selection(
            X_collinear, y_collinear, feature_names=names, max_features=3
        )
        
        # Should select at least one feature
        assert len(selected) >= 1


class TestSelectVariablesWrapper:
    """Tests for the select_variables_forward_stepwise wrapper function."""

    def setup_method(self):
        """Setup test fixtures."""
        np.random.seed(123)
        self.X = np.random.randn(50, 4)
        self.y = self.X[:, 0] * 2.0 + self.X[:, 1] * (-1.0) + np.random.randn(50) * 0.3
        self.feature_names = ["a", "b", "c", "d"]

    def test_returns_only_names(self):
        """Test that wrapper returns only feature names."""
        result = select_variables_forward_stepwise(
            self.X, self.y, feature_names=self.feature_names, max_features=2
        )
        
        assert isinstance(result, list)
        assert all(isinstance(name, str) for name in result)
        assert len(result) <= 2

    def test_consistency_with_full_function(self):
        """Test that wrapper returns same features as full function."""
        selected_full, _ = forward_stepwise_selection(
            self.X, self.y, feature_names=self.feature_names, max_features=2
        )
        selected_wrapper = select_variables_forward_stepwise(
            self.X, self.y, feature_names=self.feature_names, max_features=2
        )
        
        assert selected_full == selected_wrapper