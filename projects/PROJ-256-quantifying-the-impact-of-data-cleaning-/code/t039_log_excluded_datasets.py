"""
Log datasets excluded due to excessive missing outcome rates (Task T039).
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from utils import setup_logging

logger = setup_logging(log_level="INFO")

def load_baseline_metrics() -> List[Dict[str, Any]]:
    path = Path("data/processed/baseline_metrics.json")
    if not path.is_file():
        logger.error("Baseline metrics not found.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_cleaned_metrics() -> List[Dict[str, Any]]:
    path = Path("data/processed/cleaned_metrics.json")
    if not path.is_file():
        logger.error("Cleaned metrics not found.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_missing_outcome_rate(df: Any) -> bool:
    """
    Return True if >80% of the outcome column is missing.
    """
    if not hasattr(df, "columns"):
        return False
    # Heuristic: first binary column is outcome
    outcome_col = None
    for col in df.columns:
        uniq = set(df[col].dropna().unique())
        if uniq <= {0, 1}:
            outcome_col = col
            break
    if outcome_col is None:
        return False
    missing_frac = df[outcome_col].isna().mean()
    return missing_frac > 0.80

def log_excluded_datasets() -> None:
    raw_dir = Path("data/raw")
    for csv_path in raw_dir.glob("*.csv"):
        df = pd.read_csv(csv_path)
        if check_missing_outcome_rate(df):
            logger.warning(
                f"Dataset {csv_path.name} excluded (>80% missing outcome)."
            )

def main() -> None:
    log_excluded_datasets()

if __name__ == "__main__":
    main()