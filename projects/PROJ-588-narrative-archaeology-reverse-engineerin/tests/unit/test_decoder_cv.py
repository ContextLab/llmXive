"""
Unit tests for T031: K-Fold Cross-Validation implementation.
"""
import pytest
import numpy as np
import json
from pathlib import Path
import sys

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.decoder_cv import run_kfold_cross_validation, load_roi_features_and_labels

class TestDecoderCV:
    """Tests for the K-Fold Cross-Validation logic."""

    def test_chance_baseline_calculation(self):
        """Verify that chance baseline is correctly calculated as 1/N."""
        # Create synthetic data with 4 classes
        n_samples = 100
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        y = np.array([0, 1, 2, 3] * 25) # 4 classes
        
        results = run_kfold_cross_validation(X, y, k=5, random_state=42)
        
        expected_chance = 1.0 / 4.0
        assert abs(results['chance_baseline'] - expected_chance) < 1e-6, \
            f"Chance baseline should be {expected_chance}, got {results['chance_baseline']}"
    
    def test_kfold_structure(self):
        """Verify that K-Fold returns correct structure."""
        n_samples = 50
        n_features = 5
        X = np.random.randn(n_samples, n_features)
        y = np.array([0, 1, 0, 1] * 12 + [0, 1]) # Binary
        
        results = run_kfold_cross_validation(X, y, k=5, random_state=42)
        
        assert 'k_folds' in results
        assert 'mean_accuracy' in results
        assert 'std_accuracy' in results
        assert 'fold_scores' in results
        assert len(results['fold_scores']) == 5
        assert 'deviation_from_chance' in results
    
    def test_accuracy_range(self):
        """Verify that accuracy is between 0 and 1."""
        n_samples = 50
        n_features = 5
        X = np.random.randn(n_samples, n_features)
        y = np.array([0, 1] * 25)
        
        results = run_kfold_cross_validation(X, y, k=5)
        
        assert 0.0 <= results['mean_accuracy'] <= 1.0, \
            f"Accuracy {results['mean_accuracy']} out of range [0, 1]"
    
    def test_fold_count(self):
        """Verify that the number of fold scores matches K."""
        for k in [3, 5, 10]:
            n_samples = 100
            n_features = 5
            X = np.random.randn(n_samples, n_features)
            y = np.array([0, 1, 2] * 33 + [0])
            
            results = run_kfold_cross_validation(X, y, k=k)
            assert len(results['fold_scores']) == k, \
                f"Expected {k} fold scores, got {len(results['fold_scores'])}"
    
    def test_reproducibility(self):
        """Verify that results are reproducible with same random_state."""
        n_samples = 50
        n_features = 5
        X = np.random.randn(n_samples, n_features)
        y = np.array([0, 1] * 25)
        
        res1 = run_kfold_cross_validation(X, y, k=5, random_state=42)
        res2 = run_kfold_cross_validation(X, y, k=5, random_state=42)
        
        assert res1['mean_accuracy'] == res2['mean_accuracy'], \
            "Results should be identical with same random_state"
        assert res1['fold_scores'] == res2['fold_scores'], \
            "Fold scores should be identical with same random_state"
    
    def test_label_encoder_integration(self):
        """Verify that label encoding works correctly with CV."""
        # This test ensures the logic handles integer labels correctly
        # (which is what LabelEncoder produces)
        n_samples = 40
        n_features = 5
        X = np.random.randn(n_samples, n_features)
        # Use non-contiguous labels to ensure encoding is robust
        y = np.array([0, 5, 10, 15] * 10) 
        
        results = run_kfold_cross_validation(X, y, k=4)
        
        assert results['n_classes'] == 4
        assert results['chance_baseline'] == 0.25

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
