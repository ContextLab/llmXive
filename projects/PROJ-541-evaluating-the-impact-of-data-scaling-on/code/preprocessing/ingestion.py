"""
Real-world dataset ingestion pipeline.
Handles loading, cleaning, and metadata logging for public datasets.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import time
import itertools
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union, Iterator

import pandas as pd
import yaml

# Import streaming and sampling utilities if available, otherwise fallback to standard load
try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None  # type: ignore

from simulation.logger import setup_logger

# Ensure output directory exists
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logger("ingestion")


@dataclass
class RealWorldDataset:
    """Entity representing a loaded real-world dataset with metadata."""
    dataset_id: str
    source_url: str
    data: pd.DataFrame
    row_count: int
    checksum: str
    status: str = "pending"
    error_message: Optional[str] = None
    loaded_at: str = ""

    def __post_init__(self):
        if not self.loaded_at:
            self.loaded_at = time.strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging, excluding the DataFrame."""
        d = asdict(self)
        d['data'] = "DataFrame Object (not serialized)"
        return d


def load_dataset_config(config_path: str = "data/config/datasets.yaml") -> List[Dict[str, Any]]:
    """
    Load the list of verified datasets from the YAML configuration file.
    
    Args:
        config_path: Path to the datasets.yaml file.
        
    Returns:
        List of dataset configuration dictionaries.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset configuration file not found: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if not config or 'datasets' not in config:
        logger.warning("No 'datasets' key found in configuration. Returning empty list.")
        return []
    
    return config['datasets']


def download_dataset(dataset_id: str, config: Dict[str, Any], streaming: bool = True) -> pd.DataFrame:
    """
    Download a dataset using the Hugging Face datasets library.
    
    Args:
        dataset_id: The Hugging Face dataset ID.
        config: Configuration dictionary for the dataset (splits, etc.).
        streaming: If True, stream the data; otherwise load fully.
        
    Returns:
        A pandas DataFrame containing the dataset.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    if load_dataset is None:
        raise RuntimeError("The 'datasets' library is not installed. Cannot fetch real data.")
    
    try:
        # Determine split to load. Default to 'train' if not specified or if split list is empty.
        splits = config.get('splits', ['train'])
        split = splits[0] if splits else 'train'
        
        logger.info(f"Fetching dataset: {dataset_id} (split: {split}, streaming: {streaming})")
        
        ds = load_dataset(dataset_id, split=split, streaming=streaming)
        
        if streaming:
            # Convert streaming dataset to dataframe by materializing a sample or full set
            # For T027c, we ingest available datasets. We will stream and convert to DF.
            # If the dataset is huge, we might need to sample, but the task says "Ingest Available".
            # We assume the datasets in config are manageable or we stream to a DF.
            # Note: pd.DataFrame(list(ds)) works for streaming if we iterate.
            df = pd.DataFrame(ds)
        else:
            df = ds.to_pandas()
            
        return df
        
    except Exception as e:
        # Fail loudly as per T025
        raise RuntimeError(f"Failed to download dataset '{dataset_id}': {str(e)}") from e


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform basic cleaning on the dataset: drop rows with all NaN, handle simple types.
    
    Args:
        df: The raw DataFrame.
        
    Returns:
        Cleaned DataFrame.
    """
    if df.empty:
        return df
    
    # Drop rows where ALL values are NaN
    df_clean = df.dropna(how='all')
    
    # Optional: Drop columns that are all NaN
    df_clean = df_clean.dropna(axis=1, how='all')
    
    return df_clean


def compute_checksum(df: pd.DataFrame) -> str:
    """
    Compute a simple checksum of the DataFrame content.
    """
    if df.empty:
        return hashlib.md5(b"empty").hexdigest()
    
    # Convert to a string representation (sorted to ensure consistency if order varies)
    # Using a subset of columns for checksum if too large, but for logging we do full.
    # For robustness, we hash the string representation of the values.
    csv_buffer = df.to_csv(index=False)
    return hashlib.md5(csv_buffer.encode('utf-8')).hexdigest()


def update_manifest(log_entries: List[RealWorldDataset], output_path: str = "results/real_world_ingestion_log.csv"):
    """
    Append or overwrite the ingestion log CSV.
    
    Args:
        log_entries: List of RealWorldDataset objects.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['dataset_id', 'source_url', 'status', 'row_count', 'checksum']
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for entry in log_entries:
            writer.writerow({
                'dataset_id': entry.dataset_id,
                'source_url': entry.source_url,
                'status': entry.status,
                'row_count': entry.row_count,
                'checksum': entry.checksum
            })
    
    logger.info(f"Ingestion log written to {output_path}")


def process_real_world_dataset(dataset_config: Dict[str, Any]) -> RealWorldDataset:
    """
    Process a single dataset configuration: download, clean, and log.
    
    Args:
        dataset_config: Dictionary containing dataset metadata and ID.
        
    Returns:
        RealWorldDataset object with status and metadata.
    """
    dataset_id = dataset_config.get('id', 'unknown')
    source_url = dataset_config.get('source', 'unknown')
    description = dataset_config.get('description', '')
    
    logger.info(f"Processing dataset: {dataset_id}")
    
    try:
        # Download
        df = download_dataset(dataset_id, dataset_config, streaming=True)
        
        # Clean
        df_clean = clean_dataset(df)
        
        # Compute stats
        row_count = len(df_clean)
        checksum = compute_checksum(df_clean)
        
        entry = RealWorldDataset(
            dataset_id=dataset_id,
            source_url=source_url,
            data=df_clean,
            row_count=row_count,
            checksum=checksum,
            status="success"
        )
        
        logger.info(f"Successfully ingested {dataset_id}: {row_count} rows")
        return entry
        
    except Exception as e:
        logger.error(f"Failed to ingest {dataset_id}: {str(e)}")
        return RealWorldDataset(
            dataset_id=dataset_id,
            source_url=source_url,
            data=pd.DataFrame(),
            row_count=0,
            checksum="",
            status="failed",
            error_message=str(e)
        )


def run_ingestion_pipeline(config_path: str = "data/config/datasets.yaml", output_path: str = "results/real_world_ingestion_log.csv") -> List[RealWorldDataset]:
    """
    Main entry point for the ingestion pipeline.
    Reads the config, processes each dataset, and writes the log.
    
    Args:
        config_path: Path to the datasets.yaml config.
        output_path: Path to write the ingestion log CSV.
        
    Returns:
        List of RealWorldDataset objects.
    """
    logger.info("Starting real-world dataset ingestion pipeline.")
    
    try:
        configs = load_dataset_config(config_path)
    except FileNotFoundError as e:
        logger.error(f"Configuration file missing: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return []
    
    if not configs:
        logger.warning("No datasets found in configuration. Exiting.")
        return []
    
    results = []
    for config in configs:
        result = process_real_world_dataset(config)
        results.append(result)
    
    update_manifest(results, output_path)
    
    success_count = sum(1 for r in results if r.status == "success")
    logger.info(f"Ingestion pipeline complete. Success: {success_count}/{len(results)}")
    
    return results


def validate_dataset_availability(config_path: str = "data/config/datasets.yaml") -> Tuple[int, int]:
    """
    Helper to validate availability (used by T027a). 
    Returns (available_count, total_count).
    """
    try:
        configs = load_dataset_config(config_path)
    except Exception:
        return 0, 0
    
    if not configs:
        return 0, 0
    
    available = 0
    for config in configs:
        try:
            # Attempt a lightweight fetch (streaming metadata)
            # We don't download full data here, just check if it loads
            if load_dataset:
                ds = load_dataset(config['id'], split=config['splits'][0] if config.get('splits') else 'train', streaming=True)
                # If we get here without exception, it's available
                available += 1
            else:
                logger.warning("datasets library not installed, skipping validation")
                return 0, len(configs)
        except Exception:
            continue
    
    return available, len(configs)
