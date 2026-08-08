"""
Data ingestion module for OpenNeuro MEG dataset (ds000246).
Uses streaming to handle large datasets efficiently.
"""
import os
import sys
from pathlib import Path
import pandas as pd
from datasets import load_dataset

def download_meg_streamed(output_dir: str = "data/raw") -> str:
    """
    Download and stream OpenNeuro ds000246 MEG data, converting to Parquet.

    This function uses the Hugging Face datasets library to stream the OpenNeuro
    ds000246 dataset (MEG recordings) without loading the entire dataset into memory.
    It processes the data in chunks and saves the result as a Parquet file.

    Args:
        output_dir: Directory where the output Parquet file will be saved.

    Returns:
        Path to the created Parquet file.

    Raises:
        RuntimeError: If the dataset cannot be loaded or processed.
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "meg_streamed.parquet"

    # Check if file already exists to avoid re-downloading
    if output_file.exists():
        print(f"File {output_file} already exists. Skipping download.")
        return str(output_file)

    print("Loading OpenNeuro ds000246 dataset with streaming...")
    try:
        # Load the dataset with streaming enabled
        # ds000246 is the OpenNeuro MEG dataset
        dataset = load_dataset("openneuro-py/ds000246", split="train", streaming=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset ds000246: {e}")

    # Process the dataset in chunks
    chunk_size = 1000
    chunks = []
    total_rows = 0

    print("Streaming and processing data...")
    try:
        for idx, row in enumerate(dataset):
            # Convert row to dictionary if needed
            if isinstance(row, dict):
                chunks.append(row)
            else:
                # Handle non-dict rows if necessary
                chunks.append({"data": str(row)})

            total_rows += 1

            # Write to parquet in chunks to manage memory
            if len(chunks) >= chunk_size:
                df_chunk = pd.DataFrame(chunks)
                if total_rows == chunk_size:
                    # First chunk: write new file
                    df_chunk.to_parquet(output_file, engine='pyarrow')
                else:
                    # Subsequent chunks: append
                    df_chunk.to_parquet(output_file, engine='pyarrow', append=True)
                chunks = []
                print(f"Processed {total_rows} rows...")

        # Write remaining rows
        if chunks:
            df_remaining = pd.DataFrame(chunks)
            if total_rows == 0:
                df_remaining.to_parquet(output_file, engine='pyarrow')
            else:
                df_remaining.to_parquet(output_file, engine='pyarrow', append=True)

        print(f"Successfully saved {total_rows} rows to {output_file}")
        return str(output_file)

    except Exception as e:
        # Clean up partial file on error
        if output_file.exists():
            output_file.unlink()
        raise RuntimeError(f"Error processing dataset stream: {e}")

if __name__ == "__main__":
    # Default execution
    output_file = download_meg_streamed()
    print(f"Output file: {output_file}")
    # Verification
    df = pd.read_parquet(output_file)
    print(f"Verification: DataFrame has {len(df)} rows and {len(df.columns)} columns")
    if len(df) > 1000:
        print("Verification PASSED: Dataset contains > 1000 rows")
    else:
        print("Verification WARNING: Dataset contains <= 1000 rows")
