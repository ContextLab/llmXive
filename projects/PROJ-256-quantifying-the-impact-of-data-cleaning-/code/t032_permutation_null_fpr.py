"""
T032 – Permutation Null FPR Estimation
-------------------------------------------------
This script generates null datasets by shuffling the outcome variable while
keeping all predictors unchanged. For each permuted dataset it runs the
baseline analysis pipeline and records the p‑values. The false‑positive rate
(FPR) is estimated as the proportion of permutations that yield a
statistically significant p‑value (p ≤ 0.05).
The resulting metrics are written to:
    data/processed/null_fpr_metrics.json
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# Local imports – these modules already exist in the repository
from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis

DEFAULT_NUM_PERMUTATIONS = 100
DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_OUTPUT_FILE = Path("data/processed/null_fpr_metrics.json")
SIGNIFICANCE_THRESHOLD = 0.05


def _load_first_dataset(raw_dir: Path) -> pd.DataFrame:
    """Load the first CSV file found in ``raw_dir``."""
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")
    df = pd.read_csv(csv_files[0])
    if df.empty:
        raise ValueError(f"The dataset {csv_files[0]} is empty.")
    return df


def _infer_outcome_column(df: pd.DataFrame) -> str:
    """
    Heuristic to guess the outcome/target column.
    Preference order:
        1. Column named 'target' or 'outcome' (case‑insensitive)
        2. The last column in the DataFrame
    """
    lowered = [c.lower() for c in df.columns]
    for cand in ("target", "outcome"):
        if cand in lowered:
            return df.columns[lowered.index(cand)]
    # Fallback to the last column
    return df.columns[-1]


def generate_null_fpr_metrics(
    num_permutations: int = DEFAULT_NUM_PERMUTATIONS,
    raw_dir: Path = DEFAULT_RAW_DIR,
    output_path: Path = DEFAULT_OUTPUT_FILE,
) -> Dict[str, any]:
    """
    Generate null‑dataset metrics for false‑positive‑rate estimation.

    Parameters
    ----------
    num_permutations : int
        Number of shuffled datasets to generate.
    raw_dir : Path
        Directory containing the original raw dataset(s).
    output_path : Path
        Where to write the resulting JSON file.

    Returns
    -------
    dict
        Dictionary containing the number of permutations, the estimated FPR,
        and the list of collected p‑values.
    """
    logger = setup_logging(log_level="INFO")
    logger.info("Starting permutation‑based FPR estimation")
    pin_random_seed(42)

    df_original = _load_first_dataset(raw_dir)
    outcome_col = _infer_outcome_column(df_original)
    logger.info(f"Inferred outcome column: '{outcome_col}'")

    p_values: List[float] = []

    for i in range(num_permutations):
        # Shuffle only the outcome column
        df_perm = df_original.copy()
        shuffled = np.random.permutation(df_perm[outcome_col].values)
        df_perm[outcome_col] = shuffled

        # Run the baseline analysis on the permuted data.
        # ``run_baseline_analysis`` is tolerant to being called with a
        # ``dataframe=`` keyword (see its flexible signature).
        try:
            metrics = run_baseline_analysis(dataframe=df_perm)
        except Exception as exc:
            logger.error(f"Baseline analysis failed on permutation {i}: {exc}")
            continue

        # Extract the p‑value from the returned metrics.
        # Expected structure (based on earlier tasks):
        #   {"t_test": {"p_value": <float>, ...}, "linear_regression": {...}}
        p_val = None
        if isinstance(metrics, dict):
            t_test = metrics.get("t_test", {})
            p_val = t_test.get("p_value")
        if p_val is None:
            logger.warning(
                f"Permutation {i}: could not locate p‑value in analysis output."
            )
            continue
        p_values.append(float(p_val))

    # Compute false‑positive rate
    significant = [p for p in p_values if p <= SIGNIFICANCE_THRESHOLD]
    fpr = len(significant) / max(len(p_values), 1)

    result = {
        "num_permutations": num_permutations,
        "outcome_column": outcome_col,
        "false_positive_rate": round(fpr, 5),
        "p_values": [round(p, 5) for p in p_values],
    }

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(
        f"Null‑FPR metrics written to {output_path} (FPR={result['false_positive_rate']})"
    )
    return result


def main() -> None:
    """
    Entry‑point for ``python code/t032_permutation_null_fpr.py``.
    Uses environment variables if present, otherwise defaults.
    """
    num_perm = int(os.getenv("NULL_FPR_PERMUTATIONS", DEFAULT_NUM_PERMUTATIONS))
    raw_dir = Path(os.getenv("RAW_DATA_PATH", DEFAULT_RAW_DIR))
    out_path = Path(os.getenv("NULL_FPR_OUTPUT", DEFAULT_OUTPUT_FILE))

    generate_null_fpr_metrics(num_permutations=num_perm, raw_dir=raw_dir, output_path=out_path)


if __name__ == "__main__":
    main()
