import logging
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from config import get_config
from utils import setup_logging

logger = logging.getLogger(__name__)


def load_retrieval_results() -> pd.DataFrame:
    """
    Load the retrieval results from the processed data file.

    Returns:
        pd.DataFrame: DataFrame containing retrieval results with columns:
            planet_name, water_mixing_ratio, uncertainty, is_upper_limit,
            detection_limit, min_detectable_concentration

    Raises:
        FileNotFoundError: If the retrieval results file does not exist.
    """
    config = get_config()
    results_path = config["paths"]["processed_dir"] / "retrieval_results.csv"

    if not results_path.exists():
        raise FileNotFoundError(
            f"Retrieval results file not found at {results_path}. "
            "Please ensure T020 has been completed successfully."
        )

    df = pd.read_csv(results_path)
    logger.info(f"Loaded {len(df)} retrieval results from {results_path}")
    return df


def load_metadata() -> pd.DataFrame:
    """
    Load the metadata CSV to get equilibrium temperatures.

    Returns:
        pd.DataFrame: DataFrame with columns including planet_name and temperature.

    Raises:
        FileNotFoundError: If the metadata file does not exist.
    """
    config = get_config()
    metadata_path = config["paths"]["processed_dir"] / "metadata.csv"

    if not results_path.exists():
        raise FileNotFoundError(
            f"Metadata file not found at {metadata_path}. "
            "Please ensure T012 has been completed successfully."
        )

    df = pd.read_csv(metadata_path)
    logger.info(f"Loaded {len(df)} metadata entries from {metadata_path}")
    return df


def merge_data(retrieval_df: pd.DataFrame, metadata_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge retrieval results with metadata on planet_name.

    Args:
        retrieval_df: DataFrame from load_retrieval_results
        metadata_df: DataFrame from load_metadata

    Returns:
        pd.DataFrame: Merged DataFrame with water mixing ratio and temperature.
    """
    merged = pd.merge(
        retrieval_df,
        metadata_df[["planet_name", "temperature"]],
        on="planet_name",
        how="inner"
    )

    logger.info(f"Merged data: {len(merged)} planets with both retrieval and temperature data")
    return merged


def plot_water_vs_temperature(
    df: pd.DataFrame,
    output_path: Path,
    figsize: Tuple[int, int] = (10, 6)
) -> None:
    """
    Generate a diagnostic plot of Water Abundance vs. Temperature.

    This plot visualizes the relationship between water vapor mixing ratio
    (log10) and equilibrium temperature (K). It handles censored data (upper limits)
    by plotting them as downward arrows with error bars, as per the requirements
    for handling low S/N spectra.

    Args:
        df: Merged DataFrame with columns:
            - water_mixing_ratio
            - uncertainty
            - is_upper_limit (bool)
            - temperature
            - planet_name (optional, for labeling)
        output_path: Path where the PNG figure will be saved.
        figsize: Tuple of (width, height) in inches.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=figsize)

    # Separate detected values and upper limits
    detected = df[~df["is_upper_limit"]]
    upper_limits = df[df["is_upper_limit"]]

    # Plot detected values (circles)
    if not detected.empty:
        ax.errorbar(
            detected["temperature"],
            detected["water_mixing_ratio"],
            yerr=detected["uncertainty"],
            fmt='o',
            color='#1f77b4',
            ecolor='#1f77b4',
            capsize=3,
            label='Detected',
            alpha=0.7,
            markersize=6
        )

    # Plot upper limits (downward arrows)
    if not upper_limits.empty:
        # For upper limits, we plot at the limit value with an arrow pointing down
        # We use the uncertainty as the length of the arrow to represent the range
        ax.errorbar(
            upper_limits["temperature"],
            upper_limits["water_mixing_ratio"],
            yerr=[[0], upper_limits["uncertainty"]], # Asymmetric error: 0 up, uncertainty down
            fmt='v',
            color='#d62728',
            ecolor='#d62728',
            capsize=3,
            label='Upper Limit',
            alpha=0.7,
            markersize=6
        )

    # Labels and Title
    ax.set_xlabel("Equilibrium Temperature (K)", fontsize=12)
    ax.set_ylabel(r"Water Mixing Ratio (log$_{10}$)", fontsize=12)
    ax.set_title("Water Abundance vs. Equilibrium Temperature", fontsize=14)

    # Legend
    ax.legend(loc='best')

    # Add a note about censored data if present
    if not upper_limits.empty:
        ax.text(
            0.02, 0.98,
            f"Note: {len(upper_limits)} upper limits included (red triangles)",
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Diagnostic plot saved to {output_path}")


def main() -> None:
    """
    Main entry point for generating the Water vs. Temperature diagnostic plot.
    """
    # Setup logging
    log_path = get_config()["paths"]["log_dir"] / "plotting.log"
    setup_logging(log_file=str(log_path), level=logging.INFO)

    try:
        logger.info("Starting Water Abundance vs. Temperature plot generation...")

        # Load data
        retrieval_df = load_retrieval_results()
        metadata_df = load_metadata()

        # Merge
        merged_df = merge_data(retrieval_df, metadata_df)

        if merged_df.empty:
            logger.error("No data available to plot. Merged DataFrame is empty.")
            return

        # Define output path
        config = get_config()
        output_path = config["paths"]["results_dir"] / "plots" / "water_vs_temp.png"

        # Generate plot
        plot_water_vs_temperature(merged_df, output_path)

        logger.info("Plot generation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during plot generation: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
