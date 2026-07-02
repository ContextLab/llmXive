"""
Population Mean Calculator (Task T020)

Implements Constitution Principle VII and FR-010:
Compute the mean of the FULL UCI DATASET ARRAY for each variable
to serve as operational ground truth.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

from config import get_data_dir, get_output_dir
from data_loader import load_uci_dataset_raw, identify_continuous_variables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_cleaned_dataset(dataset_id: str, data_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load a cleaned dataset for a specific dataset_id.
    Uses the existing data_loader pipeline to ensure consistency.
    """
    try:
        # Load raw data
        raw_df = load_uci_dataset_raw(dataset_id, data_dir)
        if raw_df is None or raw_df.empty:
            logger.warning(f"Dataset {dataset_id} is empty or could not be loaded.")
            return None

        # Identify continuous variables
        continuous_vars = identify_continuous_variables(raw_df)
        if not continuous_vars:
            logger.warning(f"No continuous variables found in {dataset_id}.")
            return None

        # Filter for continuous variables only
        df_clean = raw_df[continuous_vars].copy()

        # Drop rows with missing values (as per data cleaner logic)
        df_clean = df_clean.dropna()

        if df_clean.empty:
            logger.warning(f"No valid rows remaining in {dataset_id} after cleaning.")
            return None

        return df_clean

    except Exception as e:
        logger.error(f"Error loading dataset {dataset_id}: {e}")
        return None


def calculate_population_means(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate the mean of the FULL DATASET ARRAY for each continuous variable.
    This serves as the operational ground truth (Constitution Principle VII).
    """
    means = {}
    for col in df.columns:
        if np.issubdtype(df[col].dtype, np.number):
            means[col] = float(df[col].mean())
        else:
            # Fallback for non-numeric columns that slipped through
            try:
                means[col] = float(df[col].mean())
            except (TypeError, ValueError):
                logger.warning(f"Skipping non-numeric column {col} in mean calculation.")
    return means


def save_population_means(means_by_dataset: Dict[str, Dict[str, float]], output_path: Path):
    """
    Save the population means to a JSON file.
    Structure: { "dataset_id": { "variable_name": mean_value, ... }, ... }
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(means_by_dataset, f, indent=2)
    logger.info(f"Population means saved to {output_path}")


def run_population_mean_calculation():
    """
    Main entry point for T020:
    Iterate over configured datasets, load them, compute full-array means,
    and save to data/processed/population_means.json.
    """
    data_dir = get_data_dir()
    processed_dir = get_data_dir().parent / "processed" # Usually data/processed
    # Ensure we use the project's standard processed directory
    if not processed_dir.exists():
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)

    output_file = processed_dir / "population_means.json"

    # List of datasets to process (defined in tasks.md T016)
    datasets = [
        "Wine",
        "Wine Quality Red",
        "Wine Quality White",
        "Ionosphere",
        "Heart Disease (Cleveland)"
    ]

    results = {}

    logger.info(f"Starting population mean calculation for {len(datasets)} datasets.")

    for dataset_id in datasets:
        logger.info(f"Processing dataset: {dataset_id}")
        df = load_cleaned_dataset(dataset_id, data_dir)

        if df is not None and not df.empty:
            means = calculate_population_means(df)
            results[dataset_id] = means
            logger.info(f"  Found {len(means)} continuous variables. Means computed.")
        else:
            logger.warning(f"Skipping {dataset_id} due to loading/cleaning issues.")

    if results:
        save_population_means(results, output_file)
        logger.info("Population mean calculation complete.")
    else:
        logger.error("No population means were calculated. No output file generated.")
        raise RuntimeError("Failed to calculate any population means.")


def main():
    run_population_mean_calculation()


if __name__ == "__main__":
    main()
