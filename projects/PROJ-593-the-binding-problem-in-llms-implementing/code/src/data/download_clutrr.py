import os
from pathlib import Path
import pandas as pd
from datasets import load_dataset

def download_clutrr(output_path: str = "data/raw/clutrr.parquet") -> None:
    """
    Downloads the CLUTRR dataset from Hugging Face and saves it as a Parquet file.
    
    The dataset 'tasksource/clutrr' contains synthetic stories and questions
    for testing compositional reasoning in language models.
    
    Args:
        output_path: Relative path where the Parquet file will be saved.
    
    Raises:
        Exception: If the dataset cannot be downloaded or processed.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading dataset 'tasksource/clutrr' from Hugging Face...")
    try:
        # Load the dataset with streaming=False to get the full dataset in memory
        # as we need to convert it to a single Parquet file.
        dataset = load_dataset("tasksource/clutrr", split="train")
        
        print(f"Dataset loaded. Number of examples: {len(dataset)}")
        print(f"Features: {dataset.features}")
        
        # Convert to pandas DataFrame
        df = dataset.to_pandas()
        
        # Save to Parquet
        df.to_parquet(output_file, index=False)
        
        print(f"Successfully saved CLUTRR dataset to {output_file}")
        
    except Exception as e:
        raise RuntimeError(f"Failed to download or process CLUTRR dataset: {e}")

if __name__ == "__main__":
    download_clutrr()
