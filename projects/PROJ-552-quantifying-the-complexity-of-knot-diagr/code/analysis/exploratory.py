"""
Exploratory analysis module for the knot complexity project.

This script generates a scatter plot of crossing number vs. braid index,
stratified by alternating vs. non‑alternating classification.  The plot is
saved to ``data/plots/crossing_vs_braid.png`` with a resolution of
1200×900 pixels.

If the cleaned dataset ``data/processed/knots_cleaned.csv`` does not
exist, the script will automatically download the raw Knot Atlas data,
parse it, and write the cleaned CSV before creating the plot.  This makes
the script robust when run as part of the end‑to‑end quickstart pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Reproducibility utilities
from reproducibility.logs import get_logger, log_operation

# Down‑stream pipeline utilities
from download.knot_atlas_loader import download_knot_atlas_data
from data.parser import parse_knot_atlas_data, ParsedKnotData

# Constants for file locations
RAW_JSON_PATH = Path("data/raw/knot_atlas_raw.json")
CLEANED_CSV_PATH = Path("data/processed/knots_cleaned.csv")
PLOT_PATH = Path("data/plots/crossing_vs_braid.png")

def _ensure_directories() -> None:
    """Create any missing parent directories for output files."""
    for p in (RAW_JSON_PATH, CLEANED_CSV_PATH, PLOT_PATH):
        p.parent.mkdir(parents=True, exist_ok=True)

def load_cleaned_knots(data_path: Path = CLEANED_CSV_PATH) -> pd.DataFrame:
    """
    Load the cleaned knot dataset.

    If the file does not exist, the function will:
    1. Download the raw Knot Atlas JSON.
    2. Parse the raw records into :class:`ParsedKnotData`.
    3. Write the parsed records to ``data/processed/knots_cleaned.csv``.
    4. Return the resulting DataFrame.

    Parameters
    ----------
    data_path: Path
        Path to the cleaned CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: ``crossing_number``, ``braid_index``,
        ``hyperbolic_volume``, ``classification``.
    """
    logger = get_logger()

    if data_path.is_file():
        logger.info(f"Loading existing cleaned dataset from {data_path}")
        return pd.read_csv(data_path)

    logger.info(
        f"Cleaned dataset not found at {data_path}. Initiating download & parsing."
    )
    _ensure_directories()

    # ------------------------------------------------------------------
    # Step 1: Download raw JSON
    # ------------------------------------------------------------------
    raw_data = download_knot_atlas_data()
    # Some downloaders return a list of dicts; ensure JSON serialisable.
    with RAW_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Step 2: Parse raw records
    # ------------------------------------------------------------------
    parsed_records: List[ParsedKnotData] = parse_knot_atlas_data(raw_data)

    # ------------------------------------------------------------------
    # Step 3: Convert to DataFrame and write CSV
    # ------------------------------------------------------------------
    df = pd.DataFrame([r.__dict__ for r in parsed_records])
    # Normalise column names to match downstream expectations
    df.rename(
        columns={
            "crossing_number": "crossing_number",
            "braid_index": "braid_index",
            "hyperbolic_volume": "hyperbolic_volume",
            "classification": "classification",
        },
        inplace=True,
    )
    df.to_csv(data_path, index=False)
    logger.info(f"Cleaned dataset written to {data_path}")

    return df

def create_stratified_scatter_plot(
    df: pd.DataFrame,
    output_path: Path = PLOT_PATH,
) -> None:
    """
    Create and save a scatter plot of crossing number vs. braid index,
    coloured by alternating / non‑alternating classification.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame containing at least ``crossing_number``, ``braid_index``,
        and ``classification`` columns.
    output_path: Path
        Destination file for the PNG plot.
    """
    logger = get_logger()
    logger.info("Generating stratified scatter plot.")

    # Validate required columns
    required = {"crossing_number", "braid_index", "classification"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    # Set up the plot aesthetics
    plt.figure(figsize=(12, 9))  # 1200×900 at 100 dpi
    sns.scatterplot(
        data=df,
        x="crossing_number",
        y="braid_index",
        hue="classification",
        palette="deep",
        alpha=0.7,
        edgecolor="w",
        linewidth=0.5,
    )
    plt.title("Crossing Number vs. Braid Index (stratified by classification)")
    plt.xlabel("Crossing Number")
    plt.ylabel("Braid Index")
    plt.legend(title="Classification", loc="best")
    plt.tight_layout()

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=100)
    plt.close()
    logger.info(f"Scatter plot saved to {output_path}")

def generate_exploratory_plots() -> None:
    """
    High‑level entry point used by the quickstart pipeline.

    Loads (or creates) the cleaned knot dataset and produces the required
    crossing‑vs‑braid scatter plot.
    """
    logger = get_logger()
    logger.info("Starting exploratory analysis pipeline.")

    # Load or create the cleaned dataset
    df = load_cleaned_knots()

    # Create the stratified scatter plot
    create_stratified_scatter_plot(df)

    logger.info("Exploratory analysis completed successfully.")

def main() -> None:
    """
    Command‑line entry point.
    """
    # Use the generic ``log_operation`` decorator pattern employed
    # throughout the code base.
    log_operation(
        operation="exploratory_analysis",
        input_file=str(RAW_JSON_PATH) if RAW_JSON_PATH.is_file() else None,
        output_file=str(PLOT_PATH),
    )
    generate_exploratory_plots()


if __name__ == "__main__":
    main()