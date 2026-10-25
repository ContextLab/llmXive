"""
Shim module providing the legacy API expected by the unit‑test suite.
It forwards calls to the new implementation in ``code.simulation.generator``.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict

import numpy as np

from code.simulation.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    lorenz_ode,
    generate_trajectory,
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


def lorenz_ode_single(
    t: float,
    y: np.ndarray,
    *,
    sigma: float = 10.0,
    rho: float = 28.0,
    beta: float = 8.0 / 3.0,
) -> np.ndarray:
    """
    Derivative for a *single* Lorenz oscillator (N = 1).

    Parameters
    ----------
    t : float
        Current time (unused – the system is autonomous).
    y : np.ndarray
        State vector of length 3 (``[x, y, z]``).
    sigma, rho, beta : float
        Classic Lorenz parameters; default to the canonical values.

    Returns
    -------
    np.ndarray
        Time derivative ``[dx/dt, dy/dt, dz/dt]``.
    """
    x, y_, z = y
    dx = sigma * (y_ - x)
    dy = x * (rho - z) - y_
    dz = x * y_ - beta * z
    return np.array([dx, dy, dz])


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
    Wrapper that forwards to the full coupled‑oscillator implementation.
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
    Produce random initial conditions using the same statistical model as the
    core generator (Gaussian perturbations around ``[1, 1, 1]`` for each oscillator).

    Parameters
    ----------
    N : int
        Number of coupled oscillators.
    seed : int, optional
        Seed for reproducibility.

    Returns
    -------
    np.ndarray
        Flattened initial state vector of shape ``(3 * N,)``.
    """
    rng = np.random.default_rng(seed)
    base = np.array([1.0, 1.0, 1.0])
    init = rng.normal(loc=base, scale=0.5, size=(N, 3))
    return init.ravel()


def inject_gaussian_noise(state_shape: tuple, sigma_noise: float) -> np.ndarray:
    """
    Generate an additive Gaussian noise array of the requested shape.

    Parameters
    ----------
    state_shape : tuple
        Desired shape, e.g. ``(n_samples, n_dim)``.
    sigma_noise : float
        Standard deviation of the zero‑mean Gaussian noise.

    Returns
    -------
    np.ndarray
        Noise array; zeros when ``sigma_noise == 0``.
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
    coupling_strength: float = 0.0,
    coupling_topology: str = "ring",
    seed: int | None = None,
) -> Dict[str, Any]:
    """
    Run a single trajectory using the core generator and return a legacy‑compatible
    dictionary.

    The returned dictionary contains the keys used by the historic test suite:

    - ``"trajectory"`` – the noisy state matrix (shape ``(n_steps, 3*N)``)
    - ``"time"``       – the time vector corresponding to the rows of ``trajectory``

    All arguments are passed straight through to
    :func:`code.simulation.generator.generate_trajectory`.
    """
    traj: TrajectoryData = generate_trajectory(
        N=N_oscillators,
        t_start=0.0,
        t_end=max_time,
        dt=dt,
        sigma_noise=sigma_noise,
        coupling_strength=coupling_strength,
        coupling_topology=coupling_topology,
        seed=seed,
        rtol=rtol,
        atol=atol,
    )
    return {"trajectory": traj.state, "time": traj.time}


def validate_trajectory(trajectory: np.ndarray, threshold: float = 20.0) -> bool:
    """
    Verify that every state vector lies within the allowed Euclidean norm.
    Raises :class:`UnphysicalTrajectoryError` if the check fails.

    Parameters
    ----------
    trajectory : np.ndarray
        Array of shape ``(n_steps, dim)``.
    threshold : float, optional
        Upper bound on the norm (default 20.0).

    Returns
    -------
    bool
        ``True`` if the trajectory is bounded.
    """
    norms = np.linalg.norm(trajectory, axis=1)
    if np.any(norms > threshold):
        raise UnphysicalTrajectoryError(
            f"Unphysical trajectory: norm exceeded {threshold}"
        )
    return True
