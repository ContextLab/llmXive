"""
Evaluation script for Pearson correlation analysis.

This script loads the final processed dataset, computes the Pearson
correlation coefficient and two-tailed p‑value between two numeric
columns (by default ``melting_point`` and ``latent_heat`` if they exist,
otherwise the first two numeric columns), and writes the results to
``data/results/correlation_report.json``.
"""

import json
import logging
from pathlib import Path

import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# Import logger utilities directly to avoid circular imports via utils.__init__
from utils.logger import get_pipeline_logger, log_info, log_error

logger = get_pipeline_logger(__name__)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_raw_materials_data() -> pd.DataFrame:
    """
    Load the final merged dataset produced by ``code/data/assemble_final_dataset.py``.

    Returns
    -------
    pd.DataFrame
        The processed dataset.

    Raises
    ------
    FileNotFoundError
        If the expected CSV file does not exist.
    """
    dataset_path = Path("data/processed/final_dataset.csv")
    if not dataset_path.is_file():
        log_error(f"Final dataset not found at {dataset_path}")
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    log_info(f"Loading final dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)
    return df


def _select_numeric_columns(df: pd.DataFrame) -> tuple:
    """
    Choose two numeric columns for correlation.

    Preference is given to columns named ``melting_point`` and ``latent_heat``.
    If they are not both present, the first two numeric columns are used.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    tuple(str, str)
        The names of the two columns.
    """
    preferred = ["melting_point", "latent_heat"]
    available = [col for col in preferred if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]

    if len(available) == 2:
        return available[0], available[1]

    # Fallback: first two numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        raise ValueError("Dataset does not contain at least two numeric columns for correlation.")
    return numeric_cols[0], numeric_cols[1]


def compute_pearson_r_and_p(df: pd.DataFrame) -> dict:
    """
    Compute Pearson correlation coefficient and p‑value.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    dict
        ``{'pearson_r': float, 'p_value': float}``
    """
    col_x, col_y = _select_numeric_columns(df)
    log_info(f"Computing Pearson correlation between '{col_x}' and '{col_y}'")

    x = df[col_x].to_numpy()
    y = df[col_y].to_numpy()

    # Drop NaNs pairwise
    mask = ~np.isnan(x) & ~np.isnan(y)
    if mask.sum() < 2:
        raise ValueError("Not enough valid data points to compute correlation.")

    r, p = pearsonr(x[mask], y[mask])
    log_info(f"Pearson r = {r:.6f}, p‑value = {p:.6g}")
    return {"pearson_r": r, "p_value": p}


def write_report(report: dict) -> None:
    """
    Write the correlation report to ``data/results/correlation_report.json``.

    Parameters
    ----------
    report : dict
        Dictionary containing ``pearson_r`` and ``p_value``.
    """
    output_path = Path("data/results/correlation_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    log_info(f"Correlation report written to {output_path}")


def main() -> None:
    """
    Entry point for the script.
    """
    try:
        df = load_raw_materials_data()
        report = compute_pearson_r_and_p(df)
        write_report(report)
    except Exception as exc:
        log_error(f"Correlation analysis failed: {exc}")
        raise

if __name__ == "__main__":
    # When executed as a script ``python code/evaluate.py``
    main()
