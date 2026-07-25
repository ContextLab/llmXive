"""Stratify accuracy by hop bin."""
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from utils.config import get_project_root, get_path, ensure_dir

def load_annotated_data(input_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load annotated data from CSV file."""
    data = []
    with open(input_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def bin_hop_length(chain_length: int) -> str:
    """Bin hop length into categories."""
    if chain_length == 1:
        return "1"
    elif chain_length == 2:
        return "2"
    else:
        return "3+"

def calculate_accuracy_by_bin(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Calculate accuracy for each hop bin."""
    bin_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})

    for row in data:
        chain_length = int(row.get("chain_length", 0))
        bin_label = bin_hop_length(chain_length)
        bin_stats[bin_label]["total"] += 1
        if row.get("correctness") == "correct":
            bin_stats[bin_label]["correct"] += 1

    return dict(bin_stats)

def write_results(results: Dict[str, Dict[str, int]], output_path: Union[str, Path]) -> None:
    """Write accuracy results to JSON file."""
    output_path = Path(output_path)
    ensure_dir(output_path.parent)

    accuracy_results = {}
    for bin_label, stats in results.items():
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        accuracy_results[bin_label] = {
            "accuracy": accuracy,
            "correct": stats["correct"],
            "total": stats["total"]
        }

    with open(output_path, "w") as f:
        json.dump(accuracy_results, f, indent=2)

def main() -> None:
    """Main entry point for accuracy stratification."""
    input_path = get_path("data/processed/annotated_videokr.csv")
    output_path = get_path("data/processed/stratified_accuracy.json")

    data = load_annotated_data(input_path)
    results = calculate_accuracy_by_bin(data)
    write_results(results, output_path)
    logging.info(f"Stratified accuracy written to {output_path}")
