"""
Configuration module for the OPID Critical‑First Routing Complexity Analysis project.

This module defines global constants, provides reproducibility utilities, and
includes a feasibility checker that estimates the total runtime of the full
experimental sweep. The feasibility check returns the number of episodes per
setting (as defined by ``MAX_EPISODES_PER_SETTING``) and the estimated runtime
in hours. If the estimate exceeds the 6‑hour limit, a ``RuntimeError`` is raised.
"""

import os
import random
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

import json
import numpy as np

# ---------------------------------------------------------------------------
# Global constants
# ---------------------------------------------------------------------------
SEED: int = 42

# Tier -> (min_nodes, max_nodes)
TIER_NODE_RANGES: Dict[int, Tuple[int, int]] = {
    1: (5, 10),
    2: (20, 50),
    3: (100, 200),
}

# Threshold sweep values (0.0, 0.1, ..., 1.0)
THRESHOLD_STEPS: np.ndarray = np.arange(0.0, 1.01, 0.1)

# Episodes per (tier, threshold) setting
MAX_EPISODES_PER_SETTING: int = 1000

# ---------------------------------------------------------------------------
# Reproducibility helpers
# ---------------------------------------------------------------------------
_CURRENT_SEED: Optional[int] = None


def set_seed(seed: int = SEED) -> None:
    """
    Initialise all random number generators for reproducibility.

    Args:
        seed: Integer seed to use. Defaults to the module‑level ``SEED``.
    """
    global _CURRENT_SEED
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed)}")
    if seed < 0:
        raise ValueError("Seed must be non‑negative")

    _CURRENT_SEED = seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)


def get_seed() -> Optional[int]:
    """
    Return the currently active seed (or ``None`` if ``set_seed`` has not been called).
    """
    return _CURRENT_SEED


# ---------------------------------------------------------------------------
# Tier configuration helper
# ---------------------------------------------------------------------------
def get_tier_config(tier: int) -> Tuple[int, int]:
    """
    Return the (min_nodes, max_nodes) range for the requested tier.

    Args:
        tier: Tier identifier (1, 2, or 3).

    Returns:
        Tuple of (min_nodes, max_nodes).

    Raises:
        KeyError: If an unsupported tier is requested.
    """
    return TIER_NODE_RANGES[tier]


# ---------------------------------------------------------------------------
# Directory handling (kept from the original scaffold)
# ---------------------------------------------------------------------------
def ensure_directories() -> None:
    """
    Create required output directories if they do not already exist.
    """
    from llmxive_toolkit import paths

    # The ``paths`` helper lazily creates parent directories.
    _ = paths.data("raw", "synthetic_graphs")
    _ = paths.data("processed")
    _ = paths.results()
    _ = paths.figures()


# ---------------------------------------------------------------------------
# Version / snapshot utilities (unchanged from scaffold)
# ---------------------------------------------------------------------------
def get_version_hash() -> str:
    """
    Return a timestamp‑based version hash for the current run.
    """
    return datetime.utcnow().strftime("%Y%m%d%H%M%S")


def save_config_snapshot(config: Dict[str, Any], path: str) -> None:
    """
    Save the supplied configuration dictionary as JSON.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_config_summary() -> Dict[str, Any]:
    """
    Return a dictionary summarising the current configuration.
    """
    return {
        "seed": get_seed(),
        "tier_node_ranges": TIER_NODE_RANGES,
        "threshold_steps": THRESHOLD_STEPS.tolist(),
        "max_episodes_per_setting": MAX_EPISODES_PER_SETTING,
        "version_hash": get_version_hash(),
    }


# ---------------------------------------------------------------------------
# Feasibility estimation
# ---------------------------------------------------------------------------
def verify_feasibility() -> Tuple[int, float]:
    """
    Estimate the total runtime of the full experimental sweep.

    The estimate is based on deterministic worst‑case constants:
    * maximum node count per tier (200)
    * maximum steps per episode (200)
    * episodes per setting (``MAX_EPISODES_PER_SETTING``)
    * number of thresholds (len(THRESHOLD_STEPS))
    * number of tiers (3)

    A simplistic per‑step cost (0.001 s) is assumed, which yields a
    conservative upper bound.

    Returns:
        A tuple ``(episodes_per_setting, estimated_hours)`` where
        ``episodes_per_setting`` is ``MAX_EPISODES_PER_SETTING`` and
        ``estimated_hours`` is the computed runtime in hours.

    Raises:
        RuntimeError: If the estimated runtime exceeds 6 hours.
    """
    # Deterministic constants
    max_nodes = max(r[1] for r in TIER_NODE_RANGES.values())  # 200
    max_steps_per_episode = 200
    episodes = MAX_EPISODES_PER_SETTING
    n_thresholds = len(THRESHOLD_STEPS)  # 11
    n_tiers = len(TIER_NODE_RANGES)     # 3

    # Rough operation count: each step is treated as one unit of work.
    total_steps = episodes * n_thresholds * n_tiers * max_steps_per_episode

    # Assume each step costs 1 ms (0.001 s). This is a generous upper bound.
    seconds_per_step = 0.001
    total_seconds = total_steps * seconds_per_step
    estimated_hours = total_seconds / 3600.0

    if estimated_hours > 6.0:
        raise RuntimeError(
            f"Estimated runtime {estimated_hours:.2f} h exceeds the 6 h limit. "
            "Consider reducing MAX_EPISODES_PER_SETTING."
        )

    return episodes, estimated_hours


# ---------------------------------------------------------------------------
# Main entry point (kept for backward compatibility)
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Simple CLI entry point for quick inspection of the configuration.
    Prints the config summary and the feasibility estimate.
    """
    print("Configuration summary:")
    for k, v in get_config_summary().items():
        print(f"  {k}: {v}")

    try:
        episodes, hrs = verify_feasibility()
        print(f"\nFeasibility check passed: {episodes} episodes per setting, "
              f"estimated runtime ≈ {hrs:.2f} h")
    except RuntimeError as e:
        print(f"\nFeasibility check failed: {e}")

if __name__ == "__main__":
    main()