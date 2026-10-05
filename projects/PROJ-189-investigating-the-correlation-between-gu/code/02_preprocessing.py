import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# Import from sibling utilities
from utils.logging import get_logger, log_memory_usage, check_memory_limit
from utils.resource_guard import enforce_resource_limits, ResourceLimitExceededError

# Configure logger
logger = get_logger(__name__)

# Constants
MIN_RAREFACTION_DEPTH = 5000  # Default minimum depth, will be adjusted based on data
OUTPUT_DIR = Path("data/processed")
MERGED_DATA_PATH = OUTPUT_DIR / "merged_dataset.parquet"
RAREFIED_OUTPUT_PATH = OUTPUT_DIR / "rarefied_genus_table.parquet"
RAREFACTION_LOG_PATH = OUTPUT_DIR / "rarefaction_log.json"

def load_merged_data() -> pd.DataFrame:
    """Load the merged dataset from the preprocessing pipeline."""
    if not MERGED_DATA_PATH.exists():
        raise FileNotFoundError(f"Merged data file not found at {MERGED_DATA_PATH}. "
                                "Run data ingestion pipeline first.")
    logger.info(f"Loading merged data from {MERGED_DATA_PATH}")
    df = pd.read_parquet(MERGED_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    return df

def filter_by_age(df: pd.DataFrame, min_age: int = 60) -> pd.DataFrame:
    """Filter samples to include only participants aged >= min_age."""
    logger.info(f"Filtering for age >= {min_age}")
    initial_count = len(df)
    df_filtered = df[df['age'] >= min_age].copy()
    filtered_count = len(df_filtered)
    logger.info(f"Filtered from {initial_count} to {filtered_count} rows based on age")
    return df_filtered

def impute_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing values in covariates (BMI, education) using median/mode."""
    logger.info("Imputing missing covariates")
    df_imputed = df.copy()
    
    # Impute BMI with median
    if 'bmi' in df_imputed.columns:
        bmi_median = df_imputed['bmi'].median()
        df_imputed['bmi'] = df_imputed['bmi'].fillna(bmi_median)
        logger.info(f"Imputed BMI missing values with median: {bmi_median}")
    
    # Impute education with mode
    if 'education' in df_imputed.columns:
        education_mode = df_imputed['education'].mode()[0]
        df_imputed['education'] = df_imputed['education'].fillna(education_mode)
        logger.info(f"Imputed education missing values with mode: {education_mode}")
    
    return df_imputed

def validate_covariate_imputation(df: pd.DataFrame) -> bool:
    """Validate that covariates have no missing values after imputation."""
    missing_covariates = []
    if 'bmi' in df.columns and df['bmi'].isnull().any():
        missing_covariates.append('bmi')
    if 'education' in df.columns and df['education'].isnull().any():
        missing_covariates.append('education')
    
    if missing_covariates:
        logger.error(f"Covariates with missing values after imputation: {missing_covariates}")
        return False
    logger.info("All covariates successfully imputed")
    return True

def validate_null_values(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """Validate that required columns have no null values."""
    missing_required = []
    for col in required_columns:
        if col not in df.columns:
            missing_required.append(f"{col} (missing column)")
        elif df[col].isnull().any():
            missing_required.append(f"{col} ({df[col].isnull().sum()} nulls)")
    
    if missing_required:
        logger.error(f"Required columns with missing values: {missing_required}")
        return False
    logger.info("All required columns validated successfully")
    return True

def rarefy_samples(abundance_df: pd.DataFrame, target_depth: int) -> pd.DataFrame:
    """
    Perform rarefaction (subsampling without replacement) to a uniform sequencing depth.
    
    Args:
        abundance_df: DataFrame with sample IDs as index and taxon counts as columns.
        target_depth: The uniform depth to rarefy all samples to.
        
    Returns:
        Rarefied DataFrame with same shape, counts subsampled.
    """
    logger.info(f"Starting rarefaction to depth {target_depth}")
    
    # Filter out samples with total reads < target_depth
    sample_sums = abundance_df.sum(axis=1)
    retained_samples = sample_sums[sample_sums >= target_depth].index.tolist()
    dropped_samples = sample_sums[sample_sums < target_depth].index.tolist()
    
    logger.info(f"Retained {len(retained_samples)} samples, dropped {len(dropped_samples)} samples "
                f"with depth < {target_depth}")
    
    if len(retained_samples) == 0:
        raise ValueError(f"No samples have sequencing depth >= {target_depth}. "
                         f"Minimum depth in data: {sample_sums.min()}")
    
    rarefied_df = abundance_df.loc[retained_samples].copy()
    
    # Perform rarefaction
    rarefied_counts = rarefied_df.apply(
        lambda row: np.random.choice(
            row.index, 
            size=target_depth, 
            replace=False, 
            p=row / row.sum()
        ).tolist(), 
        axis=1
    )
    
    # Convert list of counts back to DataFrame
    rarefied_matrix = np.zeros((len(rarefied_df), len(rarefied_df.columns)), dtype=int)
    for i, row_counts in enumerate(rarefied_counts):
        counts_dict = pd.Series(row_counts).value_counts()
        for taxon, count in counts_dict.items():
            if taxon in rarefied_df.columns:
                rarefied_matrix[i, rarefied_df.columns.get_loc(taxon)] = count
    
    rarefied_df = pd.DataFrame(
        rarefied_matrix, 
        index=rarefied_df.index, 
        columns=rarefied_df.columns
    )
    
    logger.info(f"Rarefaction complete. Output shape: {rarefied_df.shape}")
    return rarefied_df

def collapse_to_genus(counts_df: pd.DataFrame, taxonomy_map: Dict[str, str]) -> pd.DataFrame:
    """
    Collapse taxonomic counts from species/OTU level to genus level.
    
    Args:
        counts_df: DataFrame with taxon counts (columns are taxon IDs).
        taxonomy_map: Dictionary mapping taxon IDs to genus names.
        
    Returns:
        DataFrame with genus-level counts.
    """
    logger.info("Collapsing to genus level")
    
    # Map columns to genus
    genus_counts = pd.DataFrame()
    for taxon, genus in taxonomy_map.items():
        if taxon in counts_df.columns:
            if genus not in genus_counts.columns:
                genus_counts[genus] = 0
            genus_counts[genus] += counts_df[taxon]
    
    # Fill missing genera with 0
    all_genera = set(taxonomy_map.values())
    for genus in all_genera:
        if genus not in genus_counts.columns:
            genus_counts[genus] = 0
    
    logger.info(f"Collapsed to {len(genus_counts.columns)} genera")
    return genus_counts

def run_preprocessing_pipeline() -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline:
    1. Load merged data
    2. Filter by age >= 60
    3. Impute covariates
    4. Rarefy to uniform depth
    5. Collapse to genus level
    6. Validate and save output
    """
    logger.info("Starting preprocessing pipeline")
    enforce_resource_limits()  # Check RAM and CPU-only constraints
    
    # Step 1: Load merged data
    df = load_merged_data()
    
    # Step 2: Filter by age
    df = filter_by_age(df, min_age=60)
    if len(df) < 500:
        raise ValueError(f"Filtered dataset has {len(df)} samples, which is less than the required 500.")
    
    # Step 3: Impute covariates
    df = impute_covariates()
    if not validate_covariate_imputation(df):
        raise ValueError("Covariate imputation validation failed.")
    
    # Step 4: Extract abundance matrix (assuming columns starting with 'genus_' or taxon IDs)
    # We need to identify which columns are taxonomic counts
    # Assuming the merged data has a structure where taxon columns are numeric and not metadata
    metadata_cols = ['participant_id', 'age', 'bmi', 'education', 'cognitive_score']
    taxon_cols = [col for col in df.columns if col not in metadata_cols and df[col].dtype in ['int64', 'float64']]
    
    if len(taxon_cols) == 0:
        raise ValueError("No taxonomic count columns found in merged data.")
    
    abundance_df = df.set_index('participant_id')[taxon_cols].fillna(0).astype(int)
    logger.info(f"Extracted abundance matrix: {abundance_df.shape}")
    
    # Step 5: Determine rarefaction depth
    min_depth = abundance_df.sum(axis=1).min()
    target_depth = min(MIN_RAREFACTION_DEPTH, min_depth)
    logger.info(f"Minimum sequencing depth: {min_depth}, using target depth: {target_depth}")
    
    # Step 6: Rarefy samples
    rarefied_abundance = rarefy_samples(abundance_df, target_depth)
    
    # Step 7: Collapse to genus level
    # We need a taxonomy map. For now, we assume column names are already genus-level or we map them.
    # In a real scenario, this would come from the AGP metadata.
    # Here we assume columns are already genus-level for simplicity, or we map based on naming convention.
    taxonomy_map = {col: col.split('_')[0] if '_' in col else col for col in rarefied_abundance.columns}
    genus_abundance = collapse_to_genus(rarefied_abundance, taxonomy_map)
    
    # Step 8: Merge back with metadata
    metadata = df[['participant_id', 'age', 'bmi', 'education', 'cognitive_score']].set_index('participant_id')
    final_df = metadata.join(genus_abundance)
    
    # Step 9: Validate required columns
    required_genera = [col for col in final_df.columns if col not in metadata.columns]
    if len(required_genera) < 5:
        logger.warning(f"Only {len(required_genera)} genus columns found, expected at least 5.")
    
    if not validate_null_values(final_df, ['age', 'bmi', 'education', 'cognitive_score'] + required_genera):
        raise ValueError("Final dataset validation failed: null values detected in required columns.")
    
    # Step 10: Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(RAREFIED_OUTPUT_PATH, index=True)
    logger.info(f"Saved rarefied genus table to {RAREFIED_OUTPUT_PATH}")
    
    # Log rarefaction parameters
    log_data = {
        "target_depth": target_depth,
        "min_depth": min_depth,
        "samples_retained": len(final_df),
        "genera_count": len(required_genera),
        "output_path": str(RAREFIED_OUTPUT_PATH)
    }
    with open(RAREFACTION_LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Saved rarefaction log to {RAREFACTION_LOG_PATH}")
    
    return final_df

def main():
    """Main entry point for preprocessing pipeline."""
    setup_logging()
    try:
        result = run_preprocessing_pipeline()
        logger.info(f"Preprocessing pipeline completed successfully. Output: {result.shape}")
        return result
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()