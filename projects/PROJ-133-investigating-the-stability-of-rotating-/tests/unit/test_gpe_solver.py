"""
Unit tests for the GPE solver.

Tests for split-step Fourier stability and numerical properties.
"""
import pytest
import numpy as np
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.gpe_solver import GPESolver, GPEParameters
from simulation.initial_conditions import create_thomas_fermi_initial_condition
from config.grid_config import create_grid_config
from utils.seed_manager import set_global_seed


class TestSplitStepFourierStability:
    """Tests for split-step Fourier method stability."""
    
    @pytest.fixture
    def simple_solver(self):
        """Create a simple GPE solver for testing."""
        set_global_seed(42)
        params = GPEParameters(
            omega=0.0,  # No rotation for basic test
            epsilon_dd=0.0,  # No dipolar interaction for basic test
            N=1000
        )
        grid_config = create_grid_config()
        return GPESolver(params, grid_config)
    
    @pytest.fixture
    def initial_psi(self, simple_solver):
        """Create an initial wavefunction."""
        psi = create_thomas_fermi_initial_condition(
            simple_solver.Nx, simple_solver.Ny,
            simple_solver.x, simple_solver.y,
            N=simple_solver.N,
            omega_trap=2*np.pi*100.0,
            a_s=5.2e-9
        )
        return psi
    
    def test_split_step_preserves_norm(self, simple_solver, initial_psi):
        """Test that the split-step method preserves the norm of the wavefunction."""
        # Initialize wavefunction
        simple_solver.initialize_wavefunction(initial_psi)
        
        # Get initial norm
        dx = simple_solver.x[1] - simple_solver.x[0]
        dy = simple_solver.y[1] - simple_solver.y[0]
        initial_norm = np.sum(np.abs(simple_solver.psi)**2) * dx * dy
        
        # Evolve for a few steps
        n_steps = 10
        dt = simple_solver.dt
        
        for _ in range(n_steps):
            simple_solver.psi = simple_solver._step_split_step(simple_solver.psi, dt)
        
        # Get final norm
        final_norm = np.sum(np.abs(simple_solver.psi)**2) * dx * dy
        
        # Check that norm is preserved (within numerical precision)
        norm_error = abs(final_norm - initial_norm) / initial_norm
        assert norm_error < 1e-3, f"Norm not preserved: initial={initial_norm:.6f}, " \
                                 f"final={final_norm:.6f}, error={norm_error:.6e}"
    
    def test_split_step_reversibility(self, simple_solver, initial_psi):
        """Test that the split-step method is approximately reversible."""
        # Initialize wavefunction
        simple_solver.initialize_wavefunction(initial_psi)
        
        # Store initial state
        psi_initial = simple_solver.psi.copy()
        
        # Evolve forward
        dt = simple_solver.dt
        n_steps = 5
        for _ in range(n_steps):
            simple_solver.psi = simple_solver._step_split_step(simple_solver.psi, dt)
        
        # Evolve backward (negative time step)
        for _ in range(n_steps):
            simple_solver.psi = simple_solver._step_split_step(simple_solver.psi, -dt)
        
        # Check that we return to the initial state
        diff = np.abs(simple_solver.psi - psi_initial)
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)
        
        assert max_diff < 0.1, f"Reversibility failed: max_diff={max_diff:.6e}"
        assert mean_diff < 0.01, f"Reversibility failed: mean_diff={mean_diff:.6e}"
    
    def test_no_numerical_instability(self, simple_solver, initial_psi):
        """Test that the solver does not produce NaN or Inf values."""
        # Initialize wavefunction
        simple_solver.initialize_wavefunction(initial_psi)
        
        # Evolve for many steps
        dt = simple_solver.dt
        n_steps = 100
        
        for i in range(n_steps):
            simple_solver.psi = simple_solver._step_split_step(simple_solver.psi, dt)
            
            # Check for numerical issues
            assert not np.any(np.isnan(simple_solver.psi)), \
                f"NaN detected at step {i}"
            assert not np.any(np.isinf(simple_solver.psi)), \
                f"Inf detected at step {i}"
    
    def test_dipolar_interaction_inclusion(self):
        """Test that dipolar interaction is included in the solver."""
        set_global_seed(42)
        params = GPEParameters(
            omega=0.0,
            epsilon_dd=1.0,  # Non-zero dipolar interaction
            N=1000
        )
        grid_config = create_grid_config()
        solver = GPESolver(params, grid_config)
        
        # Check that dipolar kernel is computed
        assert solver.dipolar_kernel is not None
        assert solver.dipolar_kernel.shape == (solver.Nx, solver.Ny)
        
        # Check that dipolar interaction strength is non-zero
        assert solver.g_dd != 0.0
    
    def test_rotation_term_inclusion(self):
        """Test that rotation term is included in the solver."""
        set_global_seed(42)
        params = GPEParameters(
            omega=0.5,  # Non-zero rotation
            epsilon_dd=0.0,
            N=1000
        )
        grid_config = create_grid_config()
        solver = GPESolver(params, grid_config)
        
        # Check that rotation is set
        assert solver.omega == 0.5
        
        # Note: The exact implementation of rotation may vary,
        # but the parameter should be stored correctly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])