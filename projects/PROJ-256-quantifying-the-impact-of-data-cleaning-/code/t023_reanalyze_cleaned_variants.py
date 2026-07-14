"""
Re‑run statistical analyses (t‑tests + linear regressions) on every cleaned
dataset variant produced by the cleaning pipeline and store the results in
``data/processed/cleaned_metrics.json``.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis
from config import get_config

logger = setup_logging("INFO")


def _discover_cleaned_csvs(processed_dir: Path) -> List[Path]:
    """
    Return a list of CSV files that represent cleaned variants.
    The naming convention used elsewhere is ``<dataset>_cleaned_<strategy>.csv``.
    """
    return sorted(processed_dir.glob("*_cleaned_*.csv"))


def _extract_strategy_from_name(filename: str) -> str:
    """
    Very simple heuristic – the strategy name is the part after the last
    ``_cleaned_`` and before the file extension.
    """
    parts = filename.split("_cleaned_")
    if len(parts) < 2:
        return "unknown"
    return parts[1].rsplit(".", 1)[0]


def main() -> None:
    # Initialise reproducibility and logging
    cfg = get_config()
    pin_random_seed(int(cfg.get("RANDOM_SEED", 42)))
    logger.info("Starting re‑analysis of cleaned dataset variants.")

    processed_dir = Path(cfg.get("PROCESSED_DATA_PATH", "data/processed"))
    cleaned_files = _discover_cleaned_csvs(processed_dir)

    if not cleaned_files:
        logger.warning(f"No cleaned CSV files found in {processed_dir}")
        return

    aggregated_metrics: Dict[str, Dict] = {}

    for csv_path in cleaned_files:
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Failed to read cleaned dataset {csv_path}: {e}")
            continue

        # Assume the first column is the outcome variable
        outcome_col = df.columns[0]
        predictor_cols = [c for c in df.columns if c != outcome_col]

        logger.debug(f"Analyzing {csv_path.name}: outcome={outcome_col}")

        metrics = run_baseline_analysis(
            dataframe=df, outcome=outcome_col, predictors=predictor_cols
        )

        strategy = _extract_strategy_from_name(csv_path.name)
        aggregated_metrics[csv_path.stem] = {
            "strategy": strategy,
            "analysis": metrics,
            "dataset_name": csv_path.stem,
        }

    # Write the consolidated cleaned metrics JSON
    cleaned_metrics_path = Path(
        cfg.get(
            "CLEANED_METRICS_PATH",
            "data/processed/cleaned_metrics.json",
        )
    )
    cleaned_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cleaned_metrics_path, "w", encoding="utf-8") as f:
        json.dump(aggregated_metrics, f, indent=2)

    logger.info(
        f"Cleaned‑variant analysis complete – results written to {cleaned_metrics_path}"
    )


if __name__ == "__main__":
    main()
