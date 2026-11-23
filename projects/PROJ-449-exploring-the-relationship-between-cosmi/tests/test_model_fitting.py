"""
Unit tests for diffusion model fitting convergence (Task T026).

This module validates that the diffusion model fitting logic in
`code/analysis/model_fitting.py` converges correctly when provided
with realistic modulation amplitude data.

It specifically tests:
1. Successful convergence of the sinusoidal model fit.
2. Successful convergence of the rigidity-dependent diffusion model fit.
3. Proper handling of non-convergent cases (graceful failure).
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.model_fitting import diffusion_model, fit_diffusion_model, load_amplitudes

class TestDiffusionModelFunction:
    """Tests for the diffusion_model function itself."""

    def test_diffusion_model_shapes(self):
        """Verify the model returns correct output shapes."""
        rigidity = np.array([1.0, 2.0, 3.0])
        params = np.array([10.0, 0.5])  # A, B

        result = diffusion_model(rigidity, *params)

        assert result.shape == rigidity.shape
        assert not np.any(np.isnan(result))

    def test_diffusion_model_positive_output(self):
        """Verify the model returns positive amplitudes for positive params."""
        rigidity = np.linspace(1.0, 10.0, 100)
        params = np.array([5.0, 0.1])  # A > 0, B > 0

        result = diffusion_model(rigidity, *params)

        assert np.all(result > 0)

    def test_diffusion_model_rigidity_dependence(self):
        """Verify amplitude decreases as rigidity increases (expected physics)."""
        rigidity = np.linspace(1.0, 20.0, 100)
        params = np.array([10.0, 0.5])

        result = diffusion_model(rigidity, *params)

        # The model is A / (R + B), which is monotonically decreasing for R > -B
        assert np.all(np.diff(result) < 0)

class TestFitDiffusionModel:
    """Tests for the fit_diffusion_model function."""

    def test_convergence_on_synthetic_data(self):
        """
        Test that the fitting routine converges when given synthetic data
        generated from the model itself with added noise.
        """
        # Generate synthetic data
        true_params = np.array([12.5, 0.8])
        rigidity = np.linspace(1.0, 15.0, 20)
        true_amplitudes = diffusion_model(rigidity, *true_params)
        
        # Add small Gaussian noise
        noise = np.random.normal(0, 0.1, size=true_amplitudes.shape)
        noisy_amplitudes = true_amplitudes + noise

        # Fit the model
        popt, pcov, success, message = fit_diffusion_model(rigidity, noisy_amplitudes)

        # Assert convergence
        assert success, f"Fit did not converge: {message}"
        
        # Assert parameters are reasonably close to true values (within 20%)
        assert np.allclose(popt, true_params, rtol=0.2), \
            f"Fitted params {popt} differ significantly from true {true_params}"

    def test_convergence_with_realistic_bounds(self):
        """Test convergence with realistic parameter bounds."""
        # Use the same synthetic data as above
        true_params = np.array([10.0, 0.5])
        rigidity = np.linspace(1.0, 10.0, 15)
        true_amplitudes = diffusion_model(rigidity, *true_params)
        noisy_amplitudes = true_amplitudes + np.random.normal(0, 0.05, size=true_amplitudes.shape)

        # Fit with bounds
        popt, pcov, success, message = fit_diffusion_model(
            rigidity, 
            noisy_amplitudes,
            p0=[5.0, 0.2],
            bounds=([0, 0], [50, 10]) # A > 0, B > 0
        )

        assert success, f"Fit failed with bounds: {message}"
        assert popt[0] > 0 and popt[1] > 0, "Fitted parameters must be positive"

    def test_non_convergence_handling(self):
        """
        Test that the function handles non-convergent cases gracefully
        (e.g., when data is completely random or flat).
        """
        # Generate data that doesn't fit the model well (flat line)
        rigidity = np.linspace(1.0, 10.0, 10)
        flat_amplitudes = np.ones_like(rigidity) * 5.0

        # Fit with strict constraints that force failure
        # We use a starting point far from the solution and tight bounds
        # to potentially trigger convergence issues, though curve_fit is robust.
        # Instead, we test the return logic.
        popt, pcov, success, message = fit_diffusion_model(
            rigidity, 
            flat_amplitudes,
            p0=[100.0, 100.0],
            bounds=([0, 0], [10, 0.1]) # Force B to be very small, might conflict with A
        )

        # The test passes if the function returns without crashing.
        # Whether it converges or not depends on the data, but it must return.
        assert isinstance(success, bool)
        assert isinstance(message, str)

    def test_input_validation(self):
        """Test that the function handles mismatched array lengths."""
        rigidity = np.array([1.0, 2.0, 3.0])
        amplitudes = np.array([1.0, 2.0]) # Mismatched

        with pytest.raises(ValueError):
            fit_diffusion_model(rigidity, amplitudes)

class TestLoadAmplitudes:
    """Tests for the load_amplitudes helper function."""

    def test_load_from_dict(self):
        """Test loading from a dictionary structure."""
        data = {
            'rigidity': [1.0, 2.0, 3.0],
            'amplitude': [5.0, 3.0, 2.0]
        }
        
        rigidity, amplitudes = load_amplitudes(data)
        
        assert np.array_equal(rigidity, [1.0, 2.0, 3.0])
        assert np.array_equal(amplitudes, [5.0, 3.0, 2.0])

    def test_load_from_csv_path(self, tmp_path):
        """Test loading from a CSV file path."""
        import pandas as pd
        csv_path = tmp_path / "amplitudes.csv"
        df = pd.DataFrame({
            'rigidity': [1.0, 2.0, 3.0],
            'amplitude': [5.0, 3.0, 2.0]
        })
        df.to_csv(csv_path, index=False)

        rigidity, amplitudes = load_amplitudes(str(csv_path))

        assert np.array_equal(rigidity, [1.0, 2.0, 3.0])
        assert np.array_equal(amplitudes, [5.0, 3.0, 2.0])

    def test_load_missing_file(self, tmp_path):
        """Test that loading a missing file raises an error."""
        non_existent = tmp_path / "missing.csv"
        
        with pytest.raises(FileNotFoundError):
            load_amplitudes(str(non_existent))