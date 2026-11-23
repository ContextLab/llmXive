"""
Data Merger

Merges centrality metrics with cognitive scores.
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging_config import setup_logging, get_logger
from code.utils.io_utils import write_json, read_json, write_dicts_to_csv, read_csv_as_dicts

def merge_data():
    """
    Merge centrality metrics with cognitive scores.
    """
    logger = get_logger("data_merger")
    logger.info("Merging Data")

    centrality_path = project_root / "data" / "analysis" / "centrality_metrics.csv"
    clinical_path = project_root / "data" / "raw" / "clinical_data.csv"

    if not centrality_path.exists():
        logger.error("Centrality metrics not found.")
        return 1

    if not clinical_path.exists():
        logger.error("Clinical data not found.")
        return 1

    centrality_data = read_csv_as_dicts(centrality_path)
    clinical_data = read_csv_as_dicts(clinical_path)

    # Merge on participant_id
    clinical_dict = {row["participant_id"]: row for row in clinical_data}
    merged = []

    for row in centrality_data:
        pid = row["participant_id"]
        if pid in clinical_dict:
            merged_row = {**row, **clinical_dict[pid]}
            merged.append(merged_row)
        else:
            logger.warning(f"Participant {pid} not found in clinical data.")

    output_path = project_root / "data" / "analysis" / "merged_dataset.csv"
    write_dicts_to_csv(output_path, merged)

    logger.info(f"Wrote merged dataset to {output_path}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Merge Data")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)

    return merge_data()

if __name__ == "__main__":
    sys.exit(main())
