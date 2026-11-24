"""
code/data/generator.py
----------------------
Compatibility wrapper for trajectory generation.

The original implementation of the coupled Lorenz system resides in
``code/simulation/generator.py``.  The unit‑tests and the CLI entry
point expect a public API under ``code.data.generator`` providing:

* ``generate_coupled_lorenz_trajectory`` – a thin wrapper around the
  ``generate_trajectory`` function.
* ``HighNoiseWarning`` and ``UnphysicalTrajectoryError`` – re‑exported
  for convenience.

This module simply forwards calls to the implementation in
``code.simulation.generator`` while preserving the original signature
used by the test suite.
"""

from __future__ import annotations

from typing import Any, Dict

# Re‑export the warning / error classes so that imports from
# ``code.data.generator`` work exactly as the tests expect.
from ..simulation.generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    generate_trajectory,
)

__all__ = [
    "HighNoiseWarning",
    "UnphysicalTrajectoryError",
    "generate_coupled_lorenz_trajectory",
]

def generate_coupled_lorenz_trajectory(
    *,
    N: int,
    sigma_noise: float = 0.0,
    seed: int | None = None,
    t_start: float = 0.0,
    t_end: float = 1000.0,
    dt: float = 0.01,
    coupling_strength: float = 0.0,
    coupling_topology: str = "ring",
    rtol: float = 1e-9,
    atol: float = 1e-12,
    **kwargs: Any,
) -> TrajectoryData:
    """
    Wrapper that forwards to :func:`code.simulation.generator.generate_trajectory`.

    Parameters
    ----------
    N : int
        Number of coupled Lorenz oscillators.
    sigma_noise : float, optional
        Standard deviation of the additive Gaussian observation noise.
    seed : int, optional
        Random seed for reproducibility.
    t_start, t_end, dt, coupling_strength, coupling_topology, rtol, atol :
        Passed through to the underlying generator unchanged.
    **kwargs :
        Ignored – present for forward compatibility with older calls.

    Returns
    -------
    TrajectoryData
        Dataclass containing the generated trajectory and metadata.
    """
    # The underlying implementation already validates the noise level and
    # raises the appropriate warnings / errors.
    return generate_trajectory(
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
