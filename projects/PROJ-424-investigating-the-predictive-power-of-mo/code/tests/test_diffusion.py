"""
Unit tests for the diffusion analysis pipeline.

Two synthetic scenarios are exercised:

1. **Linear case** – perfect linear MSD with negligible noise.  The
   regression R² must exceed the 0.95 threshold, and the recovered
   diffusion coefficient should match the ground‑truth value within a
   tight tolerance.

2. **R²‑failure case** – an MSD curve that is deliberately noisy,
   yielding an R² below the threshold.  The analysis must report the
   ``convergence_failed`` status.
"""

import numpy as np
import pytest

# Import the public API we are testing.
from analysis.diffusion import analyze_diffusion

# The diffusion analysis relies on the low‑level MSD loader.  For the
# unit tests we monkey‑patch that loader to return deterministic synthetic
# data without needing a real trajectory file.
from analysis import msd

@pytest.fixture
def monkeypatch_msd_loader(monkeypatch):
    """
    Provide a helper that replaces ``load_trajectory_timeseries`` with a
    user‑supplied implementation.
    """
    def _set_loader(fake_func):
        monkeypatch.setattr(msd, "load_trajectory_timeseries", fake_func)
    return _set_loader

def test_linear_msd_success(monkeypatch_msd_loader):
    """
    Synthetic perfect linear MSD → R² > 0.95 → status = converged.
    """
    # Ground‑truth diffusion coefficient (m²/s).
    D_true = 2.5e-9
    # Convert to slope for t in ns: slope = 6 * D * 1e-9 (m²/ns)
    slope = 6.0 * D_true * 1e-9

    # Generate synthetic times (0‑10 ns, 101 points) and exact MSD.
    times = np.linspace(0, 10, 101)  # ns
    msd_vals = slope * times  # perfect linear MSD, no intercept

    def fake_loader(_):
        return times, msd_vals

    monkeypatch_msd_loader(fake_loader)

    result = analyze_diffusion("dummy_path")
    assert result["status"] == "converged"
    # R² should be (practically) 1.0
    assert result["r_squared"] > 0.99
    # Diffusion coefficient recovered from the slope should be close to D_true.
    assert np.isclose(result["d_calc_m2_s"], D_true, rtol=1e-6)

def test_msd_low_r2_failure(monkeypatch_msd_loader):
    """
    Add substantial random noise so that the regression R² falls below
    the required 0.95 threshold; the status must be ``convergence_failed``.
    """
    D_true = 1.8e-9
    slope = 6.0 * D_true * 1e-9

    rng = np.random.default_rng(42)
    times = np.linspace(0, 10, 101)
    # Add large noise (±30 % of the signal) to guarantee a low R².
    noise = rng.normal(scale=0.3 * slope * times.max(), size=times.shape)
    msd_vals = slope * times + noise

    def fake_loader(_):
        return times, msd_vals

    monkeypatch_msd_loader(fake_loader)

    result = analyze_diffusion("dummy_path")
    assert result["status"] == "convergence_failed"
    assert result["r_squared"] < 0.95
    # Even though the fit is poor, a diffusion coefficient is still
    # returned (it may be far from the truth).
    assert isinstance(result["d_calc_m2_s"], float)