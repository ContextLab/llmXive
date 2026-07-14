"""
Re‑run statistical analyses (t‑test and linear regression) on each cleaned
dataset variant produced by the cleaning pipeline and aggregate the results
into ``data/processed/cleaned_metrics.json``.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis

logger = setup_logging(log_level="INFO")

def _find_cleaned_csv_files(processed_dir: Path) -> list[Path]:
    """
    Locate CSV files that represent cleaned variants. By convention they
    contain the substring ``cleaned`` in their filename.
    """
    return sorted(
        [p for p in processed_dir.glob("*.csv") if "cleaned" in p.name.lower()]
    )

def main() -> None:
    """
    Entry point used by the quick‑start pipeline. It performs the following:

    1. Pins a deterministic random seed for reproducibility.
    2. Discovers cleaned CSV files in ``data/processed``.
    3. Runs ``run_baseline_analysis`` on each cleaned DataFrame.
    4. Writes a single JSON file mapping each variant name to its metrics.
    """
    # 1. Reproducibility
    pin_random_seed(42)

    processed_dir = Path("data/processed")
    cleaned_files = _find_cleaned_csv_files(processed_dir)

    if not cleaned_files:
        logger.warning(
            "No cleaned dataset files found in %s. Skipping cleaned metrics generation.",
            processed_dir,
        )
        return

    aggregated_metrics: Dict[str, Any] = {}

    for csv_path in cleaned_files:
        try:
            df = pd.read_csv(csv_path)
            logger.info("Analyzing cleaned variant: %s", csv_path.name)
            metrics = run_baseline_analysis(dataframe=df)
            variant_key = csv_path.stem  # filename without extension
            aggregated_metrics[variant_key] = metrics
        except Exception as e:
            logger.error("Failed to analyze %s: %s", csv_path.name, e)

    # Write aggregated results
    output_path = processed_dir / "cleaned_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(aggregated_metrics, f, indent=2)

    logger.info("Cleaned metrics written to %s", output_path)

if __name__ == "__main__":
    main()