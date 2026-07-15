"""
Re‑run statistical analyses (t‑test + linear regression) on each cleaned dataset
produced by the cleaning pipeline and store the aggregated results in
`data/processed/cleaned_metrics.json`.

This script is invoked by the quick‑start run‑book and serves as the concrete
implementation for task T023.
"""
import json
import logging
from pathlib import Path
from typing import List

import pandas as pd

import pandas as pd

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis

logger = setup_logging(log_level="INFO")
pin_random_seed(42)


def _load_cleaned_datasets(processed_dir: Path) -> List[Path]:
    """Return a list of CSV files that represent cleaned variants."""
    pattern = "*_cleaned.csv"
    files = list(processed_dir.glob(pattern))
    if not files:
        logger.warning("No cleaned dataset files found with pattern %s in %s", pattern, processed_dir)
    return files


def main() -> None:
    """Entry point for the script."""
    processed_dir = Path("data/processed")
    cleaned_files = _load_cleaned_datasets(processed_dir)

    cleaned_metrics = {}
    for csv_path in cleaned_files:
        try:
            df = pd.read_csv(csv_path)
            logger.info("Analyzing cleaned variant: %s", csv_path.name)
            metrics = run_baseline_analysis(dataframe=df)
            cleaned_metrics[csv_path.name] = metrics
            logger.info("Processed cleaned dataset %s", csv_path.name)
        except Exception as exc:
            logger.error("Failed to analyse %s: %s", csv_path.name, exc)

    # Write aggregated metrics
    output_path = processed_dir / "cleaned_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(cleaned_metrics, f, indent=2)
    logger.info("Cleaned metrics written to %s", output_path)

if __name__ == "__main__":
    main()