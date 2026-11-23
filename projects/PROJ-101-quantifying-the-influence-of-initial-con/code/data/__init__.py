"""
code/data/__init__.py
--------------------
Package initialiser that re‑exports the public API for trajectory generation.
The test suite and the CLI import symbols from ``code.data.generator``; this
module makes those symbols available at the package level.
"""

from .generator import (
    HighNoiseWarning,
    UnphysicalTrajectoryError,
    TrajectoryData,
    generate_coupled_lorenz_trajectory,
    generate_trajectory,
)

__all__ = [
    "HighNoiseWarning",
    "UnphysicalTrajectoryError",
    "TrajectoryData",
    "generate_coupled_lorenz_trajectory",
    "generate_trajectory",
]
