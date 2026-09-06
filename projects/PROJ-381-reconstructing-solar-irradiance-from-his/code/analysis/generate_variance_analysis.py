import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

from config import ensure_directories
from env_manager import get_data_path
from analysis.stats import run_bootstrap_analysis

logger = logging.getLogger(__name__)


def calculate_period_statistics(
    df: pd.DataFrame, period_name: str, tsi_col: str = "tsi"
) -> Dict[str, float]:
    """
    Calculate basic statistics for a specific period.

    Args:
        df: DataFrame containing the period's data.
        period_name: Name of the period (e.g., 'Maunder Minimum').
        tsi_col: Column name for TSI values.

    Returns:
        Dictionary with period statistics.
    """
    if df.empty:
        logger.warning(f"No data found for period: {period_name}")
        return {
            "period": period_name,
            "count": 0,
            "mean_tsi": None,
            "std_tsi": None,
            "min_tsi": None,
            "max_tsi": None,
        }

    stats = {
        "period": period_name,
        "count": int(len(df)),
        "mean_tsi": float(df[tsi_col].mean()),
        "std_tsi": float(df[tsi_col].std()),
        "min_tsi": float(df[tsi_col].min()),
        "max_tsi": float(df[tsi_col].max()),
    }
    return stats


def run_variance_analysis(
    reconstruction_path: str,
    output_path: str,
    periods: Dict[str, Dict[str, int]],
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run the full variance analysis pipeline including bootstrap resampling
    and comparison across historical minima.

    Args:
        reconstruction_path: Path to the reconstruction parquet file.
        output_path: Path to save the variance analysis JSON report.
        periods: Dictionary defining period names and their year ranges.
        n_bootstrap: Number of bootstrap iterations.
        seed: Random seed for reproducibility.

    Returns:
        The variance analysis report dictionary.
    """
    logger.info(f"Loading reconstruction data from {reconstruction_path}")
    if not os.path.exists(reconstruction_path):
        raise FileNotFoundError(
            f"Reconstruction file not found at {reconstruction_path}. "
            "Ensure T022 (generate_reconstruction) has been run successfully."
        )

    df = pd.read_parquet(reconstruction_path)

    if "year" not in df.columns or "tsi" not in df.columns:
        raise ValueError(
            f"Reconstruction data must contain 'year' and 'tsi' columns. "
            f"Found columns: {df.columns.tolist()}"
        )

    logger.info(f"Loaded {len(df)} records. Performing bootstrap analysis...")

    # Run the bootstrap analysis defined in stats.py
    # This function handles filtering, resampling, and comparison
    bootstrap_report = run_bootstrap_analysis(
        df=df,
        periods=periods,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )

    # Calculate basic descriptive statistics for each period
    descriptive_stats = {}
    for period_name, range_dict in periods.items():
        start_year = range_dict["start"]
        end_year = range_dict["end"]
        period_df = df[
            (df["year"] >= start_year) & (df["year"] <= end_year)
        ].copy()
        descriptive_stats[period_name] = calculate_period_statistics(
            period_df, period_name
        )

    # Construct final report
    report = {
        "analysis_config": {
            "n_bootstrap": n_bootstrap,
            "seed": seed,
            "periods_defined": list(periods.keys()),
        },
        "descriptive_statistics": descriptive_stats,
        "bootstrap_results": bootstrap_report,
    }

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Variance analysis report saved to {output_path}")
    return report


def main():
    """Main entry point for variance analysis generation."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    data_path = get_data_path()
    ensure_directories()

    reconstruction_file = "reconstruction_1610_2002.parquet"
    input_path = str(Path(data_path) / "processed" / reconstruction_file)
    output_file = "variance_analysis.json"
    output_path = str(Path(data_path) / "processed" / output_file)

    # Define historical periods of interest based on solar minima
    # These are approximate ranges often cited in solar physics literature
    periods = {
        "Maunder_Minimum": {"start": 1645, "end": 1715},
        "Dalton_Minimum": {"start": 1790, "end": 1830},
        "Modern_Maximum": {"start": 1940, "end": 2000}, # For comparison
    }

    try:
        run_variance_analysis(
            reconstruction_path=input_path,
            output_path=output_path,
            periods=periods,
            n_bootstrap=1000,
            seed=42,
        )
        logger.info("Variance analysis completed successfully.")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Error during variance analysis: {e}")
        raise