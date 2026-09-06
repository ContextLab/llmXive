"""
CLR Transformation Module (T020a).

Implements the Centered Log-Ratio (CLR) transformation for microbiome data.
Input: data/processed/cleared_shannon_log.csv
Output: data/processed/cleared_final.csv

Steps:
1. Load data.
2. Identify taxa columns.
3. Apply zero-replacement (pseudo-count).
4. Apply CLR transformation.
5. Write output.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Optional
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_pseudocount, get_random_seed, get_processed_path
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def load_cleared_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleared, Shannon-diversity, and log-transformed data.
    """
    if input_path is None:
        input_path = get_processed_path() / "cleared_shannon_log.csv"
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df

def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that represent taxa abundances.
    Heuristic: Columns that are NOT subject_id, titer_*, shannon_diversity, or log_titer.
    """
    exclude_cols = {
        'subject_id', 
        'titer_baseline', 'titer_post', 
        'shannon_diversity', 
        'titer_pre_log', 'titer_post_log',
        'log_titer'
    }
    
    taxa_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Additional check: ensure they are numeric (or can be cast to float)
    numeric_taxa = []
    for col in taxa_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_taxa.append(col)
        else:
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
                numeric_taxa.append(col)
            except (ValueError, TypeError):
                logger.warning(f"Column {col} is not numeric and cannot be cast. Skipping.")
    
    logger.info(f"Identified {len(numeric_taxa)} taxa columns: {numeric_taxa[:5]}...")
    return numeric_taxa

def apply_clr_transformation(df: pd.DataFrame, taxa_cols: List[str], pseudo_count: Optional[float] = None) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation.
    
    1. Zero Replacement: Add a small pseudo-count to all zeros in taxa columns.
    2. Log Transform: Take natural log of the values.
    3. Centering: Subtract the geometric mean (mean of logs) for each sample.
    
    Formula: clr(x_i) = ln(x_i) - mean(ln(x_j)) for j in taxa
    """
    if pseudo_count is None:
        pseudo_count = get_pseudocount()
    
    logger.info(f"Applying CLR transformation with pseudo-count: {pseudo_count}")
    
    df_transformed = df.copy()
    
    # Step 1: Zero replacement
    # We only replace zeros in the taxa columns
    for col in taxa_cols:
        # Ensure no negative values before log (though abundances should be >= 0)
        # Replace 0 with pseudo_count
        mask = df_transformed[col] == 0
        if mask.any():
            count = mask.sum()
            df_transformed.loc[mask, col] = pseudo_count
            logger.debug(f"Replaced {count} zeros in {col} with {pseudo_count}")
    
    # Step 2 & 3: Log transform and Center
    # Calculate log of taxa columns
    log_taxa = df_transformed[taxa_cols].apply(np.log)
    
    # Calculate the geometric mean (mean of logs) for each row
    # axis=1 means row-wise
    geo_mean_log = log_taxa.mean(axis=1)
    
    # Subtract row-wise mean from each log value
    clr_taxa = log_taxa.sub(geo_mean_log, axis=0)
    
    # Rename columns to indicate CLR transformation
    clr_col_names = [f"{col}_clr" for col in taxa_cols]
    clr_taxa.columns = clr_col_names
    
    # Append CLR columns to the dataframe
    # We keep original columns as well for traceability, or we could drop them.
    # Per spec: "Add columns `taxa_clr` (new columns for each taxon)."
    # We will add them alongside.
    df_transformed = pd.concat([df_transformed, clr_taxa], axis=1)
    
    logger.info(f"Added {len(clr_col_names)} CLR columns")
    return df_transformed

def write_updated_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Write the transformed dataset to CSV.
    """
    if output_path is None:
        output_path = get_processed_path() / "cleared_final.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing output to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Verify file size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Output file written: {size_mb:.2f} MB, {len(df)} rows")
    
    return output_path

def run_clr_pipeline(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
    """
    Run the full CLR pipeline.
    """
    try:
        # 1. Load
        df = load_cleared_data(input_path)
        
        # 2. Identify taxa
        taxa_cols = identify_taxa_columns(df)
        
        if not taxa_cols:
            raise ValueError("No taxa columns found for CLR transformation.")
        
        # 3. Transform
        df_clr = apply_clr_transformation(df, taxa_cols)
        
        # 4. Write
        out_path = write_updated_dataset(df_clr, output_path)
        
        return out_path
        
    except Exception as e:
        log_error_context(e)
        raise

def main():
    """
    Entry point for the script.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting CLR Transformation Pipeline (T020a)")
    
    try:
        output_path = run_clr_pipeline()
        logger.info(f"Pipeline completed successfully. Output: {output_path}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
