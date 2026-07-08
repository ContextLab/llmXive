import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional

from analysis.spatial_metrics import process_dataset_and_write_metrics

__all__ = [
    "load_autocorrelation_metrics",
    "load_fourier_metrics",
    "aggregate_spatial_metrics",
    "main",
]

def load_autocorrelation_metrics(csv_path: str) -> pd.DataFrame:
    """
    Load autocorrelation metrics from a CSV file.

    Parameters
    ----------
    csv_path: str
        Path to the CSV file containing autocorrelation metrics.

    Returns
    -------
    pd.DataFrame
        DataFrame with the loaded metrics.
    """
    logging.info("Loading autocorrelation metrics from %s", csv_path)
    return pd.read_csv(csv_path)

def load_fourier_metrics(csv_path: str) -> pd.DataFrame:
    """
    Load Fourier metrics from a CSV file.

    Parameters
    ----------
    csv_path: str
        Path to the CSV file containing Fourier metrics.

    Returns
    -------
    pd.DataFrame
        DataFrame with the loaded metrics.
    """
    logging.info("Loading Fourier metrics from %s", csv_path)
    return pd.read_csv(csv_path)

def aggregate_spatial_metrics(
    autocorr_df: pd.DataFrame, fourier_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Aggregate autocorrelation and Fourier metrics into a single DataFrame.

    The function performs an inner join on ``sample_id`` and ``element`` to
    combine the two metric sets.

    Parameters
    ----------
    autocorr_df: pd.DataFrame
        DataFrame with autocorrelation metrics.
    fourier_df: pd.DataFrame
        DataFrame with Fourier metrics.

    Returns
    -------
    pd.DataFrame
        Aggregated DataFrame containing all spatial metrics.
    """
    logging.info("Aggregating spatial metrics")
    merged = pd.merge(
        autocorr_df,
        fourier_df,
        on=["sample_id", "element"],
        how="inner",
        suffixes=("_auto", "_fourier"),
    )
    return merged

def main(input_dir: str, output_path: str) -> None:
    """
    End‑to‑end entry point for aggregating spatial metrics.

    The function expects two CSV files in ``input_dir``:
    ``autocorrelation_metrics.csv`` and ``fourier_metrics.csv``.  After
    loading and aggregating them, it writes the result to ``output_path``.

    Parameters
    ----------
    input_dir: str
        Directory containing the input CSV files.
    output_path: str
        Destination path for the aggregated CSV.
    """
    auto_path = os.path.join(input_dir, "autocorrelation_metrics.csv")
    fourier_path = os.path.join(input_dir, "fourier_metrics.csv")
    auto_df = load_autocorrelation_metrics(auto_path)
    fourier_df = load_fourier_metrics(fourier_path)
    agg_df = aggregate_spatial_metrics(auto_df, fourier_df)
    agg_df.to_csv(output_path, index=False)
    logging.info("Aggregated metrics written to %s", output_path)
