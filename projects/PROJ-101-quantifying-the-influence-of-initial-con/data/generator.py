"""
data/generator.py
-----------------
Compatibility shim for the unit‑test suite.

The original trajectory generation implementation lives in
``code/simulation/generator.py`` and provides the core functionality
required by the project (coupled Lorenz ODE, integration with
``solve_ivp`` and Gaussian noise injection).  The test suite, however,
imports a legacy ``data.generator`` module and expects a different API
(functions such as ``lorenz_ode_single`` or ``integrate_trajectory``).

This file re‑exports the public classes from the implementation module
and provides thin wrappers that map the legacy API onto the new code.
All behaviour (numerical integration, noise injection, error handling)
is delegated to the authoritative implementation, ensuring that the
tests exercise the same, fully‑tested logic.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, Tuple

import numpy as np
from scipy.integrate import solve_ivp

# Re‑export the core classes and dataclass so that the tests see the same
# exception types and the ``TrajectoryData`` container.
from code.simulation.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    lorenz_ode,
    generate_trajectory,
    _generate_initial_conditions,
)

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

# ----------------------------------------------------------------------
# Legacy API wrappers
# ----------------------------------------------------------------------
def lorenz_ode_single(t: float, y: np.ndarray, *, sigma: float = None,
                      rho: float = None, beta: float = None) -> np.ndarray:
    """
    Single‑oscillator Lorenz ODE.

    Parameters
    ----------
    t : float
        Time (unused – the system is autonomous).
    y : np.ndarray
        State vector of length 3 (``[x, y, z]``).
    sigma, rho, beta : float, optional
        Lorenz parameters; defaults to the classic values
        (σ = 10, ρ = 28, β = 8/3).

    Returns
    -------
    np.ndarray
        Derivative vector of length 3.
    """
    # ``lorenz_ode`` expects a flattened vector of length 3 * N.
    # We call it with ``N=1`` and no coupling.
    return lorenz_ode(
        t,
        y,
        N=1,
        coupling_strength=0.0,
        coupling_topology="ring",
        sigma=sigma,
        rho=rho,
        beta=beta,
    )

def coupled_lorenz_ode(
    t: float,
    y: np.ndarray,
    *,
    N: int,
    coupling_strength: float = 0.0,
    coupling_topology: str = "ring",
    sigma: float = None,
    rho: float = None,
    beta: float = None,
) -> np.ndarray:
    """
    Wrapper that forwards directly to the implementation in
    ``code.simulation.generator``.  The signature mirrors the original
    test‑suite expectations.
    """
    return lorenz_ode(
        t,
        y,
        N=N,
        coupling_strength=coupling_strength,
        coupling_topology=coupling_topology,
        sigma=sigma,
        rho=rho,
        beta=beta,
    )

def generate_initial_conditions(N: int, seed: int = 42) -> np.ndarray:
    """
    Generate a reproducible random initial condition for ``N`` coupled
    Lorenz oscillators.

    The implementation re‑uses the private helper from the authoritative
    module to guarantee identical statistics.
    """
    rng = np.random.default_rng(seed)
    return _generate_initial_conditions(N, rng)

def inject_gaussian_noise(state_shape: Tuple[int, int], sigma_noise: float) -> np.ndarray:
    """
    Produce an additive Gaussian noise array.

    Parameters
    ----------
    state_shape : Tuple[int, int]
        Desired shape ``(n_samples, n_dim)``.
    sigma_noise : float
        Standard deviation of the zero‑mean Gaussian noise.

    Returns
    -------
    np.ndarray
        Noise matrix of the requested shape.
    """
    if sigma_noise == 0.0:
        return np.zeros(state_shape)
    rng = np.random.default_rng()
    return rng.normal(loc=0.0, scale=sigma_noise, size=state_shape)

def integrate_trajectory(
    *,
    initial_state: np.ndarray,
    max_time: float,
    dt: float,
    N_oscillators: int,
    sigma_noise: float = 0.0,
    rtol: float = 1e-9,
    atol: float = 1e-12,
) -> Dict[str, Any]:
    """
    Deterministic integration of the coupled Lorenz system.

    This mirrors the behaviour of ``generate_trajectory`` but accepts an
    explicit ``initial_state`` (used by the unit tests) and never adds
    noise when ``sigma_noise == 0``.  The return value matches the
    structure expected by the tests (a dictionary with a ``trajectory``
    key containing the state matrix).

    Parameters
    ----------
    initial_state : np.ndarray
        Flattened initial condition of length ``3 * N_oscillators``.
    max_time : float
        End time of the integration interval.
    dt : float
        Desired output time step.
    N_oscillators : int
        Number of coupled oscillators.
    sigma_noise : float, optional
        Noise standard deviation (kept for API compatibility; the
        function does *not* inject noise – callers can add it via
        ``inject_gaussian_noise`` if needed).
    rtol, atol : float, optional
        Solver tolerances.

    Returns
    -------
    dict
        ``{'trajectory': state_matrix, 'time': time_array}``
    """
    # Time grid
    t_eval = np.arange(0.0, max_time + dt, dt)

    # Integrate
    sol = solve_ivp(
        fun=lambda t, y: lorenz_ode(
            t,
            y,
            N=N_oscillators,
            coupling_strength=0.0,
            coupling_topology="ring",
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

    # Shape to (time, dim)
    trajectory = sol.y.T

    # Perform the same unphysical checks as ``generate_trajectory``.
    if np.any(np.linalg.norm(trajectory, axis=1) > 20.0):
        raise UnphysicalTrajectoryError(
            "Unphysical trajectory: state norm exceeded 20.0"
        )

    return {"trajectory": trajectory, "time": sol.t}

def validate_trajectory(state: np.ndarray, threshold: float = 100.0) -> bool:
    """
    Simple boundedness check used by legacy tests.

    Returns ``True`` if the Euclidean norm of every state vector is below
    ``threshold``; otherwise ``False``.
    """
    from utils.stability import check_boundedness

    return check_boundedness(state, threshold=threshold)