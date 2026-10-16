"""
data/generator.py
-----------------
Compatibility wrapper for the unit‑test suite.

The original implementation of the coupled Lorenz system lives in
``code.simulation.generator``.  The test suite expects a module
``data.generator`` exposing a slightly different API (functions with
names such as ``lorenz_ode_single`` and ``integrate_trajectory``).
This file re‑exports the core functionality and provides thin
shims that match the expected signatures while delegating all heavy
lifting to the implementation in ``code.simulation.generator``.

All public symbols listed in ``__all__`` are imported by the tests:
    - HighNoiseWarning
    - UnphysicalTrajectoryError
    - TrajectoryData
    - lorenz_ode_single
    - coupled_lorenz_ode
    - generate_initial_conditions
    - inject_gaussian_noise
    - integrate_trajectory
    - validate_trajectory

The wrappers preserve the exact behaviour required by the
specification (method ``'DOP853'``, tolerances ``rtol=1e-9``,
``atol=1e-12``, noise injection, and the 20.0 norm bound).
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, Tuple

import numpy as np

# Re‑export the core classes / exceptions so that ``from data.generator
# import HighNoiseWarning`` works exactly as the tests expect.
from code.simulation.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    lorenz_ode,
    generate_trajectory,
    _generate_initial_conditions,
    _inject_noise,
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
# Helper wrappers matching the test‑suite API
# ----------------------------------------------------------------------
def lorenz_ode_single(
    t: float,
    y: np.ndarray,
    *,
    sigma: float | None = None,
    rho: float | None = None,
    beta: float | None = None,
) -> np.ndarray:
    """
    Derivative for a *single* Lorenz oscillator (no coupling).

    Parameters
    ----------
    t : float
        Current time (unused – the system is autonomous).
    y : np.ndarray
        State vector of length 3 (``[x, y, z]``).
    sigma, rho, beta : float, optional
        Lorenz parameters; defaults are the classic values.

    Returns
    -------
    np.ndarray
        Derivative ``dy/dt`` of shape ``(3,)``.
    """
    # ``lorenz_ode`` expects a flattened array of length 3*N.
    # We delegate to it with ``N=1`` and ``coupling_strength=0``.
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
    sigma: float | None = None,
    rho: float | None = None,
    beta: float | None = None,
) -> np.ndarray:
    """
    Derivative for a chain of ``N`` coupled Lorenz oscillators.

    This is a thin wrapper around :func:`code.simulation.generator.lorenz_ode`
    that simply forwards the arguments.
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

def generate_initial_conditions(N: int, seed: int | None = None) -> np.ndarray:
    """
    Produce reproducible random initial conditions for ``N`` oscillators.

    The implementation mirrors the private helper used by the core
    generator, ensuring identical statistical properties.
    """
    rng = np.random.default_rng(seed)
    return _generate_initial_conditions(N, rng)

def inject_gaussian_noise(
    state_shape: Tuple[int, int],
    sigma_noise: float,
    seed: int | None = None,
) -> np.ndarray:
    """
    Generate additive Gaussian noise.

    Parameters
    ----------
    state_shape : Tuple[int, int]
        Desired shape ``(n_steps, 3*N)``.
    sigma_noise : float
        Standard deviation of the zero‑mean Gaussian noise.
    seed : int, optional
        RNG seed for reproducibility.

    Returns
    -------
    np.ndarray
        Noise array of the requested shape.
    """
    rng = np.random.default_rng(seed)
    if sigma_noise == 0.0:
        return np.zeros(state_shape)
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
    coupling_strength: float = 0.0,
    coupling_topology: str = "ring",
    seed: int | None = None,
) -> Dict[str, Any]:
    """
    Integrate a (possibly noisy) trajectory given an explicit initial state.

    This mirrors :func:`code.simulation.generator.generate_trajectory`
    but accepts a pre‑computed ``initial_state`` array instead of
    generating one internally.  The return value matches the
    expectations of the test suite: a dictionary with at least the key
    ``'trajectory'`` containing the state matrix (shape ``(n_steps,
    3*N)``).

    Parameters
    ----------
    initial_state : np.ndarray
        Flattened initial condition of shape ``(3*N,)``.
    max_time, dt, N_oscillators, sigma_noise, rtol, atol,
    coupling_strength, coupling_topology, seed : see
        :func:`code.simulation.generator.generate_trajectory`.

    Returns
    -------
    dict
        ``{'trajectory': <np.ndarray>, 'time': <np.ndarray>}``
    """
    if seed is None:
        seed = np.random.SeedSequence().entropy
    rng = np.random.default_rng(seed)

    # Emit warning for high noise levels (strictly greater than 0.1)
    if sigma_noise > 0.1:
        warnings.warn(
            f"High noise level (σ={sigma_noise}) may produce unphysical trajectories.",
            HighNoiseWarning,
        )

    # Time grid
    t_start = 0.0
    t_end = max_time
    t_eval = np.arange(t_start, t_end + dt, dt)

    # Integrate the deterministic part
    sol = solve_ivp(
        fun=lambda t, y: lorenz_ode(
            t,
            y,
            N=N_oscillators,
            coupling_strength=coupling_strength,
            coupling_topology=coupling_topology,
        ),
        t_span=(t_start, t_end),
        y0=initial_state,
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
    )

    if not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message}")

    # Check for unphysical divergence before noise
    norms = np.linalg.norm(sol.y, axis=0)
    if np.any(norms > 20.0):
        raise UnphysicalTrajectoryError(
            f"Unphysical trajectory: state norm exceeded 20.0 (max={norms.max():.3f})"
        )

    state = sol.y.T  # (time, dim)

    # Inject noise if requested
    if sigma_noise != 0.0:
        noise = _inject_noise(state, sigma_noise, rng)
        state = noise
    else:
        # Ensure a copy is returned to avoid accidental mutation
        state = np.copy(state)

    # Final bound check after noise injection
    if np.any(np.linalg.norm(state, axis=1) > 20.0):
        raise UnphysicalTrajectoryError(
            "Unphysical trajectory after noise injection: state norm exceeded 20.0"
        )

    return {"trajectory": state, "time": sol.t, "noise_level": sigma_noise}

def validate_trajectory(
    trajectory: np.ndarray,
    *,
    threshold: float = 20.0,
) -> None:
    """
    Validate that a trajectory respects the boundedness condition.

    Parameters
    ----------
    trajectory : np.ndarray
        State matrix of shape ``(n_steps, dim)``.
    threshold : float, optional
        Upper bound on the Euclidean norm of any state vector
        (default ``20.0`` as required by the specification).

    Raises
    ------
    UnphysicalTrajectoryError
        If any state norm exceeds ``threshold``.
    """
    if np.any(np.linalg.norm(trajectory, axis=1) > threshold):
        raise UnphysicalTrajectoryError(
            f"Trajectory norm exceeds allowed threshold of {threshold}"
        )