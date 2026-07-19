"""
Ingestion module for real-world datasets.
Handles downloading, cleaning, and preprocessing of external data.
"""
import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union, Iterator

import pandas as pd
import numpy as np
from datasets import load_dataset
from sklearn.impute import SimpleImputer

from simulation.logger import setup_logger

# Configure logger for this module
logger = setup_logger("ingestion", batch_id="ingestion")

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "cleaned"
CONFIG_DIR = DATA_DIR / "config"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class RealWorldDataset:
    """Entity representing a real-world dataset with metadata."""
    
    def __init__(
        self,
        source: str,
        dataset_id: str,
        size: Optional[int] = None,
        missing_rate: Optional[float] = None,
        status: str = "pending",
        path: Optional[Path] = None
    ):
        self.source = source
        self.dataset_id = dataset_id
        self.size = size
        self.missing_rate = missing_rate
        self.status = status
        self.path = path
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "dataset_id": self.dataset_id,
            "size": self.size,
            "missing_rate": self.missing_rate,
            "status": self.status,
            "path": str(self.path) if self.path else None
        }
    
    def __repr__(self):
        return f"RealWorldDataset(source={self.source}, id={self.dataset_id}, status={self.status})"


def load_dataset_config(config_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load dataset configuration from YAML file.
    
    Args:
        config_path: Path to datasets.yaml. Defaults to data/config/datasets.yaml.
        
    Returns:
        List of dataset configuration dictionaries.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If config is empty or invalid.
    """
    if config_path is None:
        config_path = CONFIG_DIR / "datasets.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Dataset config not found: {config_path}")
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if not config or 'datasets' not in config:
        raise ValueError(f"Invalid config format in {config_path}: missing 'datasets' key")
    
    return config['datasets']


def download_dataset(dataset_config: Dict[str, Any]) -> RealWorldDataset:
    """
    Download a dataset using the 'datasets' library or direct URL.
    
    Args:
        dataset_config: Dictionary containing 'id', 'source', and optional parameters.
        
    Returns:
        RealWorldDataset object with status 'downloaded'.
        
    Raises:
        RuntimeError: If download fails.
    """
    dataset_id = dataset_config.get('id')
    source = dataset_config.get('source', 'huggingface')
    split = dataset_config.get('split', 'train')
    
    if not dataset_id:
        raise ValueError("Dataset config must contain 'id'")
    
    logger.info(f"Downloading dataset: {dataset_id} from {source}")
    
    try:
        if source == 'huggingface':
            # Use streaming to avoid loading full dataset into memory
            dataset = load_dataset(dataset_id, split=split, streaming=True)
            # Materialize a sample if needed, or just get the first chunk for metadata
            # For metadata, we can peek at features
            features = dataset.features
            num_columns = len(features)
            logger.info(f"Dataset features: {list(features.keys())}")
            
            # We need to get the size. With streaming, we can't easily get count without iterating.
            # For now, we'll mark size as unknown or estimate if we iterate a bit.
            # To be safe and fast, we'll just store the config and mark as downloaded.
            # If we need size, we'd need to stream through it which might be slow.
            # Let's assume we process it later or we just don't know size upfront.
            size = None 
            
            # Save a small sample or the dataset object reference?
            # Since we can't save a streaming object directly, we'll save the config and mark it.
            # Actual data processing happens in clean_dataset.
            local_path = RAW_DIR / f"{dataset_id.replace('/', '_')}.parquet"
            # We can't save streaming directly to parquet without iteration.
            # We will iterate a small sample or the whole thing if small.
            # For robustness, we'll just note it's available and let clean_dataset handle materialization.
            # But we need a path. Let's create a placeholder or process a sample.
            # Strategy: Stream first 1000 rows to verify and save as a sample, then full processing later.
            sample_size = 1000
            df_sample = pd.DataFrame(next(iter(dataset)).take(range(min(sample_size, len(dataset)))))
            df_sample.to_parquet(local_path, index=False)
            size = len(df_sample) # Approximate for now, or we could stream full.
            
        elif source == 'url':
            url = dataset_config.get('url')
            if not url:
                raise ValueError("URL source requires 'url' in config")
            # Download via pandas
            try:
                df = pd.read_csv(url)
                local_path = RAW_DIR / f"{dataset_id}.csv"
                df.to_csv(local_path, index=False)
                size = len(df)
            except Exception as e:
                raise RuntimeError(f"Failed to download from URL {url}: {e}")
        else:
            raise ValueError(f"Unsupported source: {source}")
        
        dataset_obj = RealWorldDataset(
            source=source,
            dataset_id=dataset_id,
            size=size,
            status="downloaded",
            path=local_path
        )
        logger.info(f"Successfully downloaded {dataset_id}, size: {size}")
        return dataset_obj
        
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_id}: {e}")
        raise RuntimeError(f"Data fetch failed for {dataset_id}: {e}") from e


def clean_dataset(
    dataset_obj: RealWorldDataset,
    strategy: str = "drop",
    numerical_strategy: str = "mean",
    categorical_strategy: str = "mode"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean and preprocess a dataset.
    
    Args:
        dataset_obj: RealWorldDataset object.
        strategy: How to handle missing values ('drop', 'impute').
        numerical_strategy: Imputation strategy for numerical columns ('mean', 'median', 'most_frequent').
        categorical_strategy: Imputation strategy for categorical columns.
        
    Returns:
        Tuple of (cleaned DataFrame, metadata dict).
        
    Raises:
        FileNotFoundError: If dataset file not found.
    """
    if dataset_obj.path is None or not dataset_obj.path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_obj.path}")
    
    logger.info(f"Cleaning dataset: {dataset_obj.dataset_id}")
    
    # Load data
    ext = dataset_obj.path.suffix
    if ext == '.parquet':
        df = pd.read_parquet(dataset_obj.path)
    elif ext == '.csv':
        df = pd.read_csv(dataset_obj.path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    
    original_shape = df.shape
    missing_before = df.isnull().sum().sum()
    
    # Identify numerical and categorical columns
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    cleaned_metadata = {
        "original_shape": original_shape,
        "missing_before": int(missing_before),
        "numerical_columns": numerical_cols,
        "categorical_columns": categorical_cols,
        "cleaned_shape": None,
        "missing_after": None,
        "strategy": strategy
    }
    
    if strategy == "drop":
        # Drop rows with any missing values
        df_clean = df.dropna()
    elif strategy == "impute":
        df_clean = df.copy()
        
        # Impute numerical
        if numerical_cols:
            imputer_num = SimpleImputer(strategy=numerical_strategy)
            df_clean[numerical_cols] = imputer_num.fit_transform(df[numerical_cols])
        
        # Impute categorical
        if categorical_cols:
            imputer_cat = SimpleImputer(strategy=categorical_strategy)
            df_clean[categorical_cols] = imputer_cat.fit_transform(df[categorical_cols])
    else:
        raise ValueError(f"Unknown cleaning strategy: {strategy}")
    
    missing_after = df_clean.isnull().sum().sum()
    cleaned_metadata["cleaned_shape"] = list(df_clean.shape)
    cleaned_metadata["missing_after"] = int(missing_after)
    
    # Save cleaned data
    output_filename = dataset_obj.dataset_id.replace('/', '_') + "_cleaned.parquet"
    output_path = CLEAN_DIR / output_filename
    df_clean.to_parquet(output_path, index=False)
    
    logger.info(f"Cleaned dataset saved to {output_path}")
    logger.info(f"Rows dropped: {original_shape[0] - df_clean.shape[0]}, Missing removed: {missing_before - missing_after}")
    
    return df_clean, cleaned_metadata


def process_real_world_dataset(dataset_config: Dict[str, Any]) -> RealWorldDataset:
    """
    Full pipeline: download and clean a dataset.
    
    Args:
        dataset_config: Configuration dictionary.
        
    Returns:
        Updated RealWorldDataset object.
    """
    # Download
    dataset_obj = download_dataset(dataset_config)
    
    # Clean
    try:
        df, metadata = clean_dataset(dataset_obj)
        dataset_obj.status = "cleaned"
        dataset_obj.missing_rate = metadata.get("missing_before", 0) / (metadata.get("original_shape", [0, 0])[0] or 1)
    except Exception as e:
        logger.error(f"Failed to clean dataset {dataset_config.get('id')}: {e}")
        dataset_obj.status = "failed"
        raise
    
    return dataset_obj


def get_cleaned_data_path(dataset_id: str) -> Path:
    """Get the path to a cleaned dataset."""
    filename = dataset_id.replace('/', '_') + "_cleaned.parquet"
    return CLEAN_DIR / filename


def update_manifest(manifest_path: Path, dataset_obj: RealWorldDataset) -> None:
    """Update the manifest file with dataset information."""
    if not manifest_path.parent.exists():
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
    manifest = []
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    
    # Remove existing entry for this dataset_id if present
    manifest = [d for d in manifest if d.get('dataset_id') != dataset_obj.dataset_id]
    
    manifest.append(dataset_obj.to_dict())
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Updated manifest at {manifest_path}")


def run_ingestion_pipeline(config_path: Optional[Path] = None, manifest_path: Optional[Path] = None) -> List[RealWorldDataset]:
    """
    Run the full ingestion pipeline for all datasets in config.
    
    Args:
        config_path: Path to datasets.yaml.
        manifest_path: Path to manifest.json. Defaults to data/manifest.json.
        
    Returns:
        List of processed RealWorldDataset objects.
    """
    if manifest_path is None:
        manifest_path = DATA_DIR / "manifest.json"
        
    configs = load_dataset_config(config_path)
    results = []
    
    for cfg in configs:
        try:
            logger.info(f"Processing dataset: {cfg.get('id')}")
            dataset_obj = process_real_world_dataset(cfg)
            update_manifest(manifest_path, dataset_obj)
            results.append(dataset_obj)
        except Exception as e:
            logger.warning(f"Failed to process dataset {cfg.get('id')}: {e}")
            # Create a failed object for the manifest
            failed_obj = RealWorldDataset(
                source=cfg.get('source', 'unknown'),
                dataset_id=cfg.get('id', 'unknown'),
                status="failed"
            )
            update_manifest(manifest_path, failed_obj)
            results.append(failed_obj)
    
    return results
