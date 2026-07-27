import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterator

from datasets import load_dataset
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_SAMPLES = 500
GSM8K_DATASET_ID = "gsm8k"
MINIGRID_DATASET_ID = "minigrid"
GSM8K_CONFIG = "main"
MINIGRID_CONFIG = "minigrid"

# Output directories relative to project root
DATA_DIR = Path(__file__).parent.parent.parent / "data"
GSM8K_OUTPUT_PATH = DATA_DIR / "gsm8k_subset.jsonl"
MINIGRID_OUTPUT_PATH = DATA_DIR / "minigrid_subset.jsonl"

def download_gsm8k_subset(output_path: Optional[Path] = None, max_samples: int = DEFAULT_MAX_SAMPLES) -> str:
    """
    Fetch GSM8K dataset from HuggingFace and save a representative subset.
    
    Args:
        output_path: Path to save the subset. Defaults to data/gsm8k_subset.jsonl.
        max_samples: Maximum number of samples to fetch.
        
    Returns:
        Path to the saved file as string.
        
    Raises:
        ConnectionError: If the dataset cannot be fetched from HuggingFace.
        FileNotFoundError: If the dataset does not exist.
    """
    if output_path is None:
        output_path = GSM8K_OUTPUT_PATH
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching GSM8K dataset (max {max_samples} samples)...")
    
    try:
        # Load dataset with streaming to handle large datasets efficiently
        dataset = load_dataset(
            GSM8K_DATASET_ID, 
            GSM8K_CONFIG, 
            split="train",
            streaming=True
        )
        
        # Take a representative subset using islice
        # We'll collect samples in a list and write them to file
        samples = []
        count = 0
        
        for item in dataset:
            if count >= max_samples:
                break
            
            # Extract relevant fields
            sample = {
                "prompt_id": f"gsm8k_{count}",
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "source": "gsm8k"
            }
            samples.append(sample)
            count += 1
            
            if count % 50 == 0:
                logger.info(f"Processed {count} samples...")
        
        if count == 0:
            raise ValueError("No samples were retrieved from the dataset")
        
        logger.info(f"Successfully fetched {count} GSM8K samples")
        
        # Write to JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved GSM8K subset to {output_path}")
        return str(output_path)
        
    except Exception as e:
        # Re-raise to fail loudly - no synthetic fallback
        logger.error(f"Failed to fetch GSM8K dataset: {str(e)}")
        raise ConnectionError(f"Failed to fetch GSM8K dataset: {str(e)}") from e

def download_minigrid_subset(output_path: Optional[Path] = None, max_samples: int = DEFAULT_MAX_SAMPLES) -> str:
    """
    Fetch MiniGrid dataset from HuggingFace and save a representative subset.
    
    Args:
        output_path: Path to save the subset. Defaults to data/minigrid_subset.jsonl.
        max_samples: Maximum number of samples to fetch.
        
    Returns:
        Path to the saved file as string.
        
    Raises:
        ConnectionError: If the dataset cannot be fetched from HuggingFace.
        FileNotFoundError: If the dataset does not exist.
    """
    if output_path is None:
        output_path = MINIGRID_OUTPUT_PATH
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching MiniGrid dataset (max {max_samples} samples)...")
    
    try:
        # Load dataset with streaming
        # MiniGrid might have different configurations, try common ones
        configs_to_try = [MINIGRID_CONFIG, "default", None]
        dataset = None
        
        for config in configs_to_try:
            try:
                if config:
                    dataset = load_dataset(
                        MINIGRID_DATASET_ID, 
                        config, 
                        split="train",
                        streaming=True
                    )
                else:
                    dataset = load_dataset(
                        MINIGRID_DATASET_ID, 
                        split="train",
                        streaming=True
                    )
                break
            except Exception:
                continue
        
        if dataset is None:
            raise FileNotFoundError("Could not load MiniGrid dataset with any available configuration")
        
        # Take a representative subset
        samples = []
        count = 0
        
        for item in dataset:
            if count >= max_samples:
                break
            
            # Extract relevant fields - MiniGrid structure varies by config
            sample = {
                "prompt_id": f"minigrid_{count}",
                "grid": item.get("grid", ""),
                "mission": item.get("mission", ""),
                "source": "minigrid"
            }
            
            # Add any additional fields that might be present
            for key, value in item.items():
                if key not in sample:
                    sample[key] = value
            
            samples.append(sample)
            count += 1
            
            if count % 50 == 0:
                logger.info(f"Processed {count} samples...")
        
        if count == 0:
            raise ValueError("No samples were retrieved from the dataset")
        
        logger.info(f"Successfully fetched {count} MiniGrid samples")
        
        # Write to JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved MiniGrid subset to {output_path}")
        return str(output_path)
        
    except Exception as e:
        # Re-raise to fail loudly - no synthetic fallback
        logger.error(f"Failed to fetch MiniGrid dataset: {str(e)}")
        raise ConnectionError(f"Failed to fetch MiniGrid dataset: {str(e)}") from e

def download_all_datasets(max_samples: int = DEFAULT_MAX_SAMPLES) -> Dict[str, str]:
    """
    Download both GSM8K and MiniGrid datasets.
    
    Args:
        max_samples: Maximum number of samples for each dataset.
        
    Returns:
        Dictionary mapping dataset name to file path.
        
    Raises:
        ConnectionError: If any dataset fails to download.
    """
    results = {}
    
    try:
        gsm8k_path = download_gsm8k_subset(max_samples=max_samples)
        results["gsm8k"] = gsm8k_path
    except Exception as e:
        logger.error(f"GSM8K download failed: {str(e)}")
        raise
    
    try:
        minigrid_path = download_minigrid_subset(max_samples=max_samples)
        results["minigrid"] = minigrid_path
    except Exception as e:
        logger.error(f"MiniGrid download failed: {str(e)}")
        raise
    
    return results

def main():
    """Main entry point for downloading datasets."""
    logger.info("Starting dataset download process...")
    
    try:
        results = download_all_datasets(max_samples=DEFAULT_MAX_SAMPLES)
        
        logger.info("Dataset download completed successfully:")
        for dataset_name, path in results.items():
            logger.info(f"  {dataset_name}: {path}")
        
        # Write manifest
        manifest_path = DATA_DIR / "download_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump({
                "datasets": results,
                "max_samples": DEFAULT_MAX_SAMPLES,
                "timestamp": str(torch.utils.data.get_worker_info()) if torch.utils.data.get_worker_info() else "main"
            }, f, indent=2)
        
        logger.info(f"Manifest saved to {manifest_path}")
        
    except Exception as e:
        logger.error(f"Dataset download failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()