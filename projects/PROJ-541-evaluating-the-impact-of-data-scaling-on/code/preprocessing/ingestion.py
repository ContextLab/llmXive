import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import pandas as pd
import numpy as np
from dataclasses import dataclass, field, asdict
from datetime import datetime
from datasets import load_dataset
import yaml

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class RealWorldDataset:
    """
    Entity representing a real-world dataset with its metadata.
    Used to track source, size, cleaning statistics, and storage paths.
    """
    dataset_id: str
    source: str  # 'uciml' or 'openml'
    name: str
    version: Optional[str] = None
    size_mb: Optional[float] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    missing_rate: Optional[float] = None
    cleaned_path: Optional[str] = None
    raw_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"  # pending, downloaded, cleaned, failed
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RealWorldDataset':
        """Create instance from dictionary."""
        return cls(**data)

def load_dataset_config(config_path: str = "data/config/datasets.yaml") -> List[Dict[str, Any]]:
    """
    Load the list of datasets from the YAML configuration file.
    
    Args:
        config_path: Path to the datasets.yaml file.
        
    Returns:
        List of dataset configuration dictionaries.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If YAML parsing fails.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset configuration file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    if not isinstance(config, list):
        raise ValueError(f"Expected list of datasets in {config_path}, got {type(config)}")
    
    return config

def clean_dataset(df: pd.DataFrame, target_col: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean a dataset by handling missing values and ensuring numeric types.
    
    Args:
        df: Input DataFrame.
        target_col: Optional name of the target column to exclude from imputation.
        
    Returns:
        Tuple of (cleaned DataFrame, stats dict with missing_rate, rows_before, rows_after).
    """
    stats = {
        "rows_before": len(df),
        "cols_before": len(df.columns),
        "missing_rate": 0.0
    }
    
    # Calculate initial missing rate
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    stats["missing_rate"] = missing_cells / total_cells if total_cells > 0 else 0.0
    
    # Identify numeric columns for imputation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if target_col and target_col in df.columns:
        # Impute non-target numeric columns
        cols_to_impute = [c for c in numeric_cols if c != target_col]
        if cols_to_impute:
            df[cols_to_impute] = df[cols_to_impute].fillna(df[cols_to_impute].median())
    else:
        # Impute all numeric columns
        if numeric_cols:
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    
    # Drop rows with remaining missing values in non-numeric columns
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric_cols and df[non_numeric_cols].isnull().any().any():
        logger.warning(f"Dropping {df[non_numeric_cols].isnull().sum().sum()} rows with missing non-numeric values")
        df = df.dropna(subset=non_numeric_cols)
    
    stats["rows_after"] = len(df)
    stats["cols_after"] = len(df.columns)
    
    return df, stats

def process_real_world_dataset(dataset_id: str, source: str, target_col: Optional[str] = None) -> RealWorldDataset:
    """
    Download, clean, and process a real-world dataset.
    
    Args:
        dataset_id: The ID of the dataset (e.g., 'uciml/iris', 'openml/d/2').
        source: Source type ('uciml' or 'openml').
        target_col: Optional target column name.
        
    Returns:
        RealWorldDataset entity with updated metadata.
    """
    dataset = RealWorldDataset(
        dataset_id=dataset_id,
        source=source,
        name=dataset_id.split('/')[-1],
        status="pending"
    )
    
    try:
        logger.info(f"Downloading dataset: {dataset_id} from {source}")
        
        # Load dataset using HuggingFace datasets library
        ds = load_dataset(dataset_id)
        
        # Get the first split (usually 'train' or 'default')
        split_name = list(ds.keys())[0]
        df = ds[split_name].to_pandas()
        
        # Update metadata
        dataset.raw_path = f"data/raw/{dataset_id.replace('/', '_')}.csv"
        dataset.size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)
        
        # Save raw data
        os.makedirs(os.path.dirname(dataset.raw_path), exist_ok=True)
        df.to_csv(dataset.raw_path, index=False)
        
        # Clean dataset
        df_clean, clean_stats = clean_dataset(df, target_col)
        
        dataset.missing_rate = clean_stats["missing_rate"]
        dataset.status = "cleaned"
        
        # Save cleaned data
        clean_filename = f"{dataset_id.replace('/', '_')}_cleaned.csv"
        dataset.cleaned_path = f"data/scaled/{clean_filename}"
        os.makedirs(os.path.dirname(dataset.cleaned_path), exist_ok=True)
        df_clean.to_csv(dataset.cleaned_path, index=False)
        
        logger.info(f"Successfully processed {dataset_id}: {clean_stats['rows_after']} rows, missing_rate={clean_stats['missing_rate']:.4f}")
        
    except Exception as e:
        logger.error(f"Failed to process dataset {dataset_id}: {str(e)}")
        dataset.status = "failed"
        dataset.error_message = str(e)
    
    return dataset

def update_manifest(dataset: RealWorldDataset, manifest_path: str = "data/metadata/manifest.json") -> None:
    """
    Update the manifest file with dataset metadata.
    
    Args:
        dataset: RealWorldDataset entity to record.
        manifest_path: Path to the manifest JSON file.
    """
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    
    manifest[dataset.dataset_id] = dataset.to_dict()
    
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Updated manifest for {dataset.dataset_id}")

def get_cleaned_data_path(dataset_id: str, manifest_path: str = "data/metadata/manifest.json") -> Optional[str]:
    """
    Retrieve the cleaned data path for a dataset from the manifest.
    
    Args:
        dataset_id: The ID of the dataset.
        manifest_path: Path to the manifest JSON file.
        
    Returns:
        Path to cleaned data if found, None otherwise.
    """
    if not os.path.exists(manifest_path):
        return None
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    if dataset_id in manifest and manifest[dataset_id].get('status') == 'cleaned':
        return manifest[dataset_id].get('cleaned_path')
    
    return None

def run_ingestion_pipeline(config_path: str = "data/config/datasets.yaml") -> List[RealWorldDataset]:
    """
    Run the ingestion pipeline for all datasets in the configuration.
    
    Args:
        config_path: Path to datasets.yaml.
        
    Returns:
        List of RealWorldDataset entities with final status.
    """
    configs = load_dataset_config(config_path)
    results = []
    
    for cfg in configs:
        dataset_id = cfg['id']
        source = cfg.get('source', 'uciml')
        target_col = cfg.get('target_col')
        
        dataset = process_real_world_dataset(dataset_id, source, target_col)
        update_manifest(dataset)
        results.append(dataset)
        
        if dataset.status == 'failed':
            logger.warning(f"Skipping subsequent processing for {dataset_id} due to failure")
    
    return results