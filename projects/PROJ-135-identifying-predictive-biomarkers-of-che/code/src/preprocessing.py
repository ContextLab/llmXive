import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import project config and utils
from src.config import ensure_directories
from src.utils import setup_logging, calculate_checksum

logger = logging.getLogger(__name__)

def load_processed_data(tumor_type: str, data_dir: Path) -> pd.DataFrame:
    """
    Load the harmonized and normalized data for a specific tumor type.
    Expects the file to be at data/processed/{tumor_type}_harmonized.csv
    """
    file_path = data_dir / "processed" / f"{tumor_type}_harmonized.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Harmonized data not found for {tumor_type} at {file_path}")
    
    logger.info(f"Loading harmonized data for {tumor_type} from {file_path}")
    # Assuming first column is gene symbol, rest are samples
    # Adjust index_col if the CSV structure differs
    df = pd.read_csv(file_path, index_col=0)
    return df

def filter_low_expression_genes(df: pd.DataFrame, cpm_threshold: float = 1.0, 
                                sample_fraction: float = 0.80) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter low-expression genes based on CPM (Counts Per Million).
    
    Criteria: Keep genes where CPM >= cpm_threshold in at least (1 - sample_fraction) of samples.
    i.e., Remove genes where CPM < cpm_threshold in > sample_fraction of samples.
    
    Args:
        df: DataFrame with genes as rows and samples as columns. Values are assumed to be raw counts 
            or already normalized counts. If raw counts, CPM calculation is applied.
            If the data is already CPM or log2-CPM, the logic adjusts accordingly.
            Based on T015 (Harmonization), we assume the input here is raw counts or library-size 
            normalized counts. We will calculate CPM from the raw counts.
        
        cpm_threshold: Minimum CPM value required (default 1.0).
        sample_fraction: Maximum fraction of samples allowed to be below threshold (default 0.80).
            Genes with CPM < threshold in > 80% of samples are removed.
            
    Returns:
        filtered_df: DataFrame with low-expression genes removed.
        stats: Dictionary with filtering statistics.
    """
    logger.info(f"Applying low-expression gene filter: CPM >= {cpm_threshold} in <= {1-sample_fraction:.0%} of samples")
    
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df, {"removed_count": 0, "remaining_count": 0}

    # Calculate library sizes (sum of counts per sample)
    # If the data is already CPM, we might skip this, but FR-004 implies CPM calculation.
    # Assuming input is raw counts for CPM calculation.
    # If the input is already normalized (e.g. log2), this logic needs adjustment.
    # Given T015 is "Harmonize IDs", and T017 is "Normalize to VST", 
    # T016 likely operates on the raw or library-normalized counts before VST.
    # We will assume the input is counts.
    
    library_sizes = df.sum(axis=0)
    # Avoid division by zero
    library_sizes = library_sizes.replace(0, 1e-6)
    
    # Calculate CPM: (count / library_size) * 1,000,000
    cpm_matrix = (df / library_sizes) * 1_000_000.0
    
    # Identify genes to keep
    # Condition: CPM >= threshold
    above_threshold = cpm_matrix >= cpm_threshold
    
    # Count how many samples meet the threshold for each gene
    count_above = above_threshold.sum(axis=1)
    
    # Calculate the fraction of samples above threshold
    fraction_above = count_above / df.shape[1]
    
    # Keep genes where fraction_above >= (1 - sample_fraction)
    # i.e., Remove if fraction_below > sample_fraction
    min_required_samples = (1 - sample_fraction) * df.shape[1]
    keep_mask = count_above >= min_required_samples
    
    stats = {
        "total_genes_initial": df.shape[0],
        "genes_removed": int((~keep_mask).sum()),
        "genes_remaining": int(keep_mask.sum()),
        "samples_total": df.shape[1],
        "threshold_cpm": cpm_threshold,
        "fraction_samples_below_threshold": sample_fraction
    }
    
    filtered_df = df[keep_mask]
    
    logger.info(f"Filtered {stats['genes_removed']} genes. Remaining: {stats['genes_remaining']}")
    
    return filtered_df, stats

def save_filtered_data(df: pd.DataFrame, tumor_type: str, data_dir: Path, stats: Dict[str, Any]) -> Path:
    """
    Save the filtered DataFrame to a CSV file and write filtering stats to JSON.
    """
    output_file = data_dir / "processed" / f"{tumor_type}_filtered.csv"
    logger.info(f"Saving filtered data to {output_file}")
    
    df.to_csv(output_file)
    
    # Save stats
    stats_file = data_dir / "processed" / f"{tumor_type}_filter_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
        
    return output_file

def process_tumor_type(tumor_type: str, data_dir: Path) -> bool:
    """
    Process a single tumor type: load, filter, and save.
    """
    try:
        df = load_processed_data(tumor_type, data_dir)
        filtered_df, stats = filter_low_expression_genes(df)
        save_filtered_data(filtered_df, tumor_type, data_dir, stats)
        return True
    except Exception as e:
        logger.error(f"Failed to process tumor type {tumor_type}: {e}")
        return False

def main():
    """
    Main entry point for the low-expression filtering step.
    Iterates over tumor types found in data/processed/ (harmonized files) and applies filtering.
    """
    setup_logging()
    data_dir = Path("data")
    ensure_directories()
    
    # Find all harmonized files
    processed_dir = data_dir / "processed"
    if not processed_dir.exists():
        logger.error("Data processed directory not found. Run data acquisition and harmonization first.")
        sys.exit(1)
    
    harmonized_files = list(processed_dir.glob("*_harmonized.csv"))
    
    if not harmonized_files:
        logger.warning("No harmonized files found in data/processed/. Nothing to filter.")
        sys.exit(0)
    
    logger.info(f"Found {len(harmonized_files)} harmonized files to process.")
    
    success_count = 0
    for file_path in harmonized_files:
        tumor_type = file_path.stem.replace("_harmonized", "")
        logger.info(f"Processing tumor type: {tumor_type}")
        if process_tumor_type(tumor_type, data_dir):
            success_count += 1
    
    logger.info(f"Filtering complete. Successfully processed {success_count}/{len(harmonized_files)} tumor types.")
    
    if success_count < len(harmonized_files):
        sys.exit(1)

if __name__ == "__main__":
    main()