"""
Data ingestion module for CLUTRR dataset.
Downloads and processes the 'tasksource/clutrr' dataset from Hugging Face.
"""
import os
from pathlib import Path
import pandas as pd
from datasets import load_dataset

def download_clutrr(output_path: str = "data/raw/clutrr.parquet") -> None:
    """
    Downloads the CLUTRR dataset from Hugging Face and saves it as a Parquet file.

    Args:
        output_path: Relative path from project root where the Parquet file will be saved.
    """
    # Ensure the output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load the dataset using streaming to handle large sizes efficiently if needed
    # The dataset 'tasksource/clutrr' contains reasoning tasks with family relations
    dataset = load_dataset("tasksource/clutrr", split="train", streaming=True)

    # Convert to pandas DataFrame
    # Since we are streaming, we need to collect all data into memory for Parquet
    # If the dataset is too large, we would need to write in chunks, but Parquet
    # typically requires the full schema or a writer context.
    # Given the nature of CLUTRR (relational reasoning), it fits in memory.
    df = pd.DataFrame(dataset)

    # Save to Parquet
    df.to_parquet(output_file, index=False)

    print(f"Successfully saved CLUTRR dataset to {output_path}")
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

if __name__ == "__main__":
    # Default execution to generate the required artifact
    download_clutrr("data/raw/clutrr.parquet")
