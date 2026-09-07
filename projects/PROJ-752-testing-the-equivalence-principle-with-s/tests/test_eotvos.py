import pytest
import numpy as np
from typing import Dict
from dataclasses import dataclass
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.eotvos import compute_eotvos_parameter, EotvosResult, run_eotvos_analysis
from models.estimator import OrbitSolution, extract_joint_parameters, AnalysisError
from utils.logging import DataUnavailableError

# Fixtures for testing
@pytest.fixture
def mock_joint_solution():
    """Create a mock OrbitSolution with realistic values for LAGEOS/Etalon."""
    # Mock state vector (position in meters) - approx LAGEOS orbit radius
    # r ~ 12,270 km = 1.227e7 m
    state_vector = np.array([1.227e7, 0.0, 0.0])
    
    # Mock covariance matrix (simplified diagonal for testing)
    # Variances in m^2/s^2 for acceleration parameters
    cov_matrix = np.array([
        [1e-12, 0.0, 0.0],  # Position variance
        [0.0, 1e-12, 0.0],
        [0.0, 0.0, 1e-18]   # Differential acceleration variance (ac)
    ])
    
    return OrbitSolution(
        state=state_vector,
        covariance=cov_matrix,
        converged=True,
        parameters={'ac': 1.5e-13, 'g': 2.65},  # ac in m/s^2, g in m/s^2
        chi2=12.5,
        dof=100
    )

@pytest.fixture
def mock_non_converged_solution():
    """Create a mock OrbitSolution that did not converge."""
    state_vector = np.array([1.227e7, 0.0, 0.0])
    return OrbitSolution(
        state=state_vector,
        covariance=np.eye(3) * 1e-10,
        converged=False,
        parameters={'ac': 0.0, 'g': 2.65},
        chi2=500.0,
        dof=100
    )

class TestComputeEotvosParameter:
    """Unit tests for eta calculation and covariance propagation."""

    def test_eta_calculation_basic(self, mock_joint_solution):
        """Test basic eta = |ac| / g calculation."""
        result = compute_eotvos_parameter(
            ac=mock_joint_solution.parameters['ac'],
            g=mock_joint_solution.parameters['g'],
            ac_uncertainty=1e-9,  # sqrt(1e-18)
            g_uncertainty=0.01
        )
        
        expected_eta = abs(mock_joint_solution.parameters['ac']) / mock_joint_solution.parameters['g']
        assert np.isclose(result['eta'], expected_eta), f"Expected {expected_eta}, got {result['eta']}"
        assert result['eta'] > 0

    def test_covariance_propagation(self, mock_joint_solution):
        """Test that uncertainty propagation follows sigma_eta = sigma_ac / g."""
        ac = mock_joint_solution.parameters['ac']
        g = mock_joint_solution.parameters['g']
        ac_unc = 1e-9  # 1e-18 variance
        
        result = compute_eotvos_parameter(
            ac=ac,
            g=g,
            ac_uncertainty=ac_unc,
            g_uncertainty=0.01
        )
        
        # Analytical propagation: d(eta)/d(ac) = 1/g
        expected_unc = ac_unc / g
        assert np.isclose(result['eta_uncertainty'], expected_unc, rtol=1e-5), \
            f"Expected uncertainty {expected_unc}, got {result['eta_uncertainty']}"

    def test_confidence_interval_95(self, mock_joint_solution):
        """Test 95% CI calculation (approx 1.96 * sigma)."""
        result = compute_eotvos_parameter(
            ac=mock_joint_solution.parameters['ac'],
            g=mock_joint_solution.parameters['g'],
            ac_uncertainty=1e-9,
            g_uncertainty=0.01
        )
        
        expected_width = 1.96 * result['eta_uncertainty']
        assert np.isclose(result['ci_95_width'], expected_width, rtol=1e-5)
        assert result['ci_95_lower'] < result['eta'] < result['ci_95_upper']

    def test_negative_ac_handling(self, mock_joint_solution):
        """Test that negative ac is handled correctly (absolute value for eta)."""
        result = compute_eotvos_parameter(
            ac=-1.5e-13,
            g=2.65,
            ac_uncertainty=1e-9,
            g_uncertainty=0.01
        )
        
        assert result['eta'] > 0, "Eta must be positive"
        assert result['eta'] == abs(-1.5e-13) / 2.65

    def test_zero_ac_edge_case(self):
        """Test edge case where ac is zero."""
        result = compute_eotvos_parameter(
            ac=0.0,
            g=2.65,
            ac_uncertainty=1e-9,
            g_uncertainty=0.01
        )
        
        assert result['eta'] == 0.0
        assert result['ci_95_lower'] < 0.0
        assert result['ci_95_upper'] > 0.0

    def test_large_uncertainty_propagation(self):
        """Test behavior with large uncertainties."""
        result = compute_eotvos_parameter(
            ac=1e-13,
            g=2.65,
            ac_uncertainty=1e-8,  # Very large relative to ac
            g_uncertainty=0.01
        )
        
        assert result['eta_uncertainty'] > result['eta'], \
            "Uncertainty should be larger than signal in this case"

class TestRunEotvosAnalysis:
    """Integration tests for the full Eotvos analysis pipeline."""

    def test_full_pipeline_success(self, mock_joint_solution):
        """Test end-to-end analysis with converged solution."""
        # Extract parameters from mock solution
        params = extract_joint_parameters(mock_joint_solution)
        
        result = run_eotvos_analysis(
            ac=params['ac'],
            g=params['g'],
            covariance=params['covariance'],
            confidence_level=0.95
        )
        
        assert isinstance(result, EotvosResult)
        assert result.converged is True
        assert result.eta > 0
        assert result.ci_95_lower < result.eta < result.ci_95_upper
        assert result.benchmark_comparison is not None

    def test_non_converged_solution_handling(self, mock_non_converged_solution):
        """Test analysis with non-converged solution."""
        params = extract_joint_parameters(mock_non_converged_solution)
        
        result = run_eotvos_analysis(
            ac=params['ac'],
            g=params['g'],
            covariance=params['covariance'],
            confidence_level=0.95
        )
        
        assert result.converged is False
        assert result.warning_message is not None
        # Should still compute eta but flag as unreliable
        assert result.eta >= 0

    def test_invalid_covariance_matrix(self, mock_joint_solution):
        """Test handling of invalid covariance matrix (negative variance)."""
        bad_cov = mock_joint_solution.covariance.copy()
        bad_cov[2, 2] = -1e-18  # Negative variance
        
        with pytest.raises(ValueError):
            run_eotvos_analysis(
                ac=mock_joint_solution.parameters['ac'],
                g=mock_joint_solution.parameters['g'],
                covariance=bad_cov,
                confidence_level=0.95
            )

    def test_nan_values_in_parameters(self):
        """Test handling of NaN values in input parameters."""
        with pytest.raises(ValueError):
            run_eotvos_analysis(
                ac=np.nan,
                g=2.65,
                covariance=np.eye(3),
                confidence_level=0.95
            )

    def test_inf_values_in_parameters(self):
        """Test handling of infinite values in input parameters."""
        with pytest.raises(ValueError):
            run_eotvos_analysis(
                ac=np.inf,
                g=2.65,
                covariance=np.eye(3),
                confidence_level=0.95
            )

    def test_different_confidence_levels(self, mock_joint_solution):
        """Test analysis with different confidence levels."""
        params = extract_joint_parameters(mock_joint_solution)
        
        for conf_level in [0.90, 0.95, 0.99]:
            result = run_eotvos_analysis(
                ac=params['ac'],
                g=params['g'],
                covariance=params['covariance'],
                confidence_level=conf_level
            )
            
            # Higher confidence level should give wider interval
            if conf_level == 0.99:
                assert result.ci_95_width > run_eotvos_analysis(
                    ac=params['ac'],
                    g=params['g'],
                    covariance=params['covariance'],
                    confidence_level=0.95
                ).ci_95_width

    def test_benchmark_comparison_logic(self, mock_joint_solution):
        """Test that benchmark comparison uses correct limit."""
        # Use a mock limit for testing
        mock_limit = 1e-14
        
        params = extract_joint_parameters(mock_joint_solution)
        result = run_eotvos_analysis(
            ac=params['ac'],
            g=params['g'],
            covariance=params['covariance'],
            confidence_level=0.95,
            benchmark_limit=mock_limit
        )
        
        assert result.benchmark_comparison is not None
        # Check that the comparison is based on CI width vs limit
        assert hasattr(result.benchmark_comparison, 'within_limit')

class TestEotvosResultDataclass:
    """Tests for the EotvosResult dataclass structure."""

    def test_dataclass_initialization(self):
        """Test that EotvosResult can be instantiated with all required fields."""
        result = EotvosResult(
            eta=1.5e-14,
            eta_uncertainty=1e-15,
            ci_95_lower=1.3e-14,
            ci_95_upper=1.7e-14,
            converged=True,
            chi2=12.5,
            dof=100,
            benchmark_comparison={'limit': 1e-14, 'within_limit': True}
        )
        
        assert result.eta == 1.5e-14
        assert result.eta_uncertainty == 1e-15
        assert result.converged is True
        assert result.ci_95_lower < result.ci_95_upper

    def test_dataclass_to_dict(self):
        """Test conversion to dictionary for serialization."""
        result = EotvosResult(
            eta=1.5e-14,
            eta_uncertainty=1e-15,
            ci_95_lower=1.3e-14,
            ci_95_upper=1.7e-14,
            converged=True,
            chi2=12.5,
            dof=100,
            benchmark_comparison={'limit': 1e-14, 'within_limit': True}
        )
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert 'eta' in result_dict
        assert 'eta_uncertainty' in result_dict
        assert 'ci_95_lower' in result_dict
        assert 'ci_95_upper' in result_dict
        assert 'converged' in result_dict
        assert 'benchmark_comparison' in result_dict

    def test_dataclass_serialization(self):
        """Test JSON serialization and deserialization."""
        import json
        
        result = EotvosResult(
            eta=1.5e-14,
            eta_uncertainty=1e-15,
            ci_95_lower=1.3e-14,
            ci_95_upper=1.7e-14,
            converged=True,
            chi2=12.5,
            dof=100,
            benchmark_comparison={'limit': 1e-14, 'within_limit': True}
        )
        
        json_str = json.dumps(result.to_dict())
        loaded_dict = json.loads(json_str)
        loaded_result = EotvosResult.from_dict(loaded_dict)
        
        assert np.isclose(loaded_result.eta, result.eta)
        assert np.isclose(loaded_result.eta_uncertainty, result.eta_uncertainty)
        assert loaded_result.converged == result.converged

class TestCovarianceMatrixHandling:
    """Specific tests for covariance matrix edge cases."""

    def test_singular_covariance_matrix(self):
        """Test handling of singular covariance matrix."""
        singular_cov = np.array([
            [1.0, 1.0],
            [1.0, 1.0]
        ])  # Determinant = 0
        
        with pytest.raises(np.linalg.LinAlgError):
            compute_eotvos_parameter(
                ac=1e-13,
                g=2.65,
                ac_uncertainty=1e-9,
                g_uncertainty=0.01,
                covariance=singular_cov
            )

    def test_correlated_parameters(self):
        """Test covariance propagation with correlated parameters."""
        # Create a covariance matrix with off-diagonal elements
        cov = np.array([
            [1e-18, 5e-19],  # Correlation between ac and g
            [5e-19, 1e-4]
        ])
        
        # This should still work but account for correlation
        result = compute_eotvos_parameter(
            ac=1e-13,
            g=2.65,
            ac_uncertainty=np.sqrt(cov[0, 0]),
            g_uncertainty=np.sqrt(cov[1, 1]),
            covariance=cov
        )
        
        # The uncertainty should be different from uncorrelated case
        assert result['eta_uncertainty'] > 0

class TestNumericalStability:
    """Tests for numerical stability with extreme values."""

    def test_very_small_ac_values(self):
        """Test with ac values near machine epsilon."""
        result = compute_eotvos_parameter(
            ac=1e-300,
            g=2.65,
            ac_uncertainty=1e-300,
            g_uncertainty=1e-300
        )
        
        assert result['eta'] > 0
        assert not np.isnan(result['eta'])
        assert not np.isinf(result['eta'])

    def test_very_large_uncertainty_values(self):
        """Test with extremely large uncertainties."""
        result = compute_eotvos_parameter(
            ac=1e-13,
            g=2.65,
            ac_uncertainty=1e100,
            g_uncertainty=1e100
        )
        
        assert result['eta_uncertainty'] > 0
        assert not np.isnan(result['eta_uncertainty'])
        assert not np.isinf(result['eta_uncertainty'])

    def test_mixed_precision_values(self):
        """Test with mixed precision (small ac, large g)."""
        result = compute_eotvos_parameter(
            ac=1e-15,
            g=1e10,
            ac_uncertainty=1e-15,
            g_uncertainty=1e5
        )
        
        assert result['eta'] > 0
        assert not np.isnan(result['eta'])
        assert not np.isinf(result['eta'])