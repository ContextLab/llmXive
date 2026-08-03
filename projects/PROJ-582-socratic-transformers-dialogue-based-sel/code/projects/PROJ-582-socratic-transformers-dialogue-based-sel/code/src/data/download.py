"""
Dataset downloader for GSM8K and MATH datasets.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from datasets import load_dataset

from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)

def ensure_data_dirs(config: Optional[SocraticConfig] = None):
    """Ensure data directories exist."""
    if config is None:
        config = get_config()
    
    raw_dir = Path(config.data_raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dataset subdirectories
    (raw_dir / "gsm8k").mkdir(exist_ok=True)
    (raw_dir / "math").mkdir(exist_ok=True)

def download_dataset(
    dataset_name: str,
    config: Optional[SocraticConfig] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Download a dataset from HuggingFace and save it locally.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'gsm8k', 'math').
        config: Configuration object.
        output_dir: Optional output directory override.
        
    Returns:
        Path to the downloaded dataset directory.
    """
    if config is None:
        config = get_config()
    
    if output_dir is None:
        raw_dir = Path(config.data_raw_dir)
        ensure_data_dirs(config)
        output_dir = raw_dir / dataset_name
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {dataset_name}...")
    
    try:
        if dataset_name == "gsm8k":
            dataset = load_dataset("gsm8k", "main")
        elif dataset_name == "math":
            dataset = load_dataset("competition_math")
        else:
            raise ValueError(f"Unsupported dataset: {dataset_name}")
        
        # Save to local JSONL
        for split in dataset:
            split_data = dataset[split]
            file_path = output_dir / f"{split}.jsonl"
            split_data.to_json(str(file_path), orient="records", lines=True)
            logger.info(f"Saved {split} split to {file_path}")
        
        logger.info(f"Successfully downloaded {dataset_name} to {output_dir}")
        return output_dir
        
    except Exception as e:
        logger.error(f"Failed to download {dataset_name}: {e}")
        raise

def download_all_datasets(config: Optional[SocraticConfig] = None) -> Dict[str, Path]:
    """Download all required datasets."""
    if config is None:
        config = get_config()
    
    datasets = ["gsm8k", "math"]
    paths = {}
    
    for ds in datasets:
        try:
            paths[ds] = download_dataset(ds, config)
        except Exception as e:
            logger.error(f"Skipping {ds} due to error: {e}")
            paths[ds] = None
    
    return paths

def main():
    """Main entry point for dataset downloader."""
    config = get_config()
    logger.info("Starting dataset download")
    
    results = download_all_datasets(config)
    
    for ds, path in results.items():
        if path:
            logger.info(f"{ds}: {path}")
        else:
            logger.warning(f"{ds}: Failed to download")
    
    if all(v is None for v in results.values()):
        logger.error("No datasets were downloaded successfully.")
        sys.exit(1)
    else:
        logger.info("Dataset download completed.")
        sys.exit(0)
