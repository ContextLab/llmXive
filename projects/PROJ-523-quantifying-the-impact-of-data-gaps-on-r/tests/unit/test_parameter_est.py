import os
import sys
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.parameter_est import (
    get_leakage_matrix_path,
    load_leakage_matrix,
    validate_leakage_matrix,
    estimate_parameters_from_grid
)
from config import N_SIDE, DATA_DERIVED_DIR

class TestLeakageMatrixFunctions:
    def test_get_leakage_matrix_path_format(self):
        """Test that leakage matrix path follows expected format."""
        test_id = "realization_001"
        path = get_leakage_matrix_path(test_id)
        
        assert path.name == f"leakage_matrix_{test_id}.npy"
        assert path.parent == Path(DATA_DERIVED_DIR)

    def test_validate_leakage_matrix_dimensions(self):
        """Test validation of leakage matrix dimensions."""
        l_max = 10
        correct_size = l_max + 1
        
        valid_matrix = np.random.rand(correct_size, correct_size)
        invalid_matrix = np.random.rand(correct_size + 1, correct_size)
        
        assert validate_leakage_matrix(valid_matrix, l_max) is True
        assert validate_leakage_matrix(invalid_matrix, l_max) is False

    def test_validate_leakage_matrix_nan_check(self):
        """Test that matrices with NaN values are rejected."""
        l_max = 10
        valid_matrix = np.random.rand(l_max + 1, l_max + 1)
        invalid_matrix = valid_matrix.copy()
        invalid_matrix[0, 0] = np.nan
        
        assert validate_leakage_matrix(valid_matrix, l_max) is True
        assert validate_leakage_matrix(invalid_matrix, l_max) is False

class TestParameterEstimation:
    def test_estimate_parameters_from_grid_with_mock(self):
        """Test parameter estimation with mocked grid data."""
        # Create a mock leakage matrix
        l_max = 100
        leakage_matrix = np.random.rand(l_max + 1, l_max + 1).astype(np.float32)
        
        # Create mock observed power spectrum
        observed_cl = np.random.rand(l_max + 1).astype(np.float32)
        
        # Mock the grid data
        mock_grid_data = {
            'params': {
                'H0': [67.0, 68.0, 69.0],
                'Omega_m': [0.30, 0.31, 0.32],
                'n_s': [0.96, 0.97, 0.98],
                'tau': [0.05, 0.06, 0.07]
            },
            'likelihoods': np.random.rand(3, 3, 3, 3)
        }
        
        # Mock the load_precomputed_grid function
        with patch('analysis.parameter_est.load_precomputed_grid') as mock_load_grid:
            mock_load_grid.return_value = mock_grid_data
            
            # Mock the compute_theoretical_spectrum function
            with patch('analysis.parameter_est.compute_theoretical_spectrum') as mock_theory:
                mock_theory.return_value = observed_cl  # Return observed as "theory" for perfect match
                
                # Run estimation
                result = estimate_parameters_from_grid(
                    leakage_matrix=leakage_matrix,
                    observed_cl=observed_cl,
                    l_max=l_max
                )
                
                # Verify result structure
                assert isinstance(result, dict)
                assert 'estimated_params' in result
                assert 'likelihood_max' in result
                
                # Verify estimated params contain expected keys
                est_params = result['estimated_params']
                assert 'H0' in est_params
                assert 'Omega_m' in est_params
                assert 'n_s' in est_params
                assert 'tau' in est_params

    def test_estimate_parameters_from_grid_edge_case(self):
        """Test parameter estimation with edge case inputs."""
        l_max = 10
        
        # Small leakage matrix
        leakage_matrix = np.eye(l_max + 1, dtype=np.float32)
        observed_cl = np.ones(l_max + 1, dtype=np.float32)
        
        mock_grid_data = {
            'params': {
                'H0': [67.0],
                'Omega_m': [0.30],
                'n_s': [0.96],
                'tau': [0.05]
            },
            'likelihoods': np.array([[[[1.0]]]])
        }
        
        with patch('analysis.parameter_est.load_precomputed_grid') as mock_load_grid:
            mock_load_grid.return_value = mock_grid_data
            
            with patch('analysis.parameter_est.compute_theoretical_spectrum') as mock_theory:
                mock_theory.return_value = observed_cl
                
                result = estimate_parameters_from_grid(
                    leakage_matrix=leakage_matrix,
                    observed_cl=observed_cl,
                    l_max=l_max
                )
                
                assert result is not None
                assert result['estimated_params']['H0'] == 67.0

    def test_estimate_parameters_from_grid_invalid_leakage(self):
        """Test that invalid leakage matrix raises appropriate error."""
        l_max = 10
        invalid_leakage = np.full((l_max + 2, l_max + 2), np.nan)  # Wrong size
        observed_cl = np.ones(l_max + 1, dtype=np.float32)
        
        mock_grid_data = {
            'params': {
                'H0': [67.0],
                'Omega_m': [0.30],
                'n_s': [0.96],
                'tau': [0.05]
            },
            'likelihoods': np.array([[[[1.0]]]])
        }
        
        with patch('analysis.parameter_est.load_precomputed_grid') as mock_load_grid:
            mock_load_grid.return_value = mock_grid_data
            
            with patch('analysis.parameter_est.compute_theoretical_spectrum') as mock_theory:
                mock_theory.return_value = observed_cl
                
                # Should raise ValueError for invalid matrix
                with pytest.raises(ValueError):
                    estimate_parameters_from_grid(
                        leakage_matrix=invalid_leakage,
                        observed_cl=observed_cl,
                        l_max=l_max
                    )

class TestIntegration:
    def test_parameter_estimation_workflow(self):
        """Test the complete parameter estimation workflow."""
        l_max = 50
        
        # Generate realistic test data
        np.random.seed(42)
        leakage_matrix = np.random.rand(l_max + 1, l_max + 1).astype(np.float32)
        observed_cl = np.abs(np.random.randn(l_max + 1)).astype(np.float32)
        
        # Create mock grid
        mock_grid_data = {
            'params': {
                'H0': [67.0, 68.0, 69.0],
                'Omega_m': [0.29, 0.30, 0.31],
                'n_s': [0.95, 0.96, 0.97],
                'tau': [0.04, 0.05, 0.06]
            },
            'likelihoods': np.random.rand(3, 3, 3, 3)
        }
        
        with patch('analysis.parameter_est.load_precomputed_grid') as mock_load_grid:
            mock_load_grid.return_value = mock_grid_data
            
            with patch('analysis.parameter_est.compute_theoretical_spectrum') as mock_theory:
                # Return a spectrum that matches one of the grid points
                mock_theory.return_value = observed_cl
                
                result = estimate_parameters_from_grid(
                    leakage_matrix=leakage_matrix,
                    observed_cl=observed_cl,
                    l_max=l_max
                )
                
                # Verify result completeness
                assert 'estimated_params' in result
                assert 'likelihood_max' in result
                assert 'grid_index' in result
                
                # Verify parameter values are within grid bounds
                est = result['estimated_params']
                assert 67.0 <= est['H0'] <= 69.0
                assert 0.29 <= est['Omega_m'] <= 0.31
                assert 0.95 <= est['n_s'] <= 0.97
                assert 0.04 <= est['tau'] <= 0.06