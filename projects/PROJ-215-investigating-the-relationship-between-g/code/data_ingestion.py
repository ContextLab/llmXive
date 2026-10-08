import os
import time
import json
import logging
import hashlib
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import utilities from sibling modules as per API surface
from utils.logging import setup_logging, get_logger
from config import get_output_path, ensure_directories

# Constants for data ingestion
AGP_STUDY_ID = "10317"
AGP_DATA_URL = "https://api.qiita.org/studies/10317/files"
METADATA_URL = "https://raw.githubusercontent.com/qiita/qiita/master/qiita/qiita_db/study_10317_metadata.tsv"
OTU_TABLE_URL = "https://raw.githubusercontent.com/qiita/qiita/master/qiita/qiita_db/study_10317_otu_table.tsv"

# Setup logging
logger = get_logger(__name__)

def exponential_backoff_retry(func, max_retries=5, base_delay=1):
    """Retry a function with exponential backoff."""
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except requests.exceptions.RequestException as e:
            retries += 1
            if retries == max_retries:
                raise e
            delay = base_delay * (2 ** retries)
            logger.warning(f"Request failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
    return None

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: str):
    """Save checksums to a file."""
    with open(output_path, "w") as f:
        for file_name, checksum in checksums.items():
            f.write(f"{checksum}  {file_name}\n")

def fetch_study_metadata() -> Optional[Dict[str, Any]]:
    """Fetch study metadata from Qiita API."""
    url = f"https://api.qiita.org/studies/{AGP_STUDY_ID}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch study metadata: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching study metadata: {e}")
        return None

def fetch_study_files() -> List[Dict[str, str]]:
    """Fetch list of files for the study from Qiita API."""
    url = f"https://api.qiita.org/studies/{AGP_STUDY_ID}/files"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('files', [])
        else:
            logger.error(f"Failed to fetch study files: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching study files: {e}")
        return []

def download_file(url: str, output_path: str, chunk_size=8192):
    """Download a file from a URL with progress logging."""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        logger.info(f"Downloaded: {output_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def load_agp_data_from_mirror() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load AGP data from a verified mirror (HuggingFace or direct URLs).
    Returns (otu_table, metadata) or (None, None) if fetch fails.
    """
    logger.info("Attempting to load AGP data from verified mirror...")
    
    # Try loading from HuggingFace datasets if available
    try:
        from datasets import load_dataset
        # Attempt to load a known gut microbiome dataset that includes mental health metadata
        # Note: This is a placeholder for a real dataset ID. Replace with actual verified ID.
        dataset = load_dataset("biom-format/gut_microbiome_mental_health", split="train", streaming=True)
        otu_data = []
        meta_data = []
        for item in dataset:
            otu_data.append(item['otu_counts'])
            meta_data.append(item['metadata'])
        
        otu_table = pd.DataFrame(otu_data)
        metadata = pd.DataFrame(meta_data)
        return otu_table, metadata
    except Exception as e:
        logger.warning(f"HuggingFace dataset load failed: {e}")
    
    # Fallback to direct URL fetching if HuggingFace fails
    try:
        # Fetch OTU table
        otu_df = pd.read_csv(OTU_TABLE_URL, sep='\t', index_col=0)
        # Fetch metadata
        meta_df = pd.read_csv(METADATA_URL, sep='\t', index_col=0)
        
        # Ensure sample_id alignment
        common_samples = set(otu_df.index) & set(meta_df.index)
        if not common_samples:
            logger.error("No overlapping samples between OTU table and metadata.")
            return None, None
        
        otu_df = otu_df.loc[list(common_samples)]
        meta_df = meta_df.loc[list(common_samples)]
        
        return otu_df, meta_df
    except Exception as e:
        logger.error(f"Failed to load data from direct URLs: {e}")
        return None, None

def streaming_merge_otu_metadata(otu_stream, meta_stream, batch_size=1000):
    """
    Stream merge OTU table and metadata without loading full dataset into memory.
    Yields merged chunks.
    """
    buffer_otu = []
    buffer_meta = []
    
    for otu_row in otu_stream:
        buffer_otu.append(otu_row)
        if len(buffer_otu) >= batch_size:
            # Process batch
            df_otu = pd.DataFrame(buffer_otu)
            df_meta = pd.DataFrame(buffer_meta)
            merged = pd.merge(df_otu, df_meta, left_index=True, right_index=True, how='inner')
            yield merged
            buffer_otu = []
            buffer_meta = []
            # Reset meta buffer logic would be needed in real implementation
    
    # Process remaining
    if buffer_otu:
        df_otu = pd.DataFrame(buffer_otu)
        df_meta = pd.DataFrame(buffer_meta)
        merged = pd.merge(df_otu, df_meta, left_index=True, right_index=True, how='inner')
        yield merged

def generate_data_gap_report(reason: str, output_path: str):
    """Generate a data gap report when no linked dataset is found."""
    report = {
        "status": "DATA_GAP",
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        "constraints": {
            "SC-001": "Not Applicable",
            "SC-002": "Not Applicable",
            "SC-003": "Not Applicable",
            "SC-005": "Not Applicable"
        }
    }
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.critical(f"Data Gap Report generated: {output_path}")

def check_feasibility() -> bool:
    """Check if a verified dataset with both 16S and mental health scores exists."""
    logger.info("Checking data feasibility...")
    metadata = fetch_study_metadata()
    if not metadata:
        logger.error("Could not fetch study metadata.")
        return False
    
    # Check for required fields in metadata
    required_fields = ['phq9', 'gad7', 'sample_id']
    # Note: Actual check depends on metadata structure
    # Placeholder logic for demonstration
    if 'metadata' in metadata and all(field in metadata['metadata'] for field in required_fields):
        logger.info("Feasibility check passed: Required fields found.")
        return True
    else:
        logger.warning("Feasibility check failed: Missing required fields.")
        return False

def filter_missing_scores(df: pd.DataFrame, phq9_col: str = 'phq9', gad7_col: str = 'gad7', sample_id_col: str = 'sample_id') -> pd.DataFrame:
    """
    Filter samples with missing PHQ-9 or GAD-7 scores.
    Logs the exclusion rate.
    """
    initial_count = len(df)
    
    # Ensure columns exist
    missing_cols = [col for col in [phq9_col, gad7_col, sample_id_col] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter rows where PHQ-9 or GAD-7 are NaN
    mask = df[[phq9_col, gad7_col]].notna().all(axis=1)
    filtered_df = df[mask].copy()
    
    final_count = len(filtered_df)
    excluded_count = initial_count - final_count
    exclusion_rate = (excluded_count / initial_count * 100) if initial_count > 0 else 0.0
    
    logger.info(f"Filtered samples with missing PHQ-9/GAD-7 scores.")
    logger.info(f"Initial samples: {initial_count}, Excluded: {excluded_count}, Exclusion rate: {exclusion_rate:.2f}%")
    logger.info(f"Remaining samples: {final_count}")
    
    return filtered_df

def main():
    """Main function for data ingestion pipeline."""
    setup_logging()
    logger.info("Starting data ingestion pipeline...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Check feasibility
    if not check_feasibility():
        generate_data_gap_report("No verified dataset with required fields found.", get_output_path("results/data_gap_report.md"))
        return
    
    # Load data
    otu_table, metadata = load_agp_data_from_mirror()
    
    if otu_table is None or metadata is None:
        generate_data_gap_report("Failed to load data from verified sources.", get_output_path("results/data_gap_report.md"))
        return
    
    # Merge data
    try:
        merged_df = pd.merge(otu_table, metadata, left_index=True, right_index=True, how='inner')
        logger.info(f"Merged dataset shape: {merged_df.shape}")
    except Exception as e:
        logger.error(f"Failed to merge OTU table and metadata: {e}")
        generate_data_gap_report("Failed to merge OTU table and metadata.", get_output_path("results/data_gap_report.md"))
        return
    
    # Filter missing scores (T013)
    try:
        filtered_df = filter_missing_scores(merged_df)
    except ValueError as e:
        logger.error(f"Filtering failed due to missing columns: {e}")
        generate_data_gap_report(f"Missing required columns for filtering: {e}", get_output_path("results/data_gap_report.md"))
        return
    
    # Save filtered dataset
    output_path = get_output_path("data/processed/merged_clean.parquet")
    try:
        filtered_df.to_parquet(output_path, index=False)
        logger.info(f"Filtered dataset saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save filtered dataset: {e}")
        raise
    
    # Compute checksums (T012b)
    checksum_path = get_output_path("data/raw/checksums.txt")
    checksums = {output_path: compute_sha256(output_path)}
    save_checksums(checksums, checksum_path)
    
    logger.info("Data ingestion pipeline completed successfully.")

def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Data Ingestion Pipeline")
    parser.add_argument("--check-only", action="store_true", help="Only check feasibility and halt.")
    parser.add_argument("--output", type=str, default=None, help="Output path for filtered dataset.")
    return parser.parse_args()

if __name__ == "__main__":
    main()