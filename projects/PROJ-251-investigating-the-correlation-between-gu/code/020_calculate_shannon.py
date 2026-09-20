"""
Shannon Diversity Calculation Pipeline (Task T020c).

This module calculates the Shannon diversity index for each subject
based on normalized microbiome data and writes the results to a new CSV file.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from utils.config import get_processed_path, get_random_seed

logger = get_logger(__name__)


def load_cleared_data(input_path: Path) -> pd.DataFrame:
    """
    Load the normalized dataset from the previous step.

    Args:
        input_path: Path to the input CSV file (cleared_norm.csv).

    Returns:
        DataFrame containing the normalized data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading normalized data from {input_path}")
    df = pd.read_csv(input_path)

    if df.empty:
        raise ValueError("Input dataset is empty.")

    # Basic validation: ensure subject_id exists
    if 'subject_id' not in df.columns:
        raise ValueError("Input dataset must contain 'subject_id' column.")

    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df


def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns representing taxon abundances.

    Strategy: Exclude known non-taxon columns (subject_id, titer_*, shannon_*, log_*, clr_*).
    Assume any numeric column not in the exclusion list is a taxon.

    Args:
        df: The input DataFrame.

    Returns:
        List of column names representing taxa.
    """
    exclude_prefixes = ['subject_id', 'titer_', 'shannon_', 'log_', 'clr_', 'responder']
    taxa_cols = []

    for col in df.columns:
        if col == 'subject_id':
            continue
        if any(col.startswith(prefix) for prefix in exclude_prefixes):
            continue
        # Check if numeric (abundance data should be numeric)
        if pd.api.types.is_numeric_dtype(df[col]):
            taxa_cols.append(col)

    if not taxa_cols:
        raise ValueError("No taxon columns found in the dataset. "
                         "Please ensure normalized abundance columns exist.")

    logger.info(f"Identified {len(taxa_cols)} taxon columns: {taxa_cols[:5]}...")
    return taxa_cols


def calculate_shannon_diversity(df: pd.DataFrame, taxa_cols: List[str]) -> pd.Series:
    """
    Calculate Shannon diversity index (H') for each row.

    Formula: H' = - sum(p_i * ln(p_i))
    where p_i is the proportion of the i-th taxon.

    Args:
        df: DataFrame containing taxon abundances.
        taxa_cols: List of taxon column names.

    Returns:
        Series of Shannon diversity values indexed by row.
    """
    logger.info("Calculating Shannon diversity index...")

    # Extract taxon data
    taxon_data = df[taxa_cols].values

    # Ensure non-negative
    if np.any(taxon_data < 0):
        logger.warning("Negative values detected in taxon data. Clipping to 0.")
        taxon_data = np.clip(taxon_data, 0, None)

    # Calculate row sums to ensure relative abundance (though input should be normalized)
    row_sums = taxon_data.sum(axis=1)

    # Avoid division by zero
    row_sums[row_sums == 0] = 1.0

    # Calculate proportions
    proportions = taxon_data / row_sums[:, np.newaxis]

    # Calculate Shannon index: -sum(p * ln(p))
    # Handle log(0) -> 0 by masking
    with np.errstate(divide='ignore', invalid='ignore'):
        log_proportions = np.log(proportions)
        log_proportions[proportions == 0] = 0.0

    shannon_values = -np.sum(proportions * log_proportions, axis=1)

    return pd.Series(shannon_values, index=df.index, name='shannon_diversity')


def write_updated_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the DataFrame with the new Shannon diversity column to the output path.

    Args:
        df: The updated DataFrame.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing results to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Successfully wrote output file.")


def run_shannon_pipeline(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
    """
    Execute the full Shannon diversity calculation pipeline.

    1. Load normalized data.
    2. Identify taxon columns.
    3. Calculate Shannon index.
    4. Append to DataFrame.
    5. Write to new file.

    Args:
        input_path: Path to input CSV. Defaults to config path for cleared_norm.csv.
        output_path: Path to output CSV. Defaults to config path for cleared_shannon.csv.

    Returns:
        Path to the generated output file.
    """
    # Resolve paths
    if input_path is None:
        input_path = get_processed_path() / "cleared_norm.csv"
    if output_path is None:
        output_path = get_processed_path() / "cleared_shannon.csv"

    logger.info(f"Starting Shannon Diversity Pipeline. Input: {input_path}, Output: {output_path}")

    # 1. Load Data
    df = load_cleared_data(input_path)

    # 2. Identify Taxa
    taxa_cols = identify_taxa_columns(df)

    # 3. Calculate Shannon
    shannon_series = calculate_shannon_diversity(df, taxa_cols)

    # 4. Append Column
    df['shannon_diversity'] = shannon_series

    # 5. Write Output
    write_updated_dataset(df, output_path)

    # Verification
    logger.info("Verification: Checking output file...")
    if not output_path.exists():
        raise RuntimeError("Output file was not created.")

    df_out = pd.read_csv(output_path)
    assert 'shannon_diversity' in df_out.columns, "shannon_diversity column missing in output."
    assert len(df_out) == len(df), "Row count mismatch in output."

    logger.info(f"Pipeline completed successfully. Output: {output_path}")
    return output_path


def main():
    """Entry point for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        run_shannon_pipeline()
        logger.info("Task T020c completed successfully.")
    except Exception as e:
        logger.error(f"Task T020c failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()