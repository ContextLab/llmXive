"""
t023_reanalyze_cleaned_variants.py
----------------------------------

Re‑runs statistical analyses (t‑tests and linear regressions) on each cleaned
dataset that resides in ``data/processed/``.  The script aggregates the results
and writes them to ``data/processed/cleaned_metrics.json``.

This script is invoked by the quick‑start run‑book; it relies on the flexible
``run_baseline_analysis`` implementation in ``code.analysis``.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis

logger = setup_logging(log_level="INFO")
pin_random_seed(42)


def _find_cleaned_csv_files(processed_dir: Path) -> List[Path]:
    """
    Return a list of CSV files that represent cleaned variants.
    Heuristic: filenames containing the word ``cleaned`` or any
    ``*_outlier_removed.csv`` style naming used by the cleaning step.
    """
    patterns = ["*cleaned*.csv", "*outlier_removed*.csv", "*imputed*.csv", "*recoded*.csv"]
    files: List[Path] = []
    for pat in patterns:
        files.extend(processed_dir.glob(pat))
    # De‑duplicate while preserving order
    seen = set()
    uniq = []
    for f in files:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def main() -> None:
    """
    Entry point for the quick‑start pipeline.

    Steps:
    1. Locate cleaned CSV files under ``data/processed/``.
    2. For each file, load it into a DataFrame and invoke
       ``run_baseline_analysis`` (DataFrame‑mode) to obtain metrics.
    3. Aggregate the per‑file metrics into a single dictionary.
    4. Write the aggregated dictionary to
       ``data/processed/cleaned_metrics.json``.
    """
    processed_dir = Path("data/processed")
    if not processed_dir.is_dir():
        logger.error(f"Processed directory {processed_dir} does not exist.")
        return

    cleaned_files = _find_cleaned_csv_files(processed_dir)
    if not cleaned_files:
        logger.warning("No cleaned CSV files found – cleaned_metrics.json will be empty.")
    else:
        logger.info(f"Found {len(cleaned_files)} cleaned dataset(s) to analyse.")

    all_metrics: Dict[str, Dict] = {}
    for csv_path in cleaned_files:
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Analyzing cleaned dataset: {csv_path.name}")
            metrics = run_baseline_analysis(dataframe=df)
            if metrics:  # could be empty if analysis failed
                all_metrics[csv_path.name] = metrics
        except Exception as e:
            logger.exception(f"Failed to process {csv_path.name}: {e}")

    output_path = processed_dir / "cleaned_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_metrics, f, indent=2)
        logger.info(f"Wrote cleaned metrics to {output_path}")
    except Exception as e:
        logger.exception(f"Failed to write cleaned metrics JSON: {e}")


if __name__ == "__main__":
    main()
