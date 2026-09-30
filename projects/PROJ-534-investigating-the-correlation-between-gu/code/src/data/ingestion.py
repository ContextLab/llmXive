"""
Ingestion module for loading and merging synthetic microbiome and cognitive data.

This module implements User Story 1 (T010):
- Load synthetic 16S rRNA sequencing data and linked cognitive assessment data
- Merge on participant_id
- Validate output against dataset schema
"""
import os
import pandas as pd
from pathlib import Path
import logging
import sys
from typing import Tuple, Optional

from code.src.utils.config import (
    SEED, 
    DATA_DIR, 
    RAW_DATA_DIR, 
    LOGS_DIR, 
    ensure_directories, 
    set_global_seed,
    get_raw_data_dir,
    get_project_root
)
from code.src.utils.validation import (
    load_schema, 
    validate_dataframe_against_schema
)

# Setup logging
logger = logging.getLogger(__name__)

def load_microbiome_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load microbiome data from the raw data directory.
    
    Args:
        data_path: Optional path to the microbiome data file. If None, uses
                  the default path from config (data/raw/synthetic_data.csv).
    
    Returns:
        pd.DataFrame: DataFrame containing microbiome and participant data.
    
    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the data file is empty or malformed.
    """
    if data_path is None:
        data_path = get_raw_data_dir() / "synthetic_data.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Microbiome data file not found at: {data_path}")
    
    logger.info(f"Loading microbiome data from: {data_path}")
    
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")
    
    if df.empty:
        raise ValueError("Loaded microbiome data is empty")
    
    logger.info(f"Loaded {len(df)} rows of microbiome data")
    return df

def load_cognitive_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load cognitive assessment data from the raw data directory.
    
    In this synthetic setup, cognitive data is already merged with microbiome
    data in the same file. This function serves as a placeholder for future
    real-world scenarios where cognitive data might be in a separate file.
    
    Args:
        data_path: Optional path to the cognitive data file.
    
    Returns:
        pd.DataFrame: DataFrame containing cognitive assessment data.
    """
    # For synthetic data, cognitive data is in the same file as microbiome data
    # This function returns the same data but conceptually represents
    # loading cognitive assessments separately
    if data_path is None:
        data_path = get_raw_data_dir() / "synthetic_data.csv"
    
    logger.info(f"Loading cognitive data from: {data_path}")
    
    # In a real scenario, we would load a separate file here
    # For now, we return the same data structure
    return load_microbiome_data(data_path)

def merge_datasets(
    microbiome_df: pd.DataFrame, 
    cognitive_df: pd.DataFrame,
    key: str = "participant_id"
) -> pd.DataFrame:
    """
    Merge microbiome and cognitive datasets on participant_id.
    
    Args:
        microbiome_df: DataFrame containing microbiome data.
        cognitive_df: DataFrame containing cognitive assessment data.
        key: The column name to merge on (default: "participant_id").
    
    Returns:
        pd.DataFrame: Merged DataFrame containing both microbiome and cognitive data.
    
    Raises:
        ValueError: If the merge key is not found in both DataFrames.
    """
    if key not in microbiome_df.columns:
        raise ValueError(f"Merge key '{key}' not found in microbiome data")
    if key not in cognitive_df.columns:
        raise ValueError(f"Merge key '{key}' not found in cognitive data")
    
    logger.info(f"Merging datasets on key: {key}")
    
    # Perform inner join to ensure only participants with both data types are included
    merged_df = pd.merge(
        microbiome_df, 
        cognitive_df, 
        on=key, 
        how='inner',
        suffixes=('_microbiome', '_cognitive')
    )
    
    logger.info(f"Merged dataset contains {len(merged_df)} participants")
    return merged_df

def ingest_synthetic_cohort(
    data_path: Optional[Path] = None,
    schema_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Ingest the synthetic cohort by loading and merging data, then validating.
    
    This is the main entry point for T010. It:
    1. Loads synthetic microbiome data
    2. Loads cognitive data (in synthetic case, same file)
    3. Merges on participant_id
    4. Validates against the dataset schema
    
    Args:
        data_path: Optional path to the synthetic data file.
        schema_path: Optional path to the schema file. If None, uses default.
    
    Returns:
        pd.DataFrame: Validated merged cohort DataFrame.
    
    Raises:
        FileNotFoundError: If required files do not exist.
        ValueError: If validation fails.
    """
    if data_path is None:
        data_path = get_raw_data_dir() / "synthetic_data.csv"
    
    if schema_path is None:
        schema_path = get_project_root() / "contracts" / "dataset.schema.yaml"
    
    logger.info("Starting synthetic cohort ingestion")
    
    # Load data
    microbiome_df = load_microbiome_data(data_path)
    cognitive_df = load_cognitive_data(data_path)
    
    # Merge datasets
    merged_df = merge_datasets(microbiome_df, cognitive_df)
    
    # Validate against schema
    logger.info(f"Validating merged data against schema: {schema_path}")
    
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}, skipping validation")
        return merged_df
    
    schema = load_schema(schema_path)
    
    try:
        validation_errors = validate_dataframe_against_schema(merged_df, schema)
        if validation_errors:
            error_msg = "\n".join(validation_errors)
            raise ValueError(f"Schema validation failed:\n{error_msg}")
        logger.info("Schema validation passed successfully")
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise
    
    return merged_df

def save_merged_cohort(
    df: pd.DataFrame, 
    output_path: Optional[Path] = None
) -> Path:
    """
    Save the merged cohort to a CSV file.
    
    Args:
        df: The merged cohort DataFrame to save.
        output_path: Optional path for the output file. If None, uses
                    default path (data/processed/merged_cohort.csv).
    
    Returns:
        Path: The path where the file was saved.
    
    Raises:
        IOError: If the file cannot be written.
    """
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "merged_cohort.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving merged cohort to: {output_path}")
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} rows to {output_path}")
    except Exception as e:
        raise IOError(f"Failed to save merged cohort: {e}")
    
    return output_path

def main():
    """
    Main entry point for the ingestion script.
    
    This function:
    1. Sets up logging
    2. Ensures directories exist
    3. Sets global seed
    4. Ingests the synthetic cohort
    5. Validates the output
    6. Saves the merged cohort
    """
    # Setup
    set_global_seed(SEED)
    ensure_directories()
    
    # Configure logging
    log_file = LOGS_DIR / "ingestion.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger.info("Starting synthetic cohort ingestion pipeline")
    
    try:
        # Ingest data
        merged_cohort = ingest_synthetic_cohort()
        
        # Save results
        output_path = save_merged_cohort(merged_cohort)
        
        logger.info(f"Ingestion pipeline completed successfully. Output: {output_path}")
        return merged_cohort, output_path
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()