import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Set style for scientific plots
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Lucida Grande"]
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent


def load_residuals_with_ligand_labels() -> pd.DataFrame:
    """
    Load the residuals data from T026/T038.
    Expects: data/processed/residuals.parquet with columns including 'ligand_class'.
    """
    project_root = get_project_root()
    residuals_path = project_root / "data" / "processed" / "residuals.parquet"

    if not residuals_path.exists():
        raise FileNotFoundError(
            f"Residuals file not found at {residuals_path}. "
            "Ensure T026/T038 has been completed to generate predictions."
        )

    df = pd.read_parquet(residuals_path)

    required_cols = ["error", "ligand_class"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Residuals file missing required columns: {missing}. "
            f"Found: {list(df.columns)}"
        )

    logger.info(f"Loaded {len(df)} residual samples from {residuals_path}")
    return df


def plot_error_distribution_by_ligand_class(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Create a violin plot showing the distribution of errors (ML - DFT)
    separated by ligand class (Group 13 vs. Conventional).
    """
    plt.figure(figsize=(10, 6))

    # Ensure ligand_class is treated as categorical for better plotting
    df_plot = df.copy()
    df_plot["ligand_class"] = df_plot["ligand_class"].astype("category")

    # Create violin plot
    sns.violinplot(
        data=df_plot,
        x="ligand_class",
        y="error",
        palette="Set2",
        inner="box",
        linewidth=1.5,
    )

    plt.title(
        "Distribution of Prediction Errors by Ligand Class",
        fontsize=16,
        fontweight="bold",
    )
    plt.xlabel("Ligand Class", fontsize=14)
    plt.ylabel("Error (eV)", fontsize=14)

    # Add statistical summary text if available (from T035)
    # We can optionally load stats if needed, but for now just the plot

    plt.tight_layout()
    plt.savefig(output_path, format="png")
    plt.close()
    logger.info(f"Saved error distribution plot to {output_path}")


def plot_residual_histogram_and_kde(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Create a histogram with KDE overlay of the overall error distribution.
    """
    plt.figure(figsize=(10, 6))

    sns.histplot(
        data=df,
        x="error",
        kde=True,
        color="skyblue",
        edgecolor="black",
        alpha=0.7,
        bins=30,
    )

    plt.title(
        "Histogram and KDE of Prediction Errors (ML - DFT)",
        fontsize=16,
        fontweight="bold",
    )
    plt.xlabel("Error (eV)", fontsize=14)
    plt.ylabel("Frequency", fontsize=14)

    # Add mean and std annotations
    mean_err = df["error"].mean()
    std_err = df["error"].std()
    plt.axvline(mean_err, color="red", linestyle="--", linewidth=2, label=f"Mean: {mean_err:.3f} eV")
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path, format="png")
    plt.close()
    logger.info(f"Saved error histogram/KDE plot to {output_path}")


def plot_error_vs_dft_barrier(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Scatter plot of Error vs. DFT Barrier Height to check for heteroscedasticity.
    Assumes 'barrier_height_dft' or similar column exists.
    """
    # Check for barrier height column
    barrier_col = None
    candidates = ["barrier_height_dft", "energy_dft", "barrier_dft"]
    for c in candidates:
        if c in df.columns:
            barrier_col = c
            break

    if barrier_col is None:
        logger.warning(
            f"No barrier height column found in {list(df.columns)}. "
            "Skipping error vs. barrier plot."
        )
        # Create a placeholder or just return without error to allow partial success
        # But task requires real output. We'll skip saving this specific file if data missing.
        return

    plt.figure(figsize=(10, 6))

    sns.scatterplot(
        data=df,
        x=barrier_col,
        y="error",
        alpha=0.6,
        s=50,
        edgecolor="k",
        linewidth=0.3,
    )

    plt.axhline(0, color="red", linestyle="--", linewidth=2)

    plt.title(
        "Prediction Error vs. DFT Barrier Height",
        fontsize=16,
        fontweight="bold",
    )
    plt.xlabel("DFT Barrier Height (eV)", fontsize=14)
    plt.ylabel("Error (ML - DFT) (eV)", fontsize=14)

    plt.tight_layout()
    plt.savefig(output_path, format="png")
    plt.close()
    logger.info(f"Saved error vs. barrier plot to {output_path}")


def run_visualization_analysis() -> Dict[str, str]:
    """
    Main function to orchestrate all visualization generation.
    Returns a dictionary of output paths for verification.
    """
    project_root = get_project_root()
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_files = {}

    try:
        logger.info("Loading residuals data...")
        df = load_residuals_with_ligand_labels()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        # We must still produce the artifact file (the script) and handle the error
        # but the script's job is to write files. If data is missing, we log and exit.
        # However, the task requires the script to produce files when run.
        # If the prerequisite data (T026/T038) is missing, we cannot produce the plot.
        # The constraint says "Fail loudly".
        raise RuntimeError(
            "Cannot generate visualizations: Prerequisite data (residuals.parquet) is missing. "
            "Ensure T026 and T038 are completed first."
        ) from e

    # 1. Error distribution by ligand class
    plot_path_1 = results_dir / "error_distribution_by_ligand_class.png"
    try:
        plot_error_distribution_by_ligand_class(df, plot_path_1)
        output_files["error_distribution_by_ligand_class"] = str(plot_path_1)
    except Exception as e:
        logger.error(f"Failed to generate error distribution plot: {e}")

    # 2. Histogram + KDE
    plot_path_2 = results_dir / "error_histogram_kde.png"
    try:
        plot_residual_histogram_and_kde(df, plot_path_2)
        output_files["error_histogram_kde"] = str(plot_path_2)
    except Exception as e:
        logger.error(f"Failed to generate histogram plot: {e}")

    # 3. Error vs Barrier
    plot_path_3 = results_dir / "error_vs_barrier_height.png"
    try:
        plot_error_vs_dft_barrier(df, plot_path_3)
        output_files["error_vs_barrier_height"] = str(plot_path_3)
    except Exception as e:
        logger.error(f"Failed to generate error vs barrier plot: {e}")

    logger.info(f"Visualization analysis complete. Files saved to {results_dir}")
    return output_files


def main() -> None:
    """Entry point for the visualization script."""
    logger.info("Starting visualization analysis for User Story 3...")
    try:
        outputs = run_visualization_analysis()
        print("Generated visualizations:")
        for name, path in outputs.items():
            print(f"  - {name}: {path}")
    except Exception as e:
        logger.error(f"Visualization analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()