"""
Diagnostic plot: Instrumental Noise vs. Signal.

Generates a scatter plot of Signal-to-Noise Ratio (SNR) vs. Water Vapor Signal
(derived from mixing ratio) to visualize the relationship between data quality
and the detected signal strength. This addresses Rosalind Franklin's concern
about distinguishing water from noise.

Dependencies:
    - data/processed/metadata.csv (from T012)
    - data/processed/retrieval_results.csv (from T020)

Output:
    - results/plots/noise_vs_signal.png
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from config import get_config
from utils import setup_logging

# Configure logging
logger = setup_logging("plots_noise_signal")

def load_analysis_data() -> pd.DataFrame:
    """
    Load and merge metadata and retrieval results.

    Returns:
        DataFrame containing 'planet_name', 'snr', 'water_mixing_ratio', 'is_upper_limit'
    """
    config = get_config()
    data_dir = Path(config["data_dir"])
    
    metadata_path = data_dir / "processed" / "metadata.csv"
    retrieval_path = data_dir / "processed" / "retrieval_results.csv"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    if not retrieval_path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {retrieval_path}")

    meta_df = pd.read_csv(metadata_path)
    retrieval_df = pd.read_csv(retrieval_path)

    # Merge on planet_name
    merged = pd.merge(
        meta_df,
        retrieval_df,
        on="planet_name",
        how="inner"
    )

    required_cols = ["planet_name", "snr", "water_mixing_ratio", "is_upper_limit"]
    missing = [c for c in required_cols if c not in merged.columns]
    if missing:
        raise ValueError(f"Missing required columns in merged data: {missing}")

    return merged

def plot_instrumental_noise_vs_signal(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Instrumental Noise vs. Signal (SNR vs. Water Abundance)"
) -> None:
    """
    Generate the diagnostic plot.

    Plotting Logic:
        - X-axis: SNR (Signal-to-Noise Ratio) from metadata
        - Y-axis: Water Mixing Ratio (log10 scale)
        - Color/Shape: Distinguish between detected values and upper limits (censored)
        - This visualizes the 'Noise vs. Signal' relationship requested by reviewers.
    """
    logger.info(f"Generating plot: {output_path}")

    # Prepare data
    # Ensure mixing ratio is numeric
    df = df.copy()
    df["water_mixing_ratio"] = pd.to_numeric(df["water_mixing_ratio"], errors="coerce")
    df["snr"] = pd.to_numeric(df["snr"], errors="coerce")

    # Drop rows with missing critical values
    valid_df = df.dropna(subset=["snr", "water_mixing_ratio"])

    if len(valid_df) == 0:
        logger.warning("No valid data points found for plotting.")
        # Create an empty plot to satisfy the artifact requirement
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No valid data available", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(title)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        return

    # Set style
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(12, 8))

    # Separate detected vs. upper limits
    detected = valid_df[~valid_df["is_upper_limit"]]
    upper_limits = valid_df[valid_df["is_upper_limit"]]

    # Plot detected values
    if not detected.empty:
        ax.scatter(
            detected["snr"],
            detected["water_mixing_ratio"],
            c="tab:blue",
            label="Detected Signal",
            alpha=0.7,
            s=100,
            edgecolors="black",
            linewidth=0.5
        )

    # Plot upper limits (using different marker)
    if not upper_limits.empty:
        # For upper limits, we might want to show them as arrows or distinct markers.
        # Here we use a distinct marker and color to indicate censored data.
        ax.scatter(
            upper_limits["snr"],
            upper_limits["water_mixing_ratio"],
            c="tab:red",
            marker="v",  # Downward triangle for upper limit
            label="Upper Limit (Censored)",
            alpha=0.7,
            s=100,
            edgecolors="black",
            linewidth=0.5
        )

    # Labels and Title
    ax.set_xlabel("Signal-to-Noise Ratio (SNR)", fontsize=12)
    ax.set_ylabel("Log10 Water Mixing Ratio", fontsize=12)
    ax.set_title(title, fontsize=14)

    # Add a grid for readability
    ax.grid(True, linestyle="--", alpha=0.6)

    # Add legend
    ax.legend(loc="best", framealpha=0.9)

    # Set Y-axis to log scale if appropriate, but mixing ratio is already log10
    # We keep it linear as it represents log10 values directly.

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Plot saved to {output_path}")

def main() -> None:
    """Entry point for the script."""
    config = get_config()
    results_dir = Path(config["results_dir"])
    plots_dir = results_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    output_path = plots_dir / "noise_vs_signal.png"

    try:
        df = load_analysis_data()
        plot_instrumental_noise_vs_signal(df, output_path)
        logger.info("Task T029d completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during plot generation: {e}")
        raise

if __name__ == "__main__":
    main()
