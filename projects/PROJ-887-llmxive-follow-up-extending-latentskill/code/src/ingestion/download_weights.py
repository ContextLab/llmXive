"""
Download real LoRA weights from HuggingFace datasets.

Implements a strict streaming policy to handle large datasets.
If the primary dataset is inaccessible or streaming fails, raises FileNotFoundError.
NEVER falls back to synthetic data.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

# Import from project config
from src.utils.config import get_project_root, get_data_path, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for dataset paths
ALFWORLD_DATASET_ID = "latent-skills/alfworld-weights"
SEARCHQA_DATASET_ID = "latent-skills/searchqa-weights"
ALFWORLD_OUTPUT = "alfworld_weights.npz"
SEARCHQA_OUTPUT = "searchqa_weights.npz"

def load_real_weights(dataset_id: str, split: str = 'train', revision: str = 'main') -> Optional[Dict[str, Any]]:
    """
    Load real weights from a HuggingFace dataset using streaming.
    
    Args:
        dataset_id: The HuggingFace dataset identifier.
        split: The dataset split to load (default: 'train').
        revision: The dataset revision (default: 'main').
        
    Returns:
        A dictionary containing the loaded weights data, or None if not found.
        
    Raises:
        FileNotFoundError: If the dataset is inaccessible or contains no valid weight files.
        Exception: Propagates any other errors from the datasets library.
    """
    logger.info(f"Attempting to load dataset: {dataset_id} (streaming=True)")
    
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Install with: pip install datasets")
        raise

    try:
        # Use streaming to avoid loading the entire dataset into memory
        dataset = load_dataset(
            dataset_id, 
            split=split, 
            revision=revision, 
            streaming=True
        )
        
        logger.info(f"Successfully connected to dataset stream: {dataset_id}")
        
        # Collect all valid weight entries
        weights_data = {}
        found_any = False
        
        for idx, item in enumerate(dataset):
            # Check for standard weight keys
            if 'weights' in item and item['weights'] is not None:
                # Item might be a dict of arrays or a single array
                if isinstance(item['weights'], dict):
                    for key, value in item['weights'].items():
                        if isinstance(value, np.ndarray):
                            weights_data[f"{key}_{idx}"] = value
                            found_any = True
                elif isinstance(item['weights'], np.ndarray):
                    weights_data[f"weights_{idx}"] = item['weights']
                    found_any = True
            
            # Fallback: check for 'A' and 'B' matrices directly if 'weights' key is missing
            # This handles cases where the dataset structure varies slightly
            if 'A' in item and 'B' in item:
                weights_data[f"A_{idx}"] = item['A']
                weights_data[f"B_{idx}"] = item['B']
                found_any = True

            # Log progress every 100 items
            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1} items from stream...")

        if not found_any:
            error_msg = f"No valid weight data found in dataset stream for {dataset_id}. " \
                        f"Scanned {idx + 1} items but found no 'weights', 'A', or 'B' arrays."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Successfully loaded {len(weights_data)} weight entries from {dataset_id}")
        return weights_data

    except Exception as e:
        # If streaming fails, we must NOT fall back to synthetic data.
        # We must raise an error so the pipeline halts.
        error_msg = f"Failed to stream dataset {dataset_id}: {str(e)}. " \
                    f"HALTING: No synthetic fallback allowed."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg) from e

def save_weights(weights_data: Dict[str, Any], output_path: Path) -> None:
    """
    Save weight data to an .npz file.
    
    Args:
        weights_data: Dictionary of numpy arrays to save.
        output_path: Path to the output .npz file.
    """
    logger.info(f"Saving {len(weights_data)} weight entries to {output_path}")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert dict values to ensure they are numpy arrays before saving
    save_dict = {k: np.array(v) for k, v in weights_data.items()}
    
    np.savez_compressed(output_path, **save_dict)
    logger.info(f"Saved weights to {output_path} (size: {output_path.stat().st_size / 1024 / 1024:.2f} MB)")

def process_dataset(dataset_id: str, output_filename: str) -> None:
    """
    Process a single dataset: load via streaming and save to disk.
    
    Args:
        dataset_id: HuggingFace dataset ID.
        output_filename: Name of the output file in data/raw/.
    """
    data_dir = get_data_path() / "raw"
    ensure_directories()
    
    output_path = data_dir / output_filename
    
    if output_path.exists():
        logger.warning(f"Output file {output_path} already exists. Overwriting.")
    
    weights_data = load_real_weights(dataset_id)
    save_weights(weights_data, output_path)

def main() -> None:
    """
    Main entry point for downloading weights.
    
    Executes the download for both ALFWorld and SearchQA datasets.
    Halts with FileNotFoundError if any download fails.
    """
    logger.info("Starting weight download process...")
    
    try:
        # Process ALFWorld
        process_dataset(ALFWORLD_DATASET_ID, ALFWORLD_OUTPUT)
        
        # Process SearchQA
        process_dataset(SEARCHQA_DATASET_ID, SEARCHQA_OUTPUT)
        
        logger.info("All weight downloads completed successfully.")
        
        # Verify outputs exist
        data_dir = get_data_path() / "raw"
        for filename in [ALFWORLD_OUTPUT, SEARCHQA_OUTPUT]:
            path = data_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"Expected output file {path} was not created.")
            
        logger.info("Verification passed: All required files exist.")
        
    except FileNotFoundError as e:
        logger.critical(f"CRITICAL FAILURE: {str(e)}")
        logger.critical("Pipeline halted due to missing real data source.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during download: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()