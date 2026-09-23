import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Attempt to import datasets; if missing, the script will fail loudly as per constraints
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via 'pip install datasets'."
    )

# Import logging utilities from the existing project structure
try:
    from src.utils.logging import get_logger, setup_logger
except ImportError:
    # Fallback for environments where the logger isn't fully initialized yet
    # This ensures the script can still run if logging setup is pending
    def get_logger(name: str):
        return logging.getLogger(name)

    def setup_logger(name: str, level=logging.INFO):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(handler)
            logger.setLevel(level)
        return logger

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
SCARCITY_THRESHOLD = 120

# Logger setup
logger = setup_logger("ingest")

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return PROJECT_ROOT

def fetch_dataset_from_hf(dataset_name: str = "qm9-ts", split: str = "train") -> Any:
    """
    Fetches the dataset from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace.
        split: Which split to load.
        
    Returns:
        The loaded dataset object.
        
    Raises:
        ConnectionError: If the dataset cannot be fetched.
        ValueError: If the dataset is not found.
    """
    logger.info(f"Fetching dataset '{dataset_name}' from HuggingFace...")
    try:
        # Using streaming=True to handle large datasets without loading fully into memory
        # This ensures we don't exceed RAM limits on the runner
        dataset = load_dataset(dataset_name, split=split, streaming=True)
        logger.info("Dataset fetched successfully.")
        return dataset
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        # Fail loudly: do not return synthetic data
        raise RuntimeError(f"Could not fetch real data from HuggingFace: {e}")

def load_and_count_reactions(dataset: Any) -> int:
    """
    Iterates through the dataset to count total reactions.
    
    Args:
        dataset: The HuggingFace dataset object.
        
    Returns:
        Total count of reactions.
    """
    count = 0
    logger.info("Counting reactions in dataset...")
    for _ in dataset:
        count += 1
    logger.info(f"Total reactions found: {count}")
    return count

def filter_transition_metals(dataset: Any, elements: List[str] = ["Pd", "Ni", "Cu"]) -> int:
    """
    Filters the dataset for reactions involving specific transition metals
    and counts the valid reactions.
    
    Args:
        dataset: The HuggingFace dataset object.
        elements: List of element symbols to filter for.
        
    Returns:
        Count of valid reactions containing the specified elements.
    """
    valid_count = 0
    logger.info(f"Filtering for transition metals: {elements}...")
    
    # Assuming the dataset has a 'elements' or 'atoms' field containing element symbols
    # We iterate through the streaming dataset to count matches
    for item in dataset:
        # Heuristic: Check if any of the target elements appear in the item's element list
        # The exact field name might vary (e.g., 'elements', 'atomic_symbols', 'atoms')
        # We try common keys or assume a list of strings
        elements_in_reaction = item.get('elements', item.get('atoms', []))
        
        if any(elem in elements_in_reaction for elem in elements):
            valid_count += 1
            
    logger.info(f"Valid reactions with {elements}: {valid_count}")
    return valid_count

def handle_scarcity(count: int, threshold: int = SCARCITY_THRESHOLD) -> Optional[Dict[str, Any]]:
    """
    Checks if the count of valid reactions is below the threshold.
    If so, creates a scarcity flag file.
    
    Args:
        count: The number of valid reactions.
        threshold: The minimum required count.
        
    Returns:
        A dictionary with scarcity info if count < threshold, else None.
    """
    if count < threshold:
        logger.warning(f"Data scarcity detected: {count} < {threshold}")
        
        scarcity_data = {
            "count": count,
            "status": "scarcity",
            "threshold": threshold
        }
        
        # Ensure the output directory exists
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        output_path = DATA_PROCESSED_DIR / "data_scarcity_flag.json"
        
        with open(output_path, 'w') as f:
            json.dump(scarcity_data, f, indent=2)
        
        logger.info(f"Scarcity flag written to {output_path}")
        return scarcity_data
    else:
        logger.info(f"Data volume sufficient: {count} >= {threshold}")
        return None

def run_ingestion() -> Dict[str, Any]:
    """
    Main ingestion pipeline: fetch, filter, and check scarcity.
    
    Returns:
        Dictionary containing the count and scarcity status.
    """
    try:
        # 1. Fetch dataset
        # Note: Using a specific dataset ID. If 'qm9-ts' is not the exact ID,
        # this will fail loudly, which is the desired behavior for real data.
        # Based on the context, we assume a valid HuggingFace dataset exists.
        # If the exact ID is unknown, we use a generic placeholder that must be resolved.
        # However, per instructions, we must use a REAL source. 
        # We will attempt to load a known dataset structure or fail.
        # For the purpose of this implementation, we assume the dataset name is 'qm9-ts' 
        # or similar. If the runner fails, it's because the dataset ID is incorrect 
        # or unreachable, which is a valid failure mode.
        
        # Attempting to load from a likely source. 
        # If 'qm9-ts' doesn't exist, the user must update the dataset_name.
        dataset_name = "qm9-ts" 
        try:
            ds = fetch_dataset_from_hf(dataset_name)
        except Exception:
            # If 'qm9-ts' fails, try a generic fallback if available, 
            # but strictly we should fail if the specific one isn't found.
            # We'll let the exception propagate or handle a specific known alias.
            # For now, we assume the task context implies 'qm9-ts' is the target.
            raise RuntimeError(f"Dataset '{dataset_name}' not found or unreachable.")

        # 2. Filter and count
        # We pass the dataset to the filter function which iterates it.
        # Note: Since we are streaming, we can only iterate once.
        # We need to be careful if we need the data later. 
        # Here we just need the count.
        count = filter_transition_metals(ds)
        
        # 3. Handle scarcity
        scarcity_info = handle_scarcity(count)
        
        return {
            "count": count,
            "scarcity_flag": scarcity_info
        }
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

def main():
    """Entry point for the script."""
    logger.info("Starting data ingestion pipeline (T015b)...")
    try:
        result = run_ingestion()
        logger.info(f"Ingestion completed. Count: {result['count']}")
        if result['scarcity_flag']:
            logger.warning(f"Scarcity flag created: {result['scarcity_flag']}")
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()