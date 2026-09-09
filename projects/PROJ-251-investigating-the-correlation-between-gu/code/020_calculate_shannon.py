import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional

# Import from existing utils to maintain API surface
from utils.config import get_processed_path, get_random_seed, get_min_sample_size
from utils.logging_config import get_logger, log_error_context

# Ensure path is set correctly for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

def load_cleared_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleared dataset from the previous step (T011d).
    """
    if input_path is None:
        input_path = get_processed_path("cleared.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading cleared data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that represent taxa abundances.
    Assumes columns are named 'taxon_0', 'taxon_1', etc., or contain 'taxon' in name.
    Excludes metadata columns like 'subject_id', 'titer_baseline', 'titer_post'.
    """
    exclude_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer'}
    taxa_cols = [col for col in df.columns if col not in exclude_cols and 'taxon' in col.lower()]
    
    if not taxa_cols:
        # Fallback: assume all numeric columns except known metadata are taxa
        # This handles cases where column names might differ slightly
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        taxa_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    logger.info(f"Identified {len(taxa_cols)} taxa columns")
    return taxa_cols

def calculate_shannon_diversity(df: pd.DataFrame, taxa_cols: List[str]) -> pd.Series:
    """
    Calculate Shannon diversity index for each sample.
    Shannon Index H = -sum(p_i * ln(p_i))
    where p_i is the proportion of taxon i.
    """
    if len(taxa_cols) == 0:
        logger.warning("No taxa columns found, returning zeros")
        return pd.Series(0.0, index=df.index)

    # Extract taxa data
    taxa_data = df[taxa_cols].copy()
    
    # Handle negative or invalid values (should not happen in OTU tables, but be safe)
    taxa_data = taxa_data.clip(lower=0)
    
    # Calculate total abundance per sample
    total_abundance = taxa_data.sum(axis=1)
    
    # Avoid division by zero
    total_abundance = total_abundance.replace(0, np.nan)
    
    # Calculate proportions
    proportions = taxa_data.div(total_abundance, axis=0)
    
    # Calculate Shannon diversity: H = -sum(p * ln(p))
    # Use np.log for natural log
    # Replace 0 with NaN before log to avoid -inf, then fill with 0 after calculation
    with np.errstate(divide='ignore', invalid='ignore'):
        log_proportions = np.log(proportions)
        shannon = -(proportions * log_proportions).sum(axis=1)
    
    # Fill NaN (from 0*inf) with 0
    shannon = shannon.fillna(0)
    
    # Ensure non-negative (numerical errors can cause tiny negatives)
    shannon = shannon.clip(lower=0)
    
    logger.info(f"Calculated Shannon diversity for {len(shannon)} samples")
    logger.info(f"Shannon diversity stats: min={shannon.min():.4f}, max={shannon.max():.4f}, mean={shannon.mean():.4f}")
    
    return shannon

def write_updated_dataset(df: pd.DataFrame, shannon_series: pd.Series, output_path: Path) -> None:
    """
    Add Shannon diversity column to the dataframe and write to CSV.
    """
    # Create a copy to avoid modifying original
    df_out = df.copy()
    df_out['shannon_diversity'] = shannon_series.values
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_out.to_csv(output_path, index=False)
    logger.info(f"Wrote updated dataset with Shannon diversity to {output_path}")
    logger.info(f"Output shape: {df_out.shape}, columns: {list(df_out.columns)}")

def run_shannon_pipeline(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
    """
    Run the full Shannon diversity calculation pipeline.
    """
    if output_path is None:
        output_path = get_processed_path("cleared_shannon.csv")
    
    logger.info("Starting Shannon diversity calculation pipeline")
    
    # Step 1: Load data
    df = load_cleared_data(input_path)
    
    # Step 2: Identify taxa columns
    taxa_cols = identify_taxa_columns(df)
    
    # Step 3: Calculate Shannon diversity
    shannon_series = calculate_shannon_diversity(df, taxa_cols)
    
    # Step 4: Write updated dataset
    write_updated_dataset(df, shannon_series, output_path)
    
    logger.info("Shannon diversity calculation pipeline completed successfully")
    return output_path

def main():
    """
    Main entry point for the Shannon diversity calculation script.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Shannon diversity calculation (T020c)")
    
    try:
        output_path = run_shannon_pipeline()
        logger.info(f"Pipeline completed. Output written to: {output_path}")
        
        # Verify output exists and has correct structure
        if os.path.exists(output_path):
            df_verify = pd.read_csv(output_path)
            assert 'shannon_diversity' in df_verify.columns, "shannon_diversity column missing"
            assert len(df_verify) > 0, "Output file is empty"
            logger.info(f"Verification passed: {len(df_verify)} rows, columns: {list(df_verify.columns)}")
        else:
            raise FileNotFoundError(f"Output file not created: {output_path}")
            
    except Exception as e:
        log_error_context(logger, "Shannon diversity calculation failed", e)
        raise

if __name__ == "__main__":
    main()
