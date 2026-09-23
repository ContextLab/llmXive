import json
import os
import sys
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datasets import load_dataset

# Add project root to path to resolve imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_path, ensure_dirs_exist

# Retry configuration
MAX_RETRIES = 5
INITIAL_BACKOFF = 2.0  # seconds
BACKOFF_MULTIPLIER = 2.0

def download_planbench_xl(output_dir: Optional[Path] = None) -> Path:
    """
    Download the PlanBench-XL dataset from HuggingFace using streaming to avoid OOM.
    Saves the raw parquet files to the specified output directory.

    Args:
        output_dir: Directory to save raw data. Defaults to data/raw/ relative to project root.

    Returns:
        Path to the directory containing the downloaded parquet files.

    Raises:
        ConnectionError: If the dataset source is unreachable after all retries.
        FileNotFoundError: If the dataset ID is invalid or not found.
    """
    if output_dir is None:
        output_dir = get_path("data_raw")
    
    ensure_dirs_exist(output_dir)
    
    dataset_id = "PlanBench/planbench-xl"
    parquet_filename = "planbench_xl_raw.parquet"
    parquet_path = output_dir / parquet_filename

    # Check if already downloaded to avoid re-downloading
    if parquet_path.exists():
        print(f"Dataset already exists at {parquet_path}. Skipping download.")
        return output_dir

    print(f"Attempting to download {dataset_id} with streaming...")
    
    last_exception = None
    backoff = INITIAL_BACKOFF

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Download attempt {attempt}/{MAX_RETRIES}...")
            
            # Load dataset in streaming mode to handle large sizes
            # We stream to a local file to satisfy the "save raw parquet" requirement
            # while keeping memory usage low during the fetch.
            ds = load_dataset(dataset_id, split="train", streaming=True)
            
            # Since streaming yields an iterator, we need to collect it into a file.
            # We'll convert the streaming dataset to a Pandas DataFrame in chunks 
            # and then write to parquet, or use the dataset's to_parquet if available.
            # The 'datasets' library allows saving a streaming dataset directly to parquet 
            # if we iterate, but to ensure we save a *single* raw file as requested:
            
            # Strategy: Iterate through the streaming dataset and write to parquet using pyarrow.
            # This avoids loading everything into RAM at once.
            
            import pyarrow as pa
            import pyarrow.parquet as pq
            
            # We need to infer schema or handle it dynamically.
            # For PlanBench-XL, we assume standard schema. If schema varies, we handle it.
            # A robust way with streaming: collect batches.
            
            batch_size = 1000
            writer = None
            
            with open(parquet_path, 'wb') as f:
                # We will write rows to a buffer and flush periodically
                # However, pyarrow requires a schema for the writer.
                # Let's try to get the schema from the first batch.
                
                batch_iter = iter(ds)
                first_batch = None
                
                try:
                    first_batch = next(batch_iter)
                except StopIteration:
                    raise RuntimeError("Dataset is empty.")
                
                # Convert first batch to Arrow Table to get schema
                table = pa.Table.from_pydict(first_batch)
                schema = table.schema
                
                # Create writer
                writer = pq.ParquetWriter(f, schema)
                
                # Write first batch
                writer.write_table(table)
                
                # Write remaining
                count = 1
                for batch in batch_iter:
                    table = pa.Table.from_pydict(batch)
                    writer.write_table(table)
                    count += 1
                    if count % 100 == 0:
                        print(f"  Processed {count} batches...")
                
                writer.close()
            
            print(f"Successfully downloaded and saved to {parquet_path}")
            return output_dir

        except Exception as e:
            last_exception = e
            print(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"Retrying in {backoff:.1f} seconds...")
                time.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER
            else:
                print(f"All {MAX_RETRIES} attempts failed.")
                raise ConnectionError(f"Failed to download dataset {dataset_id} after {MAX_RETRIES} attempts. Last error: {e}") from e

    # Should not reach here
    raise ConnectionError("Download loop terminated unexpectedly.")

def load_injected_data(path: str | Path) -> List[Dict[str, Any]]:
    """
    Load the implicit failure subset from a JSONL file.
    
    Args:
        path: Path to the JSONL file (e.g., data/derived/implicit_failure_subset.jsonl)
            
    Returns:
        List of task dictionaries.
    """
    tasks = []
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                task = json.loads(line)
                tasks.append(task)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON at line {line_num}: {e}")
                
    return tasks

def main():
    """Main entry point for the loader module."""
    try:
        output_dir = download_planbench_xl()
        print(f"Data ready at: {output_dir}")
    except Exception as e:
        print(f"Error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
