"""
Download Micro-Corpus from Project Gutenberg and The Stack.

This script fetches data streams from two real sources:
1. Project Gutenberg (via the 'gutenberg' dataset on Hugging Face)
2. The Stack (via 'bigcode/the-stack-smol' dataset)

It uses streaming to avoid loading the entire dataset into memory at once,
adhering to CPU constraints. The script fails loudly if data sources are
unreachable, with no synthetic fallbacks.
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datasets import load_dataset
from utils.logging import get_logger, info, error, warning, setup_logging
from utils.config import get_config, get_raw_dir, ConfigError

logger = get_logger(__name__)

# Configuration constants
GUTENBERG_DATASET = "gutenberg"
THE_STACK_DATASET = "bigcode/the-stack-smol"
THE_STACK_SPLIT = "train"
GUTENBERG_SPLIT = "train"

# Target sample sizes (approximate, for streaming limits)
# These are soft limits for the streaming process to ensure we get a representative sample
# without waiting for the entire massive dataset.
GUTENBERG_MAX_SAMPLES = 50000  # ~50k books/articles
THE_STACK_MAX_SAMPLES = 200000 # ~200k code snippets

def setup_logging():
    """Initialize logging for the script."""
    setup_logging()

def fetch_gutenberg_samples() -> Generator[Dict[str, Any], None, None]:
    """
    Fetch samples from Project Gutenberg using streaming.
    
    Yields:
        Dict containing 'text' and 'source' fields.
    """
    logger.info(f"Fetching Project Gutenberg samples from {GUTENBERG_DATASET}...")
    try:
        dataset = load_dataset(GUTENBERG_DATASET, split=GUTENBERG_SPLIT, streaming=True)
        count = 0
        for item in dataset:
            if count >= GUTENBERG_MAX_SAMPLES:
                logger.info(f"Reached Gutenberg sample limit: {GUTENBERG_MAX_SAMPLES}")
                break
            
            # Gutenberg dataset typically has 'text' and 'bookid'
            text = item.get('text', '')
            if text and len(text.strip()) > 100: # Filter very short entries
                yield {
                    "text": text,
                    "source": "gutenberg",
                    "id": f"gutenberg_{item.get('bookid', count)}",
                    "raw_length": len(text)
                }
                count += 1
                
            if count % 10000 == 0:
                logger.info(f"Processed {count} Gutenberg samples...")
                
    except Exception as e:
        error(f"Failed to fetch Gutenberg data: {e}")
        raise

def fetch_the_stack_samples() -> Generator[Dict[str, Any], None, None]:
    """
    Fetch samples from The Stack using streaming.
    
    Yields:
        Dict containing 'text' and 'source' fields.
    """
    logger.info(f"Fetching The Stack samples from {THE_STACK_DATASET}...")
    try:
        # The Stack Smol is a smaller, filtered version suitable for CPU constraints
        dataset = load_dataset(THE_STACK_DATASET, split=THE_STACK_SPLIT, streaming=True)
        count = 0
        
        for item in dataset:
            if count >= THE_STACK_MAX_SAMPLES:
                logger.info(f"Reached The Stack sample limit: {THE_STACK_MAX_SAMPLES}")
                break
            
            # The Stack typically has 'content' or 'text' depending on the version
            # We check common keys
            text = item.get('content') or item.get('text', '')
            
            if text and len(text.strip()) > 100:
                yield {
                    "text": text,
                    "source": "the_stack",
                    "id": f"stack_{count}",
                    "raw_length": len(text)
                }
                count += 1
                
            if count % 10000 == 0:
                logger.info(f"Processed {count} The Stack samples...")

    except Exception as e:
        error(f"Failed to fetch The Stack data: {e}")
        raise

def save_samples_to_jsonl(samples: List[Dict[str, Any]], output_path: Path):
    """
    Save a list of samples to a JSONL file.
    
    Args:
        samples: List of dictionaries to save.
        output_path: Path to the output file.
    """
    logger.info(f"Saving {len(samples)} samples to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    logger.info(f"Saved {len(samples)} samples to {output_path}")

def combine_and_save_corpus(
    gutenberg_samples: List[Dict[str, Any]], 
    stack_samples: List[Dict[str, Any]], 
    output_dir: Path
):
    """
    Combine samples from both sources and save to the raw directory.
    
    Args:
        gutenberg_samples: List of Gutenberg samples.
        stack_samples: List of The Stack samples.
        output_dir: Directory to save the combined corpus.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    combined_path = output_dir / "micro_corpus_raw.jsonl"
    
    logger.info(f"Combining {len(gutenberg_samples)} Gutenberg and {len(stack_samples)} Stack samples...")
    all_samples = gutenberg_samples + stack_samples
    
    save_samples_to_jsonl(all_samples, combined_path)
    
    # Calculate and log checksum
    checksum = hashlib.sha256()
    with open(combined_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            checksum.update(chunk)
    
    logger.info(f"Corpus saved to {combined_path}")
    logger.info(f"Total samples: {len(all_samples)}")
    logger.info(f"SHA-256: {checksum.hexdigest()}")
    
    return {
        "total_samples": len(all_samples),
        "gutenberg_count": len(gutenberg_samples),
        "stack_count": len(stack_samples),
        "output_path": str(combined_path),
        "sha256": checksum.hexdigest()
    }

def main():
    """Main entry point for downloading the micro-corpus."""
    setup_logging()
    
    try:
        config = get_config()
        raw_dir = get_raw_dir()
        
        info("Starting micro-corpus download...")
        
        # Fetch data streams
        gutenberg_gen = fetch_gutenberg_samples()
        stack_gen = fetch_the_stack_samples()
        
        # Collect samples (memory efficient for the target limits)
        gutenberg_samples = list(gutenberg_gen)
        stack_samples = list(stack_gen)
        
        if not gutenberg_samples:
            warning("No Gutenberg samples were retrieved. Check dataset availability.")
        if not stack_samples:
            warning("No The Stack samples were retrieved. Check dataset availability.")
        
        if not gutenberg_samples and not stack_samples:
            error("Failed to retrieve any data from sources. Aborting.")
            sys.exit(1)
        
        # Combine and save
        result = combine_and_save_corpus(gutenberg_samples, stack_samples, raw_dir)
        
        info("Micro-corpus download completed successfully.")
        info(f"Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        error(f"Critical error during download: {e}")
        raise

if __name__ == "__main__":
    main()