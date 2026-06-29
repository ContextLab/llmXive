import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)

def load_metrics_data(clone_path: str, perplexity_path: str) -> pd.DataFrame:
    """
    Load clone density metrics and perplexity scores, merging them on a common ``id`` column.

    Parameters
    ----------
    clone_path: str
        Path to the CSV file containing clone metrics. Expected columns include
        ``id`` and ``clone_density``.
    perplexity_path: str
        Path to the CSV file containing perplexity scores. Expected columns include
        ``id`` and ``perplexity``.

    Returns
    -------
    pd.DataFrame
        Merged DataFrame containing ``id``, ``clone_density`` and ``perplexity``.
    """
    clone_df = pd.read_csv(clone_path)
    perplexity_df = pd.read_csv(perplexity_path)
    merged = pd.merge(clone_df, perplexity_df, on="id")
    return merged

def compute_spearman_correlation(x: pd.Series, y: pd.Series) -> float:
    """
    Compute the Spearman rank correlation between two series.

    Returns
    -------
    float
        Spearman correlation coefficient.
    """
    corr, _ = spearmanr(x, y)
    return float(corr)

def compute_correlation_matrix(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Compute a Spearman correlation matrix for the specified columns of ``df``.
    """
    corr = df[columns].corr(method="spearman")
    return corr

def run_correlation_analysis(clone_path: str, perplexity_path: str) -> float:
    """
    End‑to‑end correlation analysis returning a single Spearman coefficient.
    """
    df = load_metrics_data(clone_path, perplexity_path)
    return compute_spearman_correlation(df["clone_density"], df["perplexity"])

def save_correlation_results(output_path: str, result: float) -> None:
    """
    Write the correlation result to ``output_path`` as a one‑row CSV.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"spearman_correlation": [result]}).to_csv(output_path, index=False)

def sensitivity_analysis(
    clone_metrics_path: str,
    perplexity_path: str,
    thresholds: List[float],
) -> Dict[float, float]:
    """
    Perform sensitivity analysis across a list of clone‑density thresholds.

    For each threshold ``t`` we keep only rows where ``clone_density >= t`` and
    compute the Spearman correlation between ``clone_density`` and ``perplexity``.
    The function returns a mapping ``threshold -> correlation``.

    Parameters
    ----------
    clone_metrics_path: str
        Path to the CSV file containing clone metrics.
    perplexity_path: str
        Path to the CSV file containing perplexity scores.
    thresholds: List[float]
        List of clone‑density thresholds to evaluate (e.g. [0.7, 0.8, 0.9]).

    Returns
    -------
    Dict[float, float]
        Mapping from each threshold to its Spearman correlation coefficient.
    """
    df = load_metrics_data(clone_metrics_path, perplexity_path)
    results: Dict[float, float] = {}
    for thr in thresholds:
        subset = df[df["clone_density"] >= thr]
        if len(subset) < 2:
            # Not enough data points to compute a meaningful correlation.
            results[thr] = float("nan")
            continue
        corr = compute_spearman_correlation(
            subset["clone_density"], subset["perplexity"]
        )
        results[thr] = corr
    return results

def main(argv: Optional[List[str]] = None) -> None:
    """
    CLI entry point.

    Usage examples:
    - Basic correlation:
          python correlation_analysis.py --clone data/processed/clone_metrics.csv \\
              --perplexity data/processed/perplexity_scores.csv \\
              --output data/analysis/correlation_results.csv

    - Sensitivity analysis:
          python correlation_analysis.py --clone ... --perplexity ... \\
              --output data/analysis/sensitivity_results.csv \\
              --thresholds 0.7 0.8 0.9
    """
    import argparse

    parser = argparse.ArgumentParser(description="Correlation analysis")
    parser.add_argument(
        "--clone", required=True, help="Path to clone metrics CSV"
    )
    parser.add_argument(
        "--perplexity", required=True, help="Path to perplexity scores CSV"
    )
    parser.add_argument(
        "--output", required=True, help="Path to write correlation result(s)"
    )
    parser.add_argument(
        "--thresholds",
        nargs="*",
        type=float,
        help="Optional list of thresholds for sensitivity analysis",
    )
    args = parser.parse_args(argv)

    if args.thresholds:
        results = sensitivity_analysis(
            args.clone, args.perplexity, args.thresholds
        )
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            list(results.items()),
            columns=["threshold", "spearman_correlation"],
        ).to_csv(output_path, index=False)
    else:
        corr = run_correlation_analysis(args.clone, args.perplexity)
        save_correlation_results(args.output, corr)

if __name__ == "__main__":
    main()
