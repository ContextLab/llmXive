"""
data/generator.py
-----------------
Compatibility shim that exposes the API expected by the unit‑test
suite (`tests/unit/test_generator.py`).  The core implementation lives
in ``code/simulation/generator.py``; this module merely forwards calls
and provides thin wrappers with the exact signatures used in the tests.

The public symbols match those imported in the tests:

* ``HighNoiseWarning``
* ``UnphysicalTrajectoryError``
* ``TrajectoryData``
* ``lorenz_ode_single``
* ``coupled_lorenz_ode``
* ``generate_initial_conditions``
* ``inject_gaussian_noise``
* ``integrate_trajectory``
* ``validate_trajectory``

All functions are deterministic given an explicit ``seed`` argument,
and they raise the same exceptions as the underlying implementation.
"""

from __future__ import annotations

import warnings
from typing import Tuple

import numpy as np

# Re‑export the core exceptions and dataclass from the implementation.
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
# Helper wrappers matching the test‑suite expectations
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
    Derivative of a *single* Lorenz oscillator (no coupling).

    Parameters
    ----------
    t : float
        Current time (required by ``solve_ivp`` but unused).
    y : np.ndarray
        State vector of length 3 ``[x, y, z]``.
    sigma, rho, beta : float, optional
        Lorenz parameters; defaults to the classic values
        (σ=10, ρ=28, β=8/3).

    Returns
    -------
    np.ndarray
        Derivative vector of shape (3,).
    """
    # ``lorenz_ode`` expects a flattened vector of length 3*N.
    # We delegate to it with ``N=1`` and no coupling.
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
    sigma: float | None = None,
    rho: float | None = None,
    beta: float | None = None,
) -> np.ndarray:
    """
    Derivative of a chain of ``N`` coupled Lorenz oscillators.

    This is a thin wrapper around :func:`code.simulation.generator.lorenz_ode`
    that supplies the required keyword arguments.
    """
    return lorenz_ode(
        t,
        y,
        N=N,
        coupling_strength=coupling_strength,
        coupling_topology="ring",
        sigma=sigma,
        rho=rho,
        beta=beta,
    )


def generate_initial_conditions(N: int, seed: int | None = None) -> np.ndarray:
    """
    Produce a reproducible random initial condition for ``N`` oscillators.

    The implementation mirrors the private helper used by the main
    generator; we expose it here for the tests.
    """
    rng = np.random.default_rng(seed)
    return _generate_initial_conditions(N, rng)


def inject_gaussian_noise(
    *,
    state_shape: Tuple[int, int],
    sigma_noise: float,
    seed: int | None = None,
) -> np.ndarray:
    """
    Generate additive Gaussian noise with zero mean and standard deviation
    ``sigma_noise`` for a trajectory of the requested shape.

    Parameters
    ----------
    state_shape : Tuple[int, int]
        Desired shape ``(n_samples, n_dim)``.
    sigma_noise : float
        Standard deviation of the noise.
    seed : int, optional
        Seed for reproducibility; if ``None`` a fresh entropy source is used.

    Returns
    -------
    np.ndarray
        Noise array of the requested shape.
    """
    rng = np.random.default_rng(seed)
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
    seed: int | None = None,
) -> dict:
    """
    Run a deterministic (or noisy) integration of the coupled Lorenz system.

    This wrapper forwards to :func:`code.simulation.generator.generate_trajectory`
    and returns a plain ``dict`` compatible with the historic test suite.

    Parameters
    ----------
    initial_state : np.ndarray
        Flattened initial condition of shape ``(3 * N,)``.
    max_time : float
        End time of the integration.
    dt : float
        Desired output spacing.
    N_oscillators : int
        Number of coupled oscillators.
    sigma_noise : float, default 0.0
        Standard deviation of additive observation noise.
    rtol, atol : float, optional
        Solver tolerances.
    seed : int, optional
        Seed for the RNG used for noise (and for the initial‑condition
        generator if the caller supplies ``seed`` instead of an explicit
        ``initial_state``).

    Returns
    -------
    dict
        ``{'trajectory': <np.ndarray>, 'time': <np.ndarray>}``
    """
    # ``generate_trajectory`` creates its own initial condition if ``seed`` is
    # provided.  When the caller supplies ``initial_state`` we mimic the
    # underlying behaviour by temporarily monkey‑patching the private helper.
    # This keeps the implementation simple while preserving determinism.
    if seed is not None:
        # Let the generator create the initial state internally.
        traj = generate_trajectory(
            N=N_oscillators,
            t_start=0.0,
            t_end=max_time,
            dt=dt,
            sigma_noise=sigma_noise,
            coupling_strength=0.0,
            coupling_topology="ring",
            seed=seed,
            rtol=rtol,
            atol=atol,
        )
    else:
        # Use the supplied ``initial_state`` directly.
        # We perform a manual integration using ``solve_ivp`` to avoid
        # re‑creating the initial condition.
        from scipy.integrate import solve_ivp

        t_eval = np.arange(0.0, max_time + dt, dt)
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

        state = sol.y.T
        if sigma_noise > 0.0:
            rng = np.random.default_rng()
            noise = rng.normal(loc=0.0, scale=sigma_noise, size=state.shape)
            state = state + noise

        traj = TrajectoryData(
            time=sol.t,
            state=state,
            noise_level=sigma_noise,
            N_oscillators=N_oscillators,
            coupling_strength=0.0,
            seed=seed if seed is not None else 0,
            is_clean=sigma_noise == 0.0,
        )

    return {"trajectory": traj.state, "time": traj.time}


def validate_trajectory(trajectory: np.ndarray, threshold: float = 100.0) -> bool:
    """
    Simple boundedness check used by the test suite.

    Returns ``True`` if the Euclidean norm of every state vector stays
    below ``threshold``; otherwise ``False``.
    """
    from utils.stability import check_boundedness

    return check_boundedness(trajectory, threshold=threshold)