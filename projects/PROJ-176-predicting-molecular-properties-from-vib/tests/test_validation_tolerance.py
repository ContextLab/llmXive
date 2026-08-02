import os
import json
import tempfile
import numpy as np
import torch
from pathlib import Path
import pytest

# Mock the model import for testing
from unittest.mock import MagicMock, patch

# Import the functions to test
from evaluation.validate import compute_validation_metrics, MAE_TOLERANCE_FACTOR

class TestValidationTolerance:
    def test_mae_within_tolerance(self):
        """Test that MAE within 20% of test MAE is not flagged."""
        y_true = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        y_pred = np.array([[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]])
        
        test_metrics = {
            'dipole': {'mae': 0.1},
            'polarizability': {'mae': 0.1},
            'homo_lumo_gap': {'mae': 0.1}
        }
        
        results = compute_validation_metrics(y_true, y_pred, test_metrics)
        
        assert results['dipole']['exceeds_tolerance'] == False
        assert results['polarizability']['exceeds_tolerance'] == False
        assert results['homo_lumo_gap']['exceeds_tolerance'] == False

    def test_mae_exceeds_tolerance(self):
        """Test that MAE > 20% of test MAE is flagged."""
        # Create data where MAE is significantly higher
        y_true = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        # Predictions with large error
        y_pred = np.array([[1.5, 2.5, 3.5], [4.5, 5.5, 6.5]])
        
        test_metrics = {
            'dipole': {'mae': 0.1},
            'polarizability': {'mae': 0.1},
            'homo_lumo_gap': {'mae': 0.1}
        }
        
        results = compute_validation_metrics(y_true, y_pred, test_metrics)
        
        # Calculate expected MAE: mean(|1.0-1.5|, |1.5-4.5|...) -> approx 0.5
        # Threshold: 0.1 * 1.2 = 0.12
        # 0.5 > 0.12 -> should exceed
        assert results['dipole']['exceeds_tolerance'] == True
        assert results['polarizability']['exceeds_tolerance'] == True
        assert results['homo_lumo_gap']['exceeds_tolerance'] == True

    def test_mae_exactly_at_tolerance(self):
        """Test behavior when MAE is exactly at the tolerance threshold."""
        y_true = np.array([[1.0], [2.0]])
        # MAE = 0.12 exactly
        y_pred = np.array([[1.12], [2.12]])
        
        test_metrics = {
            'dipole': {'mae': 0.1}
        }
        
        results = compute_validation_metrics(y_true, y_pred, test_metrics)
        
        # Threshold is 0.12. If MAE is 0.12, is it > 0.12? No.
        # So it should be False (within tolerance)
        # The condition is `mae > tolerance_threshold`
        assert results['dipole']['exceeds_tolerance'] == False

    def test_missing_test_metrics(self):
        """Test that missing test metrics results in None for tolerance flags."""
        y_true = np.array([[1.0]])
        y_pred = np.array([[1.1]])
        
        test_metrics = {} # Empty
        
        results = compute_validation_metrics(y_true, y_pred, test_metrics)
        
        assert results['dipole']['exceeds_tolerance'] == None
        assert results['dipole']['test_mae'] == None
        assert results['dipole']['tolerance_threshold'] == None

    def test_output_json_structure(self):
        """Verify the structure of the output JSON dictionary."""
        y_true = np.array([[1.0, 2.0, 3.0]])
        y_pred = np.array([[1.1, 2.1, 3.1]])
        test_metrics = {
            'dipole': {'mae': 0.1},
            'polarizability': {'mae': 0.1},
            'homo_lumo_gap': {'mae': 0.1}
        }
        
        results = compute_validation_metrics(y_true, y_pred, test_metrics)
        
        # Check required keys
        assert 'dipole' in results
        assert 'polarizability' in results
        assert 'homo_lumo_gap' in results
        assert 'summary' in results
        
        # Check sub-keys
        for prop in ['dipole', 'polarizability', 'homo_lumo_gap']:
            assert 'mae' in results[prop]
            assert 'r2' in results[prop]
            assert 'exceeds_tolerance' in results[prop]
            assert 'test_mae' in results[prop]
            assert 'tolerance_threshold' in results[prop]
        
        # Check summary
        assert 'avg_mae' in results['summary']
        assert 'max_mae_increase_ratio' in results['summary']