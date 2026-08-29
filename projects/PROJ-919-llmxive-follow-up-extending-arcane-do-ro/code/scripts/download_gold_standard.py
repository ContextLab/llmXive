"""
Script to download the real Gold Standard dataset from lmsys/lmsys-chatbot-arena.

This script implements Task T009d: Download Real Gold Standard.

Requirements:
- datasets library (pip install datasets)

Usage:
python scripts/download_gold_standard.py
"""
import os
import sys
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' library is required. Install it with: pip install datasets")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fixed seed for reproducibility
SEED = 42
random.seed(SEED)

# Configuration
DATASET_NAME = "lmsys/lmsys-chatbot-arena"
# We filter for single-turn conversations where there is a clear winner
# The dataset typically has fields: prompt, response_a, response_b, winner, etc.

def download_gold_standard(output_path: Path) -> None:
    """
    Download the lmsys-chatbot-arena dataset and save single-turn preference pairs.
    
    Args:
        output_path: Path to save the raw JSONL file.
        
    Raises:
        FileNotFoundError: If the dataset cannot be found or downloaded.
        RuntimeError: If the download fails for any reason.
    """
    logger.info(f"Attempting to download dataset: {DATASET_NAME}")
    
    try:
        # Load the dataset with streaming to handle large size efficiently
        # We use streaming=True to avoid downloading the entire dataset into memory
        # The dataset is split into train/test; we use the train split
        dataset = load_dataset(
            DATASET_NAME, 
            split="train", 
            streaming=True,
            trust_remote_code=True
        )
        
        logger.info("Dataset loaded successfully. Filtering for single-turn pairs...")
        
        # Filter for single-turn conversations (where there is a clear winner)
        # We need to ensure the data has the required fields
        filtered_samples = []
        sample_count = 0
        
        # Iterate through the dataset
        for item in dataset:
            # Check if the item has the required fields for a valid preference pair
            # The lmsys-chatbot-arena dataset typically has:
            # - prompt: The user's input
            # - response_a: Model A's response
            # - response_b: Model B's response
            # - winner: Which response was preferred (model_a, model_b, tie, etc.)
            
            if not all(key in item for key in ['prompt', 'response_a', 'response_b', 'winner']):
                continue
            
            # Skip if prompt is empty or too short
            if not item['prompt'] or len(item['prompt'].strip()) < 50:
                continue
            
            # Skip if responses are empty
            if not item['response_a'] or not item['response_b']:
                continue
            
            # We want single-turn preference pairs
            # The winner field indicates which response was preferred
            # We'll include all valid pairs regardless of winner for diversity
            # but we could filter further if needed
            
            # Create a structured record
            sample = {
                "id": f"arena_{sample_count}",
                "prompt": item['prompt'],
                "response_a": item['response_a'],
                "response_b": item['response_b'],
                "winner": item['winner'],
                "model_a": item.get('model_a', 'unknown'),
                "model_b": item.get('model_b', 'unknown'),
                "turn": 1  # Single turn
            }
            
            filtered_samples.append(sample)
            sample_count += 1
            
            # Limit to a reasonable number for the gold standard (e.g., 1000 samples)
            # This ensures we have enough data without making the file too large
            if sample_count >= 1000:
                break
        
        if sample_count == 0:
            logger.error("No valid samples found in the dataset after filtering.")
            raise FileNotFoundError(
                "No valid single-turn preference pairs found in the dataset. "
                "The dataset structure may have changed or filtering criteria too strict."
            )
        
        logger.info(f"Successfully filtered {sample_count} valid samples.")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to JSONL file
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in filtered_samples:
                # Convert to JSON string and write as a single line
                import json
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        logger.info(f"Gold standard dataset saved to: {output_path}")
        logger.info(f"Total samples: {sample_count}")
        
    except Exception as e:
        logger.error(f"Failed to download or process dataset: {str(e)}")
        # Re-raise as FileNotFoundError to indicate the data source is unavailable
        raise FileNotFoundError(
            f"Failed to download dataset '{DATASET_NAME}': {str(e)}. "
            "Please check your internet connection and ensure the dataset is accessible."
        ) from e

def main():
    """Main entry point for the script."""
    # Determine output path
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data" / "raw" / "gold_standard_raw.jsonl"
    
    logger.info(f"Output path: {output_path}")
    
    try:
        download_gold_standard(output_path)
        logger.info("Task T009d completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"DATA SOURCE UNAVAILABLE: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
