import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import pandas as pd
import numpy as np
import yaml
from datasets import load_dataset

logger = logging.getLogger(__name__)

class RealWorldDataset:
    """Entity representing a loaded real-world dataset."""
    def __init__(self, dataset_id: str, source: str, data: pd.DataFrame, metadata: Dict[str, Any]):
        self.dataset_id = dataset_id
        self.source = source
        self.data = data
        self.metadata = metadata

def load_dataset_config(config_path: Path) -> Dict[str, Any]:
    """Load dataset configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def download_dataset(dataset_entry: Dict[str, Any]) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Download dataset based on configuration.
    Supports UCI (via datasets library) and OpenML (via datasets library).
    """
    dataset_id = dataset_entry.get("id")
    source = dataset_entry.get("source")
    
    try:
        # Use HuggingFace datasets library for both UCI and OpenML
        # This handles the actual download and caching
        ds = load_dataset(dataset_id)
        
        # Handle different split structures
        if "train" in ds:
            df = ds["train"].to_pandas()
        elif "test" in ds:
            df = ds["test"].to_pandas()
        else:
            # Fallback: take first available split
            first_split = next(iter(ds))
            df = ds[first_split].to_pandas()
        
        return df, "success"
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_id}: {e}")
        return None, str(e)

def clean_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    """
    Clean dataset: handle missing values, convert types.
    Returns cleaned DataFrame and missing rate.
    """
    if df is None or df.empty:
        return pd.DataFrame(), 0.0
    
    # Calculate initial missing rate
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    missing_rate = missing_cells / total_cells if total_cells > 0 else 0.0
    
    # Drop rows with all NaN
    df = df.dropna(how='all')
    
    # Impute remaining missing values with median for numeric, mode for categorical
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns
    
    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    
    for col in categorical_cols:
        if df[col].isnull().any():
            mode_val = df[col].mode()[0] if not df[col].mode().empty else "Unknown"
            df[col] = df[col].fillna(mode_val)
    
    return df, missing_rate

def process_real_world_dataset(dataset_entry: Dict[str, Any]) -> Tuple[Optional[RealWorldDataset], Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Full pipeline: download, clean, and wrap dataset.
    Returns (DatasetObject, CleanedDF, Metadata)
    """
    dataset_id = dataset_entry.get("id")
    source = dataset_entry.get("source")
    
    # Download
    df, status = download_dataset(dataset_entry)
    
    if status != "success" or df is None:
        logger.error(f"Download failed for {dataset_id}")
        return None, None, {"status": "failed", "error": status}
    
    # Clean
    clean_df, missing_rate = clean_dataset(df)
    
    metadata = {
        "source": source,
        "original_size": len(df),
        "cleaned_size": len(clean_df),
        "missing_rate": missing_rate,
        "status": "success"
    }
    
    dataset_obj = RealWorldDataset(
        dataset_id=dataset_id,
        source=source,
        data=clean_df,
        metadata=metadata
    )
    
    return dataset_obj, clean_df, metadata

def get_cleaned_data_path(dataset_id: str) -> Path:
    """Generate path for cleaned dataset."""
    safe_id = dataset_id.replace("/", "_").replace(":", "_")
    return Path("data/raw") / f"{safe_id}_cleaned.csv"

def update_manifest(manifest: List[Dict[str, Any]], entry: Dict[str, Any]):
    """Update manifest list with a new entry."""
    # Remove existing entry with same ID if present
    manifest = [e for e in manifest if e.get("id") != entry.get("id")]
    manifest.append(entry)
    return manifest

def run_ingestion_pipeline(config_path: Path = Path("data/config/datasets.yaml")) -> List[Dict[str, Any]]:
    """
    Run full ingestion pipeline for all datasets in config.
    Returns list of processed entries for manifest.
    """
    config = load_dataset_config(config_path)
    datasets = config.get("datasets", [])
    manifest = []
    
    for ds in datasets:
        try:
            _, _, meta = process_real_world_dataset(ds)
            entry = {
                "id": ds.get("id"),
                "source": ds.get("source"),
                "expected_size": ds.get("expected_size"),
                "actual_size": meta.get("cleaned_size", 0),
                "missing_rate": meta.get("missing_rate", 0.0),
                "status": meta.get("status", "unknown")
            }
            manifest.append(entry)
        except Exception as e:
            logger.error(f"Pipeline failed for {ds.get('id')}: {e}")
            manifest.append({
                "id": ds.get("id"),
                "status": "failed",
                "error": str(e)
            })
    
    return manifest
