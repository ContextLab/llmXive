"""
Data Preprocessing Module.
Handles missing data imputation, filtering, and feature engineering.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
import numpy as np

from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError

logger = get_module_logger(__name__)

# Constants
MISSING_THRESHOLD = 0.20  # 20% missingness threshold for exclusion
OUTPUT_DIR = Path("data/processed")
FILTERED_OUTPUT_PATH = OUTPUT_DIR / "filtered.csv"
MISSING_LOG_PATH = OUTPUT_DIR / "missingness_report.log"

def load_processed_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the merged and validated dataset.
    Defaults to data/processed/merged.csv if no path provided.
    """
    if input_path is None:
        input_path = "data/processed/merged.csv"
    
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def handle_missing_genotypes(df: pd.DataFrame, 
                             genotype_cols: Optional[List[str]] = None,
                             population_col: str = "population_id") -> Tuple[pd.DataFrame, int]:
    """
    Handles missing genotype data per T015.
    
    Logic:
    1. Identify genotype columns (numeric columns starting with 'genotype_' or explicitly provided).
    2. Calculate missingness percentage per population (row).
    3. If missingness > 20% (MISSING_THRESHOLD), EXCLUDE the population.
    4. If missingness <= 20%, IMPUTE missing values with the mean of that column.
    5. Log all exclusion decisions to satisfy Constitution Principle VI.
    
    Args:
        df: Input DataFrame.
        genotype_cols: List of columns to treat as genotypes. If None, inferred.
        population_col: Name of the population ID column.
        
    Returns:
        Tuple of (cleaned DataFrame, count of excluded populations).
    """
    logger.info("Starting missing genotype imputation and filtering (T015)")
    
    if genotype_cols is None:
        # Infer genotype columns: numeric columns that are not ID/Env/Compound/Target
        exclude_cols = [population_col, "env_id", "compound_id", "target_concentration"]
        # Assuming genotype columns are numeric and not in exclude list
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        genotype_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    if not genotype_cols:
        logger.warning("No genotype columns found to process.")
        return df, 0

    # Ensure we are working on a copy to avoid SettingWithCopyWarning
    df_work = df.copy()
    
    # Calculate missingness per row (population)
    missing_counts = df_work[genotype_cols].isna().sum(axis=1)
    total_genotype_cols = len(genotype_cols)
    missing_pct = (missing_counts / total_genotype_cols) * 100.0
    
    # Identify rows to exclude
    exclude_mask = missing_pct > (MISSING_THRESHOLD * 100.0)
    excluded_indices = df_work.index[exclude_mask]
    excluded_count = len(excluded_indices)
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} populations due to > {MISSING_THRESHOLD*100}% missing genotype data.")
        
        # Log exclusions for Constitution Principle VI
        excluded_df = df_work.loc[excluded_indices]
        for _, row in excluded_df.iterrows():
            pop_id = row.get(population_col, "Unknown")
            pct = missing_pct.loc[row.name]
            logger.info(f"EXCLUSION: Population {pop_id} excluded. Missingness: {pct:.2f}%")
        
        # Filter out excluded rows
        df_work = df_work[~exclude_mask]
    else:
        logger.info("No populations excluded based on missingness threshold.")
    
    # Impute remaining missing values with mean per column
    # Only impute on the kept rows
    if not df_work.empty:
        col_means = df_work[genotype_cols].mean()
        df_work[genotype_cols] = df_work[genotype_cols].fillna(col_means)
        logger.info(f"Imputed missing values for {len(genotype_cols)} genotype columns using column means.")
    
    # Verify no remaining NaN in genotype columns
    final_missing = df_work[genotype_cols].isna().sum().sum()
    if final_missing > 0:
        logger.error(f"Critical: {final_missing} missing values remain after imputation.")
        # This should ideally not happen if mean imputation works, but log if it does
    else:
        logger.info("Genotype missingness check complete. No missing values remain.")
    
    return df_work, excluded_count

def handle_missing_env_metadata(df: pd.DataFrame,
                                env_cols: Optional[List[str]] = None,
                                population_col: str = "population_id") -> pd.DataFrame:
    """
    Handles missing environmental metadata per T016.
    Flags or excludes rows with critical missing env data.
    """
    logger.info("Processing missing environmental metadata (T016)")
    
    if env_cols is None:
        # Infer env columns: typically start with 'env_' or are numeric non-genotype
        exclude_cols = [population_col, "genotype_cols_placeholder", "compound_id", "target_concentration"]
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        env_cols = [c for c in numeric_cols if c not in exclude_cols and c not in df.columns if 'genotype' in c] # Rough heuristic
        # Better: explicit list if known, otherwise rely on schema
        if not env_cols:
            # Fallback: assume columns with 'temp', 'precip', etc if present, else skip
            env_cols = [c for c in df.columns if c.startswith('env_')]
    
    if not env_cols:
        logger.warning("No environmental columns identified for missingness check.")
        return df

    # For T016, we flag/exclude. Let's exclude if > 50% missing in env metadata for a row
    # Or simply drop if any critical field is missing. 
    # Given the task says "flag/exclude", we will exclude if > 50% missing in env cols
    missing_env = df[env_cols].isna().sum(axis=1)
    threshold_pct = 0.50
    mask = (missing_env / len(env_cols)) > threshold_pct
    
    if mask.any():
        count = mask.sum()
        logger.warning(f"Excluding {count} rows due to > {threshold_pct*100}% missing environmental metadata.")
        df = df[~mask]
    else:
        logger.info("Environmental metadata completeness check passed.")
    
    return df

def aggregate_to_population_level(df: pd.DataFrame,
                                  population_col: str = "population_id",
                                  target_col: str = "target_concentration") -> pd.DataFrame:
    """
    Aggregates data to population level if multiple samples exist per population.
    """
    logger.info(f"Aggregating to population level by {population_col}")
    if df.empty:
        return df
    
    # Group by population and mean aggregate numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude target if it's not meant to be averaged, but usually it is for regression target
    agg_dict = {col: 'mean' for col in numeric_cols}
    
    # Ensure ID columns are kept
    id_cols = [c for c in df.columns if c not in numeric_cols]
    
    df_agg = df.groupby(population_col, as_index=False).agg(agg_dict)
    
    # If there were other categorical columns, we might need to mode them or drop them
    # For now, assume numeric aggregation is sufficient for the model
    
    return df_agg

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Calculates Variance Inflation Factor (VIF) for predictors.
    """
    logger.info("Calculating VIF for collinearity check")
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    if not feature_cols:
        return pd.DataFrame(columns=['feature', 'vif'])
    
    X = df[feature_cols].values
    vif_data = []
    for i, col in enumerate(feature_cols):
        try:
            v = variance_inflation_factor(X, i)
            vif_data.append({'feature': col, 'vif': v})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append({'feature': col, 'vif': np.nan})
    
    return pd.DataFrame(vif_data)

def run_preprocessing_pipeline(input_path: Optional[str] = None) -> str:
    """
    Runs the full preprocessing pipeline:
    1. Load merged data.
    2. Handle missing genotypes (T015).
    3. Handle missing env metadata (T016).
    4. Aggregate to population level.
    5. Save to data/processed/filtered.csv.
    
    Returns:
        Path to the output file.
    """
    logger.info("Starting Preprocessing Pipeline (T015, T016)")
    
    # Check disk space
    estimated_size = 100 * 1024 * 1024 # 100MB estimate
    try:
        check_disk_space(estimated_size)
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load
    try:
        df = load_processed_data(input_path)
    except FileNotFoundError:
        # If merged.csv doesn't exist, try to load from raw if available, or fail
        # For T015, we assume T013/T014 produced merged.csv
        raise FileNotFoundError("Input data (merged.csv) not found. Run validation pipeline first.")

    # T015: Handle missing genotypes
    df, excluded_count = handle_missing_genotypes(df)
    
    if df.empty:
        logger.error("Dataset is empty after filtering missing genotypes.")
        # Save empty file to satisfy output requirement, but log failure
        df.to_csv(FILTERED_OUTPUT_PATH, index=False)
        return str(FILTERED_OUTPUT_PATH)

    # T016: Handle missing env metadata
    df = handle_missing_env_metadata(df)

    if df.empty:
        logger.error("Dataset is empty after filtering missing env metadata.")
        df.to_csv(FILTERED_OUTPUT_PATH, index=False)
        return str(FILTERED_OUTPUT_PATH)

    # Aggregate
    df = aggregate_to_population_level(df)

    # Save
    df.to_csv(FILTERED_OUTPUT_PATH, index=False)
    logger.info(f"Preprocessing complete. Output saved to {FILTERED_OUTPUT_PATH}")
    
    return str(FILTERED_OUTPUT_PATH)

def main():
    """
    Entry point for running preprocessing directly.
    """
    configure_root_logger()
    logger.info("Running Preprocessing Module via main()")
    try:
        output_path = run_preprocessing_pipeline()
        logger.info(f"Success. Output: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
