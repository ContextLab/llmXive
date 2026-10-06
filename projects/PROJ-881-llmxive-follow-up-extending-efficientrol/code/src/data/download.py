"""
Data download module for GSM8K and MiniGrid datasets.

Implements streaming download with explicit example capping (500 examples per dataset).
No synthetic fallbacks - fails loudly if real data cannot be fetched.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterator
from itertools import islice

# Import from existing API surface
from src.config import Config, load_env_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default cap as per FR-001
DEFAULT_MAX_SAMPLES = 500

def download_gsm8k_subset(
    output_path: Optional[Path] = None,
    max_samples: int = DEFAULT_MAX_SAMPLES
) -> Path:
    """
    Download GSM8K dataset from HuggingFace with streaming and example capping.
    
    Args:
        output_path: Path to save the downloaded dataset. Defaults to data/raw/gsm8k.jsonl
        max_samples: Maximum number of examples to download (default: 500 per FR-001)
    
    Returns:
        Path to the downloaded dataset file
    
    Raises:
        ConnectionError: If HuggingFace datasets cannot be fetched
        FileNotFoundError: If the dataset is not found
        RuntimeError: If download fails
    """
    if output_path is None:
        output_path = Path("data/raw/gsm8k.jsonl")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading GSM8K dataset (max {max_samples} examples) from HuggingFace...")
    
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError(
            "The 'datasets' package is required. Install it via: pip install datasets"
        ) from e
    
    try:
        # Load GSM8K dataset in streaming mode
        # GSM8K is available at: https://huggingface.co/datasets/gsm8k
        dataset = load_dataset(
            "gsm8k",
            "main",  # GSM8K has a "main" config
            split="train",
            streaming=True
        )
        
        # Apply example capping using itertools.islice
        # This ensures we only process the first max_samples examples
        capped_dataset = islice(dataset, max_samples)
        
        # Write to JSONL file
        written_count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in capped_dataset:
                # GSM8K schema: {"question": str, "answer": str, "id": str}
                # We store the full example
                f.write(json.dumps(example) + '\n')
                written_count += 1
                
                # Log progress every 100 examples
                if written_count % 100 == 0:
                    logger.info(f"  Downloaded {written_count} examples...")
        
        logger.info(f"Successfully downloaded {written_count} GSM8K examples to {output_path}")
        
        # Verify we got the expected number (or less if dataset is smaller)
        if written_count < max_samples:
            logger.warning(
                f"Dataset contained only {written_count} examples, "
                f"requested {max_samples}"
            )
        
        return output_path
        
    except Exception as e:
        # Re-raise with clear error message - NO synthetic fallback
        error_msg = (
            f"Failed to download GSM8K dataset from HuggingFace: {str(e)}. "
            "This is a real data fetch failure - no synthetic fallback will be used."
        )
        logger.error(error_msg)
        if isinstance(e, (ConnectionError, FileNotFoundError)):
            raise
        raise ConnectionError(error_msg) from e

def download_minigrid_subset(
    output_path: Optional[Path] = None,
    max_samples: int = DEFAULT_MAX_SAMPLES
) -> Path:
    """
    Download MiniGrid dataset from HuggingFace with streaming and example capping.
    
    Args:
        output_path: Path to save the downloaded dataset. Defaults to data/raw/minigrid.jsonl
        max_samples: Maximum number of examples to download (default: 500 per FR-001)
    
    Returns:
        Path to the downloaded dataset file
    
    Raises:
        ConnectionError: If HuggingFace datasets cannot be fetched
        FileNotFoundError: If the dataset is not found
        RuntimeError: If download fails
    """
    if output_path is None:
        output_path = Path("data/raw/minigrid.jsonl")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading MiniGrid dataset (max {max_samples} examples) from HuggingFace...")
    
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError(
            "The 'datasets' package is required. Install it via: pip install datasets"
        ) from e
    
    try:
        # Load MiniGrid dataset in streaming mode
        # Using minigrid from HuggingFace datasets
        # Available at: https://huggingface.co/datasets/maximeg/MiniGrid-10k
        # or similar MiniGrid variants
        # We'll try the most common one first
        dataset_name = "maximeg/MiniGrid-10k"
        
        try:
            dataset = load_dataset(
                dataset_name,
                split="train",
                streaming=True
            )
        except Exception as e:
            # Try alternative MiniGrid dataset if the first one fails
            logger.warning(
                f"Failed to load {dataset_name}, trying alternative: minigrid"
            )
            dataset_name = "minigrid"
            dataset = load_dataset(
                dataset_name,
                split="train",
                streaming=True
            )
        
        # Apply example capping using itertools.islice
        capped_dataset = islice(dataset, max_samples)
        
        # Write to JSONL file
        written_count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in capped_dataset:
                # MiniGrid schema varies by dataset version
                # Common fields: {"observation": dict, "action": int, "reward": float, 
                #                "done": bool, "info": dict, "id": str}
                # We store the full example
                f.write(json.dumps(example) + '\n')
                written_count += 1
                
                # Log progress every 100 examples
                if written_count % 100 == 0:
                    logger.info(f"  Downloaded {written_count} examples...")
        
        logger.info(f"Successfully downloaded {written_count} MiniGrid examples to {output_path}")
        
        # Verify we got the expected number (or less if dataset is smaller)
        if written_count < max_samples:
            logger.warning(
                f"Dataset contained only {written_count} examples, "
                f"requested {max_samples}"
            )
        
        return output_path
        
    except Exception as e:
        # Re-raise with clear error message - NO synthetic fallback
        error_msg = (
            f"Failed to download MiniGrid dataset from HuggingFace: {str(e)}. "
            "This is a real data fetch failure - no synthetic fallback will be used."
        )
        logger.error(error_msg)
        if isinstance(e, (ConnectionError, FileNotFoundError)):
            raise
        raise ConnectionError(error_msg) from e

def download_all_datasets(
    gsm8k_path: Optional[Path] = None,
    minigrid_path: Optional[Path] = None,
    max_samples: int = DEFAULT_MAX_SAMPLES
) -> Dict[str, Path]:
    """
    Download both GSM8K and MiniGrid datasets.
    
    Args:
        gsm8k_path: Path for GSM8K output. Defaults to data/raw/gsm8k.jsonl
        minigrid_path: Path for MiniGrid output. Defaults to data/raw/minigrid.jsonl
        max_samples: Maximum examples per dataset (default: 500 per FR-001)
    
    Returns:
        Dictionary mapping dataset names to their output paths
    """
    results = {}
    
    if gsm8k_path:
        results['gsm8k'] = download_gsm8k_subset(gsm8k_path, max_samples)
    else:
        results['gsm8k'] = download_gsm8k_subset(max_samples=max_samples)
    
    if minigrid_path:
        results['minigrid'] = download_minigrid_subset(minigrid_path, max_samples)
    else:
        results['minigrid'] = download_minigrid_subset(max_samples=max_samples)
    
    return results

def main():
    """Main entry point for dataset download."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download GSM8K and MiniGrid datasets with streaming and capping"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=DEFAULT_MAX_SAMPLES,
        help=f"Maximum examples per dataset (default: {DEFAULT_MAX_SAMPLES})"
    )
    parser.add_argument(
        "--gsm8k-path",
        type=str,
        default=None,
        help="Output path for GSM8K dataset"
    )
    parser.add_argument(
        "--minigrid-path",
        type=str,
        default=None,
        help="Output path for MiniGrid dataset"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_env_file()
    
    # Set output paths
    gsm8k_path = Path(args.gsm8k_path) if args.gsm8k_path else None
    minigrid_path = Path(args.minigrid_path) if args.minigrid_path else None
    
    try:
        results = download_all_datasets(
            gsm8k_path=gsm8k_path,
            minigrid_path=minigrid_path,
            max_samples=args.max_samples
        )
        
        logger.info("Download completed successfully:")
        for dataset_name, path in results.items():
            logger.info(f"  {dataset_name}: {path}")
        
        # Return exit code 0 on success
        return 0
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        # Return exit code 1 on failure
        return 1

if __name__ == "__main__":
    sys.exit(main())
