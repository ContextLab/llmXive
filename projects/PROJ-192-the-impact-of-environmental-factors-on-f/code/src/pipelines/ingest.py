import os
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import hashlib
import requests
import gzip
import shutil
from src.utils.memory import trigger_subsample, get_memory_status

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        SHA256 hex digest.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_raw_fastq(dataset_id: str, url: str, output_dir: str) -> str:
    """
    Download raw FASTQ file from a URL.
    
    Args:
        dataset_id: Identifier for the dataset.
        url: URL to download the FASTQ file.
        output_dir: Directory to save the file.
        
    Returns:
        Path to the downloaded file.
    """
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    file_name = f"{dataset_id}.fastq.gz"
    file_path = output_dir_path / file_name
    
    if file_path.exists():
        logger.info(f"File already exists: {file_path}")
        return str(file_path)
    
    logger.info(f"Downloading {url} to {file_path}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify checksum if available (simplified for this example)
        logger.info(f"Downloaded {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def validate_metadata_columns(metadata_df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that metadata DataFrame has required columns.
    
    Args:
        metadata_df: Metadata DataFrame.
        required_columns: List of required column names.
        
    Returns:
        True if all required columns are present.
    """
    missing = [col for col in required_columns if col not in metadata_df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def harmonize_metadata(metadata_df: pd.DataFrame) -> pd.DataFrame:
    """
    Harmonize metadata columns and values.
    
    Args:
        metadata_df: Raw metadata DataFrame.
        
    Returns:
        Harmonized metadata DataFrame.
    """
    # Example harmonization: standardize column names
    column_mapping = {
        'ph': 'pH',
        'nutrient_level': 'nutrients',
        'soil_moisture': 'moisture'
    }
    
    # Rename columns if they exist
    for old, new in column_mapping.items():
        if old in metadata_df.columns:
            metadata_df = metadata_df.rename(columns={old: new})
    
    # Standardize biome labels
    biome_mapping = {
        'temperate forest': 'Forest',
        'tropical forest': 'Forest',
        'grassland': 'Grassland',
        'desert': 'Desert'
    }
    
    if 'biome' in metadata_df.columns:
        metadata_df['biome'] = metadata_df['biome'].str.lower().map(biome_mapping).fillna(metadata_df['biome'])
    
    return metadata_df

def estimate_memory_usage(sample_count: int, read_depth: int) -> float:
    """
    Estimate memory usage in GB based on sample count and read depth.
    
    Args:
        sample_count: Number of samples.
        read_depth: Average read depth per sample.
        
    Returns:
        Estimated memory usage in GB.
    """
    # Simplified estimation: 1 GB per 100 samples with 1M reads
    estimated_gb = (sample_count * read_depth) / (100 * 1_000_000)
    return estimated_gb

def project_memory_and_subsample(sample_count: int, read_depth: int, max_ram_gb: float = 6.0) -> Tuple[int, bool]:
    """
    Project memory usage and trigger subsampling if necessary.
    
    Args:
        sample_count: Number of samples.
        read_depth: Average read depth per sample.
        max_ram_gb: Maximum allowed RAM in GB.
        
    Returns:
        Tuple of (subsampled_count, was_subsampling_triggered).
    """
    estimated_ram = estimate_memory_usage(sample_count, read_depth)
    
    if estimated_ram > max_ram_gb:
        logger.warning(f"Estimated memory ({estimated_ram:.2f} GB) exceeds limit ({max_ram_gb} GB). Triggering subsampling.")
        # Trigger subsampling logic
        trigger_subsample(estimated_ram, max_ram_gb)
        # For this example, we reduce sample count by 50%
        subsampled_count = int(sample_count * 0.5)
        return subsampled_count, True
    else:
        return sample_count, False

def process_ingestion(dataset_ids: List[str], urls: Dict[str, str], 
                     metadata_paths: List[str], output_base: str) -> Dict:
    """
    Process ingestion of multiple datasets.
    
    Args:
        dataset_ids: List of dataset identifiers.
        urls: Dictionary mapping dataset_id to URL.
        metadata_paths: List of metadata file paths.
        output_base: Base output directory.
        
    Returns:
        Dictionary with ingestion results.
    """
    results = {
        'downloaded_files': [],
        'metadata_files': [],
        'errors': []
    }
    
    raw_seq_dir = Path(output_base) / "raw-seq"
    metadata_dir = Path(output_base) / "metadata"
    raw_seq_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    for dataset_id, url in urls.items():
        try:
            file_path = download_raw_fastq(dataset_id, url, str(raw_seq_dir))
            results['downloaded_files'].append(file_path)
            
            # Calculate checksum
            checksum = calculate_sha256(file_path)
            logger.info(f"Checksum for {dataset_id}: {checksum}")
        except Exception as e:
            logger.error(f"Error processing {dataset_id}: {e}")
            results['errors'].append({'dataset_id': dataset_id, 'error': str(e)})
    
    for meta_path in metadata_paths:
        try:
            # Copy or process metadata files
            # For simplicity, we assume they are already in the correct format
            results['metadata_files'].append(meta_path)
        except Exception as e:
            logger.error(f"Error processing metadata {meta_path}: {e}")
            results['errors'].append({'file': meta_path, 'error': str(e)})
    
    return results

def ingest_and_report(dataset_ids: List[str], urls: Dict[str, str], 
                     metadata_paths: List[str], output_base: str) -> pd.DataFrame:
    """
    Main ingestion function that processes data and returns a harmonized metadata DataFrame.
    
    Args:
        dataset_ids: List of dataset identifiers.
        urls: Dictionary mapping dataset_id to URL.
        metadata_paths: List of metadata file paths.
        output_base: Base output directory.
        
    Returns:
        Harmonized metadata DataFrame.
    """
    # Process ingestion
    ingestion_results = process_ingestion(dataset_ids, urls, metadata_paths, output_base)
    
    if ingestion_results['errors']:
        logger.warning(f"Ingestion completed with {len(ingestion_results['errors'])} errors.")
    
    # Load and harmonize metadata
    all_metadata = []
    for meta_path in ingestion_results['metadata_files']:
        try:
            df = pd.read_csv(meta_path)
            # Validate required columns
            required = ['sample_id', 'pH', 'nutrients', 'biome']
            if validate_metadata_columns(df, required):
                harmonized = harmonize_metadata(df)
                all_metadata.append(harmonized)
            else:
                logger.warning(f"Skipping {meta_path} due to missing columns.")
        except Exception as e:
            logger.error(f"Failed to load metadata {meta_path}: {e}")
    
    if not all_metadata:
        raise ValueError("No valid metadata files were loaded.")
    
    combined_metadata = pd.concat(all_metadata, ignore_index=True)
    
    # Project memory and subsample if needed
    sample_count = len(combined_metadata)
    # Assume average read depth of 100,000 for estimation
    read_depth = 100_000
    subsampled_count, was_subsampling = project_memory_and_subsample(sample_count, read_depth)
    
    if was_subsampling:
        # In a real scenario, we would filter the DataFrame
        # For this example, we just log
        logger.info(f"Subsampling triggered: {sample_count} -> {subsampled_count} samples.")
        # combined_metadata = combined_metadata.head(subsampled_count)
    
    # Save harmonized metadata
    output_metadata_path = Path(output_base) / "harmonized_matrix.csv"
    combined_metadata.to_csv(output_metadata_path, index=False)
    logger.info(f"Saved harmonized metadata to {output_metadata_path}")
    
    return combined_metadata