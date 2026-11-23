"""
Unit test for T119 – Verify that the stability rankings across three runs
have a rank difference of at most 1 for the top‑k (k=5) features.

The expected JSON format (produced by `scripts/run_stability.py`) is:

{
    "run_1": ["feature_A", "feature_B", "feature_C", ...],
    "run_2": ["feature_B", "feature_A", "feature_D", ...],
    "run_3": ["feature_A", "feature_C", "feature_B", ...]
}

Each list is ordered from most important (rank 1) to least important.
The test computes, for each feature that appears in the top‑k of any run,
the maximum and minimum rank it occupies across the three runs and asserts
that the difference does not exceed 1.
"""

import json
import pathlib

import pytest


def _load_stability_rankings(file_path: pathlib.Path) -> dict:
    """Load the stability rankings JSON file."""
    if not file_path.is_file():
        raise AssertionError(f"Stability rankings file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def _compute_rank_differences(rankings: dict, top_k: int = 5) -> dict:
    """
    Compute the rank difference for each feature that appears in the top‑k
    of any run.

    Returns a mapping ``feature -> (min_rank, max_rank)`` where ranks are
    1‑based indices.
    """
    # Gather ranks per run
    run_ranks = {}
    for run_key, ordered_features in rankings.items():
        run_ranks[run_key] = {
            feature: idx + 1 for idx, feature in enumerate(ordered_features[:top_k])
        }

    # Union of all features appearing in any top‑k list
    all_features = set()
    for ranks in run_ranks.values():
        all_features.update(ranks.keys())

    diff_map = {}
    for feature in all_features:
        ranks = [
            run_ranks[run].get(feature, top_k + 1)  # if missing, assign rank beyond top‑k
            for run in run_ranks
        ]
        diff_map[feature] = (min(ranks), max(ranks))
    return diff_map


def test_stability_rankings_top_k_difference():
    """
    Test that for the top‑k (k=5) features, the rank difference across the
    three runs is ≤ 1.
    """
    rankings_path = pathlib.Path("output") / "stability_rankings.json"
    rankings = _load_stability_rankings(rankings_path)

    # Basic sanity check on structure
    assert isinstance(rankings, dict), "Rankings JSON must be a dictionary"
    assert len(rankings) == 3, "Exactly three runs should be present"

    diff_map = _compute_rank_differences(rankings, top_k=5)

    # Ensure every feature's rank spread is within the allowed threshold
    for feature, (min_rank, max_rank) in diff_map.items():
        rank_spread = max_rank - min_rank
        assert (
            rank_spread <= 1
        ), (
            f"Feature '{feature}' rank spread across runs is {rank_spread} (>1). "
            f"Ranks observed: min={min_rank}, max={max_rank}"
        )

    # Optional: ensure at least one feature is present (sanity)
    assert diff_map, "No features found in the top‑k rankings"

# The test can be run directly for debugging
if __name__ == "__main__":
    pytest.main([__file__])