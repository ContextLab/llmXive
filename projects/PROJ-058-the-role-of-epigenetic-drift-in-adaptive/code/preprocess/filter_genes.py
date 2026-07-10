"""
Gene filtering module for T017.

Implements logic to exclude genes with:
1. Zero variance in both epigenetic (methylation) and expression (RNA-seq) layers.
2. Missing data in either layer (NaN or empty entries).

This module assumes inputs are pandas DataFrames where:
- Rows are genes (indexed by gene ID)
- Columns are samples
- Values are normalized variance metrics (from LOGO jackknife)
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from config import get_env

logger = logging.getLogger(__name__)

def load_variance_matrix(matrix_path: str) -> pd.DataFrame:
    """
    Load the unified variance matrix from CSV.
    
    Args:
        matrix_path: Path to the variance matrix CSV file.
        
    Returns:
        DataFrame with gene IDs as index and samples as columns.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    path = Path(matrix_path)
    if not path.exists():
        raise FileNotFoundError(f"Variance matrix not found: {matrix_path}")
    
    df = pd.read_csv(path, index_col=0)
    
    if df.empty:
        raise ValueError(f"Variance matrix at {matrix_path} is empty.")
    
    logger.info(f"Loaded variance matrix: {df.shape[0]} genes, {df.shape[1]} samples")
    return df

def filter_genes_by_variance_and_missing(
    rna_df: pd.DataFrame,
    methyl_df: pd.DataFrame,
    variance_threshold: float = 1e-6
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter genes based on variance and missing data criteria.
    
    A gene is excluded if:
    1. It has zero variance in BOTH RNA-seq and Methylation layers.
       (Zero variance is defined as < variance_threshold)
    2. It has any missing data (NaN) in either layer.
    
    Args:
        rna_df: DataFrame of RNA-seq variance (genes x samples).
        methyl_df: DataFrame of Methylation variance (genes x samples).
        variance_threshold: Minimum variance to be considered "non-zero".
        
    Returns:
        Tuple of (filtered_df, stats_dict):
            - filtered_df: The combined DataFrame with only valid genes.
            - stats_dict: Dictionary containing filtering statistics.
    """
    # Ensure indices align
    common_genes = rna_df.index.intersection(methyl_df.index)
    rna_df = rna_df.loc[common_genes]
    methyl_df = methyl_df.loc[common_genes]
    
    if common_genes.empty:
        logger.warning("No common genes found between RNA and Methylation data.")
        return pd.DataFrame(), {
            "total_input": 0,
            "kept": 0,
            "removed_zero_var_both": 0,
            "removed_missing": 0,
            "removed_no_overlap": 0
        }
    
    # Check for missing data in either layer
    rna_missing = rna_df.isna().any(axis=1)
    methyl_missing = methyl_df.isna().any(axis=1)
    any_missing = rna_missing | methyl_missing
    
    # Check for zero variance in both layers
    # A gene is kept if it has significant variance in AT LEAST ONE layer
    rna_zero = rna_df.abs().sum(axis=1) < variance_threshold
    methyl_zero = methyl_df.abs().sum(axis=1) < variance_threshold
    both_zero = rna_zero & methyl_zero
    
    # Determine which genes to keep
    # Keep if: NOT (both_zero) AND NOT (any_missing)
    keep_mask = ~(both_zero | any_missing)
    
    filtered_rna = rna_df[keep_mask]
    filtered_methyl = methyl_df[keep_mask]
    
    # Construct stats
    stats = {
        "total_input": len(common_genes),
        "removed_missing": int(any_missing.sum()),
        "removed_zero_var_both": int(both_zero.sum() & ~any_missing.sum()), # Only count zero-var if not already missing
        "kept": int(keep_mask.sum())
    }
    
    # Combine into a unified DataFrame for downstream use
    # We'll use a MultiIndex or just concatenate columns with prefixes
    # For simplicity in this task, we assume the downstream consumer knows the source
    # or we create a merged view. Let's return the filtered components separately
    # or a combined object. The task asks for filtering logic, usually resulting in
    # a clean matrix. Let's return the filtered DataFrames and the stats.
    
    logger.info(f"Filtering complete. Kept {stats['kept']} / {stats['total_input']} genes.")
    logger.info(f"  - Removed due to missing data: {stats['removed_missing']}")
    logger.info(f"  - Removed due to zero variance in both layers: {stats['removed_zero_var_both']}")
    
    return filtered_rna, filtered_methyl, stats

def save_filtered_data(
    rna_df: pd.DataFrame,
    methyl_df: pd.DataFrame,
    output_rna_path: str,
    output_methyl_path: str
) -> None:
    """
    Save the filtered data to CSV files.
    
    Args:
        rna_df: Filtered RNA-seq variance DataFrame.
        methyl_df: Filtered Methylation variance DataFrame.
        output_rna_path: Path to save RNA-seq data.
        output_methyl_path: Path to save Methylation data.
    """
    rna_df.to_csv(output_rna_path)
    methyl_df.to_csv(output_methyl_path)
    logger.info(f"Saved filtered RNA-seq data to {output_rna_path}")
    logger.info(f"Saved filtered Methylation data to {output_methyl_path}")

def main() -> None:
    """
    Main entry point for the filtering script.
    
    Reads preprocessed variance data (assumed to be generated by T016 logic),
    applies filtering, and writes the results to `data/processed/`.
    """
    # Paths derived from project structure
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_processed_dir = base_dir / "data" / "processed"
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Input paths (Assuming T016 outputs these intermediate files)
    # If T016 outputs a unified matrix, we would split it here.
    # For this task, we assume the existence of intermediate variance files
    # or we read from the unified matrix if it exists.
    # Let's assume the pipeline produces:
    # data/processed/rna_variances.csv
    # data/processed/methyl_variances.csv
    
    rna_input = data_processed_dir / "rna_variances.csv"
    methyl_input = data_processed_dir / "methyl_variances.csv"
    
    # If unified matrix exists, we might need to split it. 
    # But per T019, the unified matrix is the final output of the preprocessing phase.
    # T017 is an intermediate step. Let's assume T016 produces the per-layer variance files.
    
    if not rna_input.exists() or not methyl_input.exists():
        # Fallback: Try to read from a unified matrix if per-layer files are missing
        # This handles cases where the pipeline might have skipped intermediate saves
        unified_path = data_processed_dir / "variance_matrix.csv"
        if unified_path.exists():
            logger.warning("Per-layer variance files missing. Attempting to split unified matrix.")
            # This is a simplification; real implementation would need to know column structure
            raise NotImplementedError("Splitting unified matrix not implemented in this step. Please ensure T016 outputs per-layer files.")
        else:
            logger.error("Input variance files not found. Please ensure T016 has run successfully.")
            return

    try:
        rna_df = pd.read_csv(rna_input, index_col=0)
        methyl_df = pd.read_csv(methyl_input, index_col=0)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        return

    filtered_rna, filtered_methyl, stats = filter_genes_by_variance_and_missing(rna_df, methyl_df)
    
    if filtered_rna.empty:
        logger.warning("No genes passed the filtering criteria. Output files will be empty.")
    
    # Save results
    output_rna = data_processed_dir / "rna_variances_filtered.csv"
    output_methyl = data_processed_dir / "methyl_variances_filtered.csv"
    
    save_filtered_data(filtered_rna, filtered_methyl, output_rna, output_methyl)
    
    # Save stats
    import json
    stats_path = data_processed_dir / "filtering_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Filtering stats saved to {stats_path}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
