import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import pandas as pd
import yaml
from datasets import load_dataset

logger = logging.getLogger(__name__)

class RealWorldDataset:
    def __init__(self, id: str, source: str, expected_size: int, description: str, type: str):
        self.id = id
        self.source = source
        self.expected_size = expected_size
        self.description = description
        self.type = type
        self.data: Optional[pd.DataFrame] = None
        self.clean_data: Optional[pd.DataFrame] = None

def load_dataset_config(config_path: str = "data/config/datasets.yaml") -> List[Dict[str, Any]]:
    """Load dataset configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('datasets', [])

def download_dataset(dataset_id: str) -> pd.DataFrame:
    """
    Download a dataset from the configured source.
    Supports UCI (via datasets library) and OpenML.
    """
    try:
        # Handle UCI datasets
        if dataset_id.startswith("uciml/"):
            dataset_name = dataset_id.replace("uciml/", "")
            # Map some common UCI names to datasets library names
            name_map = {
                "iris": "iris",
                "wine": "wine",
                "breast-cancer-wisconsin": "breast_cancer",
                "heart-statlog": "statlog_heart",
                "ionosphere": "ionosphere",
                "credit-a": "credit_a",
                "credit-g": "credit_g",
                "hepatitis": "hepatitis",
                "horse-colic": "horse_colic"
            }
            ds_name = name_map.get(dataset_name, dataset_name)
            ds = load_dataset(ds_name, split="train")
            return ds.to_pandas()
        
        # Handle OpenML datasets
        elif dataset_id.startswith("openml/d/"):
            openml_id = dataset_id.replace("openml/d/", "")
            ds = load_dataset("openml", dataset_id=int(openml_id), split="train")
            return ds.to_pandas()
        
        else:
            raise ValueError(f"Unknown dataset format: {dataset_id}")
            
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_id}: {str(e)}")
        raise

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean dataset: handle missing values, remove non-numeric columns if needed.
    For this implementation, we'll drop rows with missing values for simplicity.
    """
    logger.info(f"Cleaning dataset with shape {df.shape}")
    
    # Drop rows with missing values
    df_clean = df.dropna()
    
    logger.info(f"Cleaned dataset shape: {df_clean.shape}")
    return df_clean

def process_real_world_dataset(dataset_id: str, df: pd.DataFrame):
    """Process and save a real-world dataset."""
    output_dir = Path("data/cleaned")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{dataset_id}.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned dataset to {output_path}")

def get_cleaned_data_path(dataset_id: str) -> Path:
    """Get path to cleaned dataset."""
    return Path("data/cleaned") / f"{dataset_id}.csv"

def update_manifest(manifest: List[Dict], dataset_id: str, size: int, missing_rate: float, status: str):
    """Update manifest with dataset processing status."""
    entry = {
        "source": dataset_id,
        "size": size,
        "missing_rate": missing_rate,
        "status": status
    }
    
    # Remove existing entry for this dataset if present
    manifest = [e for e in manifest if e.get("source") != dataset_id]
    manifest.append(entry)
    
    return manifest

def run_ingestion_pipeline():
    """Run the full ingestion pipeline."""
    logger.info("Running ingestion pipeline")
    config_path = "data/config/datasets.yaml"
    datasets_config = load_dataset_config(config_path)
    manifest = []
    
    for ds_config in datasets_config:
        ds_id = ds_config.get('id')
        try:
            df = download_dataset(ds_id)
            df_clean = clean_dataset(df)
            process_real_world_dataset(ds_id, df_clean)
            missing_rate = df_clean.isnull().sum().sum() / df_clean.size if len(df_clean) > 0 else 0.0
            manifest = update_manifest(manifest, ds_id, len(df_clean), missing_rate, "success")
        except Exception as e:
            logger.warning(f"Failed to process {ds_id}: {str(e)}")
            manifest = update_manifest(manifest, ds_id, 0, 0.0, "skipped")
    
    # Save manifest
    with open("data/metadata/manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info("Ingestion pipeline complete")
    return manifest
