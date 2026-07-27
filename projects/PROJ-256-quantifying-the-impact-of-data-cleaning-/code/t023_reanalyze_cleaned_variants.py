"""
Re‑run statistical analyses (t‑test and linear regression) on each cleaned dataset
produced by the cleaning pipeline and store the aggregated metrics in
``data/processed/cleaned_metrics.json``.

This script is invoked from the quick‑start run‑book (see ``quickstart.md``) and
relies on the flexible ``run_baseline_analysis`` function in ``code/analysis.py``.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from analysis import run_baseline_analysis
from utils import setup_logging, pin_random_seed

logger = setup_logging(log_level="INFO")


def _load_cleaned_datasets(cleaned_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all CSV files in ``cleaned_dir`` that follow the naming convention
    ``*_cleaned.csv`` (or any CSV if the convention is not met) and return a
    mapping from filename to ``pandas.DataFrame``.
    """
    datasets: Dict[str, pd.DataFrame] = {}
    for csv_path in cleaned_dir.glob("*.csv"):
        # Heuristic: treat any CSV in the processed folder as a cleaned variant.
        df = pd.read_csv(csv_path)
        datasets[csv_path.name] = df
    return datasets


def main() -> None:
    """
    Entry point for the task.

    Steps:
    1. Ensure reproducibility.
    2. Locate the directory containing cleaned CSVs (``data/processed``).
    3. Load each cleaned dataset.
    4. Run the baseline analysis on each dataset individually.
    5. Write the combined metrics to ``data/processed/cleaned_metrics.json``.
    """
    pin_random_seed(42)

    cleaned_dir = Path("data") / "processed"
    output_path = cleaned_dir / "cleaned_metrics.json"

    logger.info(f"Loading cleaned datasets from {cleaned_dir}")
    cleaned_datasets = _load_cleaned_datasets(cleaned_dir)
    if not cleaned_datasets:
        logger.error(f"No cleaned CSV files found in {cleaned_dir}")
        raise FileNotFoundError(f"No cleaned CSV files found in {cleaned_dir}")

    all_metrics: Dict[str, Any] = {}
    for name, df in cleaned_datasets.items():
        logger.info(f"Analyzing cleaned dataset: {name}")
        # ``run_baseline_analysis`` returns a dict of metrics for the supplied DataFrame.
        metrics = run_baseline_analysis(dataframe=df)
        all_metrics[name] = metrics

    # Persist the aggregated metrics.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    logger.info(f"Cleaned‑variant metrics written to {output_path}")


if __name__ == "__main__":
    main()