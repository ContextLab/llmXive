"""
Task T020a: CLR Transformation for Microbiome Data.

This script applies a Centered Log-Ratio (CLR) transformation to the microbiome
abundance data in the pre-processed dataset. It handles zero abundances by adding
a small pseudo-count before transformation.

Input: data/processed/cleared_with_diversity.csv (output of T021)
Output: data/processed/cleared_with_diversity.csv (updated with taxa_clr columns)
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np

# Add project root to path to allow imports from code.utils
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_pseudocount, get_processed_path, get_results_path, get_use_synthetic_data
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def load_cleared_data(input_path: Path) -> pd.DataFrame:
    """Load the dataset from the previous step."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns from {input_path}")
    return df

def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify columns that represent taxon abundances.
    We assume these are numeric columns that are NOT the standard metadata columns.
    """
    exclude_cols = {
        'subject_id', 'titer_baseline', 'titer_post', 
        'shannon_diversity', 'titer_pre_log', 'titer_post_log', 'log_titer'
    }
    
    taxa_cols = []
    for col in df.columns:
        if col in exclude_cols:
            continue
        if col.startswith('taxa_') and col != 'taxa_clr':
            # Check if it's numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                taxa_cols.append(col)
        elif col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col]):
            # Fallback: assume any other numeric column is a taxon
            # This might need adjustment based on actual column naming conventions
            taxa_cols.append(col)
    
    if not taxa_cols:
        logger.warning("No taxa columns identified. Checking for columns starting with 'taxa_'...")
        # Explicit search for taxa columns
        for col in df.columns:
            if col.startswith('taxa_') and col != 'taxa_clr' and pd.api.types.is_numeric_dtype(df[col]):
                taxa_cols.append(col)
    
    logger.info(f"Identified {len(taxa_cols)} taxa columns: {taxa_cols[:5]}...")
    return taxa_cols

def apply_clr_transformation(df: pd.DataFrame, taxa_cols: List[str], pseudocount: float = 1e-6) -> pd.DataFrame:
    """
    Apply CLR transformation to the specified taxa columns.
    
    Steps:
    1. Replace zeros with pseudocount
    2. Calculate geometric mean for each row (subject)
    3. Compute log(x / geometric_mean) for each taxon
    
    The result is stored in a new column 'taxa_clr' as a JSON string or list.
    """
    logger.info(f"Applying CLR transformation with pseudocount={pseudocount}")
    
    # Create a copy to avoid modifying the original
    df_transformed = df.copy()
    
    # Extract taxa data
    taxa_data = df_transformed[taxa_cols].values.astype(float)
    
    # Step 1: Handle zeros by adding pseudocount
    zero_mask = taxa_data == 0
    taxa_data[zero_mask] = pseudocount
    
    # Step 2: Calculate geometric mean for each row
    # Geometric mean = exp(mean(log(x)))
    log_data = np.log(taxa_data)
    log_mean = np.mean(log_data, axis=1, keepdims=True)
    
    # Step 3: Compute CLR = log(x) - mean(log(x))
    clr_data = log_data - log_mean
    
    # Store results as a list in a new column
    # We'll store it as a JSON string to keep the CSV format clean
    clr_list = [list(row) for row in clr_data]
    df_transformed['taxa_clr'] = clr_list
    
    logger.info(f"CLR transformation complete. Added 'taxa_clr' column with {len(clr_list)} entries.")
    
    return df_transformed

def write_updated_dataset(df: pd.DataFrame, output_path: Path):
    """Write the updated dataset to CSV."""
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Updated dataset written to {output_path}")

def run_clr_pipeline(input_path: Optional[Path] = None, output_path: Optional[Path] = None):
    """Run the full CLR transformation pipeline."""
    logger.info("Starting CLR transformation pipeline (Task T020a)")
    
    # Determine paths
    if input_path is None:
        input_path = get_processed_path() / "cleared_with_diversity.csv"
    if output_path is None:
        output_path = get_processed_path() / "cleared_with_diversity.csv"
    
    try:
        # Load data
        df = load_cleared_data(input_path)
        
        # Identify taxa columns
        taxa_cols = identify_taxa_columns(df)
        if not taxa_cols:
            raise ValueError("No taxa columns found in the dataset. Cannot perform CLR transformation.")
        
        # Get pseudocount from config
        pseudocount = get_pseudocount()
        
        # Apply CLR transformation
        df_transformed = apply_clr_transformation(df, taxa_cols, pseudocount)
        
        # Write updated dataset
        write_updated_dataset(df_transformed, output_path)
        
        # Log success
        logger.info("CLR transformation pipeline completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"CLR transformation pipeline failed: {str(e)}", exc_info=True)
        with log_error_context("CLR Transformation Failed"):
            raise

def main():
    """Main entry point for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = run_clr_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
