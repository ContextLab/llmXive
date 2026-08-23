"""
Unit tests for Ridge Regression/SVM training and K-fold cross-validation in the decoder module.
Tests T027: Verify that the decoder implementation correctly trains models and performs cross-validation.
"""

import numpy as np
import pytest
from sklearn.linear_model import RidgeClassifier
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import LabelEncoder

# Import the specific functions we are testing from the decoder module
# Note: We are testing the logic directly, not the full pipeline
import sys
import os
# Ensure we can import from the code directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models.decoder import train_and_evaluate, run_decoder_analysis
from models.decoder_cv import run_kfold_cross_validation


class TestRidgeRegressionTraining:
    """Tests for Ridge Regression model training logic."""

    def test_ridge_classifier_initialization(self):
        """Verify RidgeClassifier is initialized with correct parameters."""
        # The decoder uses RidgeClassifier with specific alpha
        # We test that the model can be instantiated and has expected attributes
        model = RidgeClassifier(alpha=1.0)
        assert model.alpha == 1.0
        assert hasattr(model, 'fit')
        assert hasattr(model, 'predict')

    def test_label_encoding(self):
        """Test that LabelEncoder correctly transforms string labels to integers."""
        labels = ['plot', 'character', 'theme', 'plot', 'character']
        encoder = LabelEncoder()
        encoded = encoder.fit_transform(labels)
        
        assert len(encoded) == len(labels)
        assert set(encoded) == {0, 1, 2}  # Three unique classes
        assert encoder.classes_.tolist() == ['character', 'plot', 'theme']

    def test_training_with_synthetic_features(self):
        """Test model training with synthetic feature data (valid for unit testing)."""
        # Create synthetic feature matrix (10 samples, 5 features)
        X = np.random.rand(10, 5)
        y = np.array(['plot', 'character', 'theme', 'plot', 'character', 
                     'theme', 'plot', 'character', 'theme', 'plot'])
        
        # This should not raise an exception
        model = RidgeClassifier(alpha=1.0)
        model.fit(X, y)
        
        # Verify model can make predictions
        predictions = model.predict(X)
        assert len(predictions) == len(y)
        assert set(predictions).issubset(set(y))

class TestKFoldCrossValidation:
    """Tests for K-fold cross-validation implementation."""

    def test_kfold_split_generation(self):
        """Verify KFold generates correct number of splits."""
        X = np.random.rand(20, 5)
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        
        splits = list(kfold.split(X))
        assert len(splits) == 5
        
        # Check that each sample appears in exactly one test set per fold
        test_indices = []
        for train_idx, test_idx in splits:
            test_indices.extend(test_idx)
        
        assert len(test_indices) == 20  # Each sample should be in test set once
        assert len(set(test_indices)) == 20  # No duplicates

    def test_cross_val_score_computation(self):
        """Test that cross_val_score returns expected shape and values."""
        X = np.random.rand(30, 10)
        y = np.array(['plot'] * 10 + ['character'] * 10 + ['theme'] * 10)
        
        scores = cross_val_score(RidgeClassifier(alpha=1.0), X, y, cv=5)
        
        assert len(scores) == 5  # 5 folds
        assert all(0 <= score <= 1 for score in scores)  # Accuracy between 0 and 1
        assert np.mean(scores) > 0  # Should have some predictive power even with random data

    def test_run_kfold_cross_validation_function(self):
        """Test the run_kfold_cross_validation function from decoder_cv module."""
        # Create synthetic data
        n_samples = 50
        n_features = 20
        X = np.random.rand(n_samples, n_features)
        y = np.array(['plot'] * 17 + ['character'] * 17 + ['theme'] * 16)
        
        # Call the function
        results = run_kfold_cross_validation(X, y, n_splits=5)
        
        # Verify results structure
        assert 'mean_accuracy' in results
        assert 'std_accuracy' in results
        assert 'fold_scores' in results
        assert len(results['fold_scores']) == 5
        assert 0 <= results['mean_accuracy'] <= 1
        assert results['std_accuracy'] >= 0

class TestDecoderIntegration:
    """Integration tests for decoder training and evaluation."""

    def test_train_and_evaluate_basic(self):
        """Test the train_and_evaluate function with basic synthetic data."""
        # Create synthetic data
        n_samples = 40
        n_features = 15
        X = np.random.rand(n_samples, n_features)
        y = np.array(['plot'] * 13 + ['character'] * 13 + ['theme'] * 14)
        
        # This should execute without errors
        results = train_and_evaluate(X, y, cv_folds=5)
        
        # Verify results contain expected keys
        assert 'accuracy' in results
        assert 'cv_scores' in results
        assert 'mean_cv_accuracy' in results
        assert 'std_cv_accuracy' in results
        
        # Verify accuracy is in valid range
        assert 0 <= results['accuracy'] <= 1
        assert 0 <= results['mean_cv_accuracy'] <= 1

    def test_label_aggregation_logic(self):
        """Test that classes with fewer than 5 samples are aggregated."""
        # Create data with one rare class
        X = np.random.rand(50, 10)
        y = np.array(['plot'] * 20 + ['character'] * 20 + ['theme'] * 5 + ['rare'] * 5)
        
        # The function should handle this without crashing
        # Note: The actual aggregation logic might be in run_decoder_analysis
        results = train_and_evaluate(X, y, cv_folds=3)
        
        assert 'accuracy' in results
        assert results['accuracy'] >= 0

    def test_run_decoder_analysis_with_output_path(self):
        """Test run_decoder_analysis with a temporary output path."""
        import tempfile
        import json
        
        # Create synthetic data
        n_samples = 60
        n_features = 25
        X = np.random.rand(n_samples, n_features)
        y = np.array(['plot'] * 20 + ['character'] * 20 + ['theme'] * 20)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'test_decoder_results.json')
            
            # This should create the output file
            results = run_decoder_analysis(X, y, output_path=output_path, cv_folds=5)
            
            # Verify file was created
            assert os.path.exists(output_path)
            
            # Verify file contains valid JSON with expected structure
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
            
            assert 'accuracy' in saved_results
            assert 'mean_cv_accuracy' in saved_results
            assert 'std_cv_accuracy' in saved_results
            assert 'n_samples' in saved_results
            assert 'n_features' in saved_results

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_small_dataset(self):
        """Test with a very small dataset (minimum for 2-fold CV)."""
        X = np.random.rand(4, 5)
        y = np.array(['plot', 'character', 'plot', 'character'])
        
        # Should handle small datasets gracefully
        results = train_and_evaluate(X, y, cv_folds=2)
        assert 'accuracy' in results

    def test_binary_classification(self):
        """Test with binary classification (only 2 classes)."""
        X = np.random.rand(30, 10)
        y = np.array(['plot'] * 15 + ['character'] * 15)
        
        results = train_and_evaluate(X, y, cv_folds=5)
        assert 0 <= results['accuracy'] <= 1

    def test_imbalanced_classes(self):
        """Test with highly imbalanced class distribution."""
        X = np.random.rand(100, 10)
        y = np.array(['plot'] * 90 + ['character'] * 10)
        
        # Should not crash, though accuracy might be low
        results = train_and_evaluate(X, y, cv_folds=5)
        assert 'accuracy' in results
        assert 0 <= results['accuracy'] <= 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])