import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

from utils.logging_config import get_logger
from utils.config import get_processed_path, get_results_path

logger = get_logger(__name__)


class NoFeaturesError(Exception):
    """Raised when no taxa with variance > threshold are found."""
    pass


def load_preprocessed_data(file_path: str) -> pd.DataFrame:
    """Load the preprocessed CSV data."""
    logger.info(f"Loading preprocessed data from {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Preprocessed data file not found: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df


def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that represent taxa.
    Assumption: Taxa columns are those not in the standard metadata list
    and contain numeric data.
    """
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post', 'shannon_diversity', 'titer_pre_log', 'titer_post_log', 'log_titer']
    # Filter out metadata columns and non-numeric columns
    candidate_cols = [col for col in df.columns if col not in metadata_cols]
    taxa_cols = []
    for col in candidate_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            taxa_cols.append(col)
        else:
            logger.warning(f"Column {col} is not numeric, skipping.")
    
    # Specific check for CLR columns if they exist (e.g., ending in _clr or specific naming)
    # Based on T020a, CLR columns are added. If they are named explicitly, we should target them.
    # If the dataframe contains columns like 'taxon_0', 'taxon_1', or 'taxa_clr_...', we select them.
    # For robustness, we assume the numeric columns remaining after metadata removal are the taxa features.
    
    logger.info(f"Identified {len(taxa_cols)} taxa columns: {taxa_cols[:5]}...")
    return taxa_cols


def identify_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> List[str]:
    """
    Identify taxa columns with variance below the threshold.
    """
    zero_var_taxa = []
    for col in taxa_cols:
        var = df[col].var()
        if var < threshold:
            zero_var_taxa.append(col)
    return zero_var_taxa


def filter_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> List[str]:
    """
    Filter out taxa with variance < threshold.
    Returns the list of kept taxa columns.
    """
    zero_var_taxa = identify_zero_variance_taxa(df, taxa_cols, threshold)
    kept_taxa = [col for col in taxa_cols if col not in zero_var_taxa]
    
    logger.info(f"Zero variance taxa removed ({len(zero_var_taxa)}): {zero_var_taxa}")
    logger.info(f"Kept {len(kept_taxa)} taxa with variance > {threshold}")
    
    return kept_taxa


def save_results(kept_taxa: List[str], output_path: str):
    """Save the list of kept taxa to a JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w') as f:
        json.dump(kept_taxa, f, indent=2)
    logger.info(f"Saved variance filtered taxa list to {output_path}")


def run_variance_filter(threshold: float = 1e-9, k: int = 10):
    """
    Main entry point for the variance filter task.
    
    1. Load preprocessed data.
    2. Identify taxa columns.
    3. Filter out taxa with variance < threshold.
    4. Handle edge case: if fewer than k taxa remain, keep all available.
    5. If no taxa remain, raise NoFeaturesError.
    6. Save results to JSON.
    """
    processed_path = get_processed_path()
    results_path = get_results_path()
    
    input_file = os.path.join(processed_path, "cleared_final.csv")
    output_file = os.path.join(results_path, "variance_filtered_taxa.json")
    
    logger.info(f"Starting variance filter pipeline. Input: {input_file}")
    
    try:
        df = load_preprocessed_data(input_file)
        taxa_cols = identify_taxa_columns(df)
        
        if not taxa_cols:
            raise NoFeaturesError("NoFeaturesError: No taxa columns found in dataset.")
        
        kept_taxa = filter_zero_variance_taxa(df, taxa_cols, threshold)
        
        # Edge Case Handling
        if len(kept_taxa) == 0:
            raise NoFeaturesError("NoFeaturesError: No taxa with variance > 1e-9 found.")
        
        if len(kept_taxa) < k:
            logger.warning(f"Only {len(kept_taxa)} taxa remained after filtering (threshold {threshold}), which is less than k={k}. Keeping all available.")
            # kept_taxa is already the full list, so no change needed.
        
        save_results(kept_taxa, output_file)
        
        logger.info("Variance filter completed successfully.")
        return kept_taxa
        
    except NoFeaturesError as e:
        logger.error(str(e))
        # Log to error log file as requested
        error_log_path = os.path.join(results_path, "error_log.txt")
        with open(error_log_path, 'a') as err_file:
            err_file.write(f"{pd.Timestamp.now()}: {str(e)}\n")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during variance filter: {str(e)}", exc_info=True)
        raise


def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    try:
        run_variance_filter()
    except NoFeaturesError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
