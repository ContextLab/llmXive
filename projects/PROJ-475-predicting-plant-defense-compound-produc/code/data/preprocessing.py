"""
Data Preprocessing Module.
Handles missing data imputation, exclusion, and feature engineering.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import pandas as pd
import numpy as np

# Import logging utilities
from utils.logging import get_module_logger

# Import config for paths
from config import get_config

logger = get_module_logger(__name__)

# Constants
MISSING_THRESHOLD = 0.20  # 20% missingness threshold for exclusion

def load_processed_data() -> pd.DataFrame:
    """
    Loads the merged and validated data from the previous stage.
    Expects data/raw/merged_validation.csv or similar intermediate.
    For T015, we assume the output of T013/T014 (validation) is available.
    Since T014 produces a retention report, the actual merged data is likely
    in a temporary location or needs to be re-merged from raw sources if not saved.
    
    However, per T013/T014 descriptions, the pipeline should produce a merged dataset.
    We will attempt to load `data/processed/merged.csv` (standard intermediate)
    or fall back to re-merging raw JSONs if that file is missing (robustness).
    """
    config = get_config()
    processed_dir = Path(config['paths']['processed'])
    merged_path = processed_dir / 'merged.csv'
    
    if merged_path.exists():
        logger.info(f"Loading merged data from {merged_path}")
        return pd.read_csv(merged_path)
    
    # Fallback: Re-merge from raw JSONs if intermediate is missing
    # This handles the case where the pipeline was restarted without the intermediate file.
    logger.warning(f"Merged data not found at {merged_path}. Attempting to re-merge from raw JSONs.")
    raw_dir = Path(config['paths']['raw'])
    
    try:
        genomic = pd.read_json(raw_dir / 'genomic_vcf.json')
        env = pd.read_json(raw_dir / 'env_data.json')
        compound = pd.read_json(raw_dir / 'compound_data.json')
        
        # Perform a simplified merge based on IDs present in all
        # Assuming columns: population_id, env_id, compound_id, and data columns
        # We perform an inner join on all key IDs to ensure completeness
        merged = genomic.merge(env, on=['population_id', 'env_id'], how='inner')
        merged = merged.merge(compound, on=['population_id', 'compound_id'], how='inner')
        
        # Save the re-merged file for subsequent runs
        processed_dir.mkdir(parents=True, exist_ok=True)
        merged.to_csv(merged_path, index=False)
        logger.info(f"Re-merged data saved to {merged_path}")
        return merged
    except FileNotFoundError as e:
        logger.error(f"Raw data files missing, cannot re-merge: {e}")
        raise

def handle_missing_genotypes(df: pd.DataFrame, genotype_cols: Optional[List[str]] = None) -> Tuple[pd.DataFrame, int]:
    """
    Handles missing genotype data per T015.
    
    Logic:
    1. Per-population check: Calculate missingness percentage for genotype columns.
    2. If missingness > 20% for a population, EXCLUDE the row (population).
    3. For remaining populations, impute missing values with the mean of the column.
    4. Log all exclusion decisions to satisfy Constitution Principle VI.
    
    Args:
        df: Input DataFrame.
        genotype_cols: List of columns representing genotypes. If None, attempts to infer.
        
    Returns:
        Tuple of (processed DataFrame, count of excluded populations)
    """
    if genotype_cols is None:
        # Heuristic: columns that are numeric and not ID columns
        # Assuming ID columns are string/object or specific names
        id_cols = ['population_id', 'env_id', 'compound_id', 'source_study']
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        genotype_cols = [c for c in numeric_cols if c not in id_cols]
        
    if not genotype_cols:
        logger.warning("No genotype columns found to process.")
        return df, 0

    excluded_count = 0
    excluded_populations = []
    
    # Identify the population identifier column
    pop_id_col = 'population_id' if 'population_id' in df.columns else df.columns[0]

    logger.info(f"Processing missing genotypes for columns: {genotype_cols}")
    logger.info(f"Missingness threshold: {MISSING_THRESHOLD * 100}%")

    # Calculate missingness per population
    missing_counts = df[genotype_cols].isna().sum(axis=1)
    total_genotype_cols = len(genotype_cols)
    missing_pct = missing_counts / total_genotype_cols

    # Identify populations to exclude
    mask_exclude = missing_pct > MISSING_THRESHOLD
    mask_keep = ~mask_exclude

    excluded_populations = df.loc[mask_exclude, pop_id_col].tolist()
    excluded_count = len(excluded_populations)

    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} populations due to missingness > {MISSING_THRESHOLD * 100}%")
        for pop in excluded_populations:
            logger.info(f"Excluded population: {pop} (Missingness: {missing_pct[df[pop_id_col] == pop].values[0]:.2%})")
    
    # Filter DataFrame
    df_filtered = df[mask_keep].copy()
    
    if df_filtered.empty:
        logger.error("All populations excluded due to missingness. Cannot proceed.")
        raise ValueError("No data remaining after missingness filtering.")

    # Impute remaining missing values with mean per column
    logger.info(f"Imputing missing values in {len(genotype_cols)} columns with column means.")
    
    # Calculate means only on non-null values
    means = df_filtered[genotype_cols].mean()
    df_filtered[genotype_cols] = df_filtered[genotype_cols].fillna(means)
    
    # Verify no NaNs remain in genotype columns
    if df_filtered[genotype_cols].isna().any().any():
        logger.warning("Some missing values remain after imputation (possibly non-numeric).")
    else:
        logger.info("Imputation complete. No missing values in genotype columns.")

    return df_filtered, excluded_count

def handle_missing_env_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handles missing environmental metadata per T016.
    Flags or excludes rows with missing critical env metadata.
    """
    # Identify env columns (heuristic: columns with 'env' or 'temp', 'precip' etc.)
    # For now, we assume all non-genotype, non-compound, non-ID columns are env
    # A more robust implementation would use schema info.
    id_cols = ['population_id', 'env_id', 'compound_id', 'source_study']
    # Assuming genotype_cols were already handled, remaining numeric might be env
    # This is a simplified placeholder for T016 logic as T015 is the focus.
    # In a real scenario, we'd have a specific list.
    return df

def aggregate_to_population_level(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates data to population level if necessary.
    """
    return df

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.Series:
    """
    Calculates Variance Inflation Factor for features.
    """
    from utils.stats import calculate_vif
    return calculate_vif(df, feature_cols)

def run_preprocessing_pipeline(input_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Runs the full preprocessing pipeline for T015.
    1. Loads data.
    2. Handles missing genotypes (impute or exclude).
    3. Saves result to data/processed/filtered.csv.
    """
    logger.info("Starting preprocessing pipeline (T015).")
    
    if input_df is None:
        df = load_processed_data()
    else:
        df = input_df
    
    logger.info(f"Loaded {len(df)} rows for preprocessing.")
    
    # Handle missing genotypes
    df_processed, excluded_count = handle_missing_genotypes(df)
    
    logger.info(f"Processed {len(df_processed)} rows after filtering {excluded_count} populations.")
    
    # Ensure output directory exists
    config = get_config()
    processed_dir = Path(config['paths']['processed'])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = processed_dir / 'filtered.csv'
    df_processed.to_csv(output_path, index=False)
    
    logger.info(f"Filtered data saved to {output_path}")
    
    return df_processed

def main():
    """
    Entry point for running the preprocessing pipeline standalone.
    """
    from utils.logging import configure_root_logger
    configure_root_logger()
    
    try:
        result = run_preprocessing_pipeline()
        logger.info(f"Preprocessing complete. Output: {len(result)} rows.")
        return 0
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
