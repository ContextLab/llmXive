"""
Unit tests for code/analysis/split_half_validator.py
Covers validate, edge cases: convergence failure, N=1.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

from analysis.split_half_validator import (
    SplitHalfValidationError,
    validate_split_half,
    run_split_half_validation,
    main
)
from analysis.glm_fitter import fit_glm

class TestSplitHalfValidator:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_data(self):
        """Generate mock data for split-half validation."""
        np.random.seed(42)
        n_subjects = 20
        n_timepoints = 100
        n_rois = 5
        
        # Create data with a known effect
        # X: design matrix (timepoints x features)
        # Y: ROI time series (subjects x timepoints x rois)
        X = np.random.randn(n_timepoints, 3)
        Y = np.random.randn(n_subjects, n_timepoints, n_rois)
        
        # Inject a signal in the first ROI
        signal = np.sin(np.linspace(0, 4*np.pi, n_timepoints))
        Y[:, :, 0] += signal * 2.0
        
        return X, Y

    def test_validate_split_half_basic(self, sample_data):
        """Test basic split-half validation."""
        X, Y = sample_data
        
        # Mock the GLM fit to return a known result to avoid full pipeline dependency
        with patch('analysis.split_half_validator.fit_glm') as mock_fit:
            mock_result = {
                'coefficients': np.array([1.0, 0.5, 0.2]),
                'p_values': np.array([0.01, 0.5, 0.8]),
                'converged': True,
                'effect_size': 1.5
            }
            mock_fit.return_value = mock_result
            
            result = validate_split_half(X, Y, seed=42)
            
            assert result is not None
            assert 'training_effect_size' in result
            assert 'test_effect_size' in result
            assert 'replication_success' in result
            assert 'p_value' in result

    def test_validate_split_half_convergence_failure(self, sample_data):
        """Test validation when GLM fails to converge."""
        X, Y = sample_data
        
        with patch('analysis.split_half_validator.fit_glm') as mock_fit:
            # Simulate convergence failure
            mock_result = {
                'coefficients': np.array([0.0, 0.0, 0.0]),
                'p_values': np.array([1.0, 1.0, 1.0]),
                'converged': False,
                'effect_size': 0.0
            }
            mock_fit.return_value = mock_result
            
            result = validate_split_half(X, Y, seed=42)
            
            # The validator should detect non-convergence and mark replication as failure
            assert result['replication_success'] is False
            assert result['converged'] is False

    def test_validate_split_half_N_equals_1(self):
        """Test edge case: N=1 (single subject)."""
        np.random.seed(123)
        X = np.random.randn(100, 3)
        Y = np.random.randn(1, 100, 5)  # Only 1 subject
        
        # Split-half with N=1 is impossible (cannot split 1 subject into train/test)
        # The function should raise an error or handle it gracefully.
        # Assuming it raises a validation error.
        with pytest.raises(SplitHalfValidationError):
            validate_split_half(X, Y, seed=42)

    def test_validate_split_half_N_equals_2(self):
        """Test edge case: N=2 (minimum for split-half)."""
        np.random.seed(123)
        X = np.random.randn(100, 3)
        Y = np.random.randn(2, 100, 5)  # 2 subjects
        
        with patch('analysis.split_half_validator.fit_glm') as mock_fit:
            mock_result = {
                'coefficients': np.array([1.0, 0.5, 0.2]),
                'p_values': np.array([0.01, 0.5, 0.8]),
                'converged': True,
                'effect_size': 1.5
            }
            mock_fit.return_value = mock_result
            
            # With N=2, split is 1 train, 1 test
            result = validate_split_half(X, Y, seed=42)
            
            assert result is not None
            assert result['replication_success'] is not None

    def test_run_split_half_validation_loop(self, sample_data, temp_dir):
        """Test the full bootstrap loop."""
        X, Y = sample_data
        output_path = temp_dir / "validation_results.json"
        
        with patch('analysis.split_half_validator.fit_glm') as mock_fit:
            mock_result = {
                'coefficients': np.array([1.0, 0.5, 0.2]),
                'p_values': np.array([0.01, 0.5, 0.8]),
                'converged': True,
                'effect_size': 1.5
            }
            mock_fit.return_value = mock_result
            
            # Run a small loop (e.g., 5 iterations)
            results = run_split_half_validation(
                X, Y, 
                n_iterations=5, 
                sample_size=10,
                output_path=str(output_path),
                seed=42
            )
            
            assert len(results) == 5
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == 5

    def test_unreliable_flagging(self, sample_data, temp_dir):
        """Test that runs with >20% failure are flagged as Unreliable."""
        X, Y = sample_data
        output_path = temp_dir / "unreliable_results.json"
        
        call_count = 0
        def mock_fit_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Force failure on 50% of calls to trigger unreliable flag
            if call_count % 2 == 0:
                return {
                    'coefficients': np.array([0.0, 0.0, 0.0]),
                    'p_values': np.array([1.0, 1.0, 1.0]),
                    'converged': False,
                    'effect_size': 0.0
                }
            return {
                'coefficients': np.array([1.0, 0.5, 0.2]),
                'p_values': np.array([0.01, 0.5, 0.8]),
                'converged': True,
                'effect_size': 1.5
            }

        with patch('analysis.split_half_validator.fit_glm', side_effect=mock_fit_side_effect):
            results = run_split_half_validation(
                X, Y,
                n_iterations=10,
                sample_size=10,
                output_path=str(output_path),
                seed=42
            )
            
            # 50% failure rate -> should be flagged
            assert results['unreliable'] is True
            assert results['failure_rate'] > 0.2