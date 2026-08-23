"""
Unit tests for K-fold cross-validation implementation (T031).
"""
import pytest
import numpy as np
from code.models.decoder_cv import run_kfold_cross_validation

def test_kfold_basic_functionality():
    """Test that cross-validation runs and produces expected output structure."""
    # Create synthetic test data
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = np.array(['A'] * 50 + ['B'] * 50)
    
    results = run_kfold_cross_validation(X, y, n_splits=5)
    
    # Verify result structure
    assert 'mean_accuracy' in results
    assert 'std_accuracy' in results
    assert 'chance_baseline' in results
    assert 'fold_scores' in results
    assert 'n_classes' in results
    
    # Verify numerical properties
    assert 0 <= results['mean_accuracy'] <= 1
    assert results['n_classes'] == 2
    assert results['chance_baseline'] == 0.5
    assert len(results['fold_scores']) == 5

def test_kfold_with_imbalanced_classes():
    """Test cross-validation with imbalanced class distribution."""
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = np.array(['A'] * 80 + ['B'] * 20)
    
    results = run_kfold_cross_validation(X, y, n_splits=5)
    
    # Chance baseline should be 1/2 = 0.5 for 2 classes
    assert results['n_classes'] == 2
    assert results['chance_baseline'] == 0.5

def test_kfold_single_class():
    """Test behavior with single class (edge case)."""
    np.random.seed(42)
    X = np.random.randn(20, 5)
    y = np.array(['A'] * 20)
    
    results = run_kfold_cross_validation(X, y, n_splits=5)
    
    # With single class, accuracy should be 1.0 and chance baseline 1.0
    assert results['n_classes'] == 1
    assert results['chance_baseline'] == 1.0
    assert results['mean_accuracy'] == 1.0

def test_kfold_fold_scores_consistency():
    """Test that fold scores are consistent with mean accuracy."""
    np.random.seed(42)
    X = np.random.randn(60, 8)
    y = np.array(['A'] * 30 + ['B'] * 30)
    
    results = run_kfold_cross_validation(X, y, n_splits=5)
    
    # Verify mean accuracy matches average of fold scores
    expected_mean = np.mean(results['fold_scores'])
    assert np.isclose(results['mean_accuracy'], expected_mean)
    
    # Verify standard deviation
    expected_std = np.std(results['fold_scores'])
    assert np.isclose(results['std_accuracy'], expected_std)

def test_kfold_deviation_calculation():
    """Test that deviation from chance is calculated correctly."""
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = np.array(['A'] * 50 + ['B'] * 50)
    
    results = run_kfold_cross_validation(X, y, n_splits=5)
    
    expected_deviation = results['mean_accuracy'] - results['chance_baseline']
    assert np.isclose(results['deviation_from_chance'], expected_deviation)
    
    # Verify improvement flag
    expected_improvement = results['deviation_from_chance'] > 0
    assert results['improvement_over_chance'] == expected_improvement