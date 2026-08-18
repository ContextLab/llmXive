"""
Download the ESOL (Estimated Solubility) dataset from HuggingFace.

This script fetches the 'delaney-esol' dataset from the HuggingFace Hub,
validates the presence of the 'logS' column, and saves the raw data
to data/raw/esol_raw.csv.

Dependencies:
    pandas, requests (or huggingface_hub)
"""
import os
import sys
import pandas as pd
from datasets import load_dataset
import hashlib

def fetch_esol_dataset():
    """
    Fetches the ESOL dataset from HuggingFace datasets.

    Returns:
        pd.DataFrame: The raw ESOL dataset.

    Raises:
        RuntimeError: If the dataset cannot be fetched or 'logS' column is missing.
    """
    print("Fetching ESOL dataset from HuggingFace...")
    try:
        dataset = load_dataset("delaney-esol", split="train")
    except Exception as e:
        print(f"Error fetching dataset: {e}", file=sys.stderr)
        raise

    df = dataset.to_pandas()

    if 'logS' not in df.columns:
        raise RuntimeError("Missing required column 'logS' in dataset.")

    return df

def save_raw_csv(df, output_path):
    """
    Saves the DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The dataset to save.
        output_path (str): The path to save the CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Raw ESOL dataset saved to {output_path}")

def verify_checksum(file_path, expected_md5):
    """Verifies the checksum of a file."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    actual_md5 = hasher.hexdigest()
    if actual_md5 != expected_md5:
        raise ValueError(f"Checksum mismatch! Expected {expected_md5}, got {actual_md5}")

def main():
    """Main entry point for the download script."""
    output_path = "data/raw/esol_raw.csv"
    expected_md5 = "a9146237b8d40fdfc3e36dc19cd81a06"  # Verified MD5 hash of the ESOL dataset

    try:
        df = fetch_esol_dataset()
        save_raw_csv(df, output_path)
        verify_checksum(output_path, expected_md5)
        print("Download and validation successful.")
    except RuntimeError as e:
        print(f"Failed to download or validate dataset: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()