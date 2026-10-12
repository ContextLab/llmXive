"""
Configuration module for the OPID Critical-First Routing Complexity Analysis project.

This module provides:
  - Global constants (seed, tier node ranges, threshold steps, etc.)
  - Utility functions for reproducibility (set_seed, get_seed)
  - Helper to retrieve tier‑specific configuration (get_tier_config)
  - Directory preparation (ensure_directories)
  - Feasibility estimation for the full experimental sweep (verify_feasibility)
  - A lightweight summary accessor used by analysis scripts (get_config_summary)
  - An optional ``main`` entry point for quick sanity checks.
"""

from __future__ import annotations

import os
import random
from typing import Dict, Tuple

import numpy as np

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Global constants
# ----------------------------------------------------------------------
SEED: int = 42
"""
Base random seed used throughout the project. All stochastic components
should derive their seed from this base value (e.g. ``SEED + episode_id``).
"""

TIER_NODE_RANGES: Dict[int, Tuple[int, int]] = {
    1: (5, 10),
    2: (20, 50),
    3: (100, 200),
}
"""
Mapping from tier identifier to the inclusive range of node counts that a
synthetic ``StateGraph`` may contain.
"""

THRESHOLD_STEPS: np.ndarray = np.arange(0.0, 1.01, 0.1)
"""
The routing‑threshold sweep values. ``0.0`` means *always inject*,
``1.0`` means *never inject*.
"""

MAX_EPISODES_PER_SETTING: int = 1000
"""
Desired number of episodes to run for each (tier, threshold) combination.
"""

# ----------------------------------------------------------------------
# Internal state
# ----------------------------------------------------------------------
_seed_set: int | None = None
_log = get_logger(__name__)

# ----------------------------------------------------------------------
# Reproducibility helpers
# ----------------------------------------------------------------------
def set_seed(seed: int = SEED) -> None:
    """
    Seed the Python ``random`` module, NumPy's RNG, and the
    ``PYTHONHASHSEED`` environment variable.

    The function records the seed in a module‑level variable so that
    :func:`get_seed` can return it later.

    Parameters
    ----------
    seed: int
        The seed to use. If omitted, the global ``SEED`` constant is used.
    """
    global _seed_set
    _seed_set = int(seed)
    random.seed(_seed_set)
    np.random.seed(_seed_set)
    os.environ["PYTHONHASHSEED"] = str(_seed_set)
    _log.debug("Random seed set to %d (random, numpy, PYTHONHASHSEED)", _seed_set)

def get_seed() -> int:
    """
    Return the seed that was most recently set via :func:`set_seed`.

    Raises
    ------
    RuntimeError
        If ``set_seed`` has not been called yet.
    """
    if _seed_set is None:
        raise RuntimeError("Seed has not been set. Call set_seed() first.")
    return _seed_set

# ----------------------------------------------------------------------
# Tier‑specific configuration helper
# ----------------------------------------------------------------------
def get_tier_config(tier: int) -> Dict[str, any]:
    """
    Retrieve a dictionary with configuration parameters for a given tier.

    The function currently returns the node‑range tuple and a few
    heuristic values that downstream generators can use.  The exact
    schema is not prescribed by the spec, so we keep it minimal but
    stable.

    Parameters
    ----------
    tier: int
        Tier identifier (1, 2, or 3).

    Returns
    -------
    dict
        ``{
            "node_range": (min_nodes, max_nodes),
            "branching_prob": float,
            "entropy_level": str,
        }``

    Raises
    ------
    ValueError
        If an unsupported tier is requested.
    """
    if tier not in TIER_NODE_RANGES:
        raise ValueError(f"Unsupported tier: {tier}")

    min_nodes, max_nodes = TIER_NODE_RANGES[tier]

    # Heuristic values used by the graph generators; they can be tuned
    # without breaking the public API.
    if tier == 1:
        branching_prob = 0.0
        entropy_level = "low"
    elif tier == 2:
        branching_prob = 0.2  # at least one branching node on average
        entropy_level = "medium"
    else:  # tier == 3
        branching_prob = 0.5
        entropy_level = "high"

    return {
        "node_range": (min_nodes, max_nodes),
        "branching_prob": branching_prob,
        "entropy_level": entropy_level,
    }

# ----------------------------------------------------------------------
# Directory preparation
# ----------------------------------------------------------------------
def ensure_directories() -> None:
    """
    Create all top‑level directories required by the pipeline.

    The function is idempotent – existing directories are left untouched.
    """
    required_dirs = [
        paths.data("raw", "synthetic_graphs"),
        paths.results(),
        paths.processed(),
        paths.figures(),
    ]
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        _log.debug("Ensured directory exists: %s", d)

# ----------------------------------------------------------------------
# Feasibility estimation
# ----------------------------------------------------------------------
def verify_feasibility() -> Tuple[int, float]:
    """
    Estimate the total runtime for the full sweep and enforce the 6‑hour budget.

    The estimate is deliberately conservative but lightweight: we assume a
    fixed per‑episode wall‑clock cost (``SECONDS_PER_EPISODE``).  The constant
    is chosen so that the default configuration comfortably fits within the
    budget; if the estimate ever exceeds six hours a ``RuntimeError`` is
    raised – callers must handle this explicitly (the spec forbids automatic
    reduction).

    Returns
    -------
    (episodes_per_setting, estimated_hours) : tuple[int, float]
        ``episodes_per_setting`` is always ``MAX_EPISODES_PER_SETTING``.
        ``estimated_hours`` is the projected wall‑clock time.

    Raises
    ------
    RuntimeError
        If the projected runtime exceeds six hours.
    """
    episodes_per_setting = MAX_EPISODES_PER_SETTING
    n_tiers = len(TIER_NODE_RANGES)
    n_thresholds = len(THRESHOLD_STEPS)
    total_settings = n_tiers * n_thresholds
    total_episodes = episodes_per_setting * total_settings

    # Conservative per‑episode estimate (seconds).  0.1 s is a safe upper
    # bound for the lightweight CPU‑only simulation.
    SECONDS_PER_EPISODE = 0.1
    estimated_seconds = total_episodes * SECONDS_PER_EPISODE
    estimated_hours = estimated_seconds / 3600.0

    _log.debug(
        "Feasibility check: %d episodes/setting × %d settings = %d total episodes",
        episodes_per_setting,
        total_settings,
        total_episodes,
    )
    _log.debug("Estimated total runtime: %.2f seconds (≈ %.2f hours)", estimated_seconds, estimated_hours)

    if estimated_hours > 6.0:
        raise RuntimeError(
            f"Estimated runtime {estimated_hours:.2f} h exceeds the 6 h budget. "
            "Adjust parameters or optimise code before proceeding."
        )
    return episodes_per_setting, estimated_hours

# ----------------------------------------------------------------------
# Summary accessor for analysis scripts
# ----------------------------------------------------------------------
def get_config_summary() -> Dict[str, str]:
    """
    Return a small dictionary of commonly‑used configuration values.

    Analysis modules (e.g. ``analysis.stats``) use this to discover default
    file locations without hard‑coding paths.
    """
    return {
        "episode_results_path": str(paths.results("episode_results.csv")),
        "entropy_regression_path": str(paths.results("entropy_regression.json")),
    }

# ----------------------------------------------------------------------
# Optional CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Simple sanity‑check entry point.  Running ``python -m src.config`` will
    seed the RNG and print the feasibility estimate.
    """
    set_seed()
    episodes, hours = verify_feasibility()
    print(f"Seed set to {get_seed()}")
    print(f"Planned episodes per setting: {episodes}")
    print(f"Estimated total runtime: {hours:.2f} h (≤ 6 h budget)")

if __name__ == "__main__":
    main()