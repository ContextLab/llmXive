import os
import pandas as pd
from pathlib import Path
import logging
import sys
from typing import Tuple, Optional

from code.src.utils.config import (
    get_project_root,
    get_raw_data_dir,
    get_processed_data_dir,
    ensure_directories,
    setup_logging
)
from code.src.utils.validation import load_schema, validate_dataframe_against_schema

# Initialize logger for this module
logger = logging.getLogger(__name__)

def load_microbiome_data(raw_data_dir: Path) -> pd.DataFrame:
    """
    Load 16S rRNA sequencing data (synthetic) from the raw data directory.
    
    Args:
        raw_data_dir: Path to the raw data directory.
        
    Returns:
        DataFrame containing microbiome data with participant_id and OTU counts.
    """
    file_path = raw_data_dir / "synthetic_data.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Microbiome data file not found: {file_path}")
    
    logger.info(f"Loading microbiome data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Ensure participant_id is string for consistent merging
    if 'participant_id' in df.columns:
        df['participant_id'] = df['participant_id'].astype(str)
        
    return df

def load_cognitive_data(raw_data_dir: Path) -> pd.DataFrame:
    """
    Load linked cognitive assessment data from the raw data directory.
    
    Note: In this synthetic setup, cognitive data is merged with microbiome
    data in a single file. This function loads the same file but returns
    only the cognitive-related columns for clarity.
    
    Args:
        raw_data_dir: Path to the raw data directory.
        
    Returns:
        DataFrame containing cognitive assessment data.
    """
    file_path = raw_data_dir / "synthetic_data.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Cognitive data file not found: {file_path}")
    
    logger.info(f"Loading cognitive data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Ensure participant_id is string for consistent merging
    if 'participant_id' in df.columns:
        df['participant_id'] = df['participant_id'].astype(str)
        
    return df

def merge_datasets(microbiome_df: pd.DataFrame, cognitive_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge microbiome and cognitive datasets on participant_id.
    
    Args:
        microbiome_df: DataFrame containing microbiome data.
        cognitive_df: DataFrame containing cognitive assessment data.
        
    Returns:
        Merged DataFrame with both microbiome and cognitive data.
        
    Raises:
        ValueError: If merge fails or required columns are missing.
    """
    required_cols = ['participant_id']
    
    for df_name, df in [("Microbiome", microbiome_df), ("Cognitive", cognitive_df)]:
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"{df_name} data missing required column: {col}")
    
    logger.info(f"Merging datasets on 'participant_id'. Microbiome rows: {len(microbiome_df)}, Cognitive rows: {len(cognitive_df)}")
    
    merged_df = pd.merge(
        microbiome_df,
        cognitive_df,
        on='participant_id',
        how='inner',
        suffixes=('_microbiome', '_cognitive')
    )
    
    logger.info(f"Merged dataset contains {len(merged_df)} rows")
    
    # Remove duplicate columns if any (e.g., if both files had identical columns)
    merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]
    
    return merged_df

def ingest_synthetic_cohort() -> pd.DataFrame:
    """
    Main ingestion function: loads synthetic 16S and cognitive data, merges them,
    and validates against the dataset schema.
    
    Returns:
        Validated DataFrame containing the merged synthetic cohort.
    """
    raw_data_dir = get_raw_data_dir()
    ensure_directories()
    
    logger.info("Starting synthetic cohort ingestion")
    
    try:
        microbiome_df = load_microbiome_data(raw_data_dir)
        cognitive_df = load_cognitive_data(raw_data_dir)
        
        merged_df = merge_datasets(microbiome_df, cognitive_df)
        
        # Load schema for validation
        schema = load_schema("dataset")
        
        # Validate merged dataset against schema
        validation_errors = validate_dataframe_against_schema(merged_df, schema)
        
        if validation_errors:
            error_msg = "Schema validation failed:\n" + "\n".join(validation_errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Ingestion completed successfully. Dataset validated against schema.")
        return merged_df
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found during ingestion: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error during ingestion: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise

def save_merged_cohort(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the merged cohort DataFrame to a CSV file.
    
    Args:
        df: The merged DataFrame to save.
        output_path: Optional specific path to save to. If None, uses default processed path.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        processed_dir = get_processed_data_dir()
        output_path = processed_dir / "merged_cohort.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving merged cohort to {output_path}")
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved {len(df)} rows to {output_path}")
    return output_path

def main():
    """
    Entry point for the ingestion script.
    Loads, merges, validates, and saves the synthetic cohort.
    """
    setup_logging()
    logger.info("=== Starting Data Ingestion Pipeline ===")
    
    try:
        # Ingest and validate
        cohort_df = ingest_synthetic_cohort()
        
        # Save to processed directory
        output_file = save_merged_cohort(cohort_df)
        
        logger.info(f"=== Ingestion Complete. Output: {output_file} ===")
        return cohort_df, output_file
        
    except Exception as e:
        logger.critical(f"Ingestion pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
