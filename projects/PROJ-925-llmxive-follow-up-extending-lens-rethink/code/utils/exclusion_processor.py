"""
code/utils/exclusion_processor.py
Processes exclusion logs and generates summary statistics.
"""
import os
import json
import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Tuple

from config import get_paths
from utils.logging import get_logger

logger = get_logger(__name__)

def parse_exclusion_log(log_path: Path) -> List[Dict[str, str]]:
    """Parse the exclusion log file into a list of records."""
    records = []
    if not log_path.exists():
        logger.warning(f"Exclusion log not found: {log_path}")
        return records

    with open(log_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 3:
                records.append({
                    "caption_id": parts[0],
                    "reason": parts[1],
                    "caption_preview": parts[2]
                })
            else:
                logger.warning(f"Malformed exclusion log line: {line}")
    return records

def aggregate_exclusions(records: List[Dict[str, str]]) -> Dict[str, int]:
    """Aggregate exclusion counts by reason."""
    counts = defaultdict(int)
    for record in records:
        reason = record.get("reason", "UNKNOWN")
        counts[reason] += 1
    return dict(counts)

def write_summary(summary: Dict[str, int], output_path: Path):
    """Write the exclusion summary to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Exclusion summary written to {output_path}")

def main():
    """Main entry point for exclusion processing."""
    paths = get_paths()
    log_path = paths.logs / "exclusions.log"
    output_path = paths.processed / "exclusion_summary.json"

    logger.info("Processing exclusion logs")

    records = parse_exclusion_log(log_path)
    summary = aggregate_exclusions(records)

    write_summary(summary, output_path)

    total_excluded = sum(summary.values())
    logger.info(f"Total exclusions: {total_excluded}")
    logger.info(f"Breakdown: {summary}")

    return summary

if __name__ == "__main__":
    main()
