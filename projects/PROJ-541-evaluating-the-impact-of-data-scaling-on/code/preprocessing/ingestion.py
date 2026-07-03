import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

import pandas as pd
import numpy as np
from dataclasses import dataclass, field

# Import config loader for datasets
# Assuming datasets.yaml is read via standard yaml or pandas logic here
# Since T034a created the YAML, we read it here.
import yaml

# Import logger setup (standardized across project)
from simulation.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

@dataclass
class RealWorldDataset:
    """
    Entity representing a loaded and preprocessed real-world dataset.
    Matches T037 requirements for metadata storage.
    """
    dataset_id: str
    source: str
    raw_path: str
    clean_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source": self.source,
            "raw_path": self.raw_path,
            "clean_path": self.clean_path,
            "metadata": self.metadata
        }

def load_dataset_config(config_path: str = "data/config/datasets.yaml") -> List[Dict[str, Any]]:
    """
    Reads the dataset configuration from YAML.
    T034a ensures this file exists.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset configuration not found at {config_path}. "
                                "Run T034a to generate data/config/datasets.yaml.")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    if isinstance(config, list):
        return config
    elif isinstance(config, dict) and 'datasets' in config:
        return config['datasets']
    else:
        raise ValueError("Invalid dataset config format. Expected list or dict with 'datasets' key.")

def clean_dataset(
    df: pd.DataFrame,
    dataset_id: str,
    strategy: str = "drop",
    threshold: float = 0.5,
    numeric_only: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Implements data cleaning and preprocessing (imputation/removal) as per T036.
    
    Args:
        df: Input DataFrame.
        dataset_id: Identifier for logging.
        strategy: "drop" (remove rows/cols with missing) or "impute" (fill with mean/median).
        threshold: Fraction of missing values allowed before dropping a column (0.0 to 1.0).
        numeric_only: If True, only process numeric columns for imputation/dropping.
        
    Returns:
        Tuple of (cleaned DataFrame, metadata dict with missing stats).
    """
    logger.info(f"Cleaning dataset {dataset_id} with strategy: {strategy}")
    
    original_shape = df.shape
    missing_before = df.isnull().sum().sum()
    
    metadata = {
        "original_shape": list(original_shape),
        "missing_before": int(missing_before),
        "missing_after": 0,
        "dropped_columns": [],
        "dropped_rows": 0
    }
    
    # 1. Handle Columns with High Missing Rates
    if numeric_only:
        cols_to_check = df.select_dtypes(include=[np.number]).columns
    else:
        cols_to_check = df.columns
        
    high_missing_cols = []
    for col in cols_to_check:
        missing_frac = df[col].isnull().sum() / len(df)
        if missing_frac > threshold:
            high_missing_cols.append(col)
            
    if high_missing_cols:
        logger.warning(f"Dropping {len(high_missing_cols)} columns with >{threshold*100}% missing values in {dataset_id}")
        df = df.drop(columns=high_missing_cols)
        metadata["dropped_columns"] = high_missing_cols
    
    # 2. Handle Remaining Missing Values
    if strategy == "drop":
        # Drop rows with any remaining missing values in numeric columns
        if numeric_only:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df_clean = df.dropna(subset=numeric_cols)
        else:
            df_clean = df.dropna()
        
        rows_dropped = original_shape[0] - df_clean.shape[0]
        metadata["dropped_rows"] = int(rows_dropped)
        
    elif strategy == "impute":
        df_clean = df.copy()
        if numeric_only:
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df_clean[col].isnull().any():
                    # Use median for robustness against outliers
                    median_val = df_clean[col].median()
                    if pd.isna(median_val):
                        # Fallback to 0 if column is all NaN
                        median_val = 0.0
                    df_clean[col].fillna(median_val, inplace=True)
                    logger.debug(f"Imputed missing values in {col} with median={median_val}")
        else:
            # Impute numeric with median, object with mode
            for col in df_clean.columns:
                if df_clean[col].isnull().any():
                    if pd.api.types.is_numeric_dtype(df_clean[col]):
                        val = df_clean[col].median()
                        if pd.isna(val): val = 0.0
                        df_clean[col].fillna(val, inplace=True)
                    else:
                        # Mode might be empty if all NaN, handle safely
                        mode_val = df_clean[col].mode()
                        if not mode_val.empty:
                            df_clean[col].fillna(mode_val[0], inplace=True)
                        else:
                            df_clean[col].fillna("Unknown", inplace=True)
    else:
        raise ValueError(f"Unknown cleaning strategy: {strategy}")
    
    missing_after = df_clean.isnull().sum().sum()
    metadata["missing_after"] = int(missing_after)
    metadata["final_shape"] = list(df_clean.shape)
    
    if missing_after > 0:
        logger.warning(f"Dataset {dataset_id} still has {missing_after} missing values after cleaning.")
    else:
        logger.info(f"Dataset {dataset_id} cleaned successfully. No missing values remaining.")
        
    return df_clean, metadata

def process_real_world_dataset(
    dataset_id: str,
    data_path: str,
    output_dir: str = "data/clean",
    strategy: str = "impute"
) -> RealWorldDataset:
    """
    Orchestrates loading, cleaning, and saving a real-world dataset.
    Implements T036 and T037 (entity creation).
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {data_path}")
    
    # Load based on extension
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.xlsx':
        df = pd.read_excel(path)
    else:
        # Try CSV as default fallback
        try:
            df = pd.read_csv(path)
        except Exception:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    # Clean
    df_clean, meta = clean_dataset(df, dataset_id, strategy=strategy)
    
    # Ensure output directory exists
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    clean_filename = f"{dataset_id}_cleaned.csv"
    clean_file_path = out_path / clean_filename
    
    # Save
    df_clean.to_csv(clean_file_path, index=False)
    
    # Create Entity
    dataset_entity = RealWorldDataset(
        dataset_id=dataset_id,
        source=path.name,
        raw_path=str(path),
        clean_path=str(clean_file_path),
        metadata=meta
    )
    
    logger.info(f"Saved cleaned dataset to {clean_file_path}")
    return dataset_entity

def update_manifest(
    dataset_entity: RealWorldDataset,
    manifest_path: str = "data/metadata/manifest.json"
):
    """
    Updates the manifest.json with metadata for the processed dataset.
    """
    manifest_file = Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            try:
                manifest = json.load(f)
            except json.JSONDecodeError:
                manifest = []
    else:
        manifest = []
        
    # Append or update
    existing = [item for item in manifest if item.get('dataset_id') == dataset_entity.dataset_id]
    if existing:
        # Update existing entry
        idx = manifest.index(existing[0])
        manifest[idx] = dataset_entity.to_dict()
    else:
        manifest.append(dataset_entity.to_dict())
        
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Updated manifest at {manifest_path}")

def get_cleaned_data_path(dataset_id: str, output_dir: str = "data/clean") -> Optional[str]:
    """
    Helper to locate the cleaned file for a given ID.
    """
    path = Path(output_dir) / f"{dataset_id}_cleaned.csv"
    if path.exists():
        return str(path)
    return None

def run_ingestion_pipeline(
    config_path: str = "data/config/datasets.yaml",
    strategy: str = "impute"
) -> List[RealWorldDataset]:
    """
    Main entry point to process all datasets defined in the config.
    """
    configs = load_dataset_config(config_path)
    results = []
    
    for cfg in configs:
        dataset_id = cfg.get('id') or cfg.get('dataset_id')
        if not dataset_id:
            logger.error(f"Missing dataset_id in config: {cfg}")
            continue
            
        # Check if raw data exists (T035 should have downloaded it to data/raw)
        # We expect the file to be named based on the ID or a specific path in config
        # For now, assume data/raw/{id}.csv or similar
        raw_file = Path("data/raw") / f"{dataset_id}.csv"
        
        # If not found, try to find any file matching the ID in raw
        if not raw_file.exists():
            raw_files = list(Path("data/raw").glob(f"{dataset_id}*"))
            if raw_files:
                raw_file = raw_files[0]
            else:
                logger.warning(f"Raw data not found for {dataset_id}. Skipping.")
                continue
        
        try:
            entity = process_real_world_dataset(
                dataset_id=dataset_id,
                data_path=str(raw_file),
                strategy=strategy
            )
            update_manifest(entity)
            results.append(entity)
        except Exception as e:
            logger.error(f"Failed to process {dataset_id}: {e}")
            
    return results

if __name__ == "__main__":
    # Simple CLI for testing T036
    logging.basicConfig(level=logging.INFO)
    # Run pipeline if config exists
    if Path("data/config/datasets.yaml").exists():
        run_ingestion_pipeline()
    else:
        print("data/config/datasets.yaml not found. Run T034a first.")