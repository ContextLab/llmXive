"""Simulation package.

Implements the episode runner and the experiment sweep logic.
"""

# Export the primary classes/functions used by the quick‑start script
from .runner import (
    ExperimentRunner,
    ExperimentConfig,
    EpisodeResult,
    main as simulation_main,
)  # noqa: F401

__all__ = [
    "ExperimentRunner",
    "ExperimentConfig",
    "EpisodeResult",
]
