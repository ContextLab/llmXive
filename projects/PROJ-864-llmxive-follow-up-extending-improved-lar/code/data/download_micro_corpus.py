"""
Download micro corpus from Project Gutenberg and The Stack.

This script fetches data streams from open-source datasets and
combines them into a single corpus file.
"""
import json
import os
import sys
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, info, error, warning, setup_logging
from utils.config import get_project_root, get_raw_dir, get_token_limit

logger = get_logger(__name__)

# Constants
TARGET_TOKENS = 1_000_000
MAX_SAMPLES = 50000  # Maximum number of samples to fetch
BATCH_SIZE = 1000

def setup_logging():
    """Setup logging for this module."""
    setup_logging()

def fetch_gutenberg_samples(
    max_samples: int = 10000
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch samples from Project Gutenberg via HuggingFace datasets.

    Args:
        max_samples: Maximum number of samples to fetch

    Yields:
        Dictionary containing sample data
    """
    try:
        from datasets import load_dataset
        
        logger.info("Loading Project Gutenberg dataset (streaming)...")
        # Use the 'gutenberg' dataset from HuggingFace
        dataset = load_dataset("gutenberg", "plain_text", streaming=True)
        
        sample_count = 0
        for split, data in dataset.items():
            for item in data:
                if sample_count >= max_samples:
                    return
                
                text = item.get('text', '')
                if text and len(text.strip()) > 100:  # Filter very short texts
                    sample_count += 1
                    yield {
                        'text': text.strip(),
                        'source': 'gutenberg',
                        'id': f"gutenberg_{sample_count}",
                        'split': split
                    }
                    
    except Exception as e:
        error(f"Failed to fetch Gutenberg samples: {e}")
        raise

def fetch_the_stack_samples(
    max_samples: int = 40000
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch samples from The Stack via HuggingFace datasets.

    Args:
        max_samples: Maximum number of samples to fetch

    Yields:
        Dictionary containing sample data
    """
    try:
        from datasets import load_dataset
        
        logger.info("Loading The Stack dataset (streaming)...")
        # Use a subset of The Stack (code data)
        # Note: The Stack is large, so we sample from it
        dataset = load_dataset("bigcode/the-stack", "data", streaming=True, 
                             split="train")
        
        sample_count = 0
        for item in dataset:
            if sample_count >= max_samples:
                return
            
            # Get text content
            text = item.get('content', '')
            if text and len(text.strip()) > 100:
                sample_count += 1
                yield {
                    'text': text.strip(),
                    'source': 'the_stack',
                    'id': f"stack_{sample_count}",
                    'language': item.get('language', 'unknown')
                }
                
    except Exception as e:
        error(f"Failed to fetch The Stack samples: {e}")
        raise

def count_tokens(text: str) -> int:
    """
    Estimate token count for a text.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Simple approximation: ~1.3 tokens per word
    words = len(text.split())
    return int(words * 1.3)

def count_lines(file_path: Path) -> int:
    """
    Count lines in a file.

    Args:
        file_path: Path to the file

    Returns:
        Number of lines
    """
    with open(file_path, 'r') as f:
        return sum(1 for _ in f)

def save_samples_to_jsonl(
    samples: Generator[Dict[str, Any], None, None],
    output_path: Path,
    target_tokens: int = TARGET_TOKENS
) -> Dict[str, Any]:
    """
    Save samples to a JSONL file until target tokens are reached.

    Args:
        samples: Generator yielding sample dictionaries
        output_path: Path to output file
        target_tokens: Target token count

    Returns:
        Statistics about the saved corpus
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    total_tokens = 0
    total_samples = 0
    start_time = time.time()
    
    logger.info(f"Saving samples to {output_path} (target: {target_tokens} tokens)")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            text = sample.get('text', '')
            token_count = count_tokens(text)
            
            if total_tokens + token_count > target_tokens and total_tokens > 0:
                logger.info(f"Reached target token count: {total_tokens}")
                break
            
            # Add token count to sample
            sample['estimated_tokens'] = token_count
            
            json_line = json.dumps(sample, ensure_ascii=False)
            f.write(json_line + '\n')
            
            total_tokens += token_count
            total_samples += 1
            
            if total_samples % 1000 == 0:
                elapsed = time.time() - start_time
                rate = total_samples / elapsed if elapsed > 0 else 0
                info(f"Saved {total_samples} samples ({total_tokens} tokens) - "
                     f"Rate: {rate:.2f} samples/sec")
    
    elapsed = time.time() - start_time
    stats = {
        'total_samples': total_samples,
        'total_tokens': total_tokens,
        'output_file': str(output_path),
        'elapsed_time_seconds': elapsed,
        'samples_per_second': total_samples / elapsed if elapsed > 0 else 0,
        'target_tokens': target_tokens,
        'target_met': total_tokens >= target_tokens
    }
    
    info(f"Saved {total_samples} samples with {total_tokens} tokens in {elapsed:.2f} seconds")
    return stats

def combine_and_save_corpus(
    output_path: Path,
    target_tokens: int = TARGET_TOKENS
) -> Dict[str, Any]:
    """
    Combine data from multiple sources and save to a single corpus file.

    Args:
        output_path: Path to output file
        target_tokens: Target token count

    Returns:
        Statistics about the combined corpus
    """
    # Fetch from both sources
    gutenberg_samples = fetch_gutenberg_samples(max_samples=10000)
    stack_samples = fetch_the_stack_samples(max_samples=40000)
    
    # Combine generators
    def combined_generator():
        for sample in gutenberg_samples:
            yield sample
        for sample in stack_samples:
            yield sample
    
    return save_samples_to_jsonl(combined_generator(), output_path, target_tokens)

def main():
    """Main entry point for the download_micro_corpus script."""
    setup_logging()
    
    project_root = get_project_root()
    raw_dir = get_raw_dir()
    
    output_path = raw_dir / "micro_corpus_raw.jsonl"
    
    if output_path.exists():
        warning(f"Output file already exists: {output_path}")
        response = input("Do you want to overwrite? (y/n): ").strip().lower()
        if response != 'y':
            info("Operation cancelled.")
            sys.exit(0)
    
    try:
        stats = combine_and_save_corpus(output_path)
        
        # Save stats
        stats_path = raw_dir / "download_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        info(f"Download complete. Stats saved to {stats_path}")
        
        if not stats['target_met']:
            warning(f"Target token count not met: {stats['total_tokens']} < {TARGET_TOKENS}")
            sys.exit(1)
        
    except Exception as e:
        error(f"Download failed: {e}")
        raise

if __name__ == "__main__":
    main()
