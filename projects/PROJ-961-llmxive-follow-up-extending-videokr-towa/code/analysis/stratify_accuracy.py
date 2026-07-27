"""
Module: stratify_accuracy

Purpose:
    Calculates accuracy rates for different hop-count bins to analyze
    the relationship between reasoning depth and model performance.

Functions:
    - load_annotated_data: Loads the annotated dataset.
    - bin_hop_length: Bins the hop lengths.
    - calculate_accuracy_by_bin: Calculates accuracy per bin.
    - write_results: Writes results to a file.
    - main: Entry point for the script.
"""
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_annotated_data(file_path: Path) -> list:
    """
    Loads the annotated dataset from a CSV file.

    Args:
        file_path (Path): Path to the CSV file.

    Returns:
        list: List of records.
    """
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def bin_hop_length(hop_count: int) -> str:
    """
    Bins the hop length into categories.

    Args:
        hop_count (int): The hop count.

    Returns:
        str: The bin label.
    """
    if hop_count <= 1:
        return '1'
    elif hop_count == 2:
        return '2'
    else:
        return '3+'

def calculate_accuracy_by_bin(records: list) -> dict:
    """
    Calculates accuracy for each bin.

    Args:
        records (list): List of annotated records.

    Returns:
        dict: Accuracy per bin.
    """
    bin_stats = defaultdict(lambda: {'correct': 0, 'total': 0})

    for record in records:
        hop = int(record.get('chain_length', -1))
        bin_label = bin_hop_length(hop)
        is_correct = record.get('correctness', 'False').lower() == 'true'

        bin_stats[bin_label]['total'] += 1
        if is_correct:
            bin_stats[bin_label]['correct'] += 1

    results = {}
    for bin_label, stats in bin_stats.items():
        accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0
        results[bin_label] = {
            'accuracy': accuracy,
            'count': stats['total']
        }

    return results

def write_results(results: dict, output_path: Path):
    """
    Writes results to a JSON file.

    Args:
        results (dict): Results to write.
        output_path (Path): Output file path.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """
    Main entry point for the stratify_accuracy script.
    """
    logger.info("Stratifying accuracy by hop bin...")
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "annotated_videokr.csv"
    output_path = project_root / "data" / "processed" / "stratified_accuracy.json"

    if not input_path.exists():
        logger.error("Input file not found.")
        sys.exit(1)

    records = load_annotated_data(input_path)
    results = calculate_accuracy_by_bin(records)
    write_results(results, output_path)

    logger.info(f"Results written to {output_path}")

if __name__ == "__main__":
    main()
