"""Detect reasoning threshold using permutation test."""
import json
import logging
import os
import sys
import numpy as np
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from utils.config import get_project_root, get_path, ensure_dir

def load_raw_annotated_data(input_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load raw annotated data from CSV."""
    data = []
    with open(input_path, "r") as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def load_binned_accuracy_data(input_path: Union[str, Path]) -> Dict[str, Dict[str, Any]]:
    """Load binned accuracy data from JSON."""
    with open(input_path, "r") as f:
        return json.load(f)

def calculate_effect_size(bin_stats: Dict[str, Dict[str, int]], bin1: str, bin2: str) -> float:
    """Calculate effect size between two bins."""
    acc1 = bin_stats[bin1]["correct"] / bin_stats[bin1]["total"] if bin_stats[bin1]["total"] > 0 else 0.0
    acc2 = bin_stats[bin2]["correct"] / bin_stats[bin2]["total"] if bin_stats[bin2]["total"] > 0 else 0.0
    return acc1 - acc2

def permutation_test(data: List[float], group_labels: List[int], n_permutations: int = 1000) -> float:
    """Perform a permutation test to assess significance of group difference."""
    observed_diff = np.mean([x for x, g in zip(data, group_labels) if g == 1]) - np.mean([x for x, g in zip(data, group_labels) if g == 0])

    count_extreme = 0
    for _ in range(n_permutations):
        permuted_labels = np.random.permutation(group_labels)
        perm_diff = np.mean([x for x, g in zip(data, permuted_labels) if g == 1]) - np.mean([x for x, g in zip(data, permuted_labels) if g == 0])
        if abs(perm_diff) >= abs(observed_diff):
            count_extreme += 1

    return count_extreme / n_permutations

def bonferroni_correction(p_value: float, num_tests: int) -> float:
    """Apply Bonferroni correction to a p-value."""
    return min(p_value * num_tests, 1.0)

def grid_search_change_point(data: List[Dict[str, Any]], alpha: float = 0.05, n_permutations: int = 1000) -> Dict[str, Any]:
    """Grid search for optimal change point using permutation test."""
    hop_counts = sorted(set(int(row["chain_length"]) for row in data))
    best_knot = None
    min_p_value = 1.0

    for knot in range(1, max(hop_counts)):
        group_labels = [1 if int(row["chain_length"]) > knot else 0 for row in data]
        accuracies = [1.0 if row["correctness"] == "correct" else 0.0 for row in data]

        p_raw = permutation_test(accuracies, group_labels, n_permutations)
        p_corrected = bonferroni_correction(p_raw, len(hop_counts))

        if p_corrected < min_p_value:
            min_p_value = p_corrected
            best_knot = knot

    return {
        "optimal_knot": best_knot,
        "p_value": min_p_value,
        "is_significant": min_p_value < alpha
    }

def detect_threshold(data: List[Dict[str, Any]], alpha: float = 0.05, n_permutations: int = 1000) -> Dict[str, Any]:
    """Detect the reasoning threshold in the data."""
    result = grid_search_change_point(data, alpha, n_permutations)
    result["alpha"] = alpha
    result["conclusion"] = "PASS" if result["is_significant"] else "FAIL"
    return result

def save_results(results: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """Save threshold detection results to JSON."""
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

def main() -> None:
    """Main entry point for threshold detection."""
    input_path = get_path("data/processed/annotated_videokr.csv")
    output_path = get_path("data/processed/threshold_results.json")

    data = load_raw_annotated_data(input_path)
    results = detect_threshold(data)
    save_results(results, output_path)
    logging.info(f"Threshold detection results written to {output_path}")
