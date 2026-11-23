"""
Global configuration module for the OPID routing complexity project.

Provides constants, reproducibility helpers, and a feasibility estimator.
"""

from __future__ import annotations

import os
import random
import numpy as np

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
SEED = 42
TIER_NODE_RANGES = {1: (5, 10), 2: (20, 50), 3: (100, 200)}
THRESHOLD_STEPS = np.arange(0.0, 1.01, 0.1)
MAX_EPISODES_PER_SETTING = 1000

# ----------------------------------------------------------------------
# Reproducibility utilities
# ----------------------------------------------------------------------
def set_seed(seed: int = SEED) -> None:
    """
    Seed Python's ``random``, NumPy's RNG, and the PYTHONHASHSEED env var.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_seed() -> int:
    """Return the seed that was set via :func:`set_seed`."""
    return int(os.getenv("PYTHONHASHSEED", SEED))

# ----------------------------------------------------------------------
# Configuration helpers
# ----------------------------------------------------------------------
def get_tier_config(tier: int) -> dict:
    """
    Return a dictionary with ``num_nodes``, ``branching_prob`` and
    ``entropy_level`` for the requested tier.
    """
    if tier not in TIER_NODE_RANGES:
        raise KeyError(f"Unsupported tier: {tier}")
    min_nodes, max_nodes = TIER_NODE_RANGES[tier]
    # Simple heuristic configuration per tier.
    if tier == 1:
        return {"num_nodes": min_nodes, "branching_prob": 0.0, "entropy_level": "low"}
    if tier == 2:
        return {"num_nodes": (min_nodes + max_nodes) // 2, "branching_prob": 0.3, "entropy_level": "medium"}
    # tier == 3
    return {"num_nodes": max_nodes, "branching_prob": 0.5, "entropy_level": "high"}

def ensure_directories() -> None:
    """
    Create all required output directories under the project root.
    Uses ``llmxive_toolkit.paths`` helpers for consistency.
    """
    from llmxive_toolkit import paths

    paths.data("raw", "synthetic_graphs")
    paths.results()
    paths.results("profile.txt")
    paths.results("entropy_regression.json")
    paths.results("summary_stats.csv")
    paths.results("episode_results.csv")
    paths.results("aggregated_metrics.csv")
    paths.results("success_rate_summary.csv")
    paths.results("interaction_results.json")
    paths.results("inflection_points.json")
    paths.results("policy_rigidity.csv")
    paths.results("distillation_cost_benefit.csv")

# ----------------------------------------------------------------------
# Feasibility estimation
# ----------------------------------------------------------------------
def verify_feasibility() -> tuple[int, float]:
    """
    Estimate runtime for the full experimental sweep.

    Returns ``(episodes_per_setting, estimated_hours)``.  Raises
    ``RuntimeError`` if the estimate exceeds the 6‑hour budget.
    """
    episodes = MAX_EPISODES_PER_SETTING
    tiers = 3
    thresholds = len(THRESHOLD_STEPS)
    max_nodes = max(v[1] for v in TIER_NODE_RANGES.values())
    max_steps = 200  # per‑step worst‑case assumption
    per_step_sec = 0.001  # conservative

    total_steps = episodes * tiers * thresholds * max_steps
    estimated_seconds = total_steps * per_step_sec
    estimated_hours = estimated_seconds / 3600.0

    if estimated_hours > 6.0:
        raise RuntimeError(
            f"Estimated runtime {estimated_hours:.2f} h exceeds 6 h budget."
        )
    return episodes, estimated_hours

# ----------------------------------------------------------------------
# CLI helper
# ----------------------------------------------------------------------
def main() -> None:
    set_seed()
    episodes, hours = verify_feasibility()
    print(f"Episodes per setting: {episodes}")
    print(f"Estimated total runtime: {hours:.2f} h")

if __name__ == "__main__":
    main()
