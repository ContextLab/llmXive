import os
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional, List
import hashlib
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_raw_fastq(dataset_id: str, url: str, output_dir: str) -> str:
    """
    Download raw FASTQ file from a URL.
    Returns path to downloaded file.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"{dataset_id}.fastq.gz"
    output_path = os.path.join(output_dir, filename)
    
    logger.info(f"Downloading {url} to {output_path}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    checksum = calculate_sha256(output_path)
    logger.info(f"Downloaded {filename} with checksum {checksum}")
    return output_path

def validate_metadata_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """Validate that metadata has required columns."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def harmonize_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Harmonize metadata columns and values."""
    # Standardize column names
    df = df.rename(columns=lambda x: x.strip().lower())
    
    # Example: standardize biome labels
    if 'biome' in df.columns:
        df['biome'] = df['biome'].str.replace('Temperate Forest', 'Forest', regex=False)
        df['biome'] = df['biome'].str.replace('Tropical Rainforest', 'Forest', regex=False)
    
    return df

def process_ingestion(
    dataset_ids: List[str],
    urls: Dict[str, str],
    metadata_path: str,
    raw_seq_dir: str,
    metadata_output_dir: str
) -> Dict[str, float]:
    """
    Main ingestion pipeline: download raw data, validate, harmonize metadata.
    Returns dict of dataset_id -> subsampling_ratio (for FR-009 reporting).
    """
    Path(raw_seq_dir).mkdir(parents=True, exist_ok=True)
    Path(metadata_output_dir).mkdir(parents=True, exist_ok=True)
    
    subsampling_ratios = {}
    
    # Download raw sequences
    for dataset_id in dataset_ids:
        if dataset_id in urls:
            download_raw_fastq(dataset_id, urls[dataset_id], raw_seq_dir)
            # Assume no subsampling for this example, ratio = 1.0
            subsampling_ratios[dataset_id] = 1.0
        else:
            logger.warning(f"No URL provided for {dataset_id}, skipping download")
    
    # Load and harmonize metadata
    if os.path.exists(metadata_path):
        metadata_df = pd.read_csv(metadata_path)
        
        required_cols = ['sample_id', 'pH', 'nutrients', 'biome']
        if validate_metadata_columns(metadata_df, required_cols):
            harmonized_df = harmonize_metadata(metadata_df)
            output_path = os.path.join(metadata_output_dir, "harmonized_matrix.csv")
            harmonized_df.to_csv(output_path, index=False)
            logger.info(f"Saved harmonized metadata to {output_path}")
        else:
            logger.error("Metadata validation failed, skipping harmonization")
    else:
        logger.warning(f"Metadata file not found at {metadata_path}")
    
    return subsampling_ratios

def ingest_and_report(
    dataset_ids: List[str],
    urls: Dict[str, str],
    metadata_path: str,
    raw_seq_dir: str = "data/raw-seq",
    metadata_output_dir: str = "data/metadata",
    sampling_report_path: str = "results/sampling_report.csv"
) -> None:
    """
    Run ingestion and generate sampling report in one go.
    """
    from src.pipelines.report import generate_sampling_report
    
    subsampling_ratios = process_ingestion(
        dataset_ids, urls, metadata_path, raw_seq_dir, metadata_output_dir
    )
    
    generate_sampling_report(subsampling_ratios, sampling_report_path)
    logger.info(f"Completed ingestion and generated sampling report at {sampling_report_path}")
