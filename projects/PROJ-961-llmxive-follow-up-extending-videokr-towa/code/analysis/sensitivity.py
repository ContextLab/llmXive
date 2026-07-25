"""Sensitivity analysis for threshold definitions."""
import csv
import json
import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any

from utils.config import get_project_root, get_path, ensure_dir
from analysis.detect_threshold import detect_threshold, load_raw_annotated_data

def run_pilot_sample(data: List[Dict[str, Any]], sample_size: int) -> List[Dict[str, Any]]:
    """Run a pilot sample for initial analysis."""
    return data[:sample_size]

def oversample_dataset(data: List[Dict[str, Any]], target_size: int) -> List[Dict[str, Any]]:
    """Oversample dataset to target size."""
    import random
    if len(data) >= target_size:
        return data
    return random.choices(data, k=target_size)

def merge_bins_if_needed(bin_stats: Dict[str, Dict[str, int]], min_count: int = 50) -> Dict[str, Dict[str, int]]:
    """Merge bins if they have fewer than min_count samples."""
    # Placeholder for bin merging logic
    return bin_stats

def calculate_effect_size(bin_stats: Dict[str, Dict[str, int]], bin1: str, bin2: str) -> float:
    """Calculate effect size between two bins."""
    acc1 = bin_stats[bin1]["correct"] / bin_stats[bin1]["total"] if bin_stats[bin1]["total"] > 0 else 0.0
    acc2 = bin_stats[bin2]["correct"] / bin_stats[bin2]["total"] if bin_stats[bin2]["total"] > 0 else 0.0
    return acc1 - acc2

def perform_threshold_sweep(data: List[Dict[str, Any]], thresholds: List[int] = [2, 3, 4]) -> List[Dict[str, Any]]:
    """Perform sensitivity analysis across different thresholds."""
    results = []
    for threshold in thresholds:
        # Filter data based on threshold
        filtered_data = [row for row in data if int(row["chain_length"]) >= threshold]
        if len(filtered_data) > 0:
            threshold_result = detect_threshold(filtered_data)
            results.append({
                "threshold_hop": threshold,
                "p_value": threshold_result["p_value"],
                "effect_size": calculate_effect_size({}, "1", "2"),  # Placeholder
                "is_significant": threshold_result["is_significant"]
            })
    return results

def save_results(results: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
    """Save sensitivity analysis results to CSV."""
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["threshold_hop", "p_value", "effect_size", "is_significant"])
        writer.writeheader()
        writer.writerows(results)

def run_sensitivity_analysis(data: List[Dict[str, Any]], thresholds: List[int] = [2, 3, 4]) -> List[Dict[str, Any]]:
    """Run full sensitivity analysis."""
    return perform_threshold_sweep(data, thresholds)

def main() -> None:
    """Main entry point for sensitivity analysis."""
    input_path = get_path("data/processed/annotated_videokr.csv")
    output_path = get_path("data/processed/sensitivity_thresholds.csv")

    data = load_raw_annotated_data(input_path)
    results = run_sensitivity_analysis(data)
    save_results(results, output_path)
    logging.info(f"Sensitivity analysis results written to {output_path}")
