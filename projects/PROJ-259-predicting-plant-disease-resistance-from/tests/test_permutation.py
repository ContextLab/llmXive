"""
Unit tests for permutation testing functionality.

Tests T033: Permutation testing on hold-out set
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
import pytest

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.permutation_test import (
    calculate_metric,
    run_permutation_test,
    calculate_p_value,
    permutation_test_pipeline
)


class TestCalculateMetric:
    """Tests for the calculate_metric function."""
    
    def test_accuracy_metric(self):
        """Test accuracy calculation."""
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 0, 0])
        
        score = calculate_metric(y_true, y_pred)
        assert 0.0 <= score <= 1.0
        assert score == 0.8  # 4 out of 5 correct
    
    def test_auc_metric(self):
        """Test AUC calculation with probabilities."""
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0.1, 0.9, 0.8, 0.2, 0.7])
        
        score = calculate_metric(y_true, y_pred)
        assert 0.5 <= score <= 1.0  # AUC should be between 0.5 and 1.0 for this case


class TestCalculatePValue:
    """Tests for the calculate_p_value function."""
    
    def test_p_value_greater_is_better(self):
        """Test p-value calculation when higher is better."""
        observed = 0.85
        permuted = np.array([0.70, 0.72, 0.75, 0.78, 0.80])
        
        p_value = calculate_p_value(observed, permuted, greater_is_better=True)
        
        # Observed is higher than all permuted, so p-value should be small
        # (count + 1) / (n + 1) = (0 + 1) / (5 + 1) = 1/6 ≈ 0.167
        assert 0.0 <= p_value <= 1.0
        assert p_value == pytest.approx(1/6, rel=1e-5)
    
    def test_p_value_lower_is_better(self):
        """Test p-value calculation when lower is better."""
        observed = 0.15
        permuted = np.array([0.20, 0.22, 0.25, 0.28, 0.30])
        
        p_value = calculate_p_value(observed, permuted, greater_is_better=False)
        
        # Observed is lower than all permuted
        assert 0.0 <= p_value <= 1.0
        assert p_value == pytest.approx(1/6, rel=1e-5)
    
    def test_p_value_observed_in_middle(self):
        """Test p-value when observed is in the middle of permuted distribution."""
        observed = 0.75
        permuted = np.array([0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90])
        
        p_value = calculate_p_value(observed, permuted, greater_is_better=True)
        
        # 3 values are >= 0.75 (0.75, 0.80, 0.85, 0.90)
        # (4 + 1) / (7 + 1) = 5/8 = 0.625
        assert 0.0 <= p_value <= 1.0
        assert p_value == pytest.approx(5/8, rel=1e-5)


class TestRunPermutationTest:
    """Tests for the run_permutation_test function."""
    
    def test_permutation_test_basic(self):
        """Test basic permutation test execution."""
        # Create a mock model
        mock_model = Mock()
        mock_model.predict_proba.return_value = np.array([[0.9, 0.1], [0.1, 0.9], [0.8, 0.2], [0.2, 0.8], [0.7, 0.3]])
        
        X_holdout = np.random.rand(5, 10)
        y_holdout = np.array([0, 1, 0, 1, 1])
        
        observed, perm_mean, perm_std, perm_metrics = run_permutation_test(
            mock_model,
            X_holdout,
            y_holdout,
            n_permutations=10,
            random_state=42
        )
        
        # Check that we got results
        assert observed > 0
        assert perm_mean > 0
        assert perm_std >= 0
        assert len(perm_metrics) == 10
        assert all(0 <= m <= 1 for m in perm_metrics)
    
    def test_permutation_test_reproducibility(self):
        """Test that permutation test is reproducible with random_state."""
        mock_model = Mock()
        mock_model.predict_proba.return_value = np.array([[0.9, 0.1], [0.1, 0.9], [0.8, 0.2], [0.2, 0.8], [0.7, 0.3]])
        
        X_holdout = np.random.rand(5, 10)
        y_holdout = np.array([0, 1, 0, 1, 1])
        
        # Run twice with same random state
        obs1, pm1, ps1, pm1_metrics = run_permutation_test(
            mock_model, X_holdout, y_holdout, n_permutations=20, random_state=123
        )
        
        obs2, pm2, ps2, pm2_metrics = run_permutation_test(
            mock_model, X_holdout, y_holdout, n_permutations=20, random_state=123
        )
        
        # Results should be identical
        assert obs1 == obs2
        assert pm1 == pm2
        assert ps1 == ps2
        np.testing.assert_array_equal(pm1_metrics, pm2_metrics)


class TestPermutationTestPipeline:
    """Tests for the full permutation test pipeline."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_pipeline_integration(self, temp_dir):
        """Test the full pipeline with mocked data."""
        # Create mock data files
        split_dir = temp_dir / "split"
        split_dir.mkdir()
        
        # Create mock split data
        mock_split_data = {
            'X_train': np.random.rand(80, 10),
            'y_train': np.random.randint(0, 2, 80),
            'X_holdout': np.random.rand(20, 10),
            'y_holdout': np.random.randint(0, 2, 20)
        }
        
        # Create a mock model
        mock_model = Mock()
        mock_model.predict_proba.return_value = np.random.rand(20, 2)
        
        # Mock the necessary functions
        with patch('analysis.permutation_test.load_split_data', return_value=mock_split_data), \
             patch('analysis.permutation_test.load_model', return_value=mock_model), \
             patch('analysis.permutation_test.get_path', side_effect=lambda config, key: temp_dir / key if key == 'model_path' else temp_dir):
            
            output_path = temp_dir / "holdout_metrics.json"
            
            results = permutation_test_pipeline(
                model_path=temp_dir / "model.pkl",
                split_dir=split_dir,
                output_path=output_path,
                n_permutations=50,
                random_state=42
            )
            
            # Check results structure
            assert 'observed_metric' in results
            assert 'p_value' in results
            assert 'success_criteria_met' in results
            assert 'n_permutations' in results
            
            # Check that output file was created
            assert output_path.exists()
            
            # Check file contents
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
            
            assert saved_results['observed_metric'] == results['observed_metric']
            assert saved_results['p_value'] == results['p_value']
            assert saved_results['n_permutations'] == 50