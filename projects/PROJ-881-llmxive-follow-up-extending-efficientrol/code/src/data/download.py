"""
Data download module for fetching GSM8K and MiniGrid datasets from HuggingFace.

This module provides functions to download real datasets programmatically.
It enforces strict real-data requirements: no synthetic fallbacks are permitted.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path if needed for imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from datasets import load_dataset, DatasetDict
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

# Constants for dataset configuration
GSM8K_CONFIG = "main"
MINIGRID_CONFIG = "MiniGrid-Empty-8x8-v0"  # Specific environment subset

# Output directories relative to project root
DATA_DIR = _project_root / "data"
GSM8K_OUTPUT = DATA_DIR / "gsm8k_subset.jsonl"
MINIGRID_OUTPUT = DATA_DIR / "minigrid_subset.jsonl"

# Representative subset limits to ensure tractability while maintaining real data distribution
GSM8K_LIMIT = 500  # ~500 problems from the 8.5k training set
MINIGRID_LIMIT = 200  # ~200 episodes from the environment


def _ensure_data_dir() -> Path:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def download_gsm8k_subset(
    output_path: Optional[Path] = None,
    limit: Optional[int] = None,
    streaming: bool = True
) -> Path:
    """
    Fetch a representative subset of the GSM8K dataset from HuggingFace.
    
    GSM8K contains grade school math word problems. This function downloads
    a subset to stay within memory constraints while preserving the real
    distribution of problem types and difficulty levels.
    
    Args:
        output_path: Path to write the output JSONL file. Defaults to data/gsm8k_subset.jsonl.
        limit: Maximum number of examples to fetch. Defaults to GSM8K_LIMIT (500).
        streaming: If True, stream the dataset instead of loading entirely into memory.
    
    Returns:
        Path to the written output file.
    
    Raises:
        ConnectionError: If the HuggingFace hub is unreachable.
        ValueError: If the dataset cannot be found or loaded.
        RuntimeError: If any step fails (no synthetic fallback).
    """
    if output_path is None:
        output_path = GSM8K_OUTPUT
    
    if limit is None:
        limit = GSM8K_LIMIT
    
    _ensure_data_dir()
    
    print(f"Fetching GSM8K subset (limit={limit}) from HuggingFace...")
    
    try:
        # Load the dataset using streaming to avoid OOM on large datasets
        dataset = load_dataset(
            "gsm8k",
            GSM8K_CONFIG,
            split="train",
            streaming=streaming
        )
        
        # Take a representative subset using islice
        # This ensures we get real data without loading everything
        from itertools import islice
        subset = list(islice(dataset, limit))
        
        if len(subset) == 0:
            raise RuntimeError("Failed to fetch any examples from GSM8K dataset.")
        
        # Write to JSONL format
        with open(output_path, "w", encoding="utf-8") as f:
            for item in subset:
                # GSM8K structure: {"question": str, "answer": str (with solution)}
                # We store the raw fields as provided by the dataset
                import json
                f.write(json.dumps(item) + "\n")
        
        print(f"Successfully wrote {len(subset)} GSM8K examples to {output_path}")
        return output_path
        
    except Exception as e:
        # Fail loudly - no synthetic fallback
        raise RuntimeError(f"Failed to download GSM8K dataset: {e}") from e


def download_minigrid_subset(
    output_path: Optional[Path] = None,
    limit: Optional[int] = None,
    streaming: bool = True
) -> Path:
    """
    Fetch a representative subset of the MiniGrid environment dataset from HuggingFace.
    
    MiniGrid is a collection of grid-world environments for reinforcement learning.
    This function downloads a subset of episodes from a specific environment to
    maintain tractability while preserving real data distribution.
    
    Args:
        output_path: Path to write the output JSONL file. Defaults to data/minigrid_subset.jsonl.
        limit: Maximum number of episodes to fetch. Defaults to MINIGRID_LIMIT (200).
        streaming: If True, stream the dataset instead of loading entirely into memory.
    
    Returns:
        Path to the written output file.
    
    Raises:
        ConnectionError: If the HuggingFace hub is unreachable.
        ValueError: If the dataset cannot be found or loaded.
        RuntimeError: If any step fails (no synthetic fallback).
    """
    if output_path is None:
        output_path = MINIGRID_OUTPUT
    
    if limit is None:
        limit = MINIGRID_LIMIT
    
    _ensure_data_dir()
    
    print(f"Fetching MiniGrid subset (limit={limit}) from HuggingFace...")
    
    try:
        # MiniGrid datasets are often available as specific environment variants
        # We use a common variant: MiniGrid-Empty-8x8-v0
        # Note: The exact dataset ID may vary; we use a standard one from HF Hub
        dataset_id = "MiniGrid/MiniGrid-Empty-8x8-v0"
        
        # Try to load the dataset
        try:
            dataset = load_dataset(
                dataset_id,
                split="train",
                streaming=streaming
            )
        except Exception as load_err:
            # Fallback to a known working MiniGrid dataset ID if the specific one fails
            # This is still fetching from a real source, not synthetic data
            dataset_id = "minigrid"
            try:
                dataset = load_dataset(
                    dataset_id,
                    "empty-8x8-v0",
                    split="train",
                    streaming=streaming
                )
            except Exception as inner_err:
                raise RuntimeError(
                    f"Could not load MiniGrid dataset. Tried '{dataset_id}' and specific variants. "
                    f"Original error: {load_err}, Fallback error: {inner_err}"
                ) from inner_err
        
        # Take a representative subset
        from itertools import islice
        subset = list(islice(dataset, limit))
        
        if len(subset) == 0:
            raise RuntimeError("Failed to fetch any examples from MiniGrid dataset.")
        
        # Write to JSONL format
        with open(output_path, "w", encoding="utf-8") as f:
            for item in subset:
                import json
                # MiniGrid items contain observations, actions, rewards, etc.
                # We store the raw item as provided by the dataset
                f.write(json.dumps(item) + "\n")
        
        print(f"Successfully wrote {len(subset)} MiniGrid examples to {output_path}")
        return output_path
        
    except Exception as e:
        # Fail loudly - no synthetic fallback
        raise RuntimeError(f"Failed to download MiniGrid dataset: {e}") from e


def download_all_datasets(
    gsm8k_limit: Optional[int] = None,
    minigrid_limit: Optional[int] = None,
    streaming: bool = True
) -> Dict[str, Path]:
    """
    Download both GSM8K and MiniGrid datasets.
    
    Args:
        gsm8k_limit: Limit for GSM8K subset.
        minigrid_limit: Limit for MiniGrid subset.
        streaming: Whether to use streaming mode.
    
    Returns:
        Dictionary mapping dataset name to output path.
    """
    results = {}
    
    try:
        results["gsm8k"] = download_gsm8k_subset(
            limit=gsm8k_limit,
            streaming=streaming
        )
    except Exception as e:
        print(f"Warning: GSM8K download failed: {e}")
        # Continue to try other datasets
    
    try:
        results["minigrid"] = download_minigrid_subset(
            limit=minigrid_limit,
            streaming=streaming
        )
    except Exception as e:
        print(f"Warning: MiniGrid download failed: {e}")
    
    if not results:
        raise RuntimeError("Failed to download any datasets. Check connectivity and dataset availability.")
    
    return results


def main():
    """Entry point for downloading datasets."""
    print("=" * 60)
    print("llmXive Data Download")
    print("=" * 60)
    
    try:
        paths = download_all_datasets()
        print("\nDownload Summary:")
        for name, path in paths.items():
            print(f"  {name}: {path} ({path.stat().st_size} bytes)")
        print("\nDownload complete.")
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
