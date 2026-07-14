"""
Diversity Analysis Module.

Calculates alpha diversity metrics (Shannon Index) from raw taxa abundance counts.
Implements Spec Override T045: Uses RAW counts, NOT CLR-transformed data.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional, List

# Import from project API surface
from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end

# scikit-bio is listed in requirements.txt (T002)
import skbio

logger = get_logger(__name__)

def calculate_shannon_index(taxa_matrix: pd.DataFrame, sample_column: str = 'participant_id') -> pd.DataFrame:
    """
    Calculate Shannon Index (alpha diversity) from a wide-format taxa matrix.

    IMPORTANT: This function expects RAW counts as input.
    Per Spec Override T045 (replacing FR-003), we do NOT apply CLR transformation
    before calculating alpha diversity. CLR is only applied to taxa for regression
    (Secondary Path), not for diversity metrics.

    Args:
        taxa_matrix (pd.DataFrame): Wide-format DataFrame where rows are samples
            (participants) and columns are taxa (species/genera). The first column
            should be the sample identifier.
        sample_column (str): Name of the column containing sample IDs.

    Returns:
        pd.DataFrame: Original taxa matrix with an additional 'shannon_index' column.
    """
    logger.info("Starting Shannon Index calculation from raw counts.")
    
    # Validate input
    if taxa_matrix.empty:
        log_warning("Empty taxa matrix provided to Shannon calculation.")
        return taxa_matrix

    # Ensure we are working with numeric data for taxa columns
    # Identify taxa columns (all except the sample ID column)
    taxa_cols = [col for col in taxa_matrix.columns if col != sample_column]
    
    if not taxa_cols:
        log_warning("No taxa columns found in the matrix.")
        return taxa_matrix

    # Extract the taxa data
    taxa_data = taxa_matrix[taxa_cols].copy()

    # Ensure numeric types and handle non-positive values
    # Shannon index requires counts >= 0. Negative values are invalid.
    # Zero counts are allowed (log(0) is handled by scikit-bio or we filter).
    # scikit-bio's diversity.alpha.shannon handles zeros correctly.
    
    # Convert to float to ensure compatibility
    taxa_data = taxa_data.apply(pd.to_numeric, errors='coerce').fillna(0)

    # Calculate Shannon Index using scikit-bio
    # Input: 2D array where rows are samples, columns are OTUs/Taxa
    try:
        shannon_values = skbio.diversity.alpha.shannon(taxa_data.values)
    except Exception as e:
        logger.error(f"Error calculating Shannon index: {e}")
        raise

    # Create result DataFrame
    result = taxa_matrix.copy()
    result['shannon_index'] = shannon_values

    logger.info(f"Calculated Shannon Index for {len(result)} samples.")
    return result

def run_diversity_pipeline(input_path: Optional[str] = None, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Orchestrate the diversity calculation pipeline.

    Args:
        input_path (str, optional): Path to the cleaned taxa data CSV.
            Defaults to 'data/processed/cleaned_data.csv'.
        output_path (str, optional): Path to save the results.
            Defaults to 'data/processed/diversity_metrics.csv'.

    Returns:
        pd.DataFrame: The dataframe with the added shannon_index column.
    """
    if input_path is None:
        input_path = INPUT_PATHS.get('cleaned_data', 'data/processed/cleaned_data.csv')
    
    if output_path is None:
        output_path = 'data/processed/diversity_metrics.csv'

    log_pipeline_start("Diversity Analysis Pipeline")
    log_provenance("Task", "T020")
    log_provenance("Method", "Shannon Index (Raw Counts)")

    ensure_directories()

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # Check for necessary columns (participant_id is required for merging later)
    if 'participant_id' not in df.columns:
        # Try to infer if the first column is the ID
        logger.warning("'participant_id' column not found. Assuming first column is ID.")
        # We need a column to identify samples. If the file has a generic index column,
        # we might need to handle it, but per T011, we expect 'participant_id'.
        # For safety, if the first column is numeric or looks like an ID, we use it.
        # However, strict adherence to T011 implies 'participant_id' exists.
        raise ValueError("Input data must contain 'participant_id' column.")

    # Calculate Shannon Index
    df_with_diversity = calculate_shannon_index(df, sample_column='participant_id')

    # Log summary statistics
    shannon_mean = df_with_diversity['shannon_index'].mean()
    shannon_std = df_with_diversity['shannon_index'].std()
    logger.info(f"Shannon Index - Mean: {shannon_mean:.4f}, Std: {shannon_std:.4f}")

    # Save results
    ensure_directories()
    df_with_diversity.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

    log_pipeline_end("Diversity Analysis Pipeline")

    return df_with_diversity

if __name__ == "__main__":
    run_diversity_pipeline()
