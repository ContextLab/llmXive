"""
Data ingestion module for the CLUTRR dataset.

Downloads the CLUTRR dataset from Hugging Face (tasksource/clutrr) using streaming
to handle large datasets efficiently, converts it to a pandas DataFrame, and saves
it as a parquet file.

This script fails loudly if the real data fetch fails; no synthetic fallback is provided.
"""
import os
from pathlib import Path
import pandas as pd
from datasets import load_dataset


def download_clutrr(output_path: str = "data/raw/clutrr.parquet") -> str:
    """
    Download the CLUTRR dataset from Hugging Face and save it as a parquet file.

    Args:
        output_path: Path where the parquet file will be saved.

    Returns:
        Path to the saved parquet file.

    Raises:
        RuntimeError: If the dataset download fails.
        FileNotFoundError: If the dataset is not found on Hugging Face.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    dataset_id = "tasksource/clutrr"

    try:
        # Load the dataset with streaming to avoid loading everything into memory
        # We load the 'train' split which contains the family reasoning tasks
        dataset = load_dataset(dataset_id, split="train", streaming=True)

        # Convert streaming dataset to a list of dictionaries
        # Since we need to save to parquet, we need to materialize the data
        # We'll iterate through the streaming dataset
        data_list = []
        for item in dataset:
            data_list.append(item)

        if not data_list:
            raise RuntimeError(f"Dataset {dataset_id} is empty or could not be loaded.")

        # Create DataFrame
        df = pd.DataFrame(data_list)

        # Save to parquet
        df.to_parquet(output_file, index=False)

        print(f"Successfully downloaded and saved CLUTRR dataset to {output_file}")
        print(f"Dataset shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")

        return str(output_file)

    except Exception as e:
        # Fail loudly - no synthetic fallback
        raise RuntimeError(
            f"Failed to download CLUTRR dataset from {dataset_id}: {str(e)}. "
            "This is a real data fetch failure. Please check your internet connection "
            "and verify the dataset exists on Hugging Face."
        ) from e


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download CLUTRR dataset")
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/clutrr.parquet",
        help="Output path for the parquet file"
    )

    args = parser.parse_args()

    download_clutrr(args.output)
