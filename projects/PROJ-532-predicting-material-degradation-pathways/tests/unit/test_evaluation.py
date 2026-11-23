import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

from evaluation import calculate_macro_f1, generate_stratified_baseline, perform_permutation_test

class TestMacroF1:
    def test_calculate_macro_f1_basic(self):
        """Test basic macro-F1 calculation."""
        y_true = np.array([[1, 0, 1], [0, 1, 0], [1, 1, 0]])
        y_pred = np.array([[1, 0, 1], [0, 1, 1], [1, 0, 0]])
        
        f1 = calculate_macro_f1(y_true, y_pred)
        assert 0.0 <= f1 <= 1.0
        
    def test_calculate_macro_f1_perfect(self):
        """Test perfect predictions."""
        y_true = np.array([[1, 0, 1], [0, 1, 0]])
        y_pred = np.array([[1, 0, 1], [0, 1, 0]])
        
        f1 = calculate_macro_f1(y_true, y_pred)
        assert f1 == 1.0

class TestStratifiedBaseline:
    def test_baseline_preserves_shape(self):
        """Test that baseline preserves input shape."""
        y_true = np.array([[1, 0, 1], [0, 1, 0], [1, 1, 0]])
        y_baseline = generate_stratified_baseline(y_true, random_state=42)
        
        assert y_baseline.shape == y_true.shape
        
    def test_baseline_is_permutation(self):
        """Test that baseline is a permutation of original."""
        y_true = np.array([[1, 0, 1], [0, 1, 0], [1, 1, 0]])
        y_baseline = generate_stratified_baseline(y_true, random_state=42)
        
        # Sort and compare to ensure same elements
        assert np.all(np.sort(y_baseline, axis=0).flatten() == np.sort(y_true, axis=0).flatten())

class TestPermutationTest:
    def test_permutation_test_p_value_range(self):
        """Test that p-value is in valid range."""
        y_true = np.random.randint(0, 2, (50, 3))
        y_pred = np.random.randint(0, 2, (50, 3))
        
        p_value = perform_permutation_test(y_true, y_pred, n_iterations=100, random_state=42)
        assert 0.0 <= p_value <= 1.0
        
    def test_permutation_test_deterministic(self):
        """Test that permutation test is deterministic with same seed."""
        y_true = np.random.randint(0, 2, (50, 3))
        y_pred = np.random.randint(0, 2, (50, 3))
        
        p1 = perform_permutation_test(y_true, y_pred, n_iterations=100, random_state=42)
        p2 = perform_permutation_test(y_true, y_pred, n_iterations=100, random_state=42)
        
        assert p1 == p2