"""
data/generator.py
-----------------
Compatibility layer exposing the trajectory generation API expected by the
unit tests. Internally it re‑uses the implementation in
``code/simulation/generator.py`` which provides the fully featured
coupled Lorenz system, noise injection, and unphysical‑trajectory guards.

The public symbols match the original test suite expectations:

- ``HighNoiseWarning`` – warning emitted when ``sigma_noise > 0.1``.
- ``UnphysicalTrajectoryError`` – raised when any state norm exceeds 20.0.
- ``TrajectoryData`` – dataclass container for a generated trajectory.
- ``lorenz_ode_single`` – ODE for a single Lorenz oscillator.
- ``coupled_lorenz_ode`` – ODE for an arbitrary number of coupled oscillators.
- ``generate_initial_conditions`` – helper to create reproducible initial states.
- ``inject_gaussian_noise`` – generate additive Gaussian noise of a given shape.
- ``integrate_trajectory`` – deterministic integration (no file I/O) returning a dict.
- ``validate_trajectory`` – checks a state array for unphysical divergence.

The functions are thin wrappers around the core implementation in
``code/simulation/generator.py`` to keep a single source of truth.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Tuple, Dict, Any

import numpy as np

# Import the core implementation
from code.simulation.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    lorenz_ode,
    generate_trajectory,
    _default_lorenz_parameters,
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
    sigma: float | None = None,
    rho: float | None = None,
    beta: float | None = None,
) -> np.ndarray:
    """
    Right‑hand side of the classic (single) Lorenz system.

    Parameters
    ----------
    t : float
        Current time (unused, required by ``solve_ivp``).
    y : np.ndarray
        State vector ``[x, y, z]``.
    sigma, rho, beta : float, optional
        Lorenz parameters; defaults to the classic values if ``None``.

    Returns
    -------
    np.ndarray
        Derivative ``[dx/dt, dy/dt, dz/dt]``.
    """
    # Re‑use the generic ``lorenz_ode`` with ``N=1`` and no coupling.
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
    Wrapper matching the signature used in the original test suite.
    Delegates to :func:`code.simulation.generator.lorenz_ode`.
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
    Produce a reproducible random initial condition for ``N`` coupled
    Lorenz oscillators.

    Parameters
    ----------
    N : int
        Number of oscillators.
    seed : int, optional
        Seed for the RNG; if ``None`` system entropy is used.

    Returns
    -------
    np.ndarray
        Flattened initial state of shape ``(3 * N,)``.
    """
    rng = np.random.default_rng(seed)
    # The implementation in the core module is private; we replicate its
    # logic here to keep the public API stable.
    base = np.array([1.0, 1.0, 1.0])
    init = rng.normal(loc=base, scale=0.5, size=(N, 3))
    return init.ravel()


def inject_gaussian_noise(state_shape: Tuple[int, int], sigma_noise: float, seed: int | None = None) -> np.ndarray:
    """
    Generate additive Gaussian noise with a given standard deviation.

    Parameters
    ----------
    state_shape : tuple
        Desired shape of the noise array, e.g. ``(n_samples, n_dim)``.
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
    Deterministic integration of the coupled Lorenz system (optionally
    with additive noise). Returns a plain dictionary rather than a
    ``TrajectoryData`` instance so that the legacy test suite can work
    with a simple ``{'trajectory': ..., 'time': ...}`` structure.

    Parameters
    ----------
    initial_state : np.ndarray
        Flattened initial condition (shape ``(3 * N,)``).
    max_time : float
        End time of the integration interval.
    dt : float
        Desired output spacing (passed to ``t_eval``).
    N_oscillators : int
        Number of coupled oscillators.
    sigma_noise : float, optional
        Standard deviation of additive Gaussian noise.
    rtol, atol : float, optional
        Solver tolerances.
    coupling_strength, coupling_topology : float / str, optional
        Coupling configuration.
    seed : int, optional
        RNG seed for reproducibility (used for noise generation only).

    Returns
    -------
    dict
        ``{'trajectory': np.ndarray, 'time': np.ndarray}`` where
        ``trajectory`` has shape ``(n_steps, 3 * N)``.
    """
    # Re‑use the core generator but supply the pre‑computed initial state.
    # The core ``generate_trajectory`` creates its own initial condition,
    # so we perform a small manual integration here to honour the caller‑
    # supplied ``initial_state``.
    from scipy.integrate import solve_ivp

    # Emit warning if needed (mirrors core behaviour)
    if sigma_noise > 0.1:
        warnings.warn(
            f"High noise level (σ={sigma_noise}) may produce unphysical trajectories.",
            HighNoiseWarning,
        )

    # Time points
    t_eval = np.arange(0.0, max_time + dt, dt)

    sol = solve_ivp(
        fun=lambda t, y: lorenz_ode(
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

    # State matrix (time, dim)
    state = sol.y.T

    # Inject noise if requested
    if sigma_noise > 0.0:
        rng = np.random.default_rng(seed)
        noise = rng.normal(loc=0.0, scale=sigma_noise, size=state.shape)
        state = state + noise

    return {"trajectory": state, "time": sol.t}


def validate_trajectory(state: np.ndarray) -> None:
    """
    Validate that a trajectory does not become unphysical.

    Parameters
    ----------
    state : np.ndarray
        Trajectory array of shape ``(n_steps, dim)``.

    Raises
    ------
    UnphysicalTrajectoryError
        If any state norm exceeds the bound of 20.0.
    """
    norms = np.linalg.norm(state, axis=1)
    if np.any(norms > 20.0):
        raise UnphysicalTrajectoryError(
            f"Unphysical trajectory: state norm exceeded 20.0 (max={norms.max():.3f})"
        )