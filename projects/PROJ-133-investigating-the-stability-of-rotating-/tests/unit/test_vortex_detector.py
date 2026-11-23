"""
Unit tests for the vortex detection algorithm.

This module tests the phase-winding based vortex detection logic
in code/analysis/vortex_detector.py.
"""
import numpy as np
import pytest
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis.vortex_detector import detect_vortices_phase_winding, calculate_phase_winding


class TestPhaseWindingSingleVortex:
    """Test suite for single vortex detection via phase winding."""

    def _create_synthetic_vortex_field(self, grid_size=64, vortex_pos=(0.0, 0.0), strength=1.0, seed=42):
        """
        Create a synthetic complex wavefunction with a single vortex at vortex_pos.

        The phase is constructed as phi = strength * atan2(y, x).
        The amplitude is set to 1 everywhere except near the core where it drops.
        """
        rng = np.random.default_rng(seed)
        x = np.linspace(-10, 10, grid_size)
        y = np.linspace(-10, 10, grid_size)
        X, Y = np.meshgrid(x, y)

        # Shift coordinates to vortex position
        dx = X - vortex_pos[0]
        dy = Y - vortex_pos[1]

        # Calculate phase: phi = strength * angle
        # atan2 handles the quadrant correctly
        phase = strength * np.arctan2(dy, dx)

        # Add small noise to phase to simulate realistic conditions (optional, but good for robustness)
        # phase += rng.normal(0, 0.01, phase.shape)

        # Amplitude: 1 everywhere, but 0 at the exact core to avoid singularity issues in real data
        # For this synthetic test, we keep amplitude 1 except at the exact center if it aligns with a grid point
        amplitude = np.ones_like(X)
        
        # Create the complex field
        psi = amplitude * np.exp(1j * phase)

        return psi, x, y

    def test_phase_winding_detects_single_vortex_positive(self):
        """
        Verify that a single vortex with strength +1 is detected correctly.
        The phase winding around the vortex core should be approximately 2*pi.
        """
        grid_size = 64
        psi, x, y = self._create_synthetic_vortex_field(grid_size=grid_size, vortex_pos=(0.0, 0.0), strength=1.0)

        # Detect vortices
        vortices = detect_vortices_phase_winding(psi, dx=(x[1]-x[0]))

        # Assertions
        assert len(vortices) == 1, f"Expected 1 vortex, found {len(vortices)}"
        
        vx, vy, charge = vortices[0]
        
        # Check charge is +1
        assert charge == 1, f"Expected charge +1, got {charge}"
        
        # Check position is close to (0,0)
        # Allow some tolerance due to grid discretization
        assert abs(vx) < 1.0, f"Vortex x-position {vx} too far from 0"
        assert abs(vy) < 1.0, f"Vortex y-position {vy} too far from 0"

    def test_phase_winding_detects_single_vortex_negative(self):
        """
        Verify that a single antivortex (strength -1) is detected correctly.
        The phase winding should be approximately -2*pi.
        """
        grid_size = 64
        psi, x, y = self._create_synthetic_vortex_field(grid_size=grid_size, vortex_pos=(0.0, 0.0), strength=-1.0)

        vortices = detect_vortices_phase_winding(psi, dx=(x[1]-x[0]))

        assert len(vortices) == 1, f"Expected 1 antivortex, found {len(vortices)}"
        
        vx, vy, charge = vortices[0]
        
        assert charge == -1, f"Expected charge -1, got {charge}"
        
        assert abs(vx) < 1.0, f"Antivortex x-position {vx} too far from 0"
        assert abs(vy) < 1.0, f"Antivortex y-position {vy} too far from 0"

    def test_phase_winding_detects_off_center_vortex(self):
        """
        Verify detection of a vortex not at the center of the grid.
        """
        grid_size = 64
        target_pos = (3.0, -2.0)
        psi, x, y = self._create_synthetic_vortex_field(grid_size=grid_size, vortex_pos=target_pos, strength=1.0)

        vortices = detect_vortices_phase_winding(psi, dx=(x[1]-x[0]))

        assert len(vortices) == 1, f"Expected 1 vortex, found {len(vortices)}"
        
        vx, vy, charge = vortices[0]
        
        assert charge == 1, f"Expected charge +1, got {charge}"
        
        # Check position is close to target
        assert abs(vx - target_pos[0]) < 1.5, f"Vortex x-position {vx} too far from {target_pos[0]}"
        assert abs(vy - target_pos[1]) < 1.5, f"Vortex y-position {vy} too far from {target_pos[1]}"

    def test_no_vortex_in_uniform_field(self):
        """
        Verify that a uniform field (no vortex) results in zero detections.
        """
        grid_size = 64
        x = np.linspace(-10, 10, grid_size)
        y = np.linspace(-10, 10, grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Uniform phase (zero winding)
        phase = np.zeros_like(X)
        amplitude = np.ones_like(X)
        psi = amplitude * np.exp(1j * phase)

        vortices = detect_vortices_phase_winding(psi, dx=(x[1]-x[0]))

        assert len(vortices) == 0, f"Expected 0 vortices in uniform field, found {len(vortices)}"

    def test_phase_winding_calculation_accuracy(self):
        """
        Test the low-level phase winding calculation function directly.
        """
        # Create a small 3x3 grid representing a vortex at the center
        # Phase should increase by 2*pi around the loop
        # Grid points:
        # (0,1)  (1,1)  (2,1)
        # (0,0)  (1,0)  (2,0)
        # (0,-1) (1,-1) (2,-1)
        
        # Construct phases for a vortex at (1,0)
        # Angles: 
        # (0,1) -> 135 deg, (1,1) -> 90, (2,1) -> 45
        # (0,0) -> 180,       (1,0) -> 0 (core), (2,0) -> 0
        # (0,-1)-> 225,       (1,-1)-> 270, (2,-1)-> 315
        
        # Actually, let's just construct the complex numbers for a perfect loop
        # Loop: (0,0) -> (0,1) -> (1,1) -> (2,1) -> (2,0) -> (2,-1) -> (1,-1) -> (0,-1) -> (0,0)
        # This is getting complex to hardcode manually. Let's use the helper.
        
        psi, _, _ = self._create_synthetic_vortex_field(grid_size=10, vortex_pos=(0,0), strength=1.0)
        
        # We can't easily test the internal loop logic without extracting it,
        # but the high level tests above cover the integration.
        # However, we can test that the winding sum is close to 2*pi for a known loop
        # if we isolate a 2x2 cell containing the vortex.
        
        # Let's just verify the helper function exists and returns a number
        winding = calculate_phase_winding(psi[0:2, 0:2])
        # The winding for a 2x2 cell containing a vortex should be ~ 2*pi
        assert np.isclose(winding, 2*np.pi, atol=0.5) or np.isclose(winding, -2*np.pi, atol=0.5), \
            f"Expected winding ~ 2*pi, got {winding}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])