"""
Download module for fetching Stack Overflow PostsTags data.

This module implements T012: Fetches PostsTags from the Stack Overflow
data dump (via HuggingFace) and extracts tag names and post creation dates.

Constraints:
- CPU-only streaming (no large in-memory loads)
- Uses HuggingFace datasets library for efficient streaming
- Outputs to data/raw/posts_tags.parquet
"""
import os
import sys
from pathlib import Path
from typing import Generator, Dict, Any, Optional
import json

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import pandas as pd
    import requests
    from datasets import load_dataset
except ImportError as e:
    print(f"Error: Missing required dependencies. Run: pip install pandas requests datasets")
    sys.exit(1)

# Configuration
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "posts_tags.parquet"
HUGGINGFACE_DATASET = "stack-exchange/stackoverflow"
# Using the 'posts' split which contains PostsTags data
# The dataset structure: https://huggingface.co/datasets/stack-exchange/stackoverflow
POSTS_TAGS_COLUMNS = ["Id", "CreationDate", "Tags"]

def ensure_output_dir() -> Path:
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR

def fetch_posts_tags_streaming() -> Generator[Dict[str, Any], None, None]:
    """
    Fetch PostsTags data from HuggingFace in a streaming manner.
    
    Yields:
        Dict containing 'Id', 'CreationDate', 'Tags' for each post.
    """
    print(f"Loading dataset: {HUGGINGFACE_DATASET} (streaming mode)...")
    try:
        # Load dataset in streaming mode to avoid loading entire dataset into RAM
        # This satisfies the CPU-only streaming constraint
        dataset = load_dataset(
            HUGGINGFACE_DATASET, 
            split="posts", 
            streaming=True,
            trust_remote_code=True
        )
        
        # Filter to only select columns we need to reduce memory footprint
        # Note: HuggingFace streaming might not support column selection directly in some versions
        # So we select during iteration
        for row in dataset:
            # Extract only the fields we need
            # The dataset typically returns a dict with all columns
            yield {
                "Id": row.get("Id"),
                "CreationDate": row.get("CreationDate"),
                "Tags": row.get("Tags")
            }
    except Exception as e:
        print(f"Error loading dataset: {e}")
        raise

def process_and_save_data():
    """
    Process the streaming data and save to Parquet format.
    
    This function:
    1. Streams data from HuggingFace
    2. Filters out invalid rows (missing Id, CreationDate, or Tags)
    3. Normalizes tags (lowercase, trim whitespace)
    4. Saves to Parquet for efficient downstream processing
    """
    ensure_output_dir()
    
    print(f"Starting data extraction to: {OUTPUT_FILE}")
    
    # Batch size for writing to avoid memory issues
    BATCH_SIZE = 50000
    batch_data = []
    total_rows = 0
    skipped_rows = 0
    
    stream = fetch_posts_tags_streaming()
    
    # We need to limit the dataset size for the MVP to ensure it runs within time limits
    # The full StackOverflow dump is massive. We will process the first N rows
    # that contain valid data. For a real production run, this would be configurable.
    # Per plan.md constraints, we must be CPU-only and handle streaming.
    # We will process until we have a reasonable sample (e.g., 500k rows) or exhaust the stream.
    MAX_ROWS = 500000 
    
    print(f"Processing up to {MAX_ROWS} rows...")
    
    for row in stream:
        if total_rows >= MAX_ROWS:
            print(f"Reached limit of {MAX_ROWS} rows.")
            break
            
        # Validate row
        post_id = row.get("Id")
        creation_date = row.get("CreationDate")
        tags = row.get("Tags")
        
        if post_id is None or creation_date is None or tags is None:
            skipped_rows += 1
            continue
        
        # Normalize tags: convert to lowercase and trim
        # The tags field is typically in the format <tag1><tag2>
        # We need to parse this
        if isinstance(tags, str):
            # StackOverflow tags are usually enclosed in angle brackets
            # e.g., "<python><pandas>"
            # We split by '>' and filter empty strings
            raw_tags = tags.split(">")
            cleaned_tags = [t.strip("<").strip().lower() for t in raw_tags if t.strip("<").strip()]
            # Join back with space or keep as list? 
            # For frequency analysis, we might want to keep as list or join.
            # Let's store as a space-separated string for easier aggregation later
            normalized_tags = " ".join(cleaned_tags)
        else:
            normalized_tags = str(tags).lower()
        
        batch_data.append({
            "post_id": post_id,
            "creation_date": creation_date,
            "tags": normalized_tags
        })
        
        total_rows += 1
        
        # Write batch to avoid memory buildup
        if len(batch_data) >= BATCH_SIZE:
            df_batch = pd.DataFrame(batch_data)
            # Append to file if exists, else create new
            mode = "append" if OUTPUT_FILE.exists() else "create"
            df_batch.to_parquet(
                OUTPUT_FILE, 
                mode=mode if mode == "create" else "append",
                engine="pyarrow",
                index=False
            )
            print(f"Written batch of {len(batch_data)} rows. Total: {total_rows}")
            batch_data = []
    
    # Write remaining rows
    if batch_data:
        df_batch = pd.DataFrame(batch_data)
        mode = "append" if OUTPUT_FILE.exists() else "create"
        df_batch.to_parquet(
            OUTPUT_FILE, 
            mode=mode if mode == "create" else "append",
            engine="pyarrow",
            index=False
        )
        print(f"Written final batch of {len(batch_data)} rows.")
    
    print(f"Extraction complete. Total rows: {total_rows}, Skipped: {skipped_rows}")
    print(f"Output saved to: {OUTPUT_FILE}")
    
    return OUTPUT_FILE

def main():
    """Main entry point for the download script."""
    print("=" * 60)
    print("Stack Overflow PostsTags Data Download (T012)")
    print("=" * 60)
    
    try:
        output_path = process_and_save_data()
        
        # Verify output
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"Success! Output file created: {output_path} ({file_size:,} bytes)")
            
            # Read back a sample to verify
            df_sample = pd.read_parquet(output_path).head(5)
            print("\nSample output:")
            print(df_sample.to_string())
        else:
            print("Error: Output file was not created.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during download: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()