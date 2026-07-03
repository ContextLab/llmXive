"""
Tests for the Eotvos parameter estimation module.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock

from analysis.eotvos import compute_eotvos_parameter, EotvosResult
from models.estimator import OrbitSolution
from utils.logging import AnalysisError


class TestComputeEotvosParameter:
    """Unit tests for compute_eotvos_parameter function."""

    def create_mock_solution(self, ac: float, g: float, cov_matrix: np.ndarray) -> OrbitSolution:
        """Helper to create a mock OrbitSolution with specific parameters."""
        solution = MagicMock(spec=OrbitSolution)
        # Mock the extract_joint_parameters return value
        # We need to patch the function or mock the solution such that extract_joint_parameters works.
        # Since extract_joint_parameters is imported from estimator, we mock the solution object
        # to have the necessary attributes if the function relies on them,
        # but here we are testing the logic inside compute_eotvos_parameter which calls extract_joint_parameters.
        # To avoid complex mocking of the import, we will directly test the math logic by mocking the return of extract_joint_parameters.
        return solution

    @pytest.fixture
    def valid_solution(self):
        """Create a valid mock solution."""
        from unittest.mock import patch
        with patch('analysis.eotvos.extract_joint_parameters') as mock_extract:
            mock_extract.return_value = {
                'ac': 1.0e-10,
                'g': 9.81,
                'covariance': np.array([
                    [1.0e-22, 0.0],
                    [0.0, 1.0e-10]
                ])
            }
            yield mock_extract

    def test_basic_computation(self, valid_solution):
        """Test basic η calculation."""
        from unittest.mock import patch
        with patch('analysis.eotvos.extract_joint_parameters') as mock_extract:
            mock_extract.return_value = {
                'ac': 1.0e-10,
                'g': 9.81,
                'covariance': np.array([
                    [1.0e-22, 0.0],
                    [0.0, 1.0e-10]
                ])
            }
            # We need a solution object, but the function only uses extract_joint_parameters(solution)
            # So any object works as long as the mock is in place.
            solution = MagicMock()
            result = compute_eotvos_parameter(solution)

            assert isinstance(result, EotvosResult)
            assert result.success is True
            assert result.ac == 1.0e-10
            assert result.g == 9.81
            # eta = |ac| / g = 1e-10 / 9.81
            expected_eta = abs(1.0e-10) / 9.81
            assert np.isclose(result.eta, expected_eta)
            assert result.eta_std >= 0
            assert result.eta_ci_95_lower < result.eta
            assert result.eta_ci_95_upper > result.eta

    def test_negative_ac(self, valid_solution):
        """Test that negative ac results in positive eta."""
        from unittest.mock import patch
        with patch('analysis.eotvos.extract_joint_parameters') as mock_extract:
            mock_extract.return_value = {
                'ac': -2.0e-10,
                'g': 9.81,
                'covariance': np.array([
                    [1.0e-22, 0.0],
                    [0.0, 1.0e-10]
                ])
            }
            solution = MagicMock()
            result = compute_eotvos_parameter(solution)

            assert result.eta > 0
            assert np.isclose(result.eta, abs(-2.0e-10) / 9.81)

    def test_covariance_propagation(self, valid_solution):
        """Test that covariance affects the standard deviation."""
        from unittest.mock import patch
        # Case 1: Small covariance
        with patch('analysis.eotvos.extract_joint_parameters') as mock_extract:
            mock_extract.return_value = {
                'ac': 1.0e-10,
                'g': 9.81,
                'covariance': np.array([
                    [1.0e-24, 0.0],
                    [0.0, 1.0e-12]
                ])
            }
            solution = MagicMock()
            result_small_cov = compute_eotvos_parameter(solution)

        # Case 2: Large covariance
        with patch('analysis.eotvos.extract_joint_parameters') as mock_extract:
            mock_extract.return_value = {
                'ac': 1.0e-10,
                'g': 9.81,
                'covariance': np.array([
                    [1.0e-20, 0.0],
                    [0.0, 1.0e-8]
                ])
            }
            solution = MagicMock()
            result_large_cov = compute_eotvos_parameter(solution)

        # Larger covariance should yield larger std
        assert result_large_cov.eta_std > result_small_cov.eta_std

    def test_zero_gravity_raises_error(self):
        """Test that g=0 raises AnalysisError."""
        from unittest.mock import patch
        with patch('analysis.eotvos.extract_joint_parameters') as mock_extract:
            mock_extract.return_value = {
                'ac': 1.0e-10,
                'g': 0.0,
                'covariance': np.array([
                    [1.0e-22, 0.0],
                    [0.0, 1.0e-10]
                ])
            }
            solution = MagicMock()
            with pytest.raises(AnalysisError, match="Local gravity g is zero"):
                compute_eotvos_parameter(solution)

    def test_invalid_covariance_shape_raises_error(self):
        """Test that wrong covariance shape raises AnalysisError."""
        from unittest.mock import patch
        with patch('analysis.eotvos.extract_joint_parameters') as mock_extract:
            mock_extract.return_value = {
                'ac': 1.0e-10,
                'g': 9.81,
                'covariance': np.array([
                    [1.0e-22]
                ]) # Wrong shape
            }
            solution = MagicMock()
            with pytest.raises(AnalysisError, match="Expected 2x2 covariance matrix"):
                compute_eotvos_parameter(solution)

    def test_to_dict(self):
        """Test the to_dict method of EotvosResult."""
        result = EotvosResult(
            eta=1.0,
            eta_std=0.1,
            eta_ci_95_lower=0.8,
            eta_ci_95_upper=1.2,
            ac=1.0e-10,
            g=9.81,
            covariance_ac_g=np.array([[1, 0], [0, 1]]),
            success=True,
            message="OK"
        )

        d = result.to_dict()
        assert d['eta'] == 1.0
        assert d['success'] is True
        assert isinstance(d['covariance_ac_g'], list)
        assert len(d['covariance_ac_g']) == 2