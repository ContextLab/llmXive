"""
T017: Output cleaned dataset with alpha metrics.

Reads the preprocessed OTU table and calculated alpha diversity metrics,
merges them with available metadata, filters for completeness, and outputs
a clean CSV. Verifies retention rate and minimum row count.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import ensure_directories, get_output_path
from code.utils.logging import setup_logging, get_logger

# Configure logging
setup_logging()
logger = get_logger(__name__)

def load_preprocessed_data():
    """
    Load the preprocessed OTU table and alpha diversity metrics.
    Assumes T016 has run and produced the necessary intermediate files.
    """
    # Expected paths based on project conventions
    # T016 calculates alpha diversity and should save it
    alpha_metrics_path = get_output_path("data/processed/alpha_diversity_metrics.csv")
    preprocessed_otu_path = get_output_path("data/processed/preprocessed_otu_table.csv")
    metadata_path = get_output_path("data/processed/merged_metadata.csv")

    # Check if files exist (T016 and T012/T013 must have run)
    if not os.path.exists(alpha_metrics_path):
        logger.error(f"Alpha metrics file not found: {alpha_metrics_path}")
        logger.error("Ensure T016 (calculate_alpha_diversity) has been executed.")
        return None, None, None

    if not os.path.exists(preprocessed_otu_path):
        logger.error(f"Preprocessed OTU table not found: {preprocessed_otu_path}")
        logger.error("Ensure T014/T015 (preprocessing) has been executed.")
        return None, None, None

    try:
        # Load alpha metrics
        alpha_df = pd.read_csv(alpha_metrics_path)
        logger.info(f"Loaded alpha diversity metrics: {len(alpha_df)} rows")

        # Load preprocessed OTU table (likely in long format or wide format)
        # Assuming wide format: rows=sample_id, cols=taxa
        otu_df = pd.read_csv(preprocessed_otu_path)
        
        # If OTU table has a sample_id column, set it as index for merging
        if 'sample_id' in otu_df.columns:
            otu_df = otu_df.set_index('sample_id')
        
        logger.info(f"Loaded preprocessed OTU table: {otu_df.shape}")

        # Load metadata if available (from T012/T013)
        metadata_df = None
        if os.path.exists(metadata_path):
            metadata_df = pd.read_csv(metadata_path)
            logger.info(f"Loaded metadata: {len(metadata_df)} rows")
        else:
            logger.warning("Merged metadata file not found. Proceeding without metadata merge.")

        return alpha_df, otu_df, metadata_df

    except Exception as e:
        logger.error(f"Error loading data files: {e}")
        return None, None, None

def merge_and_filter(alpha_df, otu_df, metadata_df):
    """
    Merge alpha metrics with OTU table and metadata.
    Filter out rows with missing key values.
    """
    logger.info("Merging datasets...")
    
    # Reset index if needed for merging
    if isinstance(alpha_df.index, pd.Index) and alpha_df.index.name is None:
        # Assume first column is sample_id if not set
        if 'sample_id' not in alpha_df.columns:
            # Try to infer sample_id from index if it looks like IDs
            alpha_df = alpha_df.reset_index()
            if alpha_df.columns[0] == 'index':
                alpha_df.rename(columns={'index': 'sample_id'}, inplace=True)
    elif isinstance(alpha_df.index, pd.MultiIndex):
        logger.error("Alpha metrics have MultiIndex. Cannot merge easily.")
        return None

    # Ensure sample_id is a column in alpha_df
    if 'sample_id' not in alpha_df.columns:
        # Check if index is sample_id
        if alpha_df.index.name == 'sample_id':
            alpha_df = alpha_df.reset_index()
        else:
            logger.error("Cannot find sample_id in alpha metrics. Cannot merge.")
            return None

    # Start with alpha metrics
    clean_df = alpha_df.copy()

    # Merge with OTU table if available (usually wide format)
    # We might only need a subset of taxa or just the alpha metrics
    # For T017, the primary output is alpha metrics + metadata
    if otu_df is not None:
        # If OTU table is wide, we might want to keep it or aggregate
        # For this task, we'll merge on sample_id to get the most complete row
        # If OTU table is too wide, we might select top taxa or just rely on alpha
        
        # Check if sample_id exists in otu_df columns or index
        if isinstance(otu_df.index, pd.Index) and otu_df.index.name == 'sample_id':
            otu_reset = otu_df.reset_index()
        elif 'sample_id' in otu_df.columns:
            otu_reset = otu_df
        else:
            logger.warning("OTU table lacks sample_id. Skipping OTU merge.")
            otu_reset = None

        if otu_reset is not None:
            # Merge alpha with OTU (inner join to keep only valid samples)
            clean_df = pd.merge(clean_df, otu_reset, on='sample_id', how='inner')
            logger.info(f"After OTU merge: {len(clean_df)} rows")

    # Merge with metadata if available
    if metadata_df is not None:
        if 'sample_id' not in metadata_df.columns:
            if metadata_df.index.name == 'sample_id':
                metadata_df = metadata_df.reset_index()
            else:
                logger.warning("Metadata lacks sample_id. Skipping metadata merge.")
                metadata_df = None

        if metadata_df is not None:
            clean_df = pd.merge(clean_df, metadata_df, on='sample_id', how='inner')
            logger.info(f"After metadata merge: {len(clean_df)} rows")

    # Identify key columns that must NOT be missing
    # Based on T012/T013: PHQ-9, GAD-7, and diversity metrics
    key_columns = []
    if 'phq9' in clean_df.columns:
        key_columns.append('phq9')
    if 'gad7' in clean_df.columns:
        key_columns.append('gad7')
    if 'shannon' in clean_df.columns:
        key_columns.append('shannon')
    if 'simpson' in clean_df.columns:
        key_columns.append('simpson')
    
    # Also check for common diversity metric names
    for col in clean_df.columns:
        if 'diversity' in col.lower() or 'shannon' in col.lower() or 'simpson' in col.lower():
            if col not in key_columns:
                key_columns.append(col)

    if not key_columns:
        logger.warning("No key columns identified. Cannot filter properly.")
        # Fallback: use all numeric columns that might be metrics
        key_columns = [col for col in clean_df.columns if clean_df[col].dtype in ['int64', 'float64'] and col != 'sample_id']

    logger.info(f"Filtering for non-missing values in: {key_columns}")

    # Filter out rows with any missing values in key columns
    initial_rows = len(clean_df)
    clean_df = clean_df.dropna(subset=key_columns)
    final_rows = len(clean_df)
    
    logger.info(f"Filtered rows: {initial_rows} -> {final_rows}")

    if final_rows == 0:
        logger.error("No valid rows remaining after filtering. Check data quality.")
        return None

    return clean_df

def verify_retention(clean_df, original_count):
    """
    Verify ≥ 80% retention and ≥ 100 valid rows.
    """
    if original_count == 0:
        return False, "Original count is 0"
    
    retention_rate = len(clean_df) / original_count
    logger.info(f"Retention rate: {retention_rate:.2%} ({len(clean_df)}/{original_count})")

    if retention_rate < 0.80:
        return False, f"Retention rate {retention_rate:.2%} < 80%"
    
    if len(clean_df) < 100:
        return False, f"Valid rows {len(clean_df)} < 100"
    
    return True, "Verification passed"

def main():
    """
    Main entry point for T017.
    """
    logger.info("Starting T017: Output cleaned dataset")
    
    # Ensure output directories exist
    ensure_directories()
    
    # Load data
    alpha_df, otu_df, metadata_df = load_preprocessed_data()
    
    if alpha_df is None:
        logger.error("Failed to load preprocessed data. Cannot proceed.")
        return False

    original_count = len(alpha_df)
    
    # Merge and filter
    clean_df = merge_and_filter(alpha_df, otu_df, metadata_df)
    
    if clean_df is None or len(clean_df) == 0:
        logger.error("Failed to create clean dataset. No valid rows.")
        return False

    # Verify retention
    passed, message = verify_retention(clean_df, original_count)
    
    if not passed:
        logger.warning(f"Verification failed: {message}")
        # Still save the dataset but note the failure
        # Per task: "verify ≥ 80% retention AND ≥ 100 valid rows"
        # If it fails, we log but still output what we have? 
        # The task says "Output ... and verify". If verification fails, it's a warning.
        # However, the task implies we should only proceed if it passes.
        # Let's output the file regardless but mark the status.
    
    # Define output path
    output_path = get_output_path("data/processed/cleaned_dataset.csv")
    
    try:
        clean_df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned dataset to: {output_path}")
        logger.info(f"Final dataset shape: {clean_df.shape}")
        logger.info(f"Columns: {list(clean_df.columns)}")
    except Exception as e:
        logger.error(f"Failed to save cleaned dataset: {e}")
        return False

    # Final status
    if passed:
        logger.info("✅ T017 SUCCESS: Verification passed (≥80% retention, ≥100 rows)")
        return True
    else:
        logger.warning(f"⚠️ T017 WARNING: Verification failed - {message}")
        logger.warning("Dataset saved, but retention criteria not met.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
