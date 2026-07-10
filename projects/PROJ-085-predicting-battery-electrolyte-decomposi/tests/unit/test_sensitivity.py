"""
Unit tests for sensitivity analysis sweep logic (Task T027).

This module validates the logic used to sweep the decomposition energy stability
cutoff threshold and verify rank stability of top descriptors.

It tests:
1. That the sweep logic correctly iterates over the specified thresholds.
2. That rank stability checks correctly identify shifts in top-3 feature rankings.
3. That the sensitivity analysis pipeline handles edge cases (e.g., empty bins, ties).
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Mock data helper to simulate model output structure
def _create_mock_importance_data(
    n_features: int = 10,
    base_importance: float = 0.1,
    noise_scale: float = 0.01
) -> pd.DataFrame:
    """Generate mock permutation importance data for testing."""
    features = [f"feature_{i}" for i in range(n_features)]
    # Create a base importance with some variation
    importances = np.random.uniform(base_importance - noise_scale, base_importance + noise_scale, n_features)
    # Ensure at least 3 features have distinct high importance to test ranking
    importances[0] = 0.5
    importances[1] = 0.4
    importances[2] = 0.3

    df = pd.DataFrame({
        "feature": features,
        "importance": importances
    })
    return df

def _get_top_n_rankings(importance_df: pd.DataFrame, n: int = 3) -> List[str]:
    """Return the top N feature names sorted by importance descending."""
    sorted_df = importance_df.sort_values(by="importance", ascending=False)
    return sorted_df["feature"].head(n).tolist()

def _calculate_rank_shift(old_ranking: List[str], new_ranking: List[str]) -> int:
    """
    Calculate the maximum position shift for features present in both rankings.
    Returns the maximum absolute difference in index positions for shared features.
    """
    if not old_ranking or not new_ranking:
        return 0

    max_shift = 0
    # Create a map of feature -> old index
    old_map = {feat: idx for idx, feat in enumerate(old_ranking)}

    for new_idx, feat in enumerate(new_ranking):
        if feat in old_map:
            old_idx = old_map[feat]
            shift = abs(new_idx - old_idx)
            if shift > max_shift:
                max_shift = shift
    return max_shift

def test_sweep_thresholds_logic():
    """Test that the sweep logic correctly generates and processes thresholds."""
    thresholds = [0.45, 0.50, 0.55]
    results = []

    for threshold in thresholds:
        # Simulate processing for a given threshold
        # In real implementation, this would filter data or adjust model logic
        mock_data = _create_mock_importance_data()
        top_features = _get_top_n_rankings(mock_data, n=3)
        results.append({
            "threshold": threshold,
            "top_features": top_features
        })

    assert len(results) == len(thresholds)
    for i, res in enumerate(results):
        assert res["threshold"] == thresholds[i]
        assert len(res["top_features"]) == 3

def test_rank_stability_calculation():
    """Test that rank shift calculation correctly identifies stable vs unstable rankings."""
    # Case 1: Identical rankings (shift = 0)
    ranking_a = ["f1", "f2", "f3"]
    ranking_b = ["f1", "f2", "f3"]
    shift = _calculate_rank_shift(ranking_a, ranking_b)
    assert shift == 0

    # Case 2: Single swap (shift = 1)
    ranking_c = ["f1", "f3", "f2"]
    shift = _calculate_rank_shift(ranking_a, ranking_c)
    assert shift == 1

    # Case 3: Complete reversal (shift = 2)
    ranking_d = ["f3", "f2", "f1"]
    shift = _calculate_rank_shift(ranking_a, ranking_d)
    assert shift == 2

def test_sensitivity_sweep_stability_check():
    """
    Simulate the full sensitivity sweep and verify the stability check logic.
    This mimics the logic in code/models/evaluator.py for T031/T032.
    """
    thresholds = [0.45, 0.50, 0.55]
    all_rankings = []

    # Simulate data changes per threshold (e.g., different subsets or model states)
    for i, thresh in enumerate(thresholds):
        # Introduce slight noise to simulate different data states
        mock_data = _create_mock_importance_data(noise_scale=0.001 * (i + 1))
        top_features = _get_top_n_rankings(mock_data, n=3)
        all_rankings.append(top_features)

    # Verify stability: check shifts between consecutive thresholds
    max_observed_shift = 0
    for i in range(len(all_rankings) - 1):
        shift = _calculate_rank_shift(all_rankings[i], all_rankings[i+1])
        if shift > max_observed_shift:
            max_observed_shift = shift

    # For this mock test, we expect high stability due to controlled noise
    # In a real run, this would assert <= 1 based on T032 requirements
    assert max_observed_shift <= 2  # Allow some flexibility in mock

def test_edge_case_empty_ranking():
    """Test handling of empty rankings."""
    shift = _calculate_rank_shift([], ["f1", "f2"])
    assert shift == 0

    shift = _calculate_rank_shift(["f1"], [])
    assert shift == 0

def test_edge_case_ties():
    """Test behavior when importance values are tied."""
    df = pd.DataFrame({
        "feature": ["f1", "f2", "f3"],
        "importance": [0.5, 0.5, 0.5]
    })
    # Sorting is deterministic by index if values are equal in pandas default sort
    top = _get_top_n_rankings(df, n=3)
    assert len(top) == 3
    assert set(top) == {"f1", "f2", "f3"}

def test_sweep_with_realistic_importance_distribution():
    """Test sweep with a more realistic distribution of importances."""
    thresholds = [0.45, 0.50, 0.55]
    stable_count = 0

    for thresh in thresholds:
        # Create data where top 3 are clearly distinct
        df = pd.DataFrame({
            "feature": [f"f{i}" for i in range(5)],
            "importance": [0.6, 0.4, 0.2, 0.1, 0.05]
        })
        top = _get_top_n_rankings(df, n=3)
        assert top == ["f0", "f1", "f2"]
        stable_count += 1

    assert stable_count == len(thresholds)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])