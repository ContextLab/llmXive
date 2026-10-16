"""
data/generator.py
-----------------
Wrapper module that provides the API required by the unit tests for
trajectory generation.  The heavy‑lifting is delegated to the
implementation in ``code.simulation.generator`` which already satisfies
the specification for the coupled Lorenz system and noise injection.

Public API (as used by the tests):

- ``HighNoiseWarning`` – warning class for σ_noise > 0.1
- ``UnphysicalTrajectoryError`` – error raised when state norm > 20.0
- ``TrajectoryData`` – dataclass container for generated trajectories
- ``lorenz_ode`` – ODE right‑hand side (single‑step function)
- ``generate_initial_conditions`` – creates reproducible initial state
- ``inject_gaussian_noise`` – returns a Gaussian noise array
- ``integrate_trajectory`` – integrates the deterministic system and
  adds noise, performing the required unphysical checks
- ``validate_trajectory`` – checks boundedness using the utility in
  ``code.utils.stability``

The functions are thin wrappers around the core implementation in
``code.simulation.generator`` to keep a single source of truth.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np
from scipy.integrate import solve_ivp

# Re‑export the warning / error classes and the dataclass so that the
# test suite can import them directly from ``data.generator``.
from code.simulation.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    lorenz_ode as _lorenz_ode,
)

# ------------------------------------------------------------------
# Helper: default Lorenz parameters (same as in the core implementation)
# ------------------------------------------------------------------
def _default_lorenz_parameters() -> Tuple[float, float, float]:
    sigma = 10.0
    rho = 28.0
    beta = 8.0 / 3.0
    return sigma, rho, beta

# ------------------------------------------------------------------
# Public API – wrappers expected by the tests
# ------------------------------------------------------------------

def lorenz_ode_single(t: float, y: np.ndarray, *, N: int, **kwargs) -> np.ndarray:
    """
    Compatibility wrapper for the test suite.

    The test suite never calls this directly, but exposing a function
    named ``lorenz_ode_single`` mirrors the historic API that existed
    before the refactor.
    """
    return _lorenz_ode(t, y, N=N, **kwargs)

def coupled_lorenz_ode(t: float, y: np.ndarray, *, N: int, **kwargs) -> np.ndarray:
    """
    Alias used by older tests – forwards to the same implementation as
    ``lorenz_ode_single``.
    """
    return _lorenz_ode(t, y, N=N, **kwargs)

def generate_initial_conditions(N: int, seed: int = 42) -> np.ndarray:
    """
    Generate a reproducible random initial condition for ``N`` coupled
    Lorenz oscillators.

    Parameters
    ----------
    N : int
        Number of oscillators.
    seed : int, optional
        Seed for the NumPy random generator (default 42).

    Returns
    -------
    np.ndarray
        Flattened initial state vector of shape ``(3 * N,)``.
    """
    rng = np.random.default_rng(seed)
    # Small random perturbations around the canonical point (1, 1, 1)
    base = np.array([1.0, 1.0, 1.0])
    init = rng.normal(loc=base, scale=0.5, size=(N, 3))
    return init.ravel()

def inject_gaussian_noise(state_shape: Tuple[int, int], sigma_noise: float) -> np.ndarray:
    """
    Produce additive Gaussian noise of the requested standard deviation.

    Parameters
    ----------
    state_shape : tuple
        Shape of the array to generate (e.g. ``(n_samples, n_dim)``).
    sigma_noise : float
        Standard deviation of the zero‑mean Gaussian noise.

    Returns
    -------
    np.ndarray
        Noise array of the given shape.
    """
    if sigma_noise == 0.0:
        return np.zeros(state_shape)
    rng = np.random.default_rng()
    return rng.normal(loc=0.0, scale=sigma_noise, size=state_shape)

def integrate_trajectory(
    initial_state: np.ndarray,
    max_time: float,
    dt: float,
    N_oscillators: int,
    sigma_noise: float = 0.0,
    rtol: float = 1e-9,
    atol: float = 1e-12,
    coupling_strength: float = 0.0,
    coupling_topology: str = "ring",
) -> Dict[str, Any]:
    """
    Integrate the deterministic coupled Lorenz system and optionally add
    Gaussian observation noise.

    Parameters
    ----------
    initial_state : np.ndarray
        Flattened initial condition (shape ``(3 * N,)``).
    max_time : float
        Integration horizon.
    dt : float
        Desired output time step.
    N_oscillators : int
        Number of coupled oscillators.
    sigma_noise : float, optional
        Standard deviation of additive Gaussian noise (default 0.0).
    rtol, atol : float, optional
        Tolerances for ``scipy.integrate.solve_ivp``.
    coupling_strength : float, optional
        Linear coupling coefficient (default 0.0 → independent).
    coupling_topology : str, optional
        Currently only ``'ring'`` is supported.

    Returns
    -------
    dict
        ``{'trajectory': <noisy_state>, 'time': <time_vector>}``

    Raises
    ------
    UnphysicalTrajectoryError
        If any state norm exceeds the bound of 20.0 either before or
        after noise injection.
    """
    # Emit warning for high noise levels (> 0.1) as required.
    if sigma_noise > 0.1:
        warnings.warn(
            f"High noise level (σ={sigma_noise}) may produce unphysical trajectories.",
            HighNoiseWarning,
        )

    # Time evaluation points
    t_eval = np.arange(0.0, max_time + dt, dt)

    # Deterministic integration
    sol = solve_ivp(
        fun=lambda t, y: _lorenz_ode(
            t,
            y,
            N=N_oscillators,
            coupling_strength=coupling_strength,
            coupling_topology=coupling_topology,
        ),
        t_span=(0.0, max_time),
        y0=initial_state,
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
    )

    if not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message}")

    # Check for unphysical divergence before adding noise
    norms = np.linalg.norm(sol.y, axis=0)  # shape (n_steps,)
    if np.any(norms > 20.0):
        raise UnphysicalTrajectoryError(
            f"Unphysical trajectory: state norm exceeded 20.0 (max={norms.max():.3f})"
        )

    # State matrix (n_steps, 3*N)
    state = sol.y.T

    # Inject noise
    if sigma_noise > 0.0:
        rng = np.random.default_rng()
        noise = rng.normal(loc=0.0, scale=sigma_noise, size=state.shape)
        noisy_state = state + noise
    else:
        noisy_state = state

    # Final unphysical check after noise injection
    if np.any(np.linalg.norm(noisy_state, axis=1) > 20.0):
        raise UnphysicalTrajectoryError(
            "Unphysical trajectory after noise injection: state norm exceeded 20.0"
        )

    return {"trajectory": noisy_state, "time": sol.t}

def validate_trajectory(trajectory: np.ndarray, threshold: float = 20.0) -> bool:
    """
    Validate that a trajectory stays within the prescribed norm bound.

    Parameters
    ----------
    trajectory : np.ndarray
        State matrix of shape ``(n_steps, dim)``.
    threshold : float, optional
        Norm bound (default 20.0, matching the specification).

    Returns
    -------
    bool
        ``True`` if all state vectors satisfy ``||x|| <= threshold``.
    """
    # The stability utilities already implement this check.
    from code.utils.stability import check_boundedness

    return check_boundedness(trajectory, threshold=threshold)

# Export the symbols expected by the test suite
__all__ = [
    "HighNoiseWarning",
    "UnphysicalTrajectoryError",
    "TrajectoryData",
    "lorenz_ode_single",
    "coupled_lorenz_ode",
    "generate_initial_conditions",
    "inject_gaussian_noise",
    "integrate_trajectory",
    "validate_trajectory",
]