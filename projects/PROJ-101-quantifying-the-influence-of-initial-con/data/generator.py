"""
Facade module for trajectory generation.

The original, fully‑featured implementation resides in
``code/data/generator.py``.  For backward compatibility the public API
expected by the test suite (and earlier parts of the project) is
re‑exported here.

This file provides:
- ``HighNoiseWarning`` and ``UnphysicalTrajectoryError`` exception types.
- ``TrajectoryData`` dataclass container.
- ``lorenz_ode_single`` and ``coupled_lorenz_ode`` ODE definitions.
- ``generate_initial_conditions`` for deterministic seeding.
- ``inject_gaussian_noise`` for additive noise.
- ``integrate_trajectory`` which performs the ODE integration using
  ``scipy.integrate.solve_ivp`` with method ``'DOP853'`` and the required
  tolerances.
- ``validate_trajectory`` which checks bounds, noise levels and numerical
  stability.
- ``generate_trajectory`` – a thin wrapper around the more explicitly named
  ``generate_coupled_lorenz_trajectory`` that matches the original API
  used in earlier versions of the project.

All heavy‑lifting code lives in ``code/data/generator.py``; this module
simply forwards calls, keeping the public interface stable.
"""
# Import the concrete implementation
from code.data.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    lorenz_ode_single,
    coupled_lorenz_ode,
    generate_initial_conditions,
    inject_gaussian_noise,
    integrate_trajectory,
    validate_trajectory,
    generate_coupled_lorenz_trajectory,
    generate_batch_trajectories,
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
    "generate_trajectory",
    "generate_coupled_lorenz_trajectory",
    "generate_batch_trajectories",
]

def generate_trajectory(
    N: int,
    t_start: float = 0.0,
    t_end: float = 1000.0,
    dt: float = 0.01,
    sigma_noise: float = 0.0,
    coupling_strength: float = 0.01,
    coupling_topology: str = "ring",
    seed: int | None = None,
    numerical_settings=None,
) -> TrajectoryData:
    """
    Generate a single trajectory of the coupled Lorenz system.

    This wrapper mirrors the historic ``generate_trajectory`` API while
    delegating the actual work to ``generate_coupled_lorenz_trajectory``.

    Parameters
    ----------
    N : int
        Number of coupled Lorenz oscillators.
    t_start, t_end : float
        Integration start and end times.
    dt : float
        Desired output time step.
    sigma_noise : float
        Standard deviation of additive Gaussian noise (0.0 for a clean
        trajectory).
    coupling_strength : float
        Diffusive coupling strength between neighboring oscillators.
    coupling_topology : str
        Either ``'ring'`` or ``'all-to-all'``.
    seed : int | None
        Seed for reproducible initial conditions and noise.  If ``None``,
        a random seed is generated internally.
    numerical_settings :
        Optional ``NumericalSettings`` instance controlling ``rtol`` and
        ``atol``.  Passed straight through to the underlying generator.

    Returns
    -------
    TrajectoryData
        Container holding ``time``, ``state`` and metadata.
    """
    return generate_coupled_lorenz_trajectory(
        N=N,
        t_start=t_start,
        t_end=t_end,
        dt=dt,
        sigma_noise=sigma_noise,
        coupling_strength=coupling_strength,
        coupling_topology=coupling_topology,
        seed=seed,
        numerical_settings=numerical_settings,
    )