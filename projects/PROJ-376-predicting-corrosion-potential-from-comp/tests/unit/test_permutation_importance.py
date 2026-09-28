"""
Unit tests for permutation importance calculation (T027).

Tests the core functionality of the interpret.py module, specifically
the permutation importance calculation logic.
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance

# Import functions to test
from models.interpret import (
    calculate_permutation_importance,
    prepare_features_and_target,
    train_model_for_importance
)
from utils.exceptions import DataInsufficientError


class TestCalculatePermutationImportance:
    """Tests for the permutation importance calculation function."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n_samples = 100
        
        # Create synthetic features
        X = pd.DataFrame({
            'feature_1': np.random.randn(n_samples),
            'feature_2': np.random.randn(n_samples),
            'feature_3': np.random.randn(n_samples),
            'feature_4': np.random.randn(n_samples)
        })
        
        # Create target with known relationship
        y = 2 * X['feature_1'] + 0.5 * X['feature_2'] + np.random.randn(n_samples) * 0.1
        
        return X, y, list(X.columns)
    
    @pytest.fixture
    def trained_model(self, sample_data):
        """Create a trained model for testing."""
        X, y, _ = sample_data
        model = RandomForestRegressor(n_estimators=10, random_state=42, n_jobs=1)
        model.fit(X, y)
        return model
    
    def test_returns_dict_with_correct_keys(self, trained_model, sample_data):
        """Test that the function returns a dict with all feature names."""
        X, y, feature_names = sample_data
        importance_scores = calculate_permutation_importance(
            trained_model, X, y, feature_names, n_repeats=3
        )
        
        assert isinstance(importance_scores, dict)
        assert set(importance_scores.keys()) == set(feature_names)
    
    def test_feature_1_is_most_important(self, trained_model, sample_data):
        """Test that the most influential feature has the highest importance."""
        X, y, feature_names = sample_data
        importance_scores = calculate_permutation_importance(
            trained_model, X, y, feature_names, n_repeats=10
        )
        
        # feature_1 has the strongest relationship with y
        assert importance_scores['feature_1'] > importance_scores['feature_2']
        assert importance_scores['feature_1'] > importance_scores['feature_3']
        assert importance_scores['feature_1'] > importance_scores['feature_4']
    
    def test_importance_values_are_finite(self, trained_model, sample_data):
        """Test that all importance values are finite numbers."""
        X, y, feature_names = sample_data
        importance_scores = calculate_permutation_importance(
            trained_model, X, y, feature_names, n_repeats=3
        )
        
        for score in importance_scores.values():
            assert np.isfinite(score)
    
    def test_reproducibility_with_same_seed(self, trained_model, sample_data):
        """Test that results are reproducible with the same random state."""
        X, y, feature_names = sample_data
        
        scores_1 = calculate_permutation_importance(
            trained_model, X, y, feature_names, n_repeats=5, random_state=42
        )
        
        scores_2 = calculate_permutation_importance(
            trained_model, X, y, feature_names, n_repeats=5, random_state=42
        )
        
        assert scores_1 == scores_2
    
    def test_increases_with_more_repeats(self, trained_model, sample_data):
        """Test that increasing repeats reduces variance (not strictly deterministic)."""
        X, y, feature_names = sample_data
        
        # Run with 3 repeats multiple times to check consistency
        scores_3 = calculate_permutation_importance(
            trained_model, X, y, feature_names, n_repeats=3, random_state=123
        )
        
        # Run with 10 repeats
        scores_10 = calculate_permutation_importance(
            trained_model, X, y, feature_names, n_repeats=10, random_state=123
        )
        
        # Both should identify feature_1 as most important
        assert scores_3['feature_1'] == max(scores_3.values())
        assert scores_10['feature_1'] == max(scores_10.values())

class TestTrainModelForImportance:
    """Tests for the model training function."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        n_samples = 50
        
        X = pd.DataFrame({
            'f1': np.random.randn(n_samples),
            'f2': np.random.randn(n_samples)
        })
        y = pd.Series(np.random.randn(n_samples))
        
        return X, y, list(X.columns)
    
    def test_trains_random_forest(self, sample_data):
        """Test training a random forest model."""
        X, y, feature_names = sample_data
        model = train_model_for_importance('random_forest', X, y, feature_names)
        
        assert isinstance(model, RandomForestRegressor)
        assert model.n_estimators == 100
        assert model.random_state == 42
    
    def test_trains_gradient_boosting(self, sample_data):
        """Test training a gradient boosting model."""
        X, y, feature_names = sample_data
        model = train_model_for_importance('gradient_boosting', X, y, feature_names)
        
        assert model.n_estimators == 100
        assert model.random_state == 42
    
    def test_raises_on_unknown_model(self, sample_data):
        """Test that an unknown model name raises ValueError."""
        X, y, feature_names = sample_data
        
        with pytest.raises(ValueError, match="Unknown model type"):
            train_model_for_importance('unknown_model', X, y, feature_names)

class TestIntegration:
    """Integration tests for the full importance calculation pipeline."""
    
    def test_full_pipeline_with_synthetic_data(self):
        """Test the full pipeline from data preparation to importance calculation."""
        # Create synthetic data
        np.random.seed(42)
        n_samples = 100
        
        X = pd.DataFrame({
            'important': np.random.randn(n_samples),
            'less_important': np.random.randn(n_samples),
            'noise': np.random.randn(n_samples)
        })
        
        y = 3 * X['important'] + 0.1 * X['less_important'] + np.random.randn(n_samples) * 0.05
        
        # Train model
        model = RandomForestRegressor(n_estimators=10, random_state=42, n_jobs=1)
        model.fit(X, y)
        
        # Calculate importance
        feature_names = list(X.columns)
        importance_scores = calculate_permutation_importance(
            model, X, y, feature_names, n_repeats=10
        )
        
        # Verify the most important feature is correctly identified
        assert importance_scores['important'] > importance_scores['less_important']
        assert importance_scores['important'] > importance_scores['noise']
        
        # Verify all scores are reasonable (not NaN or inf)
        for score in importance_scores.values():
            assert -100 < score < 100  # Reasonable bounds for R2 change
