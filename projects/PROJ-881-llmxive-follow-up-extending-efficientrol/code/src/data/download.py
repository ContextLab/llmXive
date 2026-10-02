"""
Dataset download module for llmXive pipeline.

Fetches GSM8K and MiniGrid datasets from HuggingFace Datasets with
streaming support and strict example capping.

CRITICAL: No synthetic fallbacks. If data fetch fails, raises ConnectionError
or FileNotFoundError immediately.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterator
from itertools import islice
from datasets import load_dataset
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_EXAMPLES = 500
GSM8K_DATASET_NAME = "gsm8k"
GSM8K_CONFIG = "main"
MINIGRID_DATASET_NAME = "MiniGrid"
MINIGRID_CONFIG = "MiniGrid-BlockedEmpty-8x8-v0"  # Specific subset as per common usage

# Output paths relative to project root
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
GSM8K_OUTPUT = OUTPUT_DIR / "gsm8k_subset.jsonl"
MINIGRID_OUTPUT = OUTPUT_DIR / "minigrid_subset.jsonl"

def _ensure_output_dir():
    """Ensure output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _check_memory_usage():
    """Check if memory usage is critically high (>90%)."""
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 90:
        logger.warning(f"Memory usage critical: {memory_percent}%")
    return memory_percent

def download_gsm8k_subset(
    max_examples: int = DEFAULT_MAX_EXAMPLES,
    output_path: Optional[Path] = None
) -> Path:
    """
    Download GSM8K dataset with streaming and example capping.
    
    Args:
        max_examples: Maximum number of examples to fetch (default 500).
        output_path: Optional custom output path.
        
    Returns:
        Path to the downloaded JSONL file.
        
    Raises:
        ConnectionError: If dataset fetch fails.
        FileNotFoundError: If dataset not found.
    """
    if output_path is None:
        output_path = GSM8K_OUTPUT
        
    _ensure_output_dir()
    _check_memory_usage()
    
    logger.info(f"Downloading GSM8K subset (max {max_examples} examples)...")
    
    try:
        # Load dataset in streaming mode to avoid loading entire dataset into memory
        dataset = load_dataset(
            GSM8K_DATASET_NAME,
            GSM8K_CONFIG,
            split="train",
            streaming=True
        )
        
        # Apply example cap using islice
        limited_dataset = islice(dataset, max_examples)
        
        # Write to JSONL file
        with open(output_path, 'w', encoding='utf-8') as f:
            count = 0
            for example in limited_dataset:
                # Convert to JSONL format
                json_line = json.dumps(example, ensure_ascii=False)
                f.write(json_line + '\n')
                count += 1
                
                # Check memory periodically
                if count % 50 == 0:
                    _check_memory_usage()
                    
        logger.info(f"Successfully downloaded {count} GSM8K examples to {output_path}")
        return output_path
        
    except Exception as e:
        # Fail loudly - no synthetic fallback
        error_msg = f"Failed to download GSM8K dataset: {str(e)}"
        logger.error(error_msg)
        if "404" in str(e) or "not found" in str(e).lower():
            raise FileNotFoundError(error_msg) from e
        raise ConnectionError(error_msg) from e

def download_minigrid_subset(
    max_examples: int = DEFAULT_MAX_EXAMPLES,
    output_path: Optional[Path] = None
) -> Path:
    """
    Download MiniGrid dataset with streaming and example capping.
    
    Args:
        max_examples: Maximum number of examples to fetch (default 500).
        output_path: Optional custom output path.
        
    Returns:
        Path to the downloaded JSONL file.
        
    Raises:
        ConnectionError: If dataset fetch fails.
        FileNotFoundError: If dataset not found.
    """
    if output_path is None:
        output_path = MINIGRID_OUTPUT
        
    _ensure_output_dir()
    _check_memory_usage()
    
    logger.info(f"Downloading MiniGrid subset (max {max_examples} examples)...")
    
    try:
        # Load dataset in streaming mode
        # Note: Using a specific MiniGrid environment config
        dataset = load_dataset(
            MINIGRID_DATASET_NAME,
            MINIGRID_CONFIG,
            split="train",
            streaming=True
        )
        
        # Apply example cap using islice
        limited_dataset = islice(dataset, max_examples)
        
        # Write to JSONL file
        with open(output_path, 'w', encoding='utf-8') as f:
            count = 0
            for example in limited_dataset:
                # Convert to JSONL format
                json_line = json.dumps(example, ensure_ascii=False)
                f.write(json_line + '\n')
                count += 1
                
                # Check memory periodically
                if count % 50 == 0:
                    _check_memory_usage()
                    
        logger.info(f"Successfully downloaded {count} MiniGrid examples to {output_path}")
        return output_path
        
    except Exception as e:
        # Fail loudly - no synthetic fallback
        error_msg = f"Failed to download MiniGrid dataset: {str(e)}"
        logger.error(error_msg)
        if "404" in str(e) or "not found" in str(e).lower():
            raise FileNotFoundError(error_msg) from e
        raise ConnectionError(error_msg) from e

def download_all_datasets(
    max_examples_gsm8k: int = DEFAULT_MAX_EXAMPLES,
    max_examples_minigrid: int = DEFAULT_MAX_EXAMPLES,
    output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """
    Download both GSM8K and MiniGrid datasets.
    
    Args:
        max_examples_gsm8k: Max examples for GSM8K.
        max_examples_minigrid: Max examples for MiniGrid.
        output_dir: Optional custom output directory.
        
    Returns:
        Dictionary mapping dataset names to their output paths.
    """
    results = {}
    
    if output_dir:
        global GSM8K_OUTPUT, MINIGRID_OUTPUT
        GSM8K_OUTPUT = output_dir / "gsm8k_subset.jsonl"
        MINIGRID_OUTPUT = output_dir / "minigrid_subset.jsonl"
        
    try:
        results['gsm8k'] = download_gsm8k_subset(max_examples_gsm8k)
    except Exception as e:
        logger.error(f"GSM8K download failed: {e}")
        raise
        
    try:
        results['minigrid'] = download_minigrid_subset(max_examples_minigrid)
    except Exception as e:
        logger.error(f"MiniGrid download failed: {e}")
        raise
        
    return results

def main():
    """Main entry point for dataset download."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download GSM8K and MiniGrid datasets")
    parser.add_argument(
        "--max-examples",
        type=int,
        default=DEFAULT_MAX_EXAMPLES,
        help=f"Maximum examples per dataset (default: {DEFAULT_MAX_EXAMPLES})"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Custom output directory"
    )
    parser.add_argument(
        "--only-gsm8k",
        action="store_true",
        help="Download only GSM8K"
    )
    parser.add_argument(
        "--only-minigrid",
        action="store_true",
        help="Download only MiniGrid"
    )
    
    args = parser.parse_args()
    
    try:
        if args.only_gsm8k:
            path = download_gsm8k_subset(args.max_examples, args.output_dir)
            print(f"Downloaded GSM8K to: {path}")
        elif args.only_minigrid:
            path = download_minigrid_subset(args.max_examples, args.output_dir)
            print(f"Downloaded MiniGrid to: {path}")
        else:
            results = download_all_datasets(
                args.max_examples,
                args.max_examples,
                args.output_dir
            )
            print("Downloaded datasets:")
            for name, path in results.items():
                print(f"  {name}: {path}")
                
    except (ConnectionError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
