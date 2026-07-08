import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

__all__ = [
    "load_correlation_results",
    "load_spatial_metrics_summary",
    "load_ingestion_stats",
    "load_sensitivity_delta",
    "load_robustness_results",
    "determine_best_model",
    "calculate_summary_statistics",
    "write_csv_report",
    "write_pdf_report",
    "main",
]

def load_correlation_results(csv_path: str) -> pd.DataFrame:
    """
    Load correlation analysis results.

    Parameters
    ----------
    csv_path: str
        Path to the CSV file produced by ``code/modeling/correlation.py``.

    Returns
    -------
    pd.DataFrame
        DataFrame with correlation results.
    """
    return pd.read_csv(csv_path)

def load_spatial_metrics_summary(csv_path: str) -> pd.DataFrame:
    """
    Load aggregated spatial metrics.

    Parameters
    ----------
    csv_path: str
        Path to the aggregated spatial metrics CSV.

    Returns
    -------
    pd.DataFrame
        DataFrame with metrics.
    """
    return pd.read_csv(csv_path)

def load_ingestion_stats(json_path: str) -> Dict[str, Any]:
    """
    Load ingestion statistics JSON.

    Parameters
    ----------
    json_path: str
        Path to ``state/ingestion_stats.json``.

    Returns
    -------
    Dict[str, Any]
        Dictionary with ingestion statistics.
    """
    with open(json_path, "r") as f:
        return json.load(f)

def load_sensitivity_delta(json_path: str) -> Dict[str, Any]:
    """
    Load sensitivity analysis delta results.

    Parameters
    ----------
    json_path: str
        Path to the JSON file produced by ``code/modeling/sensitivity.py``.

    Returns
    -------
    Dict[str, Any]
        Dictionary with ``'delta_r'`` and ``'significant'``.
    """
    with open(json_path, "r") as f:
        return json.load(f)

def load_robustness_results(csv_path: str) -> pd.DataFrame:
    """
    Load leave‑one‑out robustness results.

    Parameters
    ----------
    csv_path: str
        Path to the CSV produced by ``code/analysis/robustness.py``.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``'sample_id'`` and ``'loo_r'``.
    """
    return pd.read_csv(csv_path)

def determine_best_model(corr_df: pd.DataFrame) -> pd.Series:
    """
    Determine the best model based on the lowest p‑value.

    Parameters
    ----------
    corr_df: pd.DataFrame
        Correlation results DataFrame.

    Returns
    -------
    pd.Series
        Row of the best model.
    """
    best_idx = corr_df["pearson_p"].idxmin()
    return corr_df.loc[best_idx]

def calculate_summary_statistics(
    corr_df: pd.DataFrame,
    spatial_df: pd.DataFrame,
    ingestion_stats: Dict[str, Any],
    sensitivity: Dict[str, Any],
    robustness_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compile a summary table for the final report.

    Parameters
    ----------
    corr_df: pd.DataFrame
        Correlation results.
    spatial_df: pd.DataFrame
        Aggregated spatial metrics.
    ingestion_stats: Dict[str, Any]
        Ingestion statistics.
    sensitivity: Dict[str, Any]
        Sensitivity analysis output.
    robustness_df: pd.DataFrame
        Robustness LOO results.

    Returns
    -------
    pd.DataFrame
        One‑row summary DataFrame.
    """
    best = determine_best_model(corr_df)
    summary = {
        "best_metric": best["metric"],
        "best_pearson_r": best["pearson_r"],
        "best_pearson_p": best["pearson_p"],
        "sample_count": len(spatial_df),
        "ingestion_success_rate": ingestion_stats.get("ingestion_success_rate", np.nan),
        "sensitivity_delta_r": sensitivity.get("delta_r", np.nan),
        "max_loo_change": robustness_df["loo_r"].max() - robustness_df["loo_r"].min(),
    }
    return pd.DataFrame([summary])

def write_csv_report(df: pd.DataFrame, out_path: str) -> None:
    """
    Write the summary report to CSV.

    Parameters
    ----------
    df: pd.DataFrame
        Summary DataFrame.
    out_path: str
        Destination CSV file path.
    """
    df.to_csv(out_path, index=False)
    logging.info("CSV report written to %s", out_path)

def write_pdf_report(df: pd.DataFrame, out_path: str) -> None:
    """
    Generate a simple PDF report from the summary DataFrame.

    The implementation uses ``matplotlib`` to create a table figure and saves it as a PDF.

    Parameters
    ----------
    df: pd.DataFrame
        Summary DataFrame (single row).
    out_path: str
        Destination PDF file path.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis("off")
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    plt.tight_layout()
    plt.savefig(out_path, format="pdf")
    logging.info("PDF report written to %s", out_path)

def main():
    """
    Placeholder main function for report generation.
    """
    logging.info("Report generation placeholder – no CLI implemented.")
