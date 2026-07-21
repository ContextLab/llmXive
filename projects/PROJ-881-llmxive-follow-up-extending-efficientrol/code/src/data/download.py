"""
Data download module for fetching GSM8K and MiniGrid datasets from HuggingFace.

This module implements strict real-data fetching with no synthetic fallbacks.
If the HuggingFace datasets cannot be accessed, the module will raise an
exception immediately to ensure the pipeline fails loudly.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterator

# Import from the project's existing API surface
# Note: We assume 'datasets' is installed via requirements.txt (T002)
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Please install it via requirements.txt."
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GSM8K_DATASET_NAME = "gsm8k"
GSM8K_CONFIG = "main"
MINIGRID_DATASET_NAME = "minigrid"
MINIGRID_CONFIG = "minigrid_qa"

# Output paths relative to project root
DATA_DIR = Path("data")
GSM8K_OUTPUT = DATA_DIR / "gsm8k_subset.jsonl"
MINIGRID_OUTPUT = DATA_DIR / "minigrid_subset.jsonl"

# Limits for representative subset (as per FR-001 and T007 requirements)
# We use a streaming approach to avoid loading the full dataset into memory
DEFAULT_SUBSET_SIZE = 500

def download_gsm8k_subset(output_path: Optional[Path] = None, limit: int = DEFAULT_SUBSET_SIZE) -> Path:
    """
    Fetch GSM8K dataset from HuggingFace and save a representative subset.
    
    This function uses streaming to process data in chunks, ensuring memory
    efficiency. It strictly requires a real data source and will fail loudly
    if the dataset cannot be accessed.
    
    Args:
        output_path: Path to save the output JSONL file. Defaults to data/gsm8k_subset.jsonl.
        limit: Maximum number of examples to fetch. Defaults to 500.
    
    Returns:
        Path to the saved JSONL file.
    
    Raises:
        ConnectionError: If the HuggingFace dataset cannot be accessed.
        FileNotFoundError: If the dataset configuration is invalid.
        Exception: Any other error during download.
    """
    if output_path is None:
        output_path = GSM8K_OUTPUT
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching GSM8K dataset (limit={limit})...")
    
    try:
        # Load dataset with streaming enabled to handle large datasets
        # The 'main' config is the standard GSM8K split
        dataset = load_dataset(
            GSM8K_DATASET_NAME, 
            GSM8K_CONFIG, 
            split="train",
            streaming=True
        )
        
        logger.info("Dataset stream established successfully.")
        
        # Process the dataset in a streaming fashion
        # We iterate and collect up to 'limit' examples
        examples = []
        count = 0
        
        for item in dataset:
            if count >= limit:
                break
            
            # GSM8K structure: {'question': str, 'answer': str (with step-by-step)}
            # We normalize the structure for downstream consumption
            processed_item = {
                "prompt_id": f"gsm8k_{count}",
                "dataset": "gsm8k",
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "metadata": {
                    "split": "train",
                    "source": "huggingface"
                }
            }
            examples.append(processed_item)
            count += 1
            
            if count % 100 == 0:
                logger.info(f"Processed {count} examples...")
        
        if count == 0:
            raise RuntimeError("No examples were retrieved from the GSM8K dataset.")
        
        logger.info(f"Successfully fetched {count} GSM8K examples.")
        
        # Write to JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in examples:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved GSM8K subset to {output_path}")
        return output_path
        
    except Exception as e:
        # Fail loudly: do not catch and return synthetic data
        logger.error(f"Failed to fetch GSM8K dataset: {e}")
        raise ConnectionError(f"Could not access GSM8K dataset from HuggingFace: {e}") from e

def download_minigrid_subset(output_path: Optional[Path] = None, limit: int = DEFAULT_SUBSET_SIZE) -> Path:
    """
    Fetch MiniGrid dataset from HuggingFace and save a representative subset.
    
    This function uses streaming to process data in chunks. It strictly requires
    a real data source and will fail loudly if the dataset cannot be accessed.
    
    Args:
        output_path: Path to save the output JSONL file. Defaults to data/minigrid_subset.jsonl.
        limit: Maximum number of examples to fetch. Defaults to 500.
    
    Returns:
        Path to the saved JSONL file.
    
    Raises:
        ConnectionError: If the HuggingFace dataset cannot be accessed.
        FileNotFoundError: If the dataset configuration is invalid.
        Exception: Any other error during download.
    """
    if output_path is None:
        output_path = MINIGRID_OUTPUT
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching MiniGrid dataset (limit={limit})...")
    
    try:
        # Load dataset with streaming enabled
        # Using 'minigrid_qa' config which contains question-answering pairs for MiniGrid
        dataset = load_dataset(
            MINIGRID_DATASET_NAME,
            MINIGRID_CONFIG,
            split="train",
            streaming=True
        )
        
        logger.info("Dataset stream established successfully.")
        
        # Process the dataset in a streaming fashion
        examples = []
        count = 0
        
        for item in dataset:
            if count >= limit:
                break
            
            # MiniGrid QA structure typically includes:
            # 'question', 'answer', 'observation' (or similar)
            # We normalize for downstream consumption
            processed_item = {
                "prompt_id": f"minigrid_{count}",
                "dataset": "minigrid",
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "observation": item.get("observation", item.get("grid", "")),
                "metadata": {
                    "split": "train",
                    "source": "huggingface"
                }
            }
            examples.append(processed_item)
            count += 1
            
            if count % 100 == 0:
                logger.info(f"Processed {count} examples...")
        
        if count == 0:
            raise RuntimeError("No examples were retrieved from the MiniGrid dataset.")
        
        logger.info(f"Successfully fetched {count} MiniGrid examples.")
        
        # Write to JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in examples:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved MiniGrid subset to {output_path}")
        return output_path
        
    except Exception as e:
        # Fail loudly: do not catch and return synthetic data
        logger.error(f"Failed to fetch MiniGrid dataset: {e}")
        raise ConnectionError(f"Could not access MiniGrid dataset from HuggingFace: {e}") from e

def download_all_datasets(
    gsm8k_limit: int = DEFAULT_SUBSET_SIZE,
    minigrid_limit: int = DEFAULT_SUBSET_SIZE,
    gsm8k_path: Optional[Path] = None,
    minigrid_path: Optional[Path] = None
) -> Dict[str, Path]:
    """
    Download both GSM8K and MiniGrid datasets.
    
    Args:
        gsm8k_limit: Number of GSM8K examples to fetch.
        minigrid_limit: Number of MiniGrid examples to fetch.
        gsm8k_path: Optional path for GSM8K output.
        minigrid_path: Optional path for MiniGrid output.
    
    Returns:
        Dictionary mapping dataset names to their output file paths.
    
    Raises:
        ConnectionError: If either dataset cannot be accessed.
    """
    results = {}
    
    try:
        gsm8k_path = download_gsm8k_subset(gsm8k_path, gsm8k_limit)
        results["gsm8k"] = gsm8k_path
    except Exception as e:
        logger.error(f"GSM8K download failed: {e}")
        raise
    
    try:
        minigrid_path = download_minigrid_subset(minigrid_path, minigrid_limit)
        results["minigrid"] = minigrid_path
    except Exception as e:
        logger.error(f"MiniGrid download failed: {e}")
        raise
    
    return results

def main():
    """
    Main entry point for downloading datasets.
    """
    logger.info("Starting data download process...")
    
    try:
        paths = download_all_datasets()
        logger.info("Download process completed successfully.")
        logger.info(f"GSM8K saved to: {paths['gsm8k']}")
        logger.info(f"MiniGrid saved to: {paths['minigrid']}")
        
        # Print summary for verification
        print(json.dumps({
            "status": "success",
            "files": {
                "gsm8k": str(paths["gsm8k"]),
                "minigrid": str(paths["minigrid"])
            }
        }, indent=2))
        
    except ConnectionError as e:
        logger.error(f"Critical failure: {e}")
        print(json.dumps({"status": "failed", "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(json.dumps({"status": "failed", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()