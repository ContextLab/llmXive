"""
Strict dataset loader for llmXive simulation pipeline.

Implements T018: Strict dataset loader that raises DataUnavailableError
on fetch failure without synthetic fallback.
"""
import os
import sys
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

# Attempt to import datasets from Hugging Face
try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logging.warning("datasets library not available. Install with: pip install datasets")

from config import get_current_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataUnavailableError(Exception):
    """
    Raised when a real dataset cannot be fetched or loaded.
    
    This error is specifically designed to be caught by T015b (fallback logic)
    to trigger synthetic data generation. It must NOT be caught or suppressed
    in this loader.
    """
    def __init__(self, message: str, source: Optional[str] = None):
        super().__init__(message)
        self.source = source
        self.message = message


def load_real_dataset(
    dataset_id: str = "lhoelzl/eco_simulation_v1",
    split: str = "train",
    streaming: bool = True,
    cache_dir: Optional[str] = None
) -> Any:
    """
    Load a real dataset from Hugging Face Hub.
    
    Args:
        dataset_id: The Hugging Face dataset identifier.
        split: The dataset split to load.
        streaming: If True, stream the dataset (memory efficient).
        cache_dir: Optional cache directory for the dataset.
        
    Returns:
        The loaded dataset object (Dataset or IterableDataset).
        
    Raises:
        DataUnavailableError: If the dataset cannot be fetched or loaded.
        ImportError: If the datasets library is not installed.
    """
    if not HF_AVAILABLE:
        raise DataUnavailableError(
            "Hugging Face datasets library not installed.",
            source="pip-install"
        )

    logger.info(f"Attempting to load real dataset: {dataset_id}")
    
    try:
        if streaming:
            dataset = load_dataset(
                dataset_id,
                split=split,
                streaming=True,
                cache_dir=cache_dir
            )
        else:
            dataset = load_dataset(
                dataset_id,
                split=split,
                cache_dir=cache_dir
            )
        
        logger.info(f"Successfully loaded dataset: {dataset_id}")
        return dataset
        
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {str(e)}")
        raise DataUnavailableError(
            f"Failed to fetch real dataset '{dataset_id}': {str(e)}",
            source=dataset_id
        ) from e


def load_from_local_path(
    file_path: str,
    file_format: str = "parquet"
) -> Any:
    """
    Load dataset from a local file.
    
    Args:
        file_path: Path to the local file.
        file_format: Format of the file (parquet, csv, json).
        
    Returns:
        The loaded dataset object.
        
    Raises:
        DataUnavailableError: If the file cannot be loaded.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise DataUnavailableError(
            f"Local dataset file not found: {file_path}",
            source=file_path
        )
    
    try:
        if file_format == "parquet":
            import pandas as pd
            df = pd.read_parquet(file_path)
            return df
        elif file_format == "csv":
            import pandas as pd
            df = pd.read_csv(file_path)
            return df
        elif file_format == "json":
            import pandas as pd
            df = pd.read_json(file_path)
            return df
        else:
            raise DataUnavailableError(
                f"Unsupported file format: {file_format}",
                source=file_path
            )
            
    except Exception as e:
        logger.error(f"Failed to load local file {file_path}: {str(e)}")
        raise DataUnavailableError(
            f"Failed to load local dataset '{file_path}': {str(e)}",
            source=file_path
        ) from e


def load_simulation_dataset(
    use_streaming: bool = True,
    local_path: Optional[str] = None
) -> Any:
    """
    Main entry point for loading simulation datasets.
    
    This function attempts to load the real dataset. If it fails,
    it raises DataUnavailableError which will be caught by T015b
    to trigger fallback logic.
    
    Args:
        use_streaming: Whether to stream the dataset.
        local_path: Optional local path to load from instead of remote.
        
    Returns:
        The loaded dataset.
        
    Raises:
        DataUnavailableError: If the dataset cannot be loaded from any source.
    """
    logger.info("Starting dataset loading process")
    
    # Try local path first if provided
    if local_path:
        try:
            return load_from_local_path(local_path)
        except DataUnavailableError:
            logger.warning(f"Local path failed, attempting remote dataset")
    
    # Try remote dataset
    try:
        return load_real_dataset(
            dataset_id="lhoelzl/eco_simulation_v1",
            streaming=use_streaming
        )
    except DataUnavailableError as e:
        # Re-raise to allow T015b to handle fallback
        raise e


def main():
    """
    Command-line interface for testing the loader.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test the strict dataset loader"
    )
    parser.add_argument(
        "--local-path",
        type=str,
        default=None,
        help="Path to local dataset file"
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Load entire dataset into memory"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify dataset can be iterated"
    )
    
    args = parser.parse_args()
    
    try:
        dataset = load_simulation_dataset(
            use_streaming=not args.no_stream,
            local_path=args.local_path
        )
        
        print(f"Dataset loaded successfully: {dataset}")
        
        if args.verify:
            logger.info("Verifying dataset by iterating...")
            count = 0
            for item in dataset:
                count += 1
                if count >= 5:
                    break
            print(f"Verified {count} items from dataset")
            
    except DataUnavailableError as e:
        print(f"ERROR: {e.message}")
        print(f"Source: {e.source}")
        print("This error should be caught by fallback logic (T015b)")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(2)


if __name__ == "__main__":
    main()
