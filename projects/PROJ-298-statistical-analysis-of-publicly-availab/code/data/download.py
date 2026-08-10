"""
Download module for fetching Stack Overflow PostsTags data.

Implements robust error handling to enforce the "Fail Loudly" policy:
- Removes any fallback to synthetic/mock data.
- Raises ConnectionError or FileNotFoundError immediately if fetch fails.
- Uses streaming to handle large datasets within memory constraints.
"""
import os
import sys
from pathlib import Path
from typing import Generator, Dict, Any, Optional
import json

# Import datasets for HuggingFace streaming
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required for streaming data. "
        "Please install it via: pip install datasets"
    )

# Constants for data sources
HF_DATASET_NAME = "stack-exchange/stackoverflow-tags"
HF_SPLIT_NAME = "train"  # Adjust if a specific split exists, otherwise default
SO_DUMP_URL = "https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z"

# Output paths
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "posts_tags.jsonl"


def ensure_output_dir() -> Path:
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def fetch_posts_tags_streaming() -> Generator[Dict[str, Any], None, None]:
    """
    Fetches PostsTags data from HuggingFace using streaming mode.
    
    This function enforces a "Fail Loudly" policy:
    - If the dataset is not found or cannot be accessed, it raises a ConnectionError.
    - No synthetic data is generated as a fallback.
    
    Yields:
        Dict[str, Any]: A dictionary representing a single post/tag record.
        
    Raises:
        ConnectionError: If the dataset fetch fails or the source is unreachable.
        FileNotFoundError: If the specific dataset configuration is missing.
    """
    try:
        # Attempt to load the dataset in streaming mode
        # This avoids downloading the full dataset to disk/memory immediately
        dataset = load_dataset(
            HF_DATASET_NAME,
            split=HF_SPLIT_NAME,
            streaming=True,
            trust_remote_code=False
        )
        
        # Verify the dataset has content by attempting to fetch the first item
        # This forces a connection check without loading everything
        iterator = iter(dataset)
        try:
            first_item = next(iterator)
            # Re-yield the first item
            yield first_item
        except StopIteration:
            raise FileNotFoundError(
                f"The dataset '{HF_DATASET_NAME}' (split '{HF_SPLIT_NAME}') appears to be empty."
            )
        
        # Stream the rest of the dataset
        for item in iterator:
            yield item

    except Exception as e:
        # Explicitly handle and re-raise as a clear failure
        # We do NOT catch and return synthetic data here.
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            raise FileNotFoundError(
                f"Failed to locate dataset '{HF_DATASET_NAME}'. "
                "The dataset ID may be incorrect or the source is unavailable."
            ) from e
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            raise ConnectionError(
                f"Network error while fetching '{HF_DATASET_NAME}'. "
                "Please check your internet connection and try again."
            ) from e
        else:
            raise ConnectionError(
                f"Failed to fetch data from HuggingFace dataset '{HF_DATASET_NAME}': {error_msg}"
            ) from e


def process_and_save_data() -> Path:
    """
    Processes the streaming data and saves it to a JSONL file.
    
    This function iterates through the generator, normalizes keys if necessary,
    and writes the data to the output file. It ensures that the process
    fails loudly if the data stream is interrupted or corrupted.
    
    Returns:
        Path: The path to the saved JSONL file.
        
    Raises:
        ConnectionError: If data fetching fails during processing.
        RuntimeError: If the output file cannot be written.
    """
    output_dir = ensure_output_dir()
    output_path = output_dir / "posts_tags.jsonl"
    
    print(f"Starting data fetch from {HF_DATASET_NAME}...")
    
    try:
        stream_gen = fetch_posts_tags_streaming()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            count = 0
            for record in stream_gen:
                # Ensure record is JSON serializable (basic check)
                # If the dataset structure varies, adapt here, but do not fake data.
                try:
                    json_line = json.dumps(record, ensure_ascii=False)
                    f.write(json_line + '\n')
                    count += 1
                    if count % 10000 == 0:
                        print(f"Processed {count} records...", file=sys.stderr)
                except (TypeError, ValueError) as e:
                    # Log the specific record that failed if possible, then fail loud
                    raise RuntimeError(
                        f"Failed to serialize record #{count}: {e}. "
                        "Data integrity compromised. Halting."
                    ) from e
                
        print(f"Successfully saved {count} records to {output_path}")
        return output_path

    except (ConnectionError, FileNotFoundError) as e:
        # Re-raise to ensure the pipeline halts
        raise e
    except Exception as e:
        raise RuntimeError(f"Unexpected error during data processing: {e}") from e


def main():
    """
    Main entry point for the download script.
    
    Executes the download process. If any step fails, it raises an exception
    and does not proceed to downstream tasks.
    """
    try:
        output_path = process_and_save_data()
        print(f"Download complete. Output: {output_path}")
        return 0
    except (ConnectionError, FileNotFoundError, RuntimeError) as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        # Fail loudly: do not return success code
        return 1


if __name__ == "__main__":
    sys.exit(main())