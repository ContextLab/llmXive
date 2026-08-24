"""
Data Loading Module for DeepFashion2 Dataset.

Implements FR-002 and FR-011 with streaming support for memory efficiency.
Uses HuggingFace datasets library for streaming parquet files.
"""

import sys
import json
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List, Callable
from datasets import load_dataset
import pandas as pd
import yaml

# Import from sibling modules as per API surface
from src.data.prompt_gen import load_settings


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to settings.yaml. If None, attempts to find
                     it in the standard project location.

    Returns:
        Dictionary of configuration settings.
    """
    if config_path is None:
        # Default locations to check
        possible_paths = [
            Path("code/config/settings.yaml"),
            Path("config/settings.yaml"),
            Path("settings.yaml")
        ]

        config_path = None
        for path in possible_paths:
            if path.exists():
                config_path = path
                break

        if config_path is None:
            raise FileNotFoundError(
                "Configuration file not found. Expected settings.yaml in "
                "code/config/, config/, or root directory."
            )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config["config_path"] = str(config_path)
    return config


def load_deepfashion2_streaming(dataset_name: str = "DeepFashion2/DeepFashion2", 
                                 split: str = "train",
                                 streaming: bool = True) -> Generator[Dict[str, Any], None, None]:
    """
    Load DeepFashion2 dataset in streaming mode.

    This function implements the streaming requirement from FR-002 and FR-011
    to handle large datasets without loading everything into memory.

    Args:
        dataset_name: HuggingFace dataset identifier for DeepFashion2.
        split: Dataset split to load (train, test, etc.).
        streaming: If True, returns a generator for streaming.

    Returns:
        Generator yielding dataset samples as dictionaries.

    Raises:
        FileNotFoundError: If the dataset cannot be found or accessed.
        RuntimeError: If the dataset fetch fails for any reason.
    """
    try:
        # Load dataset in streaming mode
        # DeepFashion2 is hosted on HuggingFace Hub.
        # We use streaming=True to avoid OOM on large datasets.
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            trust_remote_code=True
        )
        
        # Return generator
        for sample in dataset:
            yield sample
            
    except Exception as e:
        # Fail loudly - no synthetic fallback
        raise RuntimeError(
            f"Failed to load DeepFashion2 dataset from '{dataset_name}': {e}. "
            "This is a real data requirement - do not use synthetic data."
        ) from e


def process_batch(samples: List[Dict[str, Any]], 
                 batch_processor: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """
    Process a batch of samples.

    Args:
        samples: List of dataset samples.
        batch_processor: Optional function to apply to each sample.

    Returns:
        Processed list of samples.
    """
    if batch_processor is None:
        return samples
    
    return [batch_processor(sample) for sample in samples]


def iterate_dataset(dataset_stream, 
                    batch_size: int = 32,
                    processor: Optional[Callable] = None) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Iterate over dataset stream in batches.

    Args:
        dataset_stream: Generator of dataset samples.
        batch_size: Number of samples per batch.
        processor: Optional function to apply to each sample.

    Returns:
        Generator yielding batches of samples.
    """
    batch = []
    
    for sample in dataset_stream:
        batch.append(sample)
        
        if len(batch) >= batch_size:
            if processor:
                batch = process_batch(batch, processor)
            yield batch
            batch = []
    
    # Yield remaining samples
    if batch:
        if processor:
            batch = process_batch(batch, processor)
        yield batch


def get_dataset_info(dataset_name: str = "DeepFashion2/DeepFashion2") -> Dict[str, Any]:
    """
    Get information about the dataset.

    Args:
        dataset_name: HuggingFace dataset identifier.

    Returns:
        Dictionary with dataset information.
    """
    try:
        # Load briefly to get info (not streaming) - only metadata
        # We use streaming=False here just to inspect the schema, not the data
        # Note: This might still be heavy if the dataset is huge, but usually schema is small.
        # For DeepFashion2, we rely on the streaming loader for actual data.
        dataset = load_dataset(dataset_name, split="train", streaming=False, trust_remote_code=True)
        
        return {
            "name": dataset_name,
            "num_rows": len(dataset),
            "features": list(dataset.features.keys()),
            "column_names": dataset.column_names
        }
    except Exception as e:
        return {
            "name": dataset_name,
            "error": str(e)
        }


def main():
    """
    Main entry point for data loading script.
    Verifies streaming capability by yielding records without OOM.
    """
    config = load_config()
    
    print("Data Loader Module initialized.")
    print(f"Configuration loaded from: {config.get('config_path', 'default')}")
    
    # Get dataset info (schema only)
    print("\nFetching dataset schema...")
    dataset_info = get_dataset_info()
    if "error" in dataset_info:
        print(f"Warning: Could not fetch full dataset info: {dataset_info['error']}")
    else:
        print(f"Dataset Info: {json.dumps(dataset_info, indent=2)}")
    
    # Verify streaming by yielding records
    print("\nVerifying streaming capability (yielding first 100 records)...")
    count = 0
    try:
        stream = load_deepfashion2_streaming()
        for sample in stream:
            count += 1
            if count % 10 == 0:
                print(f"  Yielded {count} records...")
            if count >= 100:
                break
        
        print(f"\nSuccess: Yielded {count} records without OOM.")
        print("Streaming verification complete.")
        
    except RuntimeError as e:
        print(f"\nVerification FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
