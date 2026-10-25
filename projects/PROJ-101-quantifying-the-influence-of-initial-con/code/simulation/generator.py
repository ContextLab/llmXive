"""
code/simulation/generator.py
--------------------------------
Implementation of the coupled Lorenz system and a trajectory generator
as required by task T006, now wired with stability guards from
``code.utils.stability`` (task T007).

The module provides:
- ``lorenz_ode``: computes the time derivative for a single coupled
  Lorenz oscillator (or a chain of oscillators) at a given state.
- ``generate_trajectory``: integrates the coupled system using
  ``scipy.integrate.solve_ivp`` with method ``'DOP853'`` and the
  tolerances ``rtol=1e-9`` and ``atol=1e-12``.  Additive Gaussian noise
  of user‑specified standard deviation ``sigma_noise`` is injected after
  the deterministic integration.  The function now uses the
  ``raise_if_unphysical`` and ``check_noise_level`` guards from
  ``code.utils.stability`` to enforce the project‑specific contracts.

The public API matches the specification in ``tasks.md`` and can be
imported as:

    from simulation.generator import lorenz_ode, generate_trajectory

The returned ``TrajectoryData`` dataclass contains all information
required by downstream pipeline steps (time vector, state matrix,
noise level, etc.).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Callable, Tuple

import numpy as np
from scipy.integrate import solve_ivp

# Local imports of the stability guards
from ..utils.stability import raise_if_unphysical, check_noise_level

__all__ = ["HighNoiseWarning", "UnphysicalTrajectoryError",
           "TrajectoryData", "lorenz_ode", "generate_trajectory"]


class HighNoiseWarning(UserWarning):
    """Warning raised when the injected noise level exceeds the safe threshold.

    The project specification defines a threshold of ``σ_noise > 0.1``.
    """
    pass


class UnphysicalTrajectoryError(RuntimeError):
    """Raised when any state vector norm exceeds the allowed bound (20.0)."""
    pass


@dataclass
class TrajectoryData:
    """Container for a generated trajectory.

    Attributes
    ----------
    time : np.ndarray
        1‑D array of time points (shape ``(n_steps,)``).
    state : np.ndarray
        2‑D array with shape ``(n_steps, 3 * N)`` where ``N`` is the number
        of coupled Lorenz oscillators.
    noise_level : float
        Standard deviation of the additive Gaussian noise (``σ_noise``).
    N_oscillators : int
        Number of coupled Lorenz oscillators.
    coupling_strength : float
        Strength of the linear coupling between neighbours.
    seed : int
        Random seed used for noise generation (and for reproducible
        initial conditions).
    is_clean : bool
        ``True`` when ``sigma_noise == 0``.
    """
    time: np.ndarray
    state: np.ndarray
    noise_level: float
    N_oscillators: int
    coupling_strength: float
    seed: int
    is_clean: bool


def _default_lorenz_parameters() -> Tuple[float, float, float]:
    """Standard Lorenz parameters (σ, ρ, β)."""
    sigma = 10.0
    rho = 28.0
    beta = 8.0 / 3.0
    return sigma, rho, beta


def lorenz_ode(
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
    Compute the right‑hand side of the coupled Lorenz ODEs.

    Parameters
    ----------
    t : float
        Current time (required by ``solve_ivp`` but unused for the
        autonomous Lorenz system).
    y : np.ndarray
        Flattened state vector of shape ``(3 * N,)`` ordered as
        ``[x1, y1, z1, x2, y2, z2, …]``.
    N : int
        Number of coupled oscillators.
    coupling_strength : float, optional
        Linear coupling coefficient between neighbours.  ``0.0`` yields
        independent Lorenz systems.
    coupling_topology : str, optional
        Currently only ``'ring'`` (periodic nearest‑neighbour) is
        supported.
    sigma, rho, beta : float, optional
        Lorenz parameters; if ``None`` the classic values are used.

    Returns
    -------
    np.ndarray
        Derivative vector ``dy/dt`` with the same shape as ``y``.
    """
    if sigma is None or rho is None or beta is None:
        sigma, rho, beta = _default_lorenz_parameters()

    # Reshape to (N, 3) for easier indexing
    y = y.reshape(N, 3)
    dx = np.empty_like(y)

    # Compute the uncoupled Lorenz dynamics for each oscillator
    dx[:, 0] = sigma * (y[:, 1] - y[:, 0])          # ẋ
    dx[:, 1] = y[:, 0] * (rho - y[:, 2]) - y[:, 1]  # ẏ
    dx[:, 2] = y[:, 0] * y[:, 1] - beta * y[:, 2]   # ż

    # Add linear coupling between neighbours if requested
    if coupling_strength != 0.0:
        # Periodic (ring) topology: each oscillator couples to its two
        # immediate neighbours.
        if coupling_topology != "ring":
            raise ValueError(
                f"Unsupported coupling_topology '{coupling_topology}'. "
                "Only 'ring' is implemented."
            )
        # Shifted views for neighbours
        left = np.roll(y, shift=1, axis=0)
        right = np.roll(y, shift=-1, axis=0)

        # Simple diffusive coupling on each of the three state
        # variables.
        dx += coupling_strength * (left - 2 * y + right)

    # Return flattened derivative
    return dx.ravel()


def _generate_initial_conditions(N: int, rng: np.random.Generator) -> np.ndarray:
    """
    Produce a random initial condition for ``N`` coupled Lorenz oscillators.

    The classic Lorenz attractor is typically seeded around the origin.
    We draw each component from a normal distribution with modest
    variance to avoid immediate divergence.

    Parameters
    ----------
    N : int
        Number of oscillators.
    rng : np.random.Generator
        Random number generator for reproducibility.

    Returns
    -------
    np.ndarray
        Flattened initial state vector of shape ``(3 * N,)``.
    """
    # Small random perturbations around the canonical point (1, 1, 1)
    base = np.array([1.0, 1.0, 1.0])
    init = rng.normal(loc=base, scale=0.5, size=(N, 3))
    return init.ravel()


def _inject_noise(
    state: np.ndarray,
    sigma_noise: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Additive Gaussian noise with standard deviation ``sigma_noise`` to
    each component of the state matrix.

    Parameters
    ----------
    state : np.ndarray
        Deterministic state matrix of shape ``(n_steps, 3 * N)``.
    sigma_noise : float
        Standard deviation of the zero‑mean Gaussian noise.
    rng : np.random.Generator
        RNG for reproducibility.

    Returns
    -------
    np.ndarray
        Noisy state matrix of the same shape as ``state``.
    """
    if sigma_noise == 0.0:
        return state

    noise = rng.normal(loc=0.0, scale=sigma_noise, size=state.shape)
    return state + noise


def generate_trajectory(
    *,
    N: int,
    t_start: float,
    t_end: float,
    dt: float,
    sigma_noise: float = 0.0,
    coupling_strength: float = 0.0,
    coupling_topology: str = "ring",
    seed: int | None = None,
    rtol: float = 1e-9,
    atol: float = 1e-12,
) -> TrajectoryData:
    """
    Generate a single trajectory of the coupled Lorenz system.

    The integration uses ``scipy.integrate.solve_ivp`` with the
    Dormand‑Prince 8(5,3) method ``'DOP853'`` and the specified
    tolerances.  After the deterministic integration, additive Gaussian
    noise of standard deviation ``sigma_noise`` is injected.

    The function performs the following checks:

    * If ``sigma_noise > 0.1`` a :class:`HighNoiseWarning` is issued via
      ``check_noise_level``.
    * After each integration phase (deterministic and noisy) the
      ``raise_if_unphysical`` guard is called; it raises
      :class:`UnphysicalTrajectoryError` if any state norm exceeds
      ``20.0``.
    * If any state norm exceeds ``20.0`` a
      :class:`UnphysicalTrajectoryError` is raised.

    Parameters
    ----------
    N : int
        Number of coupled Lorenz oscillators.
    t_start, t_end : float
        Integration interval.
    dt : float
        Desired output time step (the solver returns values at these
        evenly spaced points via the ``t_eval`` argument).
    sigma_noise : float, optional
        Standard deviation of the additive Gaussian observation noise.
    coupling_strength : float, optional
        Linear coupling coefficient between neighbours.
    coupling_topology : str, optional
        Currently only ``'ring'`` is supported.
    seed : int, optional
        Random seed for initial condition and noise generation.
    rtol, atol : float, optional
        Relative and absolute tolerances for ``solve_ivp``.

    Returns
    -------
    TrajectoryData
        Dataclass instance containing time, state, and metadata.
    """
    if seed is None:
        seed = np.random.SeedSequence().entropy  # system randomness
    rng = np.random.default_rng(seed)

    # Emit warning for high noise levels (strictly greater than 0.1)
    check_noise_level(sigma_noise)

    # Initial condition
    y0 = _generate_initial_conditions(N, rng)

    # Time points where we want the solution
    t_eval = np.arange(t_start, t_end + dt, dt)

    # Integrate the deterministic system
    sol = solve_ivp(
        fun=lambda t, y: lorenz_ode(
            t,
            y,
            N=N,
            coupling_strength=coupling_strength,
            coupling_topology=coupling_topology,
        ),
        t_span=(t_start, t_end),
        y0=y0,
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
    )

    if not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message}")

    # Convert to (time, dim) shape
    state_det = sol.y.T  # (n_steps, 3*N)

    # Guard against unphysical deterministic trajectory
    raise_if_unphysical(state_det, threshold=20.0)

    # Inject noise (if any)
    noisy_state = _inject_noise(state_det, sigma_noise, rng)

    # Guard against unphysical trajectory after noise injection
    raise_if_unphysical(noisy_state, threshold=20.0)

    return TrajectoryData(
        time=sol.t,
        state=noisy_state,
        noise_level=sigma_noise,
        N_oscillators=N,
        coupling_strength=coupling_strength,
        seed=seed,
        is_clean=sigma_noise == 0.0,
    )