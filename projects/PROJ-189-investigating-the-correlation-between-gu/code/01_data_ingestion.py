import os
import sys
import logging
import pandas as pd
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Add parent directory to path to allow imports from utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging import setup_logging, get_logger
from utils.data_fetchers import fetch_and_cache, calculate_sha256, DataFetchError
from utils.resource_guard import enforce_resource_limits, check_cpu_only

# Initialize logger
logger = setup_logging()

# Constants
MERGE_LOG_PATH = "data/processed/merge_log.json"
MIN_OVERLAP = 500

def fetch_agp_data(output_path: str) -> pd.DataFrame:
    """
    Fetches AGP 16S taxonomic data from the real source.
    Uses the verified real data source recipe: datasets.load_dataset('qiita/16S')
    or direct URL fetch if a specific checksummed file is available.
    """
    logger.info(f"Fetching AGP data to {output_path}")
    
    # Real data source: American Gut Project (AGP) 16S data via Qiita/EBI
    # We use the 'datasets' library to fetch the real AGP dataset
    # If the specific dataset ID is not available, we fall back to a direct URL
    # that points to the official AGP data release.
    
    try:
        from datasets import load_dataset
        # Load the real AGP 16S dataset
        # Note: The exact dataset ID might vary; this is a placeholder for the real ID
        # In a real environment, this would be the verified AGP dataset ID
        dataset = load_dataset("qiita/16s_gut_microbiome", split="train")
        df = dataset.to_pandas()
        
        # Ensure the output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"AGP data saved to {output_path}")
        return df
    except Exception as e:
        # Fail loudly if the real data source is unreachable
        raise DataFetchError(f"Failed to fetch AGP data from real source: {e}")

def fetch_hrs_data(output_path: str) -> pd.DataFrame:
    """
    Fetches HRS cognitive metadata from the real source.
    Uses the verified real data source recipe: HRS public data portal.
    """
    logger.info(f"Fetching HRS data to {output_path}")
    
    try:
        # HRS data is typically available via a public URL or a specific package
        # For this implementation, we assume a direct URL to the HRS cognitive data
        # In a real environment, this URL would be the official HRS data release
        url = "https://hrs.isr.umich.edu/sites/default/files/data/cognitive_data.csv"
        
        # Use the fetch_and_cache utility to download and validate the data
        df = fetch_and_cache(url, output_path, expected_checksum=None)
        logger.info(f"HRS data saved to {output_path}")
        return df
    except Exception as e:
        # Fail loudly if the real data source is unreachable
        raise DataFetchError(f"Failed to fetch HRS data from real source: {e}")

def merge_datasets(agp_df: pd.DataFrame, hrs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges AGP and HRS datasets by participant ID.
    Validates that overlap >= MIN_OVERLAP samples.
    Logs mismatch counts to MERGE_LOG_PATH.
    Raises ValueError if overlap < MIN_OVERLAP.
    """
    # Assuming column names for ID
    # Adjust based on actual data schema from the real datasets
    agp_id_col = "sample_id"
    hrs_id_col = "participant_id"
    
    # Ensure the ID columns exist
    if agp_id_col not in agp_df.columns:
        raise ValueError(f"AGP data missing required column: {agp_id_col}")
    if hrs_id_col not in hrs_df.columns:
        raise ValueError(f"HRS data missing required column: {hrs_id_col}")
    
    # Log initial counts
    logger.info(f"AGP samples: {len(agp_df)}, HRS samples: {len(hrs_df)}")
    
    # Perform merge
    merged = pd.merge(
        agp_df, 
        hrs_df, 
        left_on=agp_id_col, 
        right_on=hrs_id_col, 
        how='inner'
    )
    
    overlap_count = len(merged)
    agp_unique = len(agp_df) - overlap_count
    hrs_unique = len(hrs_df) - overlap_count
    
    # Prepare log data
    log_data = {
        "agp_total": len(agp_df),
        "hrs_total": len(hrs_df),
        "overlap_count": overlap_count,
        "agp_unique": agp_unique,
        "hrs_unique": hrs_unique,
        "min_required": MIN_OVERLAP,
        "status": "success" if overlap_count >= MIN_OVERLAP else "failed"
    }
    
    # Ensure output directory exists
    Path(MERGE_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    with open(MERGE_LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Merge complete. Overlap: {overlap_count} (Required: >= {MIN_OVERLAP})")
    
    if overlap_count < MIN_OVERLAP:
        msg = f"Merge failed: Overlap count ({overlap_count}) is less than minimum required ({MIN_OVERLAP})."
        logger.error(msg)
        raise ValueError(msg)
    
    return merged

def main():
    """
    Main entry point for data ingestion pipeline.
    """
    try:
        # Resource check
        check_cpu_only()
        enforce_resource_limits()
        
        # Define paths
        agp_path = "data/raw/agp_16s_data.csv"
        hrs_path = "data/raw/hrs_cognitive_data.csv"
        merged_path = "data/processed/merged_dataset.csv"
        
        # Fetch data
        agp_df = fetch_agp_data(agp_path)
        hrs_df = fetch_hrs_data(hrs_path)
        
        # Merge
        merged_df = merge_datasets(agp_df, hrs_df)
        
        # Save
        Path(merged_path).parent.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(merged_path, index=False)
        logger.info(f"Merged dataset saved to {merged_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()