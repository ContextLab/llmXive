"""
Unit tests for the CAMB likelihood grid generation.

These tests verify that the grid generation module works correctly
and produces the expected output structure.
"""
import os
import sys
import pickle
import pytest
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.generate_grid import (
    generate_parameter_grid,
    compute_theoretical_spectrum,
    calculate_likelihood,
    ensure_output_dir
)

class TestGenerateParameterGrid:
    """Tests for parameter grid generation."""
    
    def test_grid_dimensions(self):
        """Test that the grid has the correct dimensions."""
        from config import (
            GRID_H0_STEPS, GRID_OMEGA_M_STEPS, 
            GRID_NS_STEPS, GRID_TAU_STEPS
        )
        
        grid = generate_parameter_grid()
        
        assert len(grid['H0']) == GRID_H0_STEPS
        assert len(grid['Omega_m']) == GRID_OMEGA_M_STEPS
        assert len(grid['ns']) == GRID_NS_STEPS
        assert len(grid['tau']) == GRID_TAU_STEPS
    
    def test_grid_ranges(self):
        """Test that the grid covers the expected parameter ranges."""
        from config import GRID_H0_RANGE, GRID_OMEGA_M_RANGE, GRID_NS_RANGE, GRID_TAU_RANGE
        
        grid = generate_parameter_grid()
        
        assert grid['H0'][0] == GRID_H0_RANGE[0]
        assert grid['H0'][-1] == GRID_H0_RANGE[1]
        assert grid['Omega_m'][0] == GRID_OMEGA_M_RANGE[0]
        assert grid['Omega_m'][-1] == GRID_OMEGA_M_RANGE[1]
        assert grid['ns'][0] == GRID_NS_RANGE[0]
        assert grid['ns'][-1] == GRID_NS_RANGE[1]
        assert grid['tau'][0] == GRID_TAU_RANGE[0]
        assert grid['tau'][-1] == GRID_TAU_RANGE[1]

class TestComputeTheoreticalSpectrum:
    """Tests for theoretical spectrum computation."""
    
    def test_spectrum_shape(self):
        """Test that the computed spectrum has the correct shape."""
        from config import L_MAX
        
        params = {
            'H0': 70.0,
            'Omega_m': 0.3,
            'ns': 0.96,
            'tau': 0.08
        }
        
        l_values, cl_array = compute_theoretical_spectrum(params)
        
        assert len(l_values) == L_MAX + 1
        assert cl_array.shape == (L_MAX + 1, 3)  # TT, EE, TE
    
    def test_spectrum_values(self):
        """Test that the spectrum values are reasonable."""
        params = {
            'H0': 70.0,
            'Omega_m': 0.3,
            'ns': 0.96,
            'tau': 0.08
        }
        
        l_values, cl_array = compute_theoretical_spectrum(params)
        
        # Check that l_values are non-negative and increasing
        assert np.all(l_values >= 0)
        assert np.all(np.diff(l_values) == 1)
        
        # Check that TT spectrum has the expected shape (peak at low l)
        cl_tt = cl_array[:, 0]
        assert np.any(cl_tt > 0)  # Should have non-zero values

class TestCalculateLikelihood:
    """Tests for likelihood calculation."""
    
    def test_likelihood_computation(self):
        """Test that likelihood is computed correctly."""
        from config import L_MAX
        
        l_values = np.arange(L_MAX + 1)
        cl_theory = np.random.rand(L_MAX + 1, 3)
        cl_obs = cl_theory + np.random.rand(L_MAX + 1, 3) * 0.01
        
        likelihood = calculate_likelihood(cl_obs, cl_theory, l_values)
        
        assert isinstance(likelihood, float)
        assert not np.isnan(likelihood)
    
    def test_likelihood_with_l_min(self):
        """Test likelihood calculation with l_min parameter."""
        from config import L_MAX
        
        l_values = np.arange(L_MAX + 1)
        cl_theory = np.random.rand(L_MAX + 1, 3)
        cl_obs = cl_theory + np.random.rand(L_MAX + 1, 3) * 0.01
        
        likelihood = calculate_likelihood(cl_obs, cl_theory, l_values, l_min=10)
        
        assert isinstance(likelihood, float)
        assert not np.isnan(likelihood)

class TestEnsureOutputDir:
    """Tests for output directory creation."""
    
    def test_directory_creation(self):
        """Test that the output directory is created."""
        from config import DATA_DERIVED_DIR
        
        output_dir = ensure_output_dir()
        
        assert output_dir.exists()
        assert output_dir.is_dir()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])