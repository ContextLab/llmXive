import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_lod_value, get_use_synthetic_data, get_min_sample_size
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)


class NoFeaturesError(Exception):
    """Raised when no taxa with variance > threshold are found."""
    pass


def load_preprocessed_data(input_path: str) -> pd.DataFrame:
    """
    Load the preprocessed dataset from the given path.
    
    Args:
        input_path: Path to the CSV file (cleared_final.csv)
        
    Returns:
        DataFrame containing the preprocessed data
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading preprocessed data from {input_path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df


def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that represent taxa abundances.
    
    Assumes taxa columns are numeric and not standard metadata columns.
    Standard metadata columns to exclude: subject_id, titer_baseline, titer_post,
    shannon_diversity, titer_pre_log, titer_post_log, log_titer.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of column names representing taxa
    """
    exclude_cols = {
        'subject_id', 'titer_baseline', 'titer_post', 
        'shannon_diversity', 'titer_pre_log', 'titer_post_log', 'log_titer'
    }
    
    taxa_cols = []
    for col in df.columns:
        if col not in exclude_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                taxa_cols.append(col)
            else:
                # Check if it can be converted to numeric
                try:
                    pd.to_numeric(df[col])
                    taxa_cols.append(col)
                except (ValueError, TypeError):
                    logger.debug(f"Skipping non-numeric column: {col}")
                    continue
    
    logger.info(f"Identified {len(taxa_cols)} taxa columns")
    return taxa_cols


def identify_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> List[str]:
    """
    Identify taxa with variance below the threshold.
    
    Args:
        df: Input DataFrame
        taxa_cols: List of taxa column names
        threshold: Variance threshold (default 1e-9)
        
    Returns:
        List of taxa column names with variance < threshold
    """
    zero_var_taxa = []
    for col in taxa_cols:
        var = df[col].var()
        if var < threshold:
            zero_var_taxa.append(col)
    
    logger.info(f"Found {len(zero_var_taxa)} taxa with variance < {threshold}")
    return zero_var_taxa


def filter_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9, min_taxa: int = 10) -> List[str]:
    """
    Filter out taxa with variance below the threshold.
    
    If the number of remaining taxa is less than min_taxa, keep all available taxa.
    If no taxa remain, raise NoFeaturesError.
    
    Args:
        df: Input DataFrame
        taxa_cols: List of taxa column names
        threshold: Variance threshold (default 1e-9)
        min_taxa: Minimum number of taxa to retain (default 10)
        
    Returns:
        List of filtered taxa column names
        
    Raises:
        NoFeaturesError: If no taxa with variance > threshold are found
    """
    zero_var_taxa = identify_zero_variance_taxa(df, taxa_cols, threshold)
    filtered_taxa = [col for col in taxa_cols if col not in zero_var_taxa]
    
    logger.info(f"Filtered out {len(zero_var_taxa)} zero-variance taxa")
    logger.info(f"Remaining taxa: {len(filtered_taxa)}")
    
    # Edge case: if filtered set has fewer than min_taxa, take all available
    if len(filtered_taxa) < min_taxa:
        logger.warning(f"Filtered set has {len(filtered_taxa)} taxa (< {min_taxa}), keeping all {len(taxa_cols)} available taxa")
        filtered_taxa = taxa_cols
    
    # Edge case: if no taxa remain, raise error
    if len(filtered_taxa) == 0:
        msg = "NoFeaturesError: No taxa with variance > 1e-9 found."
        logger.error(msg)
        raise NoFeaturesError(msg)
    
    return filtered_taxa


def save_results(filtered_taxa: List[str], output_path: str) -> None:
    """
    Save the filtered taxa list to a JSON file.
    
    Args:
        filtered_taxa: List of filtered taxa column names
        output_path: Path to output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "filtered_taxa": filtered_taxa,
        "count": len(filtered_taxa),
        "threshold": 1e-9
    }
    
    with open(path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved {len(filtered_taxa)} filtered taxa to {output_path}")


def run_variance_filter(input_path: str, output_path: str, threshold: float = 1e-9, min_taxa: int = 10) -> List[str]:
    """
    Main function to run the variance filter pipeline.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output JSON file
        threshold: Variance threshold (default 1e-9)
        min_taxa: Minimum number of taxa to retain (default 10)
        
    Returns:
        List of filtered taxa column names
    """
    logger.info("Starting variance filter pipeline")
    
    # Load data
    df = load_preprocessed_data(input_path)
    
    # Identify taxa columns
    taxa_cols = identify_taxa_columns(df)
    
    # Filter zero-variance taxa
    filtered_taxa = filter_zero_variance_taxa(df, taxa_cols, threshold, min_taxa)
    
    # Save results
    save_results(filtered_taxa, output_path)
    
    logger.info("Variance filter pipeline completed successfully")
    return filtered_taxa


def main():
    """Main entry point for the variance filter script."""
    # Define paths
    input_file = "data/processed/cleared_final.csv"
    output_file = "data/results/variance_filtered_taxa.json"
    
    # Check if input file exists
    if not Path(input_file).exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        filtered_taxa = run_variance_filter(input_file, output_file)
        logger.info(f"Successfully filtered to {len(filtered_taxa)} taxa")
    except NoFeaturesError as e:
        logger.error(str(e))
        # Log to error_log.txt as per task requirements
        error_log_path = Path("data/results/error_log.txt")
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log_path, 'a') as f:
            f.write(f"{datetime.now()}: {str(e)}\n")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        log_error_context(e)
        sys.exit(1)


if __name__ == "__main__":
    main()