import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from config import get_config
from utils import setup_logging

logger = logging.getLogger(__name__)

def load_analysis_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load metadata and retrieval results, merging them for plotting.
    Returns:
        metadata_df: DataFrame with temperature, metallicity, SNR, Resolution
        retrieval_df: DataFrame with water abundance, uncertainty, censorship flags
    """
    config = get_config()
    metadata_path = Path(config["data"]["processed"]) / "metadata.csv"
    retrieval_path = Path(config["data"]["processed"]) / "retrieval_results.csv"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    if not retrieval_path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {retrieval_path}")

    metadata_df = pd.read_csv(metadata_path)
    retrieval_df = pd.read_csv(retrieval_path)

    # Merge on planet name or ID
    merge_key = "planet_name" if "planet_name" in metadata_df.columns else "planet_id"
    if merge_key not in retrieval_df.columns:
        merge_key = "planet_id" if "planet_id" in retrieval_df.columns else None

    if merge_key is None:
        raise ValueError("Could not find a common key to merge metadata and retrieval results.")

    merged_df = pd.merge(metadata_df, retrieval_df, on=merge_key, how="inner")
    logger.info(f"Merged {len(merged_df)} records for plotting.")
    return metadata_df, retrieval_df, merged_df

def plot_water_vs_temperature(
    df: pd.DataFrame,
    output_path: Path,
    x_col: str = "equilibrium_temperature_k",
    y_col: str = "log10_water_mixing_ratio",
    err_col: str = "log10_water_std",
    censor_col: str = "is_censored"
) -> None:
    """
    Generate a scatter plot of Water Abundance vs. Temperature.
    Includes error bars for detected values and arrows for upper limits (censored).
    """
    if not df.empty:
        plt.figure(figsize=(10, 6))
        ax = plt.gca()

        # Separate detected and censored
        detected = df[df[censor_col] == False] if censor_col in df.columns else df
        censored = df[df[censor_col] == True] if censor_col in df.columns else pd.DataFrame()

        # Plot detected values with error bars
        if not detected.empty:
            ax.errorbar(
                detected[x_col],
                detected[y_col],
                yerr=detected[err_col] if err_col in detected.columns else 0,
                fmt='o',
                color='blue',
                label='Detected',
                ecolor='blue',
                capsize=3,
                alpha=0.7
            )

        # Plot censored values (upper limits) as arrows pointing down
        if not censored.empty:
            for _, row in censored.iterrows():
                ax.annotate(
                    '',
                    xy=(row[x_col], row[y_col]),
                    xytext=(row[x_col], row[y_col] - 1.0), # Approximate arrow length
                    arrowprops=dict(arrowstyle='->', color='red', lw=1.5)
                )
                # Add a small horizontal bar at the limit
                ax.plot([row[x_col] - 50, row[x_col] + 50], [row[y_col], row[y_col]], color='red', lw=1.5)

        ax.set_xlabel("Equilibrium Temperature (K)")
        ax.set_ylabel("log10(H2O Mixing Ratio)")
        ax.set_title("Exoplanet Water Abundance vs. Equilibrium Temperature")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Saved water vs temperature plot to {output_path}")
    else:
        logger.warning("No data available to plot water vs temperature.")

def plot_residuals(
    df: pd.DataFrame,
    output_path: Path,
    y_col: str = "log10_water_mixing_ratio",
    pred_col: str = "predicted_log10_water"
) -> None:
    """
    Generate a residuals plot (Residuals vs Predicted) for the Tobit model.
    """
    if y_col in df.columns and pred_col in df.columns:
        df["residuals"] = df[y_col] - df[pred_col]

        plt.figure(figsize=(10, 6))
        ax = plt.gca()

        # Plot residuals
        ax.scatter(df[pred_col], df["residuals"], color='green', alpha=0.6, edgecolors='black')

        # Add zero line
        ax.axhline(0, color='red', linestyle='--', lw=1)

        ax.set_xlabel("Predicted log10(H2O Mixing Ratio)")
        ax.set_ylabel("Residuals")
        ax.set_title("Tobit Model Residuals")
        ax.grid(True, linestyle='--', alpha=0.6)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Saved residuals plot to {output_path}")
    else:
        logger.warning(f"Columns '{y_col}' or '{pred_col}' not found for residual plot.")

def plot_correlation_matrix(
    df: pd.DataFrame,
    output_path: Path,
    cols: Optional[List[str]] = None
) -> None:
    """
    Generate a correlation matrix heatmap for key variables.
    """
    if cols is None:
        cols = ["equilibrium_temperature_k", "host_star_metallicity", "log10_water_mixing_ratio", "mass_jupiter"]
        # Filter to only available columns
        cols = [c for c in cols if c in df.columns]

    if len(cols) < 2:
        logger.warning("Not enough columns available for correlation matrix.")
        return

    corr_matrix = df[cols].corr()

    plt.figure(figsize=(8, 6))
    ax = plt.gca()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt=".2f", ax=ax)
    ax.set_title("Correlation Matrix of Key Variables")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved correlation matrix plot to {output_path}")

def main():
    """
    Main entry point to generate all diagnostic plots.
    """
    setup_logging()
    config = get_config()
    results_plots_dir = Path(config["results"]["plots"])
    results_plots_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load data
        # Note: We expect metadata and retrieval results to be present from previous steps
        metadata_df, retrieval_df, merged_df = load_analysis_data()

        # 1. Water vs Temperature
        plot_water_vs_temperature(
            merged_df,
            results_plots_dir / "water_abundance_vs_temperature.png"
        )

        # 2. Residuals (if prediction column exists, e.g., from T027/T028)
        if "predicted_log10_water" in merged_df.columns:
            plot_residuals(
                merged_df,
                results_plots_dir / "residuals_vs_predicted.png"
            )
        else:
            logger.info("Skipping residuals plot: 'predicted_log10_water' column not found.")

        # 3. Correlation Matrix
        plot_correlation_matrix(
            merged_df,
            results_plots_dir / "correlation_matrix.png"
        )

        logger.info("All diagnostic plots generated successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data files missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        raise

if __name__ == "__main__":
    main()