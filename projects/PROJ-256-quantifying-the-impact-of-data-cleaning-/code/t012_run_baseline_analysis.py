"""
T012 – Run baseline statistical analysis on raw datasets.
Produces a raw JSON file with per‑dataset statistics that will later be
validated and recorded by T013.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
from scipy import stats

from utils import setup_logging, pin_random_seed
from config import get_config

logger = setup_logging("INFO")


def _load_csv_files(raw_dir: str) -> List[Path]:
    """Return a list of CSV files found in ``raw_dir``."""
    raw_path = Path(raw_dir)
    if not raw_path.is_dir():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        return []
    return list(raw_path.glob("*.csv"))


def _analyze_dataset(csv_path: Path) -> Dict[str, Any]:
    """
    Perform a simple baseline analysis:
    - Assume the first column is the outcome (numeric)
    - Assume the second column is a predictor (numeric)
    - Compute a two‑sample t‑test on the two columns
    - Compute Cohen's d as effect size
    - Compute a 95 % confidence interval for the mean difference
    """
    df = pd.read_csv(csv_path)

    # Require at least two numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < 2:
        logger.warning(f"Dataset {csv_path.name} does not have two numeric columns; skipping.")
        return {}

    outcome = df[numeric_cols[0]].dropna()
    predictor = df[numeric_cols[1]].dropna()

    # Ensure we have enough observations
    if len(outcome) < 2 or len(predictor) < 2:
        logger.warning(f"Not enough data in {csv_path.name} for t‑test; skipping.")
        return {}

    # Two‑sample t‑test (assuming independent groups)
    t_stat, p_val = stats.ttest_ind(outcome, predictor, equal_var=False)

    # Cohen's d
    diff = outcome.mean() - predictor.mean()
    pooled_sd = np.sqrt(((outcome.std(ddof=1) ** 2) + (predictor.std(ddof=1) ** 2)) / 2)
    effect_size = diff / pooled_sd if pooled_sd != 0 else 0.0

    # 95 % CI for the difference of means
    se = np.sqrt(outcome.var(ddof=1) / len(outcome) + predictor.var(ddof=1) / len(predictor))
    ci_lower = diff - stats.t.ppf(0.975, df=min(len(outcome), len(predictor)) - 1) * se
    ci_upper = diff + stats.t.ppf(0.975, df=min(len(outcome), len(predictor)) - 1) * se

    return {
        "dataset_name": csv_path.stem,
        "p_value": float(p_val),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "effect_size": float(effect_size),
    }


def run_baseline_analysis(raw_dir: str,
                          output_file: str,
                          *args,
                          **kwargs) -> int:
    """
    Wrapper that matches the various call signatures used across the code base.
    Accepts either positional arguments (raw_dir, output_file, config) or
    keyword arguments (raw_dir=…, output_file=…, analysis_config=…).

    Returns 0 on success, non‑zero on failure.
    """
    # Resolve possible keyword arguments
    raw_dir = kwargs.get("raw_dir", raw_dir)
    output_file = kwargs.get("output_file", output_file)

    logger.info(f"Running baseline analysis on raw data in {raw_dir}")

    csv_files = _load_csv_files(raw_dir)
    if not csv_files:
        logger.error("No CSV files found for baseline analysis.")
        return 1

    results: List[Dict[str, Any]] = []
    for csv_path in csv_files:
        res = _analyze_dataset(csv_path)
        if res:
            results.append(res)

    # Write raw results
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Baseline raw output written to {output_file}")
    return 0


def main() -> int:
    """
    Entry‑point used by the integration test.
    Reads configuration from ``config.get_config()`` if available.
    """
    cfg = get_config()
    raw_dir = cfg.get("RAW_DATA_PATH", "data/raw")
    output_file = cfg.get("BASELINE_RAW_OUTPUT_PATH",
                          "data/processed/baseline_raw_output.json")
    return run_baseline_analysis(raw_dir, output_file)


if __name__ == "__main__":
    raise SystemExit(main())
