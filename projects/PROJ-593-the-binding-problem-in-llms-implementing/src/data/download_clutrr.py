"""
Data ingestion module for the CLUTRR dataset from Hugging Face.

This module downloads the 'tasksource/clutrr' dataset and saves it as a
Parquet file. It fails loudly if the real data fetch fails, with no
synthetic fallback.
"""
import os
from pathlib import Path
import pandas as pd
from datasets import load_dataset


def download_clutrr(output_dir: str = "data/raw") -> Path:
    """
    Download the CLUTRR dataset from Hugging Face and save it as a Parquet file.
    
    Args:
        output_dir: Directory to save the downloaded data. Defaults to 'data/raw'.
        
    Returns:
        Path to the saved Parquet file.
        
    Raises:
        ConnectionError: If the dataset cannot be downloaded from Hugging Face.
        ValueError: If the dataset format is unexpected.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    parquet_file_path = output_path / "clutrr.parquet"
    
    # If file already exists, skip download (idempotent)
    if parquet_file_path.exists():
        print(f"CLUTRR dataset already exists at {parquet_file_path}. Skipping download.")
        return parquet_file_path
    
    print("Downloading CLUTRR dataset from Hugging Face (tasksource/clutrr)...")
    try:
        # Load the dataset in streaming mode to handle potential size issues
        # The CLUTRR dataset is generally small enough to load directly, but streaming
        # ensures we don't OOM if the dataset grows or if we process it differently later.
        dataset = load_dataset("tasksource/clutrr", split="train", streaming=True)
        
        # Convert to pandas DataFrame
        # Since we are streaming, we need to convert to a list of dicts first
        # to ensure we have all data before writing to parquet
        data_list = list(dataset)
        
        if not data_list:
            raise ValueError("Downloaded CLUTRR dataset is empty.")
        
        df = pd.DataFrame(data_list)
        
        # Save to Parquet
        df.to_parquet(parquet_file_path, index=False)
        
        print(f"Successfully saved CLUTRR dataset to {parquet_file_path}")
        print(f"Dataset shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
    except Exception as e:
        # Fail loudly - do not fallback to synthetic data
        raise ConnectionError(
            f"Failed to download CLUTRR dataset from Hugging Face. "
            f"Ensure you have an internet connection and the dataset ID 'tasksource/clutrr' is correct. "
            f"Original error: {str(e)}"
        ) from e
    
    return parquet_file_path


if __name__ == "__main__":
    # Execute download when run as a script
    output_file = download_clutrr()
    print(f"Download complete: {output_file}")
