"""
code/data/generator.py
----------------------
Public wrapper module that exposes the trajectory generation API expected by the
test suite and the CLI entry point.  It forwards the heavy‑lifting to the
implementation in ``code.simulation.generator`` while providing a stable
function name ``generate_coupled_lorenz_trajectory`` and re‑exporting the
warning / error classes.
"""

from __future__ import annotations

from typing import Optional

# Re‑export the warning and error classes so that imports from
# ``code.data.generator`` succeed.
from ..simulation.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    generate_trajectory as _generate_trajectory,
)

__all__ = [
    "HighNoiseWarning",
    "UnphysicalTrajectoryError",
    "TrajectoryData",
    "generate_coupled_lorenz_trajectory",
    "generate_trajectory",
]


def generate_coupled_lorenz_trajectory(
    *,
    N: int,
    sigma_noise: float = 0.0,
    seed: Optional[int] = None,
    coupling_strength: float = 0.0,
    coupling_topology: str = "ring",
) -> TrajectoryData:
    """
    Convenience wrapper used by the unit tests and the CLI.

    The wrapper fixes the integration interval and output step size to the
    values used throughout the test suite (0 → 1000 with Δt = 0.01).  All
    other arguments are passed straight through to the underlying
    ``generate_trajectory`` implementation.

    Parameters
    ----------
    N: int
        Number of coupled Lorenz oscillators.
    sigma_noise: float, optional
        Standard deviation of the additive Gaussian observation noise.
    seed: int, optional
        Random seed for reproducible initial conditions and noise.
    coupling_strength: float, optional
        Linear coupling coefficient between neighbours (default 0.0 → independent
        oscillators).
    coupling_topology: str, optional
        Currently only ``'ring'`` is supported.

    Returns
    -------
    TrajectoryData
        Dataclass containing the time vector, noisy state matrix and metadata.
    """
    # Fixed integration parameters matching the reference integration used in the
    # test suite.
    t_start = 0.0
    t_end = 1000.0
    dt = 0.01

    return _generate_trajectory(
        N=N,
        t_start=t_start,
        t_end=t_end,
        dt=dt,
        sigma_noise=sigma_noise,
        coupling_strength=coupling_strength,
        coupling_topology=coupling_topology,
        seed=seed,
    )


# Alias kept for backward compatibility with older parts of the code base
# that expected a ``generate_trajectory`` symbol inside ``code.data.generator``.
def generate_trajectory(*, N: int, sigma_noise: float = 0.0, seed: Optional[int] = None,
                       coupling_strength: float = 0.0, coupling_topology: str = "ring",
                       t_start: float = 0.0, t_end: float = 1000.0, dt: float = 0.01,
                       rtol: float = 1e-9, atol: float = 1e-12) -> TrajectoryData:
    """
    Thin wrapper that forwards all arguments to the underlying implementation.

    This function exists solely so that ``code/data/__init__.py`` can re‑export a
    name called ``generate_trajectory`` (the original project scaffold expected
    it).  New code should prefer :func:`generate_coupled_lorenz_trajectory`,
    which fixes the integration interval to the values used in the test suite.
    """
    return _generate_trajectory(
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
