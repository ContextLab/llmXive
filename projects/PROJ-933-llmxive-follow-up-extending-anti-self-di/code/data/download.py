import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from data.fetch_utils import DataFetchError, load_real_dataset, validate_dataset_structure, compute_dataset_checksum

def fetch_ultrafeedback(
    cache_dir: Optional[Path] = None,
    streaming: bool = True
) -> Any:
    """
    Fetch the UltraFeedback dataset from HuggingFace Hub.
    
    Args:
        cache_dir: Directory to cache the dataset (optional)
        streaming: If True, stream the dataset instead of loading into memory
    
    Returns:
        Dataset or IterableDataset object
    
    Raises:
        DataFetchError: If the dataset cannot be fetched
    """
    dataset_name = "HuggingFaceH4/ultrafeedback"
    
    try:
        dataset = load_real_dataset(dataset_name, split="train", streaming=streaming)
        
        # Validate structure
        required_fields = ['prompt', 'responses', 'ratings']
        validate_dataset_structure(dataset, required_fields)
        
        # Compute checksum for verification
        checksum = compute_dataset_checksum(dataset)
        print(f"UltraFeedback dataset fetched successfully. Checksum: {checksum}")
        
        return dataset
    
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Failed to fetch UltraFeedback: {str(e)}") from e

def fetch_dolly(
    cache_dir: Optional[Path] = None,
    streaming: bool = True
) -> Any:
    """
    Fetch the Dolly dataset from HuggingFace Hub.
    
    Args:
        cache_dir: Directory to cache the dataset (optional)
        streaming: If True, stream the dataset instead of loading into memory
    
    Returns:
        Dataset or IterableDataset object
    
    Raises:
        DataFetchError: If the dataset cannot be fetched
    """
    dataset_name = "databricks/databricks-dolly-15k"
    
    try:
        dataset = load_real_dataset(dataset_name, split="train", streaming=streaming)
        
        # Validate structure
        required_fields = ['instruction', 'context', 'response']
        validate_dataset_structure(dataset, required_fields)
        
        # Compute checksum for verification
        checksum = compute_dataset_checksum(dataset)
        print(f"Dolly dataset fetched successfully. Checksum: {checksum}")
        
        return dataset
    
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Failed to fetch Dolly: {str(e)}") from e

def main():
    """Main function to demonstrate data fetching with error handling."""
    print("Starting data fetch with strict error handling...")
    
    try:
        # Fetch UltraFeedback
        print("\nFetching UltraFeedback...")
        ultrafeedback = fetch_ultrafeedback(streaming=True)
        print(f"UltraFeedback loaded: {type(ultrafeedback)}")
        
        # Fetch Dolly
        print("\nFetching Dolly...")
        dolly = fetch_dolly(streaming=True)
        print(f"Dolly loaded: {type(dolly)}")
        
        print("\n✓ All datasets fetched successfully!")
        print("Note: If any fetch fails, a DataFetchError is raised.")
        print("No synthetic data is ever generated as a fallback.")
        
    except DataFetchError as e:
        print(f"\n✗ Data fetch failed: {e}")
        print("This error indicates a real data fetch failure.")
        print("The system will NOT fall back to synthetic data.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()