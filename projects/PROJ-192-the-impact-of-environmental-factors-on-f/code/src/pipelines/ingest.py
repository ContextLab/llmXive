import os
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import hashlib
import json
import requests
from urllib.parse import urljoin

from src.utils.memory import get_memory_status, trigger_subsample, is_subsampling_active, get_subsample_ratio, get_subsample_indices
from src.config.constants import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
REQUIRED_METADATA_COLUMNS = ['sample_id', 'pH', 'biome', 'latitude', 'longitude']
OPTIONAL_NUMERIC_COLUMNS = ['nutrients', 'moisture', 'temperature', 'organic_matter']

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_raw_fastq(dataset_id: str, output_dir: str, url: str) -> Tuple[str, str]:
    """Download raw FASTQ file from SRA/IMG/M."""
    output_path = Path(output_dir) / f"{dataset_id}.fastq.gz"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        checksum = calculate_sha256(str(output_path))
        logger.info(f"Downloaded {dataset_id} successfully. Checksum: {checksum}")
        return str(output_path), checksum
    except Exception as e:
        logger.error(f"Failed to download {dataset_id}: {e}")
        raise

def validate_metadata_columns(df: pd.DataFrame) -> bool:
    """Validate that required columns exist in metadata."""
    missing = [col for col in REQUIRED_METADATA_COLUMNS if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def harmonize_biome_labels(df: pd.DataFrame, mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """Standardize biome labels using ontology mapping."""
    if mapping is None:
        # Default mapping from plan.md requirements
        mapping = {
            'temperate forest': 'Forest',
            'tropical forest': 'Forest',
            'boreal forest': 'Forest',
            'grassland': 'Grassland',
            'savanna': 'Grassland',
            'desert': 'Desert',
            'wetland': 'Wetland',
            'agricultural': 'Agricultural',
            'urban': 'Urban',
            'forest': 'Forest',
            'grasslands': 'Grassland',
            'deserts': 'Desert'
        }
    
    df['biome'] = df['biome'].str.strip().str.lower().map(
        lambda x: mapping.get(x, x.capitalize() if isinstance(x, str) else x)
    )
    return df

def harmonize_metadata(df: pd.DataFrame, config: Optional[Dict] = None) -> pd.DataFrame:
    """
    Merge and clean metadata to create the Environmental Matrix.
    
    This function:
    1. Validates required columns
    2. Harmonizes biome labels using ontology mapping
    3. Handles missing values (marks for later imputation)
    4. Ensures numeric columns are properly typed
    5. Outputs the harmonized matrix
    """
    logger.info("Starting metadata harmonization...")
    
    # Make a copy to avoid modifying original
    df_harmonized = df.copy()
    
    # Validate required columns
    if not validate_metadata_columns(df_harmonized):
        raise ValueError("Metadata validation failed - missing required columns")
    
    # Harmonize biome labels (T014)
    df_harmonized = harmonize_biome_labels(df_harmonized)
    
    # Ensure sample_id is string and unique
    df_harmonized['sample_id'] = df_harmonized['sample_id'].astype(str)
    if df_harmonized['sample_id'].duplicated().any():
        logger.warning("Duplicate sample_ids found. Keeping first occurrence.")
        df_harmonized = df_harmonized.drop_duplicates(subset=['sample_id'], keep='first')
    
    # Identify and convert numeric columns
    numeric_cols = REQUIRED_METADATA_COLUMNS + OPTIONAL_NUMERIC_COLUMNS
    for col in numeric_cols:
        if col in df_harmonized.columns:
            # Convert to numeric, coercing errors to NaN
            df_harmonized[col] = pd.to_numeric(df_harmonized[col], errors='coerce')
    
    # Sort by sample_id for consistent output
    df_harmonized = df_harmonized.sort_values('sample_id').reset_index(drop=True)
    
    logger.info(f"Harmonized metadata: {len(df_harmonized)} samples, {len(df_harmonized.columns)} columns")
    logger.info(f"Columns: {list(df_harmonized.columns)}")
    
    return df_harmonized

def estimate_memory_usage(df: pd.DataFrame) -> float:
    """Estimate RAM usage in GB for processing the metadata."""
    # Rough estimate: 1 row ~ 1KB for metadata
    estimated_mb = len(df) * 1.5  # 1.5 MB per 1000 rows
    return estimated_mb / 1024  # Convert to GB

def project_memory_and_subsample(df: pd.DataFrame, max_ram_gb: float = 6.0) -> Tuple[pd.DataFrame, bool]:
    """
    Project memory usage and trigger subsampling if needed.
    
    Returns:
        Tuple of (processed_df, was_subsampled)
    """
    estimated_ram = estimate_memory_usage(df)
    logger.info(f"Estimated memory usage: {estimated_ram:.2f} GB (limit: {max_ram_gb} GB)")
    
    if estimated_ram > max_ram_gb:
        logger.warning("Memory projection exceeded limit. Triggering subsampling.")
        # For metadata, we typically don't subsample rows but rather note the issue
        # In real implementation, this might filter datasets or samples
        trigger_subsample()
        return df, True
    
    return df, False

def process_ingestion(metadata_path: str, output_dir: str, config: Optional[Dict] = None) -> str:
    """
    Process raw metadata file and output harmonized matrix.
    
    Args:
        metadata_path: Path to raw metadata file (CSV/TSV)
        output_dir: Directory to write harmonized matrix
        config: Optional configuration dictionary
    
    Returns:
        Path to the harmonized matrix file
    """
    logger.info(f"Processing metadata from: {metadata_path}")
    
    # Load metadata
    if metadata_path.endswith('.tsv'):
        df = pd.read_csv(metadata_path, sep='\t')
    else:
        df = pd.read_csv(metadata_path)
    
    logger.info(f"Loaded {len(df)} rows from {metadata_path}")
    
    # Project memory and subsample if needed
    df, was_subsampled = project_memory_and_subsample(df)
    
    # Harmonize metadata
    df_harmonized = harmonize_metadata(df, config)
    
    # Create output directory
    output_path = Path(output_dir) / "harmonized_matrix.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save harmonized matrix
    df_harmonized.to_csv(output_path, index=False)
    logger.info(f"Saved harmonized matrix to: {output_path}")
    
    return str(output_path)

def ingest_and_report(metadata_sources: List[Dict], output_dir: str, config: Optional[Dict] = None) -> Dict:
    """
    Main entry point for data ingestion pipeline.
    
    Args:
        metadata_sources: List of dicts with 'dataset_id', 'metadata_url', 'fastq_url'
        output_dir: Base output directory
        config: Configuration dictionary
    
    Returns:
        Dictionary with ingestion results
    """
    logger.info("Starting full ingestion pipeline...")
    
    results = {
        'datasets_processed': 0,
        'datasets_failed': 0,
        'total_samples': 0,
        'harmonized_matrix_path': None,
        'checksums': {}
    }
    
    all_metadata = []
    
    for source in metadata_sources:
        dataset_id = source['dataset_id']
        try:
            # Download metadata
            metadata_url = source.get('metadata_url')
            if metadata_url:
                # For this implementation, we assume metadata is already available locally
                # In real implementation, this would download from metadata_url
                metadata_path = f"data/raw-seq/{dataset_id}_metadata.csv"
                if not os.path.exists(metadata_path):
                    # Fallback: create a minimal metadata file for testing
                    logger.warning(f"Metadata file not found for {dataset_id}. Skipping.")
                    results['datasets_failed'] += 1
                    continue
                
                df = pd.read_csv(metadata_path)
                all_metadata.append(df)
                results['datasets_processed'] += 1
                results['total_samples'] += len(df)
                
                # Calculate checksum
                checksum = calculate_sha256(metadata_path)
                results['checksums'][dataset_id] = checksum
                
        except Exception as e:
            logger.error(f"Failed to process {dataset_id}: {e}")
            results['datasets_failed'] += 1
    
    if not all_metadata:
        raise ValueError("No valid metadata files found. Cannot proceed.")
    
    # Concatenate all metadata
    combined_df = pd.concat(all_metadata, ignore_index=True)
    logger.info(f"Combined metadata: {len(combined_df)} total samples")
    
    # Process and harmonize
    output_path = process_ingestion_from_df(combined_df, output_dir, config)
    results['harmonized_matrix_path'] = output_path
    
    logger.info(f"Ingestion complete. Processed {results['datasets_processed']} datasets, "
               f"failed {results['datasets_failed']}. Total samples: {results['total_samples']}")
    
    return results

def process_ingestion_from_df(df: pd.DataFrame, output_dir: str, config: Optional[Dict] = None) -> str:
    """
    Process metadata from a DataFrame and output harmonized matrix.
    
    Args:
        df: DataFrame containing raw metadata
        output_dir: Directory to write harmonized matrix
        config: Optional configuration dictionary
    
    Returns:
        Path to the harmonized matrix file
    """
    logger.info("Processing metadata from DataFrame...")
    
    # Project memory and subsample if needed
    df, was_subsampled = project_memory_and_subsample(df)
    
    # Harmonize metadata
    df_harmonized = harmonize_metadata(df, config)
    
    # Create output directory
    output_path = Path(output_dir) / "harmonized_matrix.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save harmonized matrix
    df_harmonized.to_csv(output_path, index=False)
    logger.info(f"Saved harmonized matrix to: {output_path}")
    
    return str(output_path)

# Helper function for T013d specific workflow
def load_and_harmonize_metadata(raw_metadata_path: str, output_dir: str) -> str:
    """
    Load raw metadata from file and output harmonized matrix.
    
    This is the primary function for T013d implementation.
    """
    logger.info(f"Loading raw metadata from: {raw_metadata_path}")
    
    if not os.path.exists(raw_metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {raw_metadata_path}")
    
    # Determine separator
    with open(raw_metadata_path, 'r') as f:
        first_line = f.readline()
        if '\t' in first_line:
            df = pd.read_csv(raw_metadata_path, sep='\t')
        else:
            df = pd.read_csv(raw_metadata_path)
    
    logger.info(f"Loaded {len(df)} rows")
    
    # Process and save
    return process_ingestion_from_df(df, output_dir)
