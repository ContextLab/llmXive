from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional, List, Tuple

import pandas as pd
from scipy.stats import spearmanr

__all__ = [
    "load_metrics_data",
    "compute_spearman_correlation",
    "run_correlation_analysis",
    "save_correlation_results",
    "run_sensitivity_analysis",
    "compute_correlation_matrix",
    "main",
]

def _processed_dir() -> Path:
    """Convenient accessor for the processed data directory."""
    return Path("data/processed")

def _analysis_dir() -> Path:
    """Convenient accessor for the analysis output directory."""
    return Path("data/analysis")

def load_metrics_data() -> pd.DataFrame:
    """
    Load the three metric files (clone density, perplexity, bug‑detection)
    and merge them into a single ``DataFrame``.  Missing files are ignored
    but a warning is emitted.
    """
    clone_path = _processed_dir() / "clone_metrics.csv"
    perplexity_path = _processed_dir() / "perplexity_scores.csv"
    bug_path = _processed_dir() / "bug_detection_results.csv"

    dfs: List[pd.DataFrame] = []

    if clone_path.is_file():
        df_clone = pd.read_csv(clone_path)
        dfs.append(df_clone)
    else:
        logging.warning(f"{clone_path} not found – clone density will be unavailable")

    if perplexity_path.is_file():
        df_perp = pd.read_csv(perplexity_path)
        dfs.append(df_perp)
    else:
        logging.warning(f"{perplexity_path} not found – perplexity will be unavailable")

    if bug_path.is_file():
        df_bug = pd.read_csv(bug_path)
        dfs.append(df_bug)
    else:
        logging.warning(f"{bug_path} not found – bug‑detection accuracy will be unavailable")

    if not dfs:
        raise FileNotFoundError("No metric files found in data/processed/")

    # Merge on a common identifier if present; otherwise perform a simple concatenation.
    # Many pipelines use ``file_path`` or ``problem_id`` – we attempt both.
    merged = dfs[0]
    for other in dfs[1:]:
        # Try to merge on common columns; fallback to outer join on index.
        common = set(merged.columns).intersection(other.columns)
        if common:
            merged = pd.merge(merged, other, on=list(common), how="outer")
        else:
            merged = pd.concat([merged, other], axis=1, join="outer")
    return merged

def compute_spearman_correlation(
    df: pd.DataFrame, col_x: str, col_y: str
) -> Tuple[float, float, int]:
    """
    Compute Spearman rank correlation between two columns.

    Returns
    -------
    rho : float
        Spearman correlation coefficient.
    p_value : float
        Two‑tailed p‑value.
    n : int
        Number of non‑NaN paired observations used in the computation.
    """
    if col_x not in df or col_y not in df:
        raise KeyError(f"Columns {col_x} or {col_y} not present in DataFrame")

    # Drop rows where either column is NaN
    clean = df[[col_x, col_y]].dropna()
    n = len(clean)
    if n == 0:
        raise ValueError(f"No overlapping data for columns {col_x} and {col_y}")

    rho, p_value = spearmanr(clean[col_x], clean[col_y])
    return float(rho), float(p_value), n

def save_correlation_results(
    results: List[Tuple[str, str, float, float, int]],
    output_path: Optional[Path] = None,
) -> None:
    """
    Persist correlation results (including p‑values) to CSV.

    Parameters
    ----------
    results : list of tuples
        Each tuple is ``(metric_x, metric_y, rho, p_value, n)``.
    output_path : pathlib.Path, optional
        Destination file. If omitted the default
        ``data/analysis/correlation_results.csv`` is used.
    """
    if output_path is None:
        output_path = _analysis_dir() / "correlation_results.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csvfile = csv.writer(csvfile)
        writer.writerow(
            ["metric_x", "metric_y", "spearman_rho", "p_value", "n_observations"]
        )
        for metric_x, metric_y, rho, pval, n in results:
            writer.writerow(
                [metric_x, metric_y, f"{rho:.6f}", f"{pval:.6f}", n]
            )
    logging.info(f"Correlation results saved to {output_path}")

def run_correlation_analysis() -> None:
    """
    End‑to‑end routine that loads metrics, computes the required
    Spearman correlations, and writes the results to CSV.
    """
    df = load_metrics_data()
    results: List[Tuple[str, str, float, float, int]] = []

    # Clone density ↔ Perplexity
    if "clone_density" in df.columns and "perplexity" in df.columns:
        rho, pval, n = compute_spearman_correlation(
            df, "clone_density", "perplexity"
        )
        results.append(("clone_density", "perplexity", rho, pval, n))

    # Clone density ↔ Accuracy (if available)
    if "clone_density" in df.columns and "accuracy" in df.columns:
        rho, pval, n = compute_spearman_correlation(
            df, "clone_density", "accuracy"
        )
        results.append(("clone_density", "accuracy", rho, pval, n))

    if not results:
        logging.warning("No suitable metric pairs found for correlation.")
        return

    save_correlation_results(results)

def run_sensitivity_analysis() -> None:
    """
    Placeholder for the sensitivity analysis required by US3.  The
    implementation lives in ``code/correlation_analysis.py`` (US3) and
    re‑uses ``run_correlation_analysis`` after adjusting thresholds.
    """
    # The actual sensitivity logic is implemented elsewhere; we simply
    # expose the entry‑point here for completeness.
    run_correlation_analysis()

def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a full Spearman correlation matrix for all numeric columns.
    """
    numeric_df = df.select_dtypes(include=["number"])
    corr = numeric_df.corr(method="spearman")
    return corr

def main() -> None:
    """
    Script entry‑point used by the quick‑start run‑book.
    """
    logging.basicConfig(level=logging.INFO)
    run_correlation_analysis()
