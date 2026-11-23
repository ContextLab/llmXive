"""
Unit tests for the trajectory generator (task T006/T007).

The tests verify:
* The empirical noise standard deviation matches the injected ``sigma_noise``.
* A noise‑free trajectory matches a reference deterministic integration.
* ``HighNoiseWarning`` is emitted for ``sigma_noise > 0.1``.
* ``UnphysicalTrajectoryError`` is raised when the state norm exceeds 20.0.
"""
import warnings

import numpy as np
import pytest

from code.data.generator import (
    generate_coupled_lorenz_trajectory,
    HighNoiseWarning,
    UnphysicalTrajectoryError,
)


@pytest.fixture
def rng():
    return np.random.default_rng(12345)


def test_noise_statistics(rng):
    N = 3
    sigma = 0.05
    traj = generate_coupled_lorenz_trajectory(N=N, sigma_noise=sigma, seed=0)
    # Compute empirical std‑dev of the added noise (state - deterministic part)
    # Re‑integrate deterministically for comparison
    clean = generate_coupled_lorenz_trajectory(N=N, sigma_noise=0.0, seed=0)
    noise = traj.state - clean.state
    empirical_std = np.std(noise)
    assert np.isclose(empirical_std, sigma, rtol=0.05)


def test_noise_free_accuracy():
    N = 3
    traj = generate_coupled_lorenz_trajectory(N=N, sigma_noise=0.0, seed=42)
    # Reference integration using the same ODE function but with tighter tolerances
    from scipy.integrate import solve_ivp

    def lorenz(t, y):
        # reuse the same ODE definition from the generator (no coupling)
        sigma = 10.0
        rho = 28.0
        beta = 8.0 / 3.0
        x, y_, z = y
        return [
            sigma * (y_ - x),
            x * (rho - z) - y_,
            x * y_ - beta * z,
        ]

    t_eval = np.arange(0.0, 1000.0 + 0.01, 0.01)
    y0 = traj.state[0]  # initial condition used by the generator
    ref = solve_ivp(
        lorenz,
        (0.0, 1000.0),
        y0,
        method="DOP853",
        t_eval=t_eval,
        rtol=1e-12,
        atol=1e-15,
    )
    assert np.allclose(traj.state, ref.y.T, atol=1e-9)


def test_high_noise_warning():
    N = 3
    sigma = 0.2
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        generate_coupled_lorenz_trajectory(N=N, sigma_noise=sigma, seed=1)
        assert any(issubclass(warn.category, HighNoiseWarning) for warn in w)


def test_unphysical_trajectory_error():
    N = 3
    # Choose a huge noise level that will inevitably push the norm > 20
    sigma = 1.5
    with pytest.raises(UnphysicalTrajectoryError):
        generate_coupled_lorenz_trajectory(N=N, sigma_noise=sigma, seed=2)
