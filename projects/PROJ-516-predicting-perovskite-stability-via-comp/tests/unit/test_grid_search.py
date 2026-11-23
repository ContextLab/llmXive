"""
Unit tests for grid search functionality (T022).

Tests verify:
1. Hard cap of ≤10 hyperparameter combinations is enforced
2. Parameter grids are generated correctly
3. Grid search completes without errors
4. Results contain required fields
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from grid_search import create_parameter_grid, run_grid_search, MAX_COMBINATIONS


class TestParameterGridCreation:
    """Tests for parameter grid creation with combination limits."""

    def test_random_forest_grid_limit(self):
        """Test that RF parameter grid respects MAX_COMBINATIONS."""
        grid = create_parameter_grid('random_forest')
        assert len(grid) <= MAX_COMBINATIONS, \
            f"RF grid has {len(grid)} combinations, exceeds limit of {MAX_COMBINATIONS}"

    def test_gradient_boosting_grid_limit(self):
        """Test that GB parameter grid respects MAX_COMBINATIONS."""
        grid = create_parameter_grid('gradient_boosting')
        assert len(grid) <= MAX_COMBINATIONS, \
            f"GB grid has {len(grid)} combinations, exceeds limit of {MAX_COMBINATIONS}"

    def test_elastic_net_grid_limit(self):
        """Test that Elastic Net parameter grid respects MAX_COMBINATIONS."""
        grid = create_parameter_grid('elastic_net')
        assert len(grid) <= MAX_COMBINATIONS, \
            f"EN grid has {len(grid)} combinations, exceeds limit of {MAX_COMBINATIONS}"

    def test_invalid_model_type(self):
        """Test that invalid model type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown model type"):
            create_parameter_grid('invalid_model')

    def test_rf_grid_structure(self):
        """Test that RF grid contains expected parameters."""
        grid = create_parameter_grid('random_forest')
        if len(grid) > 0:
            first_params = grid[0]
            assert 'n_estimators' in first_params
            assert 'max_depth' in first_params

    def test_en_grid_structure(self):
        """Test that Elastic Net grid contains expected parameters."""
        grid = create_parameter_grid('elastic_net')
        if len(grid) > 0:
            first_params = grid[0]
            assert 'alpha' in first_params
            assert 'l1_ratio' in first_params


class TestGridSearchExecution:
    """Tests for grid search execution."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n_samples = 100
        X = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'feature2': np.random.randn(n_samples),
            'feature3': np.random.randn(n_samples)
        })
        y = pd.Series(
            2 * X['feature1'] + 3 * X['feature2'] + np.random.randn(n_samples) * 0.5
        )
        return X, y

    @pytest.fixture
    def sample_data_with_uncertainty(self):
        """Create sample data with uncertainty for weighting."""
        X, y = self.sample_data(request.getfixturevalue('sample_data'))
        uncertainty = pd.Series(np.random.uniform(1, 10, len(y)))
        return X, y, uncertainty

    def test_rf_grid_search_completes(self, sample_data):
        """Test that RF grid search completes successfully."""
        X, y = sample_data
        results, model = run_grid_search(
            model_type='random_forest',
            X=X,
            y=y,
            cv_folds=3,  # Reduced for speed
            random_state=42
        )

        assert 'best_params' in results
        assert 'best_cv_r2' in results
        assert 'total_combinations_tested' in results
        assert results['total_combinations_tested'] <= MAX_COMBINATIONS
        assert model is not None

    def test_en_grid_search_with_weights(self, sample_data_with_uncertainty):
        """Test that Elastic Net grid search uses uncertainty weights."""
        X, y, uncertainty = sample_data_with_uncertainty
        results, model = run_grid_search(
            model_type='elastic_net',
            X=X,
            y=y,
            uncertainty=uncertainty,
            cv_folds=3,
            random_state=42
        )

        assert 'best_params' in results
        assert 'best_cv_r2' in results
        assert model is not None
        # Verify R² is reasonable (not -inf)
        assert results['best_cv_r2'] > -1.0

    def test_results_format(self, sample_data):
        """Test that results contain all required fields."""
        X, y = sample_data
        results, _ = run_grid_search(
            model_type='random_forest',
            X=X,
            y=y,
            cv_folds=3,
            random_state=42
        )

        required_fields = [
            'model_type', 'best_params', 'best_cv_r2',
            'total_combinations_tested', 'max_combinations_allowed', 'results'
        ]
        for field in required_fields:
            assert field in results, f"Missing required field: {field}"

    def test_combination_count_limit(self, sample_data):
        """Test that actual tested combinations never exceed MAX_COMBINATIONS."""
        X, y = sample_data
        results, _ = run_grid_search(
            model_type='random_forest',
            X=X,
            y=y,
            cv_folds=3,
            random_state=42
        )

        assert results['total_combinations_tested'] <= MAX_COMBINATIONS
        assert results['max_combinations_allowed'] == MAX_COMBINATIONS


class TestIntegration:
    """Integration tests for the full grid search workflow."""

    def test_all_models_run(self):
        """Test that all three model types can be run."""
        np.random.seed(42)
        n_samples = 50  # Small for speed
        X = pd.DataFrame({
            'f1': np.random.randn(n_samples),
            'f2': np.random.randn(n_samples)
        })
        y = pd.Series(np.random.randn(n_samples))

        models_to_test = ['random_forest', 'gradient_boosting', 'elastic_net']

        for model_type in models_to_test:
            results, model = run_grid_search(
                model_type=model_type,
                X=X,
                y=y,
                cv_folds=2,  # Minimal folds for speed
                random_state=42
            )
            assert model is not None, f"{model_type} model is None"
            assert 'best_params' in results
            assert results['total_combinations_tested'] <= MAX_COMBINATIONS


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
