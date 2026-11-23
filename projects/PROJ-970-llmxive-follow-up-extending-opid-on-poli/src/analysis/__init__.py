"""Analysis package.

Provides utilities for aggregating episode results and performing the
statistical analyses required by the project.
"""

# Export commonly used analysis helpers
from .aggregation import (
    load_episode_results,
    compute_summary_stats,
    calculate_baseline_success,
)  # noqa: F401
from .stats import run_entropy_regression, main as stats_main  # noqa: F401

__all__ = [
    "load_episode_results",
    "compute_summary_stats",
    "calculate_baseline_success",
    "run_entropy_regression",
]
