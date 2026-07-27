"""
Module: calculate_annotation_coverage

Purpose:
    Calculates and reports the coverage of the annotation process,
    determining how many questions were successfully mapped to the graph.

Functions:
    - load_annotated_data: Loads the annotated CSV.
    - calculate_coverage: Computes coverage metrics.
    - save_coverage_results: Saves metrics to JSON.
    - main: Entry point for the script.
"""
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_annotated_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Loads the annotated dataset from a CSV file.

    Args:
        file_path (Path): Path to the CSV file.

    Returns:
        List[Dict[str, Any]]: List of records.
    """
    import csv
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def calculate_coverage(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates coverage metrics from the annotated records.

    Args:
        records (List[Dict[str, Any]]): List of annotated records.

    Returns:
        Dict[str, Any]: Metrics including total, annotated, and proportion.
    """
    total = len(records)
    annotated = sum(1 for r in records if r.get('entity_node_id') != 'unmapped')
    unresolvable = total - annotated
    proportion = annotated / total if total > 0 else 0.0

    return {
        "total_input_records": total,
        "annotated_count": annotated,
        "unresolvable_count": unresolvable,
        "proportion": proportion
    }

def save_coverage_results(metrics: Dict[str, Any], output_path: Path):
    """
    Saves coverage metrics to a JSON file.

    Args:
        metrics (Dict[str, Any]): Metrics to save.
        output_path (Path): Path to the output JSON file.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """
    Main entry point for the calculate_annotation_coverage script.
    """
    logger.info("Calculating annotation coverage...")
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "annotated_videokr.csv"
    output_path = project_root / "data" / "processed" / "annotation_coverage.json"

    if not input_path.exists():
        logger.error("Annotated data file not found.")
        sys.exit(1)

    records = load_annotated_data(input_path)
    metrics = calculate_coverage(records)
    save_coverage_results(metrics, output_path)

    logger.info(f"Coverage calculated: {metrics['proportion']:.2%}")
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
