"""
Normalization and Imputation Pipeline for Plant Stress Proteomics.

This module implements:
1. Filtering of low-abundance proteins (detection rate < 50%).
2. Left-Censored Missing (LCM) imputation using the `imp3` library (MinProb algorithm).

Dependencies:
- pandas
- imp3 (MinProb algorithm)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, List

import pandas as pd
import numpy as np

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger, log_warning
from utils.data_utils import load_csv, save_csv
from utils.config import DATA_RAW_PATH, DATA_PROCESSED_PATH

# Initialize logger
logger = get_logger(__name__)

# Constants
DETECTION_THRESHOLD = 0.50  # 50% detection required

def calculate_detection_rate(df: pd.DataFrame, protein_cols: List[str]) -> pd.Series:
    """
    Calculate the detection rate for each protein column.
    Detection is defined as non-NaN values.

    Args:
        df: Input DataFrame.
        protein_cols: List of column names representing proteins.

    Returns:
        Series of detection rates (0.0 to 1.0) for each protein.
    """
    if not protein_cols:
        return pd.Series(dtype=float)

    # Count non-null values per column
    counts = df[protein_cols].notna().sum()
    total_rows = len(df)

    if total_rows == 0:
        return pd.Series(0.0, index=protein_cols)

    return counts / total_rows

def filter_low_abundance_proteins(
    df: pd.DataFrame,
    protein_cols: List[str],
    threshold: float = DETECTION_THRESHOLD
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out proteins with detection rates below the threshold.

    Args:
        df: Input DataFrame.
        protein_cols: List of protein column names.
        threshold: Minimum detection rate (default 0.50).

    Returns:
        Tuple of (Filtered DataFrame, List of retained protein columns).
    """
    logger.info(f"Filtering proteins with detection rate < {threshold:.1%}")
    
    if protein_cols is None or len(protein_cols) == 0:
        logger.warning("No protein columns provided for filtering.")
        return df, []

    rates = calculate_detection_rate(df, protein_cols)
    retained_cols = rates[rates >= threshold].index.tolist()
    dropped_cols = rates[rates < threshold].index.tolist()

    logger.info(f"Retained {len(retained_cols)} proteins, dropped {len(dropped_cols)} low-abundance proteins.")
    
    if dropped_cols:
        log_warning(f"Dropped low-abundance proteins: {', '.join(dropped_cols[:5])}{'...' if len(dropped_cols) > 5 else ''}")

    # Construct result DataFrame keeping non-protein columns + retained proteins
    non_protein_cols = [c for c in df.columns if c not in protein_cols]
    result_cols = non_protein_cols + retained_cols
    
    return df[result_cols], retained_cols

def apply_lcm_imputation(
    df: pd.DataFrame,
    protein_cols: List[str],
    method: str = "minprob"
) -> pd.DataFrame:
    """
    Apply Left-Censored Missing (LCM) imputation using the imp3 library.
    
    This uses the MinProb algorithm which assumes missing values are 
    left-censored (below detection limit) and imputes them based on 
    the distribution of observed values.

    Args:
        df: Input DataFrame.
        protein_cols: List of protein column names to impute.
        method: Imputation method (default "minprob").

    Returns:
        DataFrame with imputed values.
    
    Raises:
        ImportError: If imp3 is not installed.
        RuntimeError: If imp3 imputation fails.
    """
    logger.info(f"Applying LCM imputation ({method}) to {len(protein_cols)} proteins...")

    try:
        import imp3
    except ImportError:
        logger.error("The 'imp3' library is required for LCM imputation but is not installed.")
        logger.error("Please install it via: pip install imp3")
        raise ImportError("Missing required dependency: imp3")

    # Ensure we only pass numeric columns with NaNs to the imputer
    # imp3 expects a DataFrame or array-like with missing values
    subset_df = df[protein_cols].copy()
    
    # Check if there are any missing values to impute
    if subset_df.isna().sum().sum() == 0:
        logger.info("No missing values found in protein columns. Skipping imputation.")
        return df

    try:
        # imp3.MinProb is the specific class for MinProb algorithm
        # We initialize the imputer with the method
        imputer = imp3.MinProb()
        
        # Fit and transform
        # Note: imp3 API typically expects a 2D array-like. 
        # We convert to numpy, impute, and convert back to ensure dtype preservation if needed.
        # However, imp3 usually works directly with DataFrames in recent versions.
        # Let's try DataFrame first, fallback to numpy if needed.
        
        imputed_values = imputer.fit_transform(subset_df)
        
        # Verify result shape
        if imputed_values.shape != subset_df.shape:
            raise ValueError(f"Shape mismatch after imputation: {imputed_values.shape} vs {subset_df.shape}")
        
        # Convert back to DataFrame to preserve indices and column names
        imputed_df = pd.DataFrame(imputed_values, index=subset_df.index, columns=subset_df.columns)
        
        # Replace the columns in the original dataframe
        df_imputed = df.copy()
        df_imputed[protein_cols] = imputed_df

        # Verify no NaNs remain in protein columns
        remaining_nans = df_imputed[protein_cols].isna().sum().sum()
        if remaining_nans > 0:
            logger.warning(f"Imputation left {remaining_nans} NaN values. Check data types or imp3 version.")
        else:
            logger.info("Imputation complete. No NaNs remaining in protein columns.")

        return df_imputed

    except Exception as e:
        logger.error(f"Failed to perform LCM imputation: {e}")
        raise RuntimeError(f"LCM Imputation failed: {e}") from e

def run_normalization_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    protein_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Orchestrates the full normalization pipeline:
    1. Load data.
    2. Filter low-abundance proteins.
    3. Apply LCM imputation.
    4. Save results.

    Args:
        input_path: Path to input CSV. Defaults to `data/processed/merged_data.csv`.
        output_path: Path to output CSV. Defaults to `data/processed/normalized_data.csv`.
        protein_columns: List of protein columns. If None, assumes all numeric cols 
                         (excluding metadata) are proteins.

    Returns:
        The processed DataFrame.
    """
    # Determine paths
    if input_path is None:
        input_path = DATA_RAW_PATH / "merged_data.csv"
    if output_path is None:
        output_path = DATA_PROCESSED_PATH / "normalized_data.csv"

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading data from {input_path}")
    df = load_csv(input_path)
    
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")

    # Identify protein columns if not provided
    if protein_columns is None:
        # Heuristic: Assume columns starting with 'P_' or containing numeric data are proteins
        # For this specific task, we assume the data structure has a clear distinction.
        # If the merged data has a 'ProteinID' column, we might need to handle that.
        # Let's assume all numeric columns that are not sample metadata are proteins.
        # A safer bet for this specific pipeline is to assume the caller knows or we 
        # select numeric columns that have missing values.
        
        # Fallback: Select all numeric columns except common metadata names
        metadata_exclude = {'SampleID', 'Condition', 'Species', 'Stress', 'Replicate', 'ProteinID', 'GeneID'}
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        protein_columns = [c for c in numeric_cols if c not in metadata_exclude]
        
        if not protein_columns:
            log_warning("No protein columns identified automatically. Exiting.")
            raise ValueError("Could not identify protein columns. Please specify 'protein_columns'.")
        
        logger.info(f"Automatically identified {len(protein_columns)} protein columns")

    # Step 1: Filter Low Abundance
    df_filtered, retained_proteins = filter_low_abundance_proteins(df, protein_columns)

    if len(retained_proteins) == 0:
        log_warning("No proteins retained after filtering. Pipeline cannot continue.")
        raise ValueError("No proteins retained after low-abundance filtering.")

    # Step 2: LCM Imputation
    df_imputed = apply_lcm_imputation(df_filtered, retained_proteins)

    # Step 3: Save
    logger.info(f"Saving normalized data to {output_path}")
    save_csv(df_imputed, output_path)

    logger.info("Normalization pipeline completed successfully.")
    return df_imputed

def main():
    """
    Entry point for running the normalization script directly.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        run_normalization_pipeline()
        print("Success: Normalization complete.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()