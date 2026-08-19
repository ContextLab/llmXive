import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
import numpy as np

# Import from local utils to maintain project structure
try:
    from utils.config import get_pseudocount, get_processed_path, get_random_seed
    from utils.logging_config import get_logger, log_exclusion_count
except ImportError:
    # Fallback for direct execution or different import context
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.config import get_pseudocount, get_processed_path, get_random_seed
    from utils.logging_config import get_logger, log_exclusion_count

logger = get_logger(__name__)

# Constants
DEFAULT_PSEUDOCOUNT = 1e-6

def load_filtered_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the preprocessed dataset from the specified path.
    If no path is provided, uses the default processed path.
    """
    if filepath is None:
        filepath = get_processed_path("cleared_with_diversity.csv")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    logger.info(f"Loading filtered data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def identify_zero_variance_taxa(df: pd.DataFrame, taxon_columns: List[str]) -> List[str]:
    """
    Identify taxa columns that have zero variance (all values identical).
    """
    zero_var_taxa = []
    for col in taxon_columns:
        if col not in df.columns:
            continue
        if df[col].var() == 0:
            zero_var_taxa.append(col)
    return zero_var_taxa

def filter_zero_variance_taxa(df: pd.DataFrame, taxon_columns: List[str]) -> pd.DataFrame:
    """
    Filter out taxa columns with zero variance.
    """
    zero_var_taxa = identify_zero_variance_taxa(df, taxon_columns)
    if zero_var_taxa:
        logger.info(f"Removing {len(zero_var_taxa)} zero-variance taxa: {zero_var_taxa}")
        df = df.drop(columns=zero_var_taxa)
        # Update taxon_columns list to reflect changes
        taxon_columns = [c for c in taxon_columns if c not in zero_var_taxa]
    return df, taxon_columns

def apply_zero_variance_exclusion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply zero-variance exclusion to the dataframe.
    """
    # Identify taxon columns (assume columns starting with 'taxon_' or containing specific pattern)
    # For this implementation, we'll assume taxon columns are those not in a known exclusion list
    known_non_taxon_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 
                            'shannon_diversity', 'zero_variance_removed'}
    taxon_cols = [c for c in df.columns if c not in known_non_taxon_cols]
    
    df, taxon_cols = filter_zero_variance_taxa(df, taxon_cols)
    return df

def normalize_to_relative_abundance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize taxon abundances to relative abundance (sum to 1 per subject).
    """
    known_non_taxon_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 
                            'shannon_diversity', 'zero_variance_removed'}
    taxon_cols = [c for c in df.columns if c not in known_non_taxon_cols and c.endswith('_rel')]
    
    if not taxon_cols:
        # If no _rel columns exist, assume original taxon columns need normalization
        taxon_cols = [c for c in df.columns if c not in known_non_taxon_cols]
    
    if not taxon_cols:
        logger.warning("No taxon columns found for normalization")
        return df

    # Calculate sum per row
    row_sums = df[taxon_cols].sum(axis=1)
    
    # Avoid division by zero
    row_sums = row_sums.replace(0, np.nan)
    
    # Normalize
    for col in taxon_cols:
        df[f"{col}_rel"] = df[col] / row_sums
    
    logger.info(f"Normalized {len(taxon_cols)} taxa to relative abundance")
    return df

def calculate_shannon_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Shannon diversity index for each subject.
    Shannon index: -sum(p_i * ln(p_i)) where p_i is the relative abundance of taxon i.
    """
    known_non_taxon_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 
                            'shannon_diversity', 'zero_variance_removed'}
    taxon_cols = [c for c in df.columns if c not in known_non_taxon_cols and c.endswith('_rel')]
    
    if not taxon_cols:
        logger.warning("No relative abundance columns found for Shannon diversity calculation")
        return df

    # Calculate Shannon diversity
    def shannon_index(row):
        # Filter out zeros and NaNs
        abundances = row[taxon_cols].replace(0, np.nan).dropna()
        if len(abundances) == 0 or abundances.sum() == 0:
            return 0.0
        
        # Normalize to ensure sum is 1 (in case of floating point errors)
        p = abundances / abundances.sum()
        # Calculate Shannon index
        return -np.sum(p * np.log(p))
    
    df['shannon_diversity'] = df.apply(shannon_index, axis=1)
    logger.info("Calculated Shannon diversity index")
    return df

def handle_lod_titers(df: pd.DataFrame, lod: float = 0.5) -> pd.DataFrame:
    """
    Handle values below Limit of Detection (LOD) by imputing as a fraction of LOD.
    """
    # Log count of values below LOD
    below_lod_count = (df['titer_post'] < lod).sum()
    if below_lod_count > 0:
        logger.info(f"Found {below_lod_count} values below LOD ({lod}). Imputing as {lod/2}.")
        df.loc[df['titer_post'] < lod, 'titer_post'] = lod / 2
    return df

def apply_log_transform_titers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply log10 transformation to titer_post column.
    """
    if 'titer_post' not in df.columns:
        logger.warning("titer_post column not found, skipping log transform")
        return df
    
    df['log_titer'] = np.log10(df['titer_post'])
    logger.info("Applied log10 transformation to titer_post")
    return df

def apply_clr_transformation(df: pd.DataFrame, pseudocount: Optional[float] = None) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to taxon abundance columns.
    
    CLR transformation:
    1. Replace zeros with a small pseudocount
    2. Take natural log of each value
    3. Subtract the mean of the log-transformed values for each sample
    
    Args:
        df: DataFrame with taxon abundance columns
        pseudocount: Small value to replace zeros (default: 1e-6)
    
    Returns:
        DataFrame with CLR-transformed columns appended (e.g., 'taxon_A_clr')
    """
    if pseudocount is None:
        pseudocount = get_pseudocount()
    
    # Identify taxon columns (columns not in known non-taxa list and not ending with _clr or _rel)
    known_non_taxon_cols = {'subject_id', 'titer_baseline', 'titer_post', 'log_titer', 
                            'shannon_diversity', 'zero_variance_removed'}
    
    # Get all columns that are likely taxon abundances (not already processed)
    taxon_cols = [c for c in df.columns 
                 if c not in known_non_taxon_cols 
                 and not c.endswith('_clr') 
                 and not c.endswith('_rel')]
    
    if not taxon_cols:
        logger.warning("No taxon columns found for CLR transformation")
        return df

    logger.info(f"Applying CLR transformation to {len(taxon_cols)} taxa with pseudocount={pseudocount}")
    
    # Create a copy of the taxon columns to work with
    taxon_data = df[taxon_cols].copy()
    
    # Step 1: Replace zeros with pseudocount
    zero_count = (taxon_data == 0).sum().sum()
    if zero_count > 0:
        logger.info(f"Replacing {zero_count} zero values with pseudocount {pseudocount}")
        taxon_data = taxon_data.replace(0, pseudocount)
    
    # Step 2: Take natural log
    log_data = np.log(taxon_data)
    
    # Step 3: Calculate geometric mean (mean of logs) for each sample
    # This is the denominator in CLR
    geo_mean = log_data.mean(axis=1)
    
    # Step 4: Subtract geometric mean from each log value
    clr_data = log_data.sub(geo_mean, axis=0)
    
    # Append CLR-transformed columns to the original dataframe
    for col in taxon_cols:
        clr_col_name = f"{col}_clr"
        df[clr_col_name] = clr_data[col]
    
    logger.info(f"Added {len(taxon_cols)} CLR-transformed columns")
    return df

def run_normalization_pipeline(input_path: Optional[Path] = None, 
                             output_path: Optional[Path] = None,
                             pseudocount: Optional[float] = None) -> Path:
    """
    Run the complete preprocessing pipeline:
    1. Load data
    2. Apply zero-variance exclusion
    3. Normalize to relative abundance
    4. Calculate Shannon diversity
    5. Handle LOD titers
    6. Apply log transform to titers
    7. Apply CLR transformation
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output CSV file
        pseudocount: Pseudocount value for CLR transformation
    
    Returns:
        Path to the output file
    """
    # Load data
    df = load_filtered_data(input_path)
    
    # Apply zero-variance exclusion
    df = apply_zero_variance_exclusion(df)
    
    # Normalize to relative abundance
    df = normalize_to_relative_abundance(df)
    
    # Calculate Shannon diversity
    df = calculate_shannon_diversity(df)
    
    # Handle LOD titers
    df = handle_lod_titers(df)
    
    # Apply log transform to titers
    df = apply_log_transform_titers(df)
    
    # Apply CLR transformation
    df = apply_clr_transformation(df, pseudocount=pseudocount)
    
    # Determine output path
    if output_path is None:
        output_path = get_processed_path("cleared_with_diversity.csv")
    
    # Save the final dataset
    logger.info(f"Saving processed data to {output_path}")
    df.to_csv(output_path, index=False)
    
    logger.info(f"Preprocessing pipeline completed. Output: {output_path}")
    return output_path

def main():
    """
    Main entry point for the preprocessing script.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Run the normalization pipeline
        output_path = run_normalization_pipeline()
        print(f"Preprocessing completed successfully. Output saved to: {output_path}")
        
        # Verify output exists
        if os.path.exists(output_path):
            print(f"Output file size: {os.path.getsize(output_path)} bytes")
        else:
            raise RuntimeError(f"Output file was not created: {output_path}")
            
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
