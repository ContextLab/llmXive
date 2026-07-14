"""
Final report generation (Task T041).

Combines the comparison report with visualisations and writes a summary
JSON file.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from utils import setup_logging

logger = setup_logging(log_level="INFO")

def write_summary_text() -> None:
    comparison_path = Path("data/processed/comparison_report.json")
    if not comparison_path.is_file():
        logger.error("Comparison report missing; cannot generate final summary.")
        return

    comparison = json.load(open(comparison_path, "r", encoding="utf-8"))
    summary = {
        "generated_at": comparison.get("generated_at", "unknown"),
        "num_datasets": len(comparison.get("baseline_metrics", [])),
        "overall_fpr": None,
        "notes": "See accompanying visualisations in the output directory.",
    }
    summary_path = Path("output/final_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Final summary written to {summary_path}")

def main() -> None:
    write_summary_text()

if __name__ == "__main__":
    main()