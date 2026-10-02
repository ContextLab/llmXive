"""
Unit tests for leave-one-out cross-validation logic.

This module tests the core logic of the cross-validation implementation
in code/robustness/cross_val.py, specifically:
- perform_leave_one_out: Iterating through runs and excluding one at a time
- perform_bootstrap_resampling: Fallback logic when runs < 3
- calculate_cv: Computing the coefficient of variation on results
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import json
from unittest.mock import patch, MagicMock, mock_open

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from robustness.cross_val import (
    CrossValIterationResult,
    perform_leave_one_out,
    perform_bootstrap_resampling,
    calculate_cv,
    load_harmonized_data
)
from data.models import HarmonizedDataset


class TestCrossValIterationResult:
    """Test the data structure for cross-validation iteration results."""

    def test_creation(self):
        """Test that CrossValIterationResult can be created with valid data."""
        result = CrossValIterationResult(
            iteration=0,
            excluded_run=0,
            alpha_upper_limit=0.5,
            bayes_factor=10.0,
            success=True
        )
        assert result.iteration == 0
        assert result.excluded_run == 0
        assert result.alpha_upper_limit == 0.5
        assert result.bayes_factor == 10.0
        assert result.success is True

    def test_creation_with_failure(self):
        """Test creation when iteration fails."""
        result = CrossValIterationResult(
            iteration=1,
            excluded_run=1,
            alpha_upper_limit=np.nan,
            bayes_factor=np.nan,
            success=False
        )
        assert result.success is False
        assert np.isnan(result.alpha_upper_limit)

class TestPerformLeaveOneOut:
    """Tests for the leave-one-out cross-validation logic."""

    @pytest.fixture
    def mock_harmonized_data(self):
        """Create a mock harmonized dataset with multiple runs."""
        # Create mock data for 3 independent runs
        runs_data = []
        for i in range(3):
            n_points = 50
            runs_data.append({
                'run_id': i,
                'separation_m': np.linspace(1e-4, 1e-3, n_points),
                'force_n': 1e-12 * np.ones(n_points),
                'uncertainty': 1e-14 * np.ones(n_points),
                'metadata': {'source': f'run_{i}'}
            })
        return runs_data

    @pytest.fixture
    def mock_inference_result(self):
        """Mock the inference result returned by run_single_inference."""
        return {
            'alpha_upper_limit': 0.5,
            'bayes_factor': 10.0,
            'success': True
        }

    def test_leave_one_out_with_three_runs(
        self, mock_harmonized_data, mock_inference_result
    ):
        """Test LOO works correctly when there are exactly 3 runs."""
        with patch(
            'robustness.cross_val.load_harmonized_data'
        ) as mock_load, \
             patch(
                 'robustness.cross_val.run_single_inference'
             ) as mock_inference:
            
            # Mock the loaded data
            mock_load.return_value = mock_harmonized_data
            mock_inference.return_value = mock_inference_result

            # Perform LOO
            results = perform_leave_one_out(mock_harmonized_data)

            # Should have 3 results (one for each excluded run)
            assert len(results) == 3

            # Check that each run was excluded exactly once
            excluded_runs = [r.excluded_run for r in results]
            assert sorted(excluded_runs) == [0, 1, 2]

            # Check that all results are successful
            assert all(r.success for r in results)
            assert all(r.alpha_upper_limit == 0.5 for r in results)

    def test_leave_one_out_with_two_runs_fallback(
        self, mock_harmonized_data
    ):
        """Test that LOO triggers bootstrap fallback when runs < 3."""
        # Modify mock data to have only 2 runs
        two_runs_data = mock_harmonized_data[:2]

        with patch(
            'robustness.cross_val.perform_bootstrap_resampling'
        ) as mock_bootstrap:
            mock_bootstrap.return_value = [
                CrossValIterationResult(
                    iteration=0, excluded_run=-1,
                    alpha_upper_limit=0.6, bayes_factor=8.0, success=True
                )
            ]

            results = perform_leave_one_out(two_runs_data)

            # Bootstrap should be called
            mock_bootstrap.assert_called_once()
            # Should return bootstrap results
            assert len(results) >= 1

    def test_leave_one_out_handles_inference_failure(
        self, mock_harmonized_data
    ):
        """Test that LOO handles failed inference iterations gracefully."""
        def failing_inference(*args, **kwargs):
            return {
                'alpha_upper_limit': np.nan,
                'bayes_factor': np.nan,
                'success': False
            }

        with patch(
            'robustness.cross_val.load_harmonized_data'
        ) as mock_load, \
             patch(
                 'robustness.cross_val.run_single_inference',
                 side_effect=failing_inference
             ) as mock_inference:
            
            mock_load.return_value = mock_harmonized_data

            results = perform_leave_one_out(mock_harmonized_data)

            # Should still have 3 results
            assert len(results) == 3
            # But all should be marked as failed
            assert all(not r.success for r in results)

class TestPerformBootstrapResampling:
    """Tests for bootstrap resampling fallback logic."""

    @pytest.fixture
    def sample_dataset(self):
        """Create a sample dataset for bootstrap testing."""
        n_points = 100
        return HarmonizedDataset(
            separation_m=np.linspace(1e-4, 1e-3, n_points),
            force_n=1e-12 * np.ones(n_points),
            covariance_matrix=np.eye(n_points) * (1e-14 ** 2),
            metadata={'source': 'test'}
        )

    def test_bootstrap_generates_correct_number_samples(
        self, sample_dataset
    ):
        """Test that bootstrap generates the requested number of samples."""
        n_bootstrap = 50
        
        with patch(
            'robustness.cross_val.run_single_inference'
        ) as mock_inference:
            mock_inference.return_value = {
                'alpha_upper_limit': 0.5,
                'bayes_factor': 10.0,
                'success': True
            }

            results = perform_bootstrap_resampling(
                sample_dataset, n_bootstrap=n_bootstrap
            )

            # Should generate exactly n_bootstrap results
            assert len(results) == n_bootstrap

    def test_bootstrap_with_failing_inference(
        self, sample_dataset
    ):
        """Test bootstrap handles inference failures."""
        call_count = [0]
        
        def occasional_fail(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 3 == 0:
                return {
                    'alpha_upper_limit': np.nan,
                    'bayes_factor': np.nan,
                    'success': False
                }
            return {
                'alpha_upper_limit': 0.5,
                'bayes_factor': 10.0,
                'success': True
            }

        with patch(
            'robustness.cross_val.run_single_inference',
            side_effect=occasional_fail
        ):
            results = perform_bootstrap_resampling(
                sample_dataset, n_bootstrap=30
            )

            # Should have 30 results total
            assert len(results) == 30
            # Some should be failures
            failure_count = sum(1 for r in results if not r.success)
            assert failure_count > 0

    def test_bootstrap_resamples_data_correctly(
        self, sample_dataset
    ):
        """Test that bootstrap actually resamples the data."""
        original_force = sample_dataset.force_n.copy()
        
        # Track if data was actually modified
        data_modified = False
        
        def check_data(*args, **kwargs):
            nonlocal data_modified
            if len(args) > 0:
                data_subset = args[0]
                # Check if the subset is different from original
                if not np.array_equal(data_subset.force_n, original_force):
                    data_modified = True
            return {
                'alpha_upper_limit': 0.5,
                'bayes_factor': 10.0,
                'success': True
            }

        with patch(
            'robustness.cross_val.run_single_inference',
            side_effect=check_data
        ):
            perform_bootstrap_resampling(sample_dataset, n_bootstrap=5)

        # Bootstrap should have modified the data
        assert data_modified

class TestCalculateCV:
    """Tests for coefficient of variation calculation."""

    def test_cv_calculation_basic(self):
        """Test basic CV calculation."""
        results = [
            CrossValIterationResult(0, 0, 0.5, 10.0, True),
            CrossValIterationResult(1, 1, 0.6, 12.0, True),
            CrossValIterationResult(2, 2, 0.7, 11.0, True),
        ]

        cv_value, relative_shift = calculate_cv(results)

        # Mean = (0.5 + 0.6 + 0.7) / 3 = 0.6
        # Std = sqrt(((0.5-0.6)^2 + (0.6-0.6)^2 + (0.7-0.6)^2) / 3) = sqrt(0.02/3) ≈ 0.0816
        # CV = (0.0816 / 0.6) * 100 ≈ 13.6%
        expected_mean = 0.6
        expected_std = np.std([0.5, 0.6, 0.7])
        expected_cv = (expected_std / expected_mean) * 100

        assert np.isclose(cv_value, expected_cv, rtol=1e-5)
        
        # Relative shift = (max - min) / mean = (0.7 - 0.5) / 0.6 ≈ 0.333
        expected_shift = (0.7 - 0.5) / 0.6
        assert np.isclose(relative_shift, expected_shift, rtol=1e-5)

    def test_cv_with_failed_iterations(self):
        """Test CV calculation ignores failed iterations."""
        results = [
            CrossValIterationResult(0, 0, 0.5, 10.0, True),
            CrossValIterationResult(1, 1, np.nan, np.nan, False),  # Failed
            CrossValIterationResult(2, 2, 0.7, 11.0, True),
        ]

        cv_value, relative_shift = calculate_cv(results)

        # Should only use the two successful iterations
        expected_mean = (0.5 + 0.7) / 2
        expected_std = np.std([0.5, 0.7])
        expected_cv = (expected_std / expected_mean) * 100

        assert np.isclose(cv_value, expected_cv, rtol=1e-5)

    def test_cv_with_all_failures(self):
        """Test CV calculation when all iterations fail."""
        results = [
            CrossValIterationResult(0, 0, np.nan, np.nan, False),
            CrossValIterationResult(1, 1, np.nan, np.nan, False),
        ]

        cv_value, relative_shift = calculate_cv(results)

        # Should return NaN for both
        assert np.isnan(cv_value)
        assert np.isnan(relative_shift)

    def test_cv_single_success(self):
        """Test CV calculation with only one successful iteration."""
        results = [
            CrossValIterationResult(0, 0, 0.5, 10.0, True),
        ]

        cv_value, relative_shift = calculate_cv(results)

        # With one value, std is 0, so CV should be 0
        assert cv_value == 0.0
        # Relative shift is also 0 (max=min)
        assert relative_shift == 0.0

    def test_cv_acceptance_criteria(self):
        """Test that CV calculation can be used for acceptance criteria."""
        # Create results that should pass (< 15% relative shift)
        passing_results = [
            CrossValIterationResult(0, 0, 0.5, 10.0, True),
            CrossValIterationResult(1, 1, 0.52, 10.5, True),
            CrossValIterationResult(2, 2, 0.48, 9.5, True),
        ]

        cv_value, relative_shift = calculate_cv(passing_results)
        assert relative_shift < 0.15

        # Create results that should fail (>= 15% relative shift)
        failing_results = [
            CrossValIterationResult(0, 0, 0.5, 10.0, True),
            CrossValIterationResult(1, 1, 0.8, 15.0, True),
            CrossValIterationResult(2, 2, 0.3, 5.0, True),
        ]

        cv_value, relative_shift = calculate_cv(failing_results)
        assert relative_shift >= 0.15

class TestIntegration:
    """Integration tests for the cross-validation pipeline."""

    def test_full_loo_pipeline(self):
        """Test the full LOO pipeline from data loading to CV calculation."""
        # Create realistic mock data
        n_runs = 3
        n_points_per_run = 100
        
        mock_data = []
        for i in range(n_runs):
            mock_data.append({
                'run_id': i,
                'separation_m': np.linspace(1e-4, 1e-3, n_points_per_run),
                'force_n': (1e-12 + 0.1 * i * 1e-13) * np.ones(n_points_per_run),
                'uncertainty': 1e-14 * np.ones(n_points_per_run),
                'metadata': {'source': f'run_{i}'}
            })

        with patch(
            'robustness.cross_val.load_harmonized_data'
        ) as mock_load, \
             patch(
                 'robustness.cross_val.run_single_inference'
             ) as mock_inference:
            
            mock_load.return_value = mock_data
            
            # Simulate slightly different results for each iteration
            def varying_inference(*args, **kwargs):
                excluded = kwargs.get('excluded_run', 0)
                return {
                    'alpha_upper_limit': 0.5 + 0.05 * excluded,
                    'bayes_factor': 10.0 + excluded,
                    'success': True
                }
            
            mock_inference.side_effect = varying_inference

            # Run LOO
            loo_results = perform_leave_one_out(mock_data)
            
            # Calculate CV
            cv_value, relative_shift = calculate_cv(loo_results)
            
            # Verify we got results
            assert len(loo_results) == n_runs
            assert all(r.success for r in loo_results)
            
            # Verify CV was calculated
            assert not np.isnan(cv_value)
            assert not np.isnan(relative_shift)
            
            # Verify the relative shift is reasonable
            # With our mock data, shift should be (0.7 - 0.5) / 0.6 ≈ 0.33
            assert relative_shift > 0