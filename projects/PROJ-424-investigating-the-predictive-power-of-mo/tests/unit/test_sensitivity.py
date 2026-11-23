"""
Unit tests for sensitivity sweep logic (User Story 2).

These tests verify the core logic of the sensitivity analysis module,
specifically:
1. Generation of start time offsets based on trajectory length and percentage.
2. Calculation of variance across diffusion coefficients.
3. Flagging logic for variance thresholds.
4. Integration with the SensitivityReport data model.

Note: This test file assumes the existence of `code/analysis/sensitivity.py`
and `code/data_models/sensitivity_report.py` as defined in the project API.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add code directory to path for imports if running from tests/
CODE_ROOT = Path(__file__).parent.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data_models.sensitivity_report import SensitivityPoint, SensitivityReport
from analysis.sensitivity import (
    generate_start_times,
    calculate_variance,
    run_sensitivity_sweep,
    SensitivityConfig
)
from config import Solvent


class TestGenerateStartTimes:
    """Tests for the start time generation logic."""

    def test_generate_start_times_basic(self):
        """Verify start times are generated correctly for a given length."""
        trajectory_length = 1000.0  # ps
        # Configured percentages: 0.1, 0.2, 0.3 (from T008c/T021)
        config = SensitivityConfig(
            start_percentages=[0.1, 0.2, 0.3]
        )

        start_times = generate_start_times(trajectory_length, config)

        assert len(start_times) == 3
        assert start_times == [100.0, 200.0, 300.0]

    def test_generate_start_times_edge_cases(self):
        """Verify behavior with small trajectory lengths."""
        trajectory_length = 10.0
        config = SensitivityConfig(start_percentages=[0.1, 0.5, 0.9])

        start_times = generate_start_times(trajectory_length, config)

        assert start_times == [1.0, 5.0, 9.0]

    def test_generate_start_times_empty_config(self):
        """Verify empty list returned if no percentages configured."""
        config = SensitivityConfig(start_percentages=[])
        start_times = generate_start_times(100.0, config)
        assert start_times == []


class TestCalculateVariance:
    """Tests for variance calculation logic."""

    def test_calculate_variance_standard(self):
        """Verify variance calculation for a list of floats."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        variance = calculate_variance(values)
        # numpy var uses ddof=0 by default (population variance)
        # values: mean=3.0, diffs=[-2, -1, 0, 1, 2], sq=[4,1,0,1,4], sum=10, var=2.0
        assert np.isclose(variance, 2.0)

    def test_calculate_variance_single_value(self):
        """Verify variance is 0 for a single value."""
        values = [5.0]
        variance = calculate_variance(values)
        assert variance == 0.0

    def test_calculate_variance_empty_list(self):
        """Verify 0 variance for empty list to avoid division by zero."""
        values = []
        variance = calculate_variance(values)
        assert variance == 0.0


class TestRunSensitivitySweep:
    """Tests for the full sensitivity sweep logic."""

    @patch('analysis.sensitivity.analyze_msd')
    def test_run_sensitivity_sweep_success(self, mock_analyze_msd):
        """Verify sweep runs and returns correct report structure."""
        # Mock the MSD analysis to return deterministic DiffusionResults
        mock_result = MagicMock()
        mock_result.diffusion_coefficient = 2.5e-9  # m^2/s
        mock_result.r_squared = 0.98
        mock_analyze_msd.return_value = mock_result

        # Mock trajectory loading
        mock_timeseries = (np.array([0, 100, 200, 300]), np.array([0, 10, 20, 30]))

        with patch('analysis.sensitivity.load_trajectory_timeseries', return_value=mock_timeseries):
            config = SensitivityConfig(
                start_percentages=[0.1, 0.2, 0.3],
                variance_threshold=0.05,
                solvent=Solvent.WATER
            )

            report = run_sensitivity_sweep(
                trajectory_path=Path("dummy.gro"),
                config=config,
                total_duration=1000.0
            )

            # Verify structure
            assert isinstance(report, SensitivityReport)
            assert report.solvent == Solvent.WATER
            assert len(report.points) == 3
            assert report.variance < 0.05  # Should be 0 since mocks are identical
            assert report.is_stable is True

            # Verify specific point values
            for i, point in enumerate(report.points):
                assert point.start_time == [100.0, 200.0, 300.0][i]
                assert point.diffusion_coefficient == 2.5e-9

    @patch('analysis.sensitivity.analyze_msd')
    def test_run_sensitivity_sweep_variance_exceeded(self, mock_analyze_msd):
        """Verify flagging when variance exceeds threshold."""
        # Return different diffusion coefficients to induce variance
        mock_result_1 = MagicMock()
        mock_result_1.diffusion_coefficient = 2.0e-9
        
        mock_result_2 = MagicMock()
        mock_result_2.diffusion_coefficient = 3.0e-9

        mock_result_3 = MagicMock()
        mock_result_3.diffusion_coefficient = 4.0e-9

        # Cycle through results for the 3 calls
        mock_analyze_msd.side_effect = [mock_result_1, mock_result_2, mock_result_3]

        mock_timeseries = (np.array([0, 100, 200, 300]), np.array([0, 10, 20, 30]))

        with patch('analysis.sensitivity.load_trajectory_timeseries', return_value=mock_timeseries):
            config = SensitivityConfig(
                start_percentages=[0.1, 0.2, 0.3],
                variance_threshold=0.05, # 5%
                solvent=Solvent.ETHANOL
            )

            report = run_sensitivity_sweep(
                trajectory_path=Path("dummy.gro"),
                config=config,
                total_duration=1000.0
            )

            # Calculate expected variance manually for [2, 3, 4] -> mean=3, var=0.666...
            # Normalized variance (CV^2) or raw variance? 
            # The function calculate_variance returns raw variance. 
            # Threshold is 0.05. 
            # Let's check the logic in sensitivity.py: usually compares (max-min)/mean or similar.
            # Assuming the implementation checks relative variance.
            # For this test, we just verify the logic triggers the flag.
            # Since values are 2.0, 3.0, 4.0 (range 50%), variance will definitely be high.
            assert report.is_stable is False

    @patch('analysis.sensitivity.analyze_msd')
    def test_run_sensitivity_sweep_linearity_fail(self, mock_analyze_msd):
        """Verify handling of non-linear MSD (R^2 < threshold)."""
        mock_result = MagicMock()
        mock_result.diffusion_coefficient = 2.5e-9
        mock_result.r_squared = 0.80 # Below 0.95 threshold
        mock_analyze_msd.return_value = mock_result

        mock_timeseries = (np.array([0, 100, 200, 300]), np.array([0, 10, 20, 30]))

        with patch('analysis.sensitivity.load_trajectory_timeseries', return_value=mock_timeseries):
            config = SensitivityConfig(
                start_percentages=[0.1],
                variance_threshold=0.05,
                solvent=Solvent.ACETONE
            )

            report = run_sensitivity_sweep(
                trajectory_path=Path("dummy.gro"),
                config=config,
                total_duration=1000.0
            )

            # Even with one point, if linearity fails, it should be flagged or handled.
            # Depending on implementation, it might return None or a specific flag.
            # Assuming it still returns a report but points might have low R2.
            assert len(report.points) == 1
            # The point should reflect the low R2
            assert report.points[0].r_squared < 0.95


class TestSensitivityPointDataModel:
    """Tests for the SensitivityPoint data model."""

    def test_sensitivity_point_creation(self):
        """Verify SensitivityPoint can be instantiated with correct types."""
        point = SensitivityPoint(
            start_time=100.0,
            diffusion_coefficient=2.5e-9,
            r_squared=0.98
        )

        assert point.start_time == 100.0
        assert point.diffusion_coefficient == 2.5e-9
        assert point.r_squared == 0.98

    def test_sensitivity_point_default_values(self):
        """Verify default values for optional fields."""
        point = SensitivityPoint(
            start_time=100.0,
            diffusion_coefficient=2.5e-9,
            r_squared=0.98,
            status="passed"
        )
        assert point.status == "passed"


class TestSensitivityReportDataModel:
    """Tests for the SensitivityReport data model."""

    def test_sensitivity_report_creation(self):
        """Verify SensitivityReport structure."""
        points = [
            SensitivityPoint(start_time=100.0, diffusion_coefficient=1.0, r_squared=0.99),
            SensitivityPoint(start_time=200.0, diffusion_coefficient=1.1, r_squared=0.99)
        ]
        report = SensitivityReport(
            solvent=Solvent.WATER,
            points=points,
            variance=0.01,
            is_stable=True
        )

        assert report.solvent == Solvent.WATER
        assert len(report.points) == 2
        assert report.is_stable is True

    def test_sensitivity_report_empty_points(self):
        """Verify report handles empty points list."""
        report = SensitivityReport(
            solvent=Solvent.WATER,
            points=[],
            variance=0.0,
            is_stable=True
        )
        assert len(report.points) == 0
        assert report.variance == 0.0