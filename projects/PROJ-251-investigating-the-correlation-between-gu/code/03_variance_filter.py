import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Import shared utilities from the project's utility modules
# These names are guaranteed to exist per the provided API surface
from utils.logging_config import get_logger
from utils.config import get_processed_path, get_results_path, get_random_seed

logger = get_logger(__name__)


class NoFeaturesError(Exception):
    """Raised when no taxa meet the variance threshold."""
    pass


def load_preprocessed_data() -> pd.DataFrame:
    """
    Loads the final preprocessed dataset containing CLR-transformed taxa.
    Expects the file at data/processed/cleared_final.csv
    """
    input_path = get_processed_path("cleared_final.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Preprocessed data not found at {input_path}. "
                                "Ensure T020a-3 (CLR Transformation) has completed successfully.")
    
    logger.info(f"Loading preprocessed data from {input_path}")
    df = pd.read_csv(input_path)
    return df


def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """
    Identifies columns corresponding to taxa.
    Based on the schema and pipeline, CLR columns typically end with '_clr' 
    or match the pattern of taxon names. We assume columns that are numeric
    and not 'subject_id', 'titer_*', 'log_titer', 'shannon_diversity' are taxa.
    """
    exclude_cols = {
        'subject_id', 
        'titer_baseline', 
        'titer_post', 
        'titer_pre_log', 
        'titer_post_log', 
        'log_titer', 
        'shannon_diversity',
        'responder_status'
    }
    
    taxa_cols = []
    for col in df.columns:
        if col not in exclude_cols:
            # Check if the column is numeric (expected for CLR values)
            if pd.api.types.is_numeric_dtype(df[col]):
                taxa_cols.append(col)
    
    logger.info(f"Identified {len(taxa_cols)} taxa columns for variance filtering.")
    return taxa_cols


def identify_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> List[str]:
    """
    Calculates variance for each taxon and identifies those with variance < threshold.
    """
    zero_var_taxa = []
    for col in taxa_cols:
        var_val = df[col].var()
        if var_val < threshold:
            zero_var_taxa.append(col)
    
    logger.info(f"Identified {len(zero_var_taxa)} taxa with variance < {threshold}.")
    return zero_var_taxa


def filter_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> List[str]:
    """
    Filters out taxa with variance < threshold.
    Returns the list of remaining taxa.
    """
    remaining_taxa = []
    for col in taxa_cols:
        var_val = df[col].var()
        if var_val >= threshold:
            remaining_taxa.append(col)
        else:
            logger.debug(f"Filtering out {col} (variance: {var_val})")
    
    logger.info(f"Variance filtering complete. Retained {len(remaining_taxa)} taxa.")
    return remaining_taxa


def save_results(filtered_taxa: List[str]) -> Dict[str, Any]:
    """
    Saves the list of variance-filtered taxa to a JSON file.
    Output: data/results/variance_filtered_taxa.json
    """
    output_dir = get_results_path()
    output_path = os.path.join(output_dir, "variance_filtered_taxa.json")
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    result_data = {
        "filtered_taxa": filtered_taxa,
        "count": len(filtered_taxa),
        "threshold": 1e-9
    }
    
    with open(output_path, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    logger.info(f"Saved variance filtered taxa list to {output_path}")
    return result_data


def run_variance_filter() -> List[str]:
    """
    Main orchestration function for the Global Unsupervised Variance Filter.
    """
    logger.info("Starting Global Unsupervised Variance Filter (T032a)")
    
    # 1. Load Data
    df = load_preprocessed_data()
    
    # 2. Identify Taxa
    taxa_cols = identify_taxa_columns(df)
    
    if not taxa_cols:
        logger.error("No taxa columns found in the dataset.")
        raise NoFeaturesError("NoFeaturesError: No taxa with variance > 1e-9 found.")
    
    # 3. Filter
    filtered_taxa = filter_zero_variance_taxa(df, taxa_cols, threshold=1e-9)
    
    # 4. Edge Case Check
    k_default = 10
    if len(filtered_taxa) < k_default:
        if len(filtered_taxa) == 0:
            logger.error("No taxa remaining after variance filtering.")
            raise NoFeaturesError("NoFeaturesError: No taxa with variance > 1e-9 found.")
        else:
            logger.warning(f"Only {len(filtered_taxa)} taxa remain after variance filtering (threshold {k_default} not met). "
                           "Proceeding with all available taxa as per specification.")
    
    # 5. Save Results
    save_results(filtered_taxa)
    
    logger.info("Variance filtering completed successfully.")
    return filtered_taxa


def main():
    """
    Entry point for the variance filter script.
    """
    try:
        run_variance_filter()
        logger.info("Task T032a completed successfully.")
    except NoFeaturesError as e:
        logger.error(str(e))
        # Write error log as per spec
        error_log_path = os.path.join(get_results_path(), "error_log.txt")
        os.makedirs(os.path.dirname(error_log_path), exist_ok=True)
        with open(error_log_path, 'a') as f:
            f.write(f"[T032a Error] {str(e)}\n")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error in T032a: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
