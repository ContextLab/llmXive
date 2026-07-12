"""
Script to run the test type detector on extracted summaries.
"""

import json
import sys
import logging
from pathlib import Path

from code.src.audit.test_type_detector import detect_outcome_types_batch
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

logger = get_default_logger()


def main() -> int:
    """
    Main entry point for running the test type detector.
    
    Reads from data/extracted_summaries.json and writes to data/outcome_types.json.
    """
    input_path = Path("data/extracted_summaries.json")
    output_path = Path("data/outcome_types.json")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the extraction pipeline first (T020).")
        return 1

    logger.info(f"Loading summaries from {input_path}")
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            summaries_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return 1

    if not summaries_data:
        logger.warning("No summaries found in input file.")
        # Write empty results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        return 0

    # Convert to ABTestSummary objects
    try:
        summaries = [ABTestSummary(**item) for item in summaries_data]
    except Exception as e:
        logger.error(f"Failed to parse summaries: {e}")
        return 1

    logger.info(f"Running outcome type detection on {len(summaries)} summaries")
    results = detect_outcome_types_batch(summaries)

    # Count outcomes
    outcome_counts = {"binary": 0, "continuous": 0, "unknown": 0}
    for r in results:
        outcome_counts[r["outcome_type"]] += 1

    logger.info(f"Detection results: {outcome_counts}")

    # Write results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Wrote outcome type detection results to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())