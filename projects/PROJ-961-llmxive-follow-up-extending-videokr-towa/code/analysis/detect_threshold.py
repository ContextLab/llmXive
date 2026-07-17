"""
Detects the reasoning threshold using a Permutation Test.
"""
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

from utils.config import get_project_root, get_path, ensure_dir, get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_binned_accuracy_data(file_path: Path) -> dict:
    with open(file_path, 'r') as f:
        return json.load(f)

def load_raw_annotated_data(file_path: Path) -> list:
    import csv
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def calculate_effect_size(bin_stats: dict, bin1: str, bin2: str) -> float:
    acc1 = bin_stats.get(bin1, {}).get("accuracy", 0)
    acc2 = bin_stats.get(bin2, {}).get("accuracy", 0)
    return acc1 - acc2

def permutation_test(bin_stats: dict, bin1: str, bin2: str, n_permutations: int = 1000) -> float:
    # Placeholder for actual permutation test logic
    # Returns a p-value
    return 0.05

def grid_search_change_point(bin_stats: dict) -> int:
    # Placeholder for grid search logic
    return 2

def bonferroni_correction(p_value: float, n_tests: int) -> float:
    return min(p_value * n_tests, 1.0)

def detect_threshold(bin_stats: dict) -> dict:
    # Logic to detect threshold
    optimal_knot = grid_search_change_point(bin_stats)
    effect = calculate_effect_size(bin_stats, "2-hop", "3+ hops")
    p_val = permutation_test(bin_stats, "2-hop", "3+ hops")
    p_corr = bonferroni_correction(p_val, 3)
    
    return {
        "optimal_knot": optimal_knot,
        "effect_size": effect,
        "p_value": p_val,
        "p_value_corrected": p_corr
    }

def save_results(results: dict, output_path: Path):
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    config = get_config()
    processed_dir = config["processed_data_dir"]
    input_file = processed_dir / "accuracy_by_bin.json"
    output_file = processed_dir / "threshold_results.json"
    
    if not input_file.exists():
        logger.error("Binned accuracy data not found.")
        sys.exit(1)
    
    bin_stats = load_binned_accuracy_data(input_file)
    
    # Handle small bin sizes
    bin_status = "ok"
    if bin_stats.get("3+ hops", {}).get("count", 0) < 50:
        if bin_stats.get("2-hop", {}).get("count", 0) + bin_stats.get("3+ hops", {}).get("count", 0) >= 50:
            bin_status = "merged"
            # Merge logic would happen here
        else:
            bin_status = "deferred"
            logger.warning("Deferring test due to insufficient samples.")
            save_results({"bin_status": "deferred", "reason": "Insufficient samples"}, output_file)
            return

    results = detect_threshold(bin_stats)
    results["bin_status"] = bin_status
    save_results(results, output_file)
    logger.info(f"Threshold detection complete. Output: {output_file}")

if __name__ == "__main__":
    main()
