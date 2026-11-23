import sys
import json
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List, Callable
from datasets import load_dataset
import pandas as pd
import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

def load_config() -> Dict[str, Any]:
    """Load configuration from settings.yaml."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_deepfashion2_streaming() -> Generator[Dict[str, Any], None, None]:
    """
    Load DeepFashion2 dataset in strict streaming mode.
    
    This function enforces streaming=True to prevent OOM errors on large datasets.
    It explicitly raises RuntimeError if the fetch fails, ensuring no synthetic
    fallback is used.
    
    Returns:
        Generator yielding records from the DeepFashion2 dataset.
        
    Raises:
        RuntimeError: If the dataset fetch fails or streaming mode is unavailable.
        FileNotFoundError: If the dataset configuration is invalid.
    """
    try:
        # Strict streaming mode as per FR-002
        dataset = load_dataset(
            "DeepFashion2",
            "deepfashion2_image",
            split="train",
            streaming=True,
            trust_remote_code=False
        )
        
        # Verify streaming is actually enabled
        if not hasattr(dataset, 'streaming') or not dataset.streaming:
            raise RuntimeError("Streaming mode was not enabled for the dataset")
        
        return dataset
        
    except Exception as e:
        # Fail loudly - no synthetic fallback
        raise RuntimeError(f"Failed to load DeepFashion2 dataset in streaming mode: {str(e)}")

def process_batch(batch: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process a batch of records from the streaming dataset.
    
    Args:
        batch: A batch of records from the dataset.
        
    Returns:
        List of processed records.
    """
    processed = []
    for record in batch:
        processed_record = {
            'image_id': record.get('image_id'),
            'image_path': record.get('file_name'),
            'annotations': record.get('annotations', []),
            'attributes': record.get('attributes', {})
        }
        processed.append(processed_record)
    return processed

def iterate_dataset(
    dataset: Generator[Dict[str, Any], None, None],
    batch_size: int = 32,
    transform: Optional[Callable[[Dict[str, Any]], Any]] = None
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Iterate over the dataset in batches with optional transformation.
    
    Args:
        dataset: Streaming dataset generator.
        batch_size: Number of records per batch.
        transform: Optional transformation function to apply to each record.
        
    Yields:
        Batches of processed records.
    """
    batch = []
    for record in dataset:
        if transform:
            record = transform(record)
        batch.append(record)
        
        if len(batch) >= batch_size:
            yield batch
            batch = []
    
    # Yield remaining records
    if batch:
        yield batch

def get_dataset_info(dataset: Generator[Dict[str, Any], None, None]) -> Dict[str, Any]:
    """
    Get basic information about the dataset structure.
    
    Note: In streaming mode, we can only infer structure from the first record.
    
    Args:
        dataset: Streaming dataset generator.
        
    Returns:
        Dictionary containing dataset information.
    """
    try:
        # Get first record to infer structure
        first_record = next(dataset)
        
        info = {
            'total_records': 'Unknown (streaming mode)',
            'features': list(first_record.keys()),
            'sample_record': {k: str(type(v)) for k, v in first_record.items()}
        }
        
        return info
    except StopIteration:
        return {
            'total_records': 0,
            'features': [],
            'sample_record': {}
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get dataset info: {str(e)}")

def main():
    """Main function to demonstrate streaming loader functionality."""
    print("Loading DeepFashion2 dataset in streaming mode...")
    
    try:
        dataset = load_deepfashion2_streaming()
        print("Dataset loaded successfully in streaming mode")
        
        # Get dataset info
        info = get_dataset_info(dataset)
        print(f"Dataset features: {info['features']}")
        
        # Iterate over a small sample
        count = 0
        for batch in iterate_dataset(dataset, batch_size=10):
            processed = process_batch(batch)
            count += len(processed)
            print(f"Processed batch of {len(processed)} records (total: {count})")
            
            if count >= 50:  # Limit for demonstration
                break
        
        print(f"Successfully processed {count} records from streaming dataset")
        
    except RuntimeError as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()