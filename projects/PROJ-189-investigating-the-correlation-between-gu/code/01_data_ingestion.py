"""
Data Ingestion Pipeline for Gut Microbiome and Cognitive Decline Analysis.

This module handles:
1. Fetching AGP 16S taxonomic data from Qiita/EBI.
2. Fetching HRS cognitive metadata from the HRS portal.
3. Merging datasets by participant ID with overlap validation.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional

# Add parent directory to path to allow relative imports from utils
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from utils.data_fetchers import fetch_and_cache, DataFetchError
from utils.logging import setup_logger
from utils.resource_guard import check_memory

# Configure logger
logger = setup_logger(__name__)

# Constants
PROJECT_ROOT = current_dir.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Placeholder URLs - In a real scenario, these would be the specific API endpoints
# For AGP 16S data (Qiita study ID 12345 example, replace with actual from spec)
AGP_DATA_URL = "https://qiita.ucsd.edu/study/download/12345" 
AGP_FILE_NAME = "agp_16s_taxa.tsv"

# For HRS Cognitive Data (Example URL, replace with actual)
HRS_DATA_URL = "https://hrs.isr.umich.edu/sites/default/files/microdata/cognitive_scores.csv"
HRS_FILE_NAME = "hrs_cognitive_metadata.csv"

# Merged output file
MERGED_OUTPUT_FILE = DATA_PROCESSED_DIR / "merged_dataset_raw.csv"
MIN_OVERLAP_SAMPLES = 500

def fetch_agp_data() -> pd.DataFrame:
    """
    Fetches AGP 16S taxonomic data.
    Returns a DataFrame with 'sample_id' and taxonomic columns.
    """
    logger.info("Fetching AGP 16S taxonomic data...")
    try:
        # In a real implementation, this would use fetch_and_cache with real URLs
        # For now, we simulate the fetch logic structure
        file_path = DATA_RAW_DIR / AGP_FILE_NAME
        
        # Check if file exists locally (simulating cached fetch)
        if not file_path.exists():
            # Attempt to fetch (this would be the real call)
            # fetch_and_cache(AGP_DATA_URL, str(file_path), ...)
            raise FileNotFoundError(f"AGP data file not found at {file_path}. "
                                  "Ensure data fetching (T012) has populated data/raw.")
        
        # Load data
        # Assuming tab-separated with sample IDs in the first column or named 'sample_id'
        df = pd.read_csv(file_path, sep='\t')
        
        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Identify sample ID column
        id_col = None
        for cand in ['sample_id', 'sampleid', 'study_sample_id', 'qiita_sample_id']:
            if cand in df.columns:
                id_col = cand
                break
        
        if not id_col:
            raise ValueError("Could not identify sample ID column in AGP data.")
        
        df = df.rename(columns={id_col: 'participant_id'})
        logger.info(f"Loaded {len(df)} samples from AGP data.")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch AGP data: {e}")
        raise

def fetch_hrs_data() -> pd.DataFrame:
    """
    Fetches HRS cognitive metadata.
    Returns a DataFrame with 'participant_id' and cognitive score columns.
    """
    logger.info("Fetching HRS cognitive metadata...")
    try:
        file_path = DATA_RAW_DIR / HRS_FILE_NAME
        
        if not file_path.exists():
            # fetch_and_cache(HRS_DATA_URL, str(file_path), ...)
            raise FileNotFoundError(f"HRS data file not found at {file_path}. "
                                  "Ensure data fetching (T013) has populated data/raw.")
        
        # Load data
        df = pd.read_csv(file_path)
        
        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Identify participant ID column
        id_col = None
        for cand in ['participant_id', 'participantid', 'person_id', 'seqn', 'id']:
            if cand in df.columns:
                id_col = cand
                break
        
        if not id_col:
            raise ValueError("Could not identify participant ID column in HRS data.")
        
        df = df.rename(columns={id_col: 'participant_id'})
        logger.info(f"Loaded {len(df)} participants from HRS data.")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch HRS data: {e}")
        raise

def merge_datasets(agp_df: pd.DataFrame, hrs_df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Merges AGP and HRS datasets by 'participant_id'.
    Logs overlap statistics and validates minimum sample count.
    
    Returns:
        Tuple of (merged_dataframe, overlap_count)
    """
    logger.info("Merging datasets by participant_id...")
    
    # Log unique counts before merge
    agp_ids = set(agp_df['participant_id'].dropna().unique())
    hrs_ids = set(hrs_df['participant_id'].dropna().unique())
    
    logger.info(f"Unique AGP IDs: {len(agp_ids)}")
    logger.info(f"Unique HRS IDs: {len(hrs_ids)}")
    
    # Perform inner join to keep only overlapping participants
    merged_df = pd.merge(agp_df, hrs_df, on='participant_id', how='inner')
    
    overlap_count = len(merged_df)
    logger.info(f"Overlap count (inner join): {overlap_count}")
    
    # Log mismatch details
    missing_in_hrs = len(agp_ids - hrs_ids)
    missing_in_agp = len(hrs_ids - agp_ids)
    logger.info(f"Samples in AGP but missing in HRS: {missing_in_hrs}")
    logger.info(f"Samples in HRS but missing in AGP: {missing_in_agp}")
    
    # Validate minimum overlap
    if overlap_count < MIN_OVERLAP_SAMPLES:
        error_msg = (f"Overlap count ({overlap_count}) is below the required minimum "
                     f"of {MIN_OVERLAP_SAMPLES}. Cannot proceed with analysis.")
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Merge successful. {overlap_count} samples retained.")
    return merged_df, overlap_count

def main():
    """
    Main execution entry point for data ingestion and merging.
    """
    logger.info("Starting Data Ingestion Pipeline (T014)...")
    
    # Check memory resources
    if not check_memory(max_gb=7.0):
        logger.error("Memory check failed. Aborting.")
        sys.exit(1)
    
    try:
        # 1. Fetch Data
        agp_df = fetch_agp_data()
        hrs_df = fetch_hrs_data()
        
        # 2. Merge Data
        merged_df, overlap_count = merge_datasets(agp_df, hrs_df)
        
        # 3. Save Result
        merged_df.to_csv(MERGED_OUTPUT_FILE, index=False)
        logger.info(f"Saved merged dataset to {MERGED_OUTPUT_FILE}")
        
        # Log final schema summary
        logger.info(f"Merged dataset shape: {merged_df.shape}")
        logger.info(f"Columns: {list(merged_df.columns)}")
        
        return merged_df
        
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
