"""
data/generator.py
-----------------
Compatibility layer that provides the public API expected by the
unit tests and the CLI entry point (`code.main`).  The heavy‑lifting
is delegated to the implementation in ``code.simulation.generator``.
All functions defined here are thin wrappers that translate the
arguments to the underlying implementation and expose the required
symbols:

* ``HighNoiseWarning`` and ``UnphysicalTrajectoryError`` – re‑exported
  from ``code.simulation.generator``.
* ``lorenz_ode_single`` – ODE for a single Lorenz oscillator.
* ``coupled_lorenz_ode`` – ODE for an arbitrary number of coupled
  oscillators (wrapper around ``lorenz_ode``).
* ``generate_initial_conditions`` – deterministic random initial state.
* ``inject_gaussian_noise`` – generate additive Gaussian noise.
* ``integrate_trajectory`` – perform a deterministic (or noisy)
  integration and return a dictionary compatible with the test suite.
* ``validate_trajectory`` – thin wrapper around the stability helper.
* ``generate_coupled_lorenz_trajectory`` – alias used by ``code.main``.
* ``generate_trajectory`` – alias to the full trajectory generator.

The module also defines ``generate_coupled_oscillators`` and
``inject_noise`` for backward compatibility with the original
``code.data`` package API.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, Tuple

import numpy as np
from scipy.integrate import solve_ivp

# Import the core implementation
from code.simulation.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    lorenz_ode,
    generate_trajectory as _core_generate_trajectory,
)
from code.utils.stability import (
    validate_trajectory as _validate_trajectory,
    check_noise_level as _check_noise_level,
)

__all__ = [
    "HighNoiseWarning",
    "UnphysicalTrajectoryError",
    "lorenz_ode_single",
    "coupled_lorenz_ode",
    "generate_initial_conditions",
    "inject_gaussian_noise",
    "integrate_trajectory",
    "validate_trajectory",
    "generate_coupled_lorenz_trajectory",
    "generate_trajectory",
    "generate_coupled_oscillators",
    "inject_noise",
]

# ----------------------------------------------------------------------
# Helper wrappers
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
    ODE for a **single** Lorenz oscillator (N=1) without coupling.
    This matches the signature used by the original ``data.generator``
    test suite.
    """
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
    ODE for an arbitrary number of coupled Lorenz oscillators.
    Directly forwards to :func:`code.simulation.generator.lorenz_ode`.
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
    oscillators.  The implementation mirrors the private helper in
    ``code.simulation.generator`` but is re‑implemented here to avoid
    importing a private name.
    """
    rng = np.random.default_rng(seed)
    base = np.array([1.0, 1.0, 1.0])
    init = rng.normal(loc=base, scale=0.5, size=(N, 3))
    return init.ravel()

def inject_gaussian_noise(state_shape: Tuple[int, int], sigma_noise: float) -> np.ndarray:
    """
    Generate additive Gaussian noise with standard deviation
    ``sigma_noise`` for an array of shape ``state_shape``.
    """
    rng = np.random.default_rng()
    noise = rng.normal(loc=0.0, scale=sigma_noise, size=state_shape)
    return noise

# ----------------------------------------------------------------------
# Integration / trajectory generation
# ----------------------------------------------------------------------
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
) -> Dict[str, Any]:
    """
    Deterministic (or noisy) integration of the coupled Lorenz system.
    Returns a dictionary compatible with the expectations of the unit
    tests:

    ``{'trajectory': <np.ndarray>, 'time': <np.ndarray>}``

    The function mirrors the behaviour of ``generate_trajectory`` but
    accepts a pre‑computed ``initial_state`` array.
    """
    # Emit high‑noise warning if required
    _check_noise_level(sigma_noise)

    # Time vector
    t_start = 0.0
    t_eval = np.arange(t_start, max_time + dt, dt)

    # Core ODE integration
    sol = solve_ivp(
        fun=lambda t, y: lorenz_ode(
            t,
            y,
            N=N_oscillators,
            coupling_strength=0.0,
            coupling_topology="ring",
        ),
        t_span=(t_start, max_time),
        y0=initial_state,
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
    )

    if not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message}")

    state_det = sol.y.T  # shape (n_steps, 3*N)

    # Apply the unphysical guard to the deterministic result
    from code.utils.stability import raise_if_unphysical

    raise_if_unphysical(state_det, threshold=20.0)

    # Inject noise if requested
    if sigma_noise > 0.0:
        rng = np.random.default_rng(seed)
        noise = rng.normal(loc=0.0, scale=sigma_noise, size=state_det.shape)
        state_noisy = state_det + noise
    else:
        state_noisy = state_det

    # Guard after noise injection
    raise_if_unphysical(state_noisy, threshold=20.0)

    return {"trajectory": state_noisy, "time": sol.t}

def validate_trajectory(
    trajectory: np.ndarray,
    max_bound: float = 100.0,
    min_steps: int = 100,
    check_convergence: bool = False,
    convergence_tol: float = 1e-6,
) -> Any:
    """
    Wrapper around the stability utility.  Returns the same
    ``StabilityReport`` object that the underlying helper provides.
    """
    return _validate_trajectory(
        trajectory,
        max_bound=max_bound,
        min_steps=min_steps,
        check_convergence=check_convergence,
        convergence_tol=convergence_tol,
    )

# ----------------------------------------------------------------------
# Compatibility aliases used by the CLI and older code
# ----------------------------------------------------------------------
def generate_coupled_lorenz_trajectory(
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
    Alias kept for backward compatibility with ``code.main``.
    Delegates to the core implementation.
    """
    return _core_generate_trajectory(
        N=N,
        t_start=t_start,
        t_end=t_end,
        dt=dt,
        sigma_noise=sigma_noise,
        coupling_strength=coupling_strength,
        coupling_topology=coupling_topology,
        seed=seed,
        rtol=rtol,
        atol=atol,
    )

# ``generate_trajectory`` is the public name used throughout the
# project; it is simply re‑exported from the core module.
generate_trajectory = generate_coupled_lorenz_trajectory

# Backwards‑compatible names that were previously exported from the
# ``code.data`` package.
generate_coupled_oscillators = generate_coupled_lorenz_trajectory
inject_noise = inject_gaussian_noise
