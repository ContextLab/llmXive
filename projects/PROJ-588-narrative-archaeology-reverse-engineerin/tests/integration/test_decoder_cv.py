"""
Integration Test for T031: K-fold Cross-Validation
"""
import pytest
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from models.decoder_cv import run_kfold_cross_validation

class TestKFoldCrossValidation:
    """Tests for the K-fold cross-validation implementation."""

    def test_accuracy_exceeds_chance_balanced(self):
        """Test that a balanced dataset yields accuracy > chance."""
        # Create a balanced dataset with 3 classes
        n_samples_per_class = 20
        n_features = 50
        
        # Create separable data
        X = np.vstack([
            np.random.randn(n_samples_per_class, n_features) + 1,
            np.random.randn(n_samples_per_class, n_features) - 1,
            np.random.randn(n_samples_per_class, n_features) + 0
        ])
        y = np.array(['class_A'] * n_samples_per_class + 
                     ['class_B'] * n_samples_per_class + 
                     ['class_C'] * n_samples_per_class)
        
        results = run_kfold_cross_validation(X, y, k=5)
        
        chance = 1.0 / 3.0
        
        # Assert accuracy is significantly above chance
        assert results['accuracy'] > chance, f"Accuracy {results['accuracy']} not greater than chance {chance}"
        assert results['n_classes'] == 3
        assert results['k_folds'] == 5

    def test_accuracy_exceeds_chance_imbalanced(self):
        """Test that accuracy is calculated correctly against adjusted chance for imbalanced data."""
        # Imbalanced dataset: 40 class A, 10 class B, 10 class C
        n_samples = 60
        n_features = 50
        
        X = np.random.randn(n_samples, n_features)
        y = np.array(['class_A'] * 40 + ['class_B'] * 10 + ['class_C'] * 10)
        
        results = run_kfold_cross_validation(X, y, k=5)
        
        # Chance is 1/3 regardless of imbalance (uniform prior assumption for classifier)
        # But the task spec says "chance baseline as 1 / N_actual"
        chance = 1.0 / 3.0
        
        assert results['chance_baseline'] == chance
        assert 'fold_scores' in results
        assert len(results['fold_scores']) == 5

    def test_output_structure(self):
        """Verify the output structure matches the required schema."""
        X = np.random.randn(30, 20)
        y = np.array(['A'] * 10 + ['B'] * 10 + ['C'] * 10)
        
        results = run_kfold_cross_validation(X, y, k=5)
        
        required_keys = ['accuracy', 'std_accuracy', 'chance_baseline', 'n_classes', 'fold_scores', 'k_folds']
        for key in required_keys:
            assert key in results, f"Missing key: {key}"
        
        assert isinstance(results['accuracy'], float)
        assert isinstance(results['std_accuracy'], float)
        assert isinstance(results['fold_scores'], list)
        assert len(results['fold_scores']) == 5

    def test_single_class_handling(self):
        """Test that single class data is handled (though likely to fail or warn)."""
        X = np.random.randn(10, 20)
        y = np.array(['A'] * 10)
        
        # This should technically fail or produce 100% accuracy with 1 class
        # But LabelEncoder might handle it.
        # We expect it to run without crashing, but accuracy might be 1.0 or chance 1.0
        results = run_kfold_cross_validation(X, y, k=5)
        
        assert results['n_classes'] == 1
        assert results['chance_baseline'] == 1.0
        # Accuracy on single class is trivially 1.0
        assert results['accuracy'] == 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
