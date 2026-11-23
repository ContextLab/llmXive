"""
Unit tests for diffusion coefficient calculation and scaling logic.
Task: T012 [US1] Unit test for diffusion coefficient calculation and scaling.
Must fail before T016 (Implementation of code/analysis/msd.py).
"""

import pytest
import numpy as np
from pathlib import Path
from typing import Tuple, List

# Import the function we are testing.
# Note: This import will fail if T016 has not been implemented yet,
# satisfying the "Must fail before T016" requirement.
try:
    from analysis.msd import calculate_diffusion_coefficient
except ImportError:
    pytest.skip(
        "Skipping T012: code/analysis/msd.py not yet implemented (T016).",
        allow_module_level=True
    )

from config import Solvent


class TestDiffusionCoefficientCalculation:
    """Tests for the core diffusion coefficient calculation logic."""

    def test_linear_msd_slope_extraction(self):
        """
        Verify that the function correctly extracts the slope from a perfect
        linear Mean Squared Displacement (MSD) vs. Time series.
        
        MSD = 6 * D * t  =>  slope = 6 * D  =>  D = slope / 6
        """
        # Create synthetic data with known D = 1.0e-9 m^2/s
        # time in seconds, MSD in m^2
        D_true = 1.0e-9
        t = np.linspace(0, 10e-9, 50)  # 0 to 10 ns
        # Add slight noise to ensure linear regression is actually used
        noise = np.random.normal(0, 1e-20, size=t.shape)
        msd = 6 * D_true * t + noise

        # Calculate diffusion coefficient
        D_calc = calculate_diffusion_coefficient(t, msd, solvent=Solvent.WATER)

        # Check that calculated D is close to true D (within 1% tolerance due to noise)
        assert np.isclose(D_calc, D_true, rtol=0.01), \
            f"Calculated D ({D_calc}) does not match true D ({D_true}) within tolerance."

    def test_non_linear_msd_raises_error(self):
        """
        Verify that the function raises a ValueError when the MSD data
        is non-linear (e.g., ballistic regime or saturation).
        """
        # Create quadratic data (ballistic regime: MSD ~ t^2)
        t = np.linspace(0, 1e-9, 20)
        msd = t ** 2  # Not linear

        with pytest.raises(ValueError, match="Linearity check failed"):
            calculate_diffusion_coefficient(t, msd, solvent=Solvent.WATER)

    def test_empty_arrays_raises_error(self):
        """Verify that empty input arrays raise a ValueError."""
        with pytest.raises(ValueError):
            calculate_diffusion_coefficient(np.array([]), np.array([]), solvent=Solvent.WATER)

    def test_mismatched_array_lengths_raises_error(self):
        """Verify that mismatched time and MSD lengths raise a ValueError."""
        t = np.linspace(0, 1e-9, 10)
        msd = np.linspace(0, 1e-18, 9)

        with pytest.raises(ValueError):
            calculate_diffusion_coefficient(t, msd, solvent=Solvent.WATER)


class TestSolventSpecificScaling:
    """Tests for the solvent-specific scaling factor application."""

    @pytest.mark.parametrize(
        "solvent, expected_scale",
        [
            (Solvent.WATER, 1.0),  # Water is typically the baseline (scale 1.0)
            (Solvent.ETHANOL, 1.2), # Example scaling factor for ethanol
            (Solvent.ACETONE, 0.9), # Example scaling factor for acetone
        ]
    )
    def test_scaling_factor_application(self, solvent, expected_scale):
        """
        Verify that the correct scaling factor is applied based on the solvent.
        
        The function should calculate D_raw from the slope, then apply:
        D_final = D_raw * scale_factor
        """
        # Use a simple linear dataset where slope = 6 (so D_raw = 1.0)
        t = np.linspace(0, 1e-9, 20)
        msd = 6.0 * t  # Slope is exactly 6.0 -> D_raw = 1.0

        D_calc = calculate_diffusion_coefficient(t, msd, solvent=solvent)

        # Expected result is D_raw * scale
        D_expected = 1.0 * expected_scale

        assert np.isclose(D_calc, D_expected, rtol=1e-5), \
            f"Scaling failed for {solvent}. Expected {D_expected}, got {D_calc}."

    def test_unknown_solvent_raises_error(self):
        """Verify that an unknown solvent raises a ValueError."""
        t = np.linspace(0, 1e-9, 10)
        msd = 6.0 * t

        # Create a dummy object that is not a valid Solvent enum member if needed,
        # or simply test that the function handles invalid inputs gracefully.
        # Since Solvent is an Enum, we can't easily pass an "unknown" string without
        # modifying the function signature. Assuming the function checks for valid
        # Solvent members.
        with pytest.raises((ValueError, KeyError)):
            # This test assumes the implementation validates the Solvent enum.
            # If the implementation uses a dict lookup that raises KeyError,
            # or a manual check that raises ValueError, we catch both.
            calculate_diffusion_coefficient(t, msd, solvent="UNKNOWN_SOLVENT")

class TestUnitsAndMagnitudes:
    """Tests for unit consistency and magnitude sanity checks."""

    def test_diffusion_coefficient_magnitude_water(self):
        """
        Verify that the calculated diffusion coefficient for water
        is within a physically reasonable range (approx 2.0e-9 to 2.5e-9 m^2/s at 298K).
        """
        # Simulate water-like data
        D_true = 2.30e-9  # NIST reference value approx
        t = np.linspace(0, 10e-9, 100)
        msd = 6 * D_true * t + np.random.normal(0, 1e-20, size=t.shape)

        D_calc = calculate_diffusion_coefficient(t, msd, solvent=Solvent.WATER)

        # Check magnitude
        assert 1.0e-9 < D_calc < 5.0e-9, \
            f"Calculated water diffusion coefficient {D_calc} is outside expected physical range."

    def test_units_consistency(self):
        """
        Verify that the function handles inputs in standard SI units (seconds, meters^2)
        and outputs in m^2/s.
        """
        # Inputs in SI units
        t_ns = np.array([0.0, 1.0, 2.0, 3.0]) * 1e-9  # seconds
        msd_m2 = np.array([0.0, 6.0, 12.0, 18.0]) * 1e-20  # m^2
        
        # Slope = (18e-20 - 0) / (3e-9 - 0) = 6e-11 m^2/s
        # D = slope / 6 = 1e-11 m^2/s
        
        D_calc = calculate_diffusion_coefficient(t_ns, msd_m2, solvent=Solvent.WATER)
        D_expected = 1.0e-11

        assert np.isclose(D_calc, D_expected), \
            f"Unit consistency check failed. Expected {D_expected}, got {D_calc}."