"""
Download Micro-Corpus from Project Gutenberg and The Stack.

This script fetches real data from public sources. It strictly enforces
that data is downloaded from verified sources. If the download fails,
it raises an exception immediately. NO synthetic fallbacks are permitted.

Output:
    data/raw/gutenberg_samples.jsonl
    data/raw/the_stack_samples.jsonl
    data/raw/micro_corpus_combined.jsonl
"""
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
import requests
from datasets import load_dataset
from huggingface_hub import hf_hub_download

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DATA_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Verified Real Data Sources
# Source 1: Project Gutenberg (via a curated mirror or direct fetch)
# We use a specific subset of Project Gutenberg texts available via Hugging Face
# to ensure programmatic access without manual scraping.
# Dataset: "gutenberg" (subset of Project Gutenberg)
GUTENBERG_DATASET_ID = "gutenberg"
GUTENBERG_SPLIT = "train" # We will sample from this

# Source 2: The Stack (via Hugging Face)
# Dataset: "bigcode/the-stack" or a curated subset like "bigcode/the-stack-smol"
# Using 'the-stack-smol' for faster processing in constrained environments, 
# but the logic applies to the full stack.
THE_STACK_DATASET_ID = "bigcode/the-stack-smol"
THE_STACK_SPLIT = "train"

# HumanEval dataset for exclusion reference (not downloaded here, but referenced)
HUMAN_EVAL_DATASET_ID = "openai_humaneval"

logger = None

def setup_logging():
    global logger
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

def fetch_gutenberg_samples(num_samples: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetches text samples from Project Gutenberg via Hugging Face.
    
    Args:
        num_samples: Number of samples to retrieve.
        
    Returns:
        List of dictionaries with 'text' and 'source' keys.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    setup_logging()
    logger.info(f"Fetching {num_samples} samples from Project Gutenberg (Hugging Face)...")
    
    try:
        # Load dataset in streaming mode to avoid memory issues
        dataset = load_dataset(
            GUTENBERG_DATASET_ID, 
            split=GUTENBERG_SPLIT, 
            streaming=True,
            trust_remote_code=True
        )
        
        samples = []
        count = 0
        for item in dataset:
            if count >= num_samples:
                break
            
            # Filter out very short or very long texts if necessary
            # Gutenberg texts are in 'text' field usually
            text = item.get('text', '')
            if text and len(text) > 100: # Basic sanity check
                samples.append({
                    "text": text,
                    "source": "gutenberg",
                    "id": f"gutenberg_{count}"
                })
                count += 1
        
        if count == 0:
            raise RuntimeError("Failed to retrieve any valid samples from Gutenberg dataset.")
        
        logger.info(f"Successfully fetched {count} Gutenberg samples.")
        return samples

    except Exception as e:
        # Fail loudly - no fallback
        error_msg = f"CRITICAL: Failed to download Gutenberg data from {GUTENBERG_DATASET_ID}. " \
                    f"This is a real data source requirement. Error: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def fetch_the_stack_samples(num_samples: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetches code samples from The Stack via Hugging Face.
    
    Args:
        num_samples: Number of samples to retrieve.
        
    Returns:
        List of dictionaries with 'text' and 'source' keys.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    setup_logging()
    logger.info(f"Fetching {num_samples} samples from The Stack (Hugging Face)...")
    
    try:
        # Load dataset in streaming mode
        # Using 'content' as the text field for the-stack
        dataset = load_dataset(
            THE_STACK_DATASET_ID,
            split=THE_STACK_SPLIT,
            streaming=True,
            trust_remote_code=True
        )
        
        samples = []
        count = 0
        for item in dataset:
            if count >= num_samples:
                break
            
            text = item.get('content', '')
            if text and len(text) > 50:
                samples.append({
                    "text": text,
                    "source": "the-stack",
                    "id": f"stack_{count}",
                    "language": item.get('language', 'unknown')
                })
                count += 1
        
        if count == 0:
            raise RuntimeError("Failed to retrieve any valid samples from The Stack dataset.")
        
        logger.info(f"Successfully fetched {count} The Stack samples.")
        return samples

    except Exception as e:
        # Fail loudly - no fallback
        error_msg = f"CRITICAL: Failed to download The Stack data from {THE_STACK_DATASET_ID}. " \
                    f"This is a real data source requirement. Error: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def save_samples_to_jsonl(samples: List[Dict[str, Any]], filepath: Path):
    """
    Saves a list of samples to a JSONL file.
    
    Args:
        samples: List of sample dictionaries.
        filepath: Path to the output file.
    """
    setup_logging()
    logger.info(f"Saving {len(samples)} samples to {filepath}...")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    logger.info(f"Saved {len(samples)} samples to {filepath}")

def combine_and_save_corpus(gutenberg_samples: List[Dict], stack_samples: List[Dict], output_path: Path):
    """
    Combines samples from both sources and saves to the final micro-corpus file.
    """
    setup_logging()
    all_samples = gutenberg_samples + stack_samples
    save_samples_to_jsonl(all_samples, output_path)
    logger.info(f"Combined corpus saved to {output_path} with {len(all_samples)} total samples.")

def main():
    """
    Main entry point for downloading the micro-corpus.
    """
    setup_logging()
    logger.info("Starting Micro-Corpus download process...")
    
    # Configuration
    NUM_GUTENBERG_SAMPLES = 2000
    NUM_STACK_SAMPLES = 2000
    
    gutenberg_path = DATA_RAW_DIR / "gutenberg_samples.jsonl"
    stack_path = DATA_RAW_DIR / "the_stack_samples.jsonl"
    combined_path = DATA_RAW_DIR / "micro_corpus_combined.jsonl"
    
    try:
        # 1. Fetch Gutenberg
        gutenberg_samples = fetch_gutenberg_samples(NUM_GUTENBERG_SAMPLES)
        save_samples_to_jsonl(gutenberg_samples, gutenberg_path)
        
        # 2. Fetch The Stack
        stack_samples = fetch_the_stack_samples(NUM_STACK_SAMPLES)
        save_samples_to_jsonl(stack_samples, stack_path)
        
        # 3. Combine
        combine_and_save_corpus(gutenberg_samples, stack_samples, combined_path)
        
        logger.info("Micro-Corpus download completed successfully.")
        
    except RuntimeError as e:
        # Re-raise to ensure the pipeline fails loudly
        logger.critical(str(e))
        raise e
    except Exception as e:
        logger.critical(f"Unexpected error during download: {str(e)}")
        raise e

if __name__ == "__main__":
    main()