"""
validate_dataset_stats.py

Implements task **T016** – Validate Dataset Statistics.

The script validates that the generated dataset exhibits a statistically
significant non‑zero KL divergence for at least one quantization level.
If the required ``dataset_stats.json`` file is missing, the script will
compute the statistics directly from the processed training sample
parquet file (``data/processed/training_sample.parquet``) and write the
missing JSON file.  This ensures the validation step can succeed even
when the upstream generation script failed to produce the stats file.

Usage::

    python code/cli/validate_dataset_stats.py \
        [--stats PATH_TO_STATS_JSON] \
        [--data PATH_TO_TRAINING_SAMPLE_PARQUET] \
        [--alpha SIGNIFICANCE_THRESHOLD]

The ``--data`` argument is optional; it is only required when the
statistics file does not already exist.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from scipy.stats import ttest_1samp

DEFAULT_STATS_PATH = Path("data/processed/dataset_stats.json")
DEFAULT_DATA_PATH = Path("data/processed/training_sample.parquet")

def load_stats(stats_path: Path) -> dict:
    """Load the JSON statistics file."""
    if not stats_path.is_file():
        raise FileNotFoundError(f"Statistics file not found: {stats_path}")
    with open(stats_path, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_statistics(df: pd.DataFrame, levels: List[str]) -> dict:
    """
    Compute per‑level statistics (sample count, mean KL, t‑statistic,
    p‑value, non‑zero fraction) and return the JSON structure used by
    downstream validation scripts.
    """
    stats = {}
    for level in levels:
        level_kl = df[df["quantization_level"] == level]["kl_divergence"].values
        if len(level_kl) == 0:
            # No data for this level – skip it.
            continue
        t_stat, p_val = ttest_1samp(level_kl, popmean=0.0)
        stats[level] = {
            "sample_count": int(len(level_kl)),
            "mean_kl": float(np.mean(level_kl)),
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "non_zero_fraction": float(np.mean(level_kl > 0)),
        }

    overall_significant = any(v["p_value"] < 0.05 for v in stats.values())
    summary = {
        "per_level_statistics": stats,
        "overall_non_zero_kl_significant": overall_significant,
    }
    return summary

def write_stats(stats: dict, stats_path: Path) -> None:
    """Write the statistics dictionary to ``stats_path`` as pretty‑printed JSON."""
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

def validate(stats: dict, alpha: float = 0.05) -> bool:
    """
    Return ``True`` if any quantization level reports a p‑value
    smaller than ``alpha``.
    """
    per_level = stats.get("per_level_statistics", {})
    for level, metrics in per_level.items():
        p = metrics.get("p_value")
        if p is not None and p < alpha:
            return True
    return False

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that the generated dataset exhibits a statistically "
            "significant non‑zero KL divergence.  If the statistics file is "
            "missing, it will be created from the training sample parquet "
            "file."
        )
    )
    parser.add_argument(
        "--stats",
        type=str,
        default=str(DEFAULT_STATS_PATH),
        help=(
            "Path to the dataset statistics JSON file.  If the file does not "
            "exist, it will be created from the training sample data."
        ),
    )
    parser.add_argument(
        "--data",
        type=str,
        default=str(DEFAULT_DATA_PATH),
        help=(
            "Path to the processed training sample parquet file. Required only "
            "when the statistics JSON is missing."
        ),
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold (default 0.05).",
    )
    args = parser.parse_args()

    stats_path = Path(args.stats).expanduser().resolve()
    data_path = Path(args.data).expanduser().resolve()

    # Load or compute the statistics.
    try:
        stats = load_stats(stats_path)
    except FileNotFoundError:
        # Statistics file missing – attempt to compute it from the parquet data.
        if not data_path.is_file():
            print(
                f"Error: Neither statistics file nor training data found. "
                f"Missing stats: {stats_path}, missing data: {data_path}",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            df = pd.read_parquet(data_path)
        except Exception as exc:
            print(f"Failed to read training data parquet: {exc}", file=sys.stderr)
            sys.exit(1)

        # Determine the set of quantization levels present in the data.
        levels = sorted(df["quantization_level"].unique().tolist())
        stats = compute_statistics(df, levels)
        try:
            write_stats(stats, stats_path)
            print(f"Statistics written to {stats_path}")
        except Exception as exc:
            print(f"Failed to write statistics JSON: {exc}", file=sys.stderr)
            sys.exit(1)

    # Perform validation.
    if validate(stats, alpha=args.alpha):
        print(
            f"Validation passed: at least one quantization level shows p < {args.alpha}."
        )
        sys.exit(0)
    else:
        print(
            f"Validation failed: no quantization level achieved statistical "
            f"significance (p < {args.alpha}).",
            file=sys.stderr,
        )
        sys.exit(1)

if __name__ == "__main__":
    main()