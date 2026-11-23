"""
Data download module for CodeSearchNet dataset.

This module handles fetching the CodeSearchNet dataset using ir_datasets.
It strictly enforces real data retrieval and raises errors on failure.
No synthetic fallbacks are permitted.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

import ir_datasets


def ensure_directories(base_path: str = "data") -> None:
    """
    Ensure required directory structure exists.

    Args:
        base_path: Base directory for data storage (default: 'data')
    """
    raw_dir = Path(base_path) / "raw"
    processed_dir = Path(base_path) / "processed"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)


def load_dataset_subset(
    language: str = "python",
    split: str = "test",
    dataset_id: str = "codesearchnet"
) -> Any:
    """
    Load a specific subset of the CodeSearchNet dataset.

    Args:
        language: Programming language subset (e.g., 'python', 'java')
        split: Dataset split (e.g., 'test', 'train', 'valid')
        dataset_id: The ir_datasets identifier

    Returns:
        The loaded dataset object from ir_datasets

    Raises:
        ValueError: If the dataset or subset cannot be loaded
        RuntimeError: If ir_datasets fails to fetch the data
    """
    try:
        # Construct the specific dataset path for ir_datasets
        # ir_datasets typically uses format: codesearchnet/{language}/{split}
        full_dataset_id = f"{dataset_id}/{language}/{split}"

        # Attempt to load the dataset
        dataset = ir_datasets.load(full_dataset_id)

        if dataset is None:
            raise ValueError(f"Failed to load dataset: {full_dataset_id}")

        return dataset

    except Exception as e:
        # CRITICAL: Do not fallback to synthetic data.
        # Let the error propagate so the execution stage can identify the failure.
        raise RuntimeError(f"Failed to load real dataset '{full_dataset_id}': {str(e)}") from e


def download_and_save_subset(
    language: str = "python",
    split: str = "test",
    output_dir: Optional[str] = None,
    dataset_id: str = "codesearchnet"
) -> Dict[str, Any]:
    """
    Download a dataset subset and save it to disk as JSON.

    This function iterates through the dataset, extracts relevant fields,
    and saves them to a JSON file for downstream processing.

    Args:
        language: Programming language (e.g., 'python', 'java')
        split: Dataset split (e.g., 'test')
        output_dir: Directory to save the output file
        dataset_id: The ir_datasets identifier

    Returns:
        Dictionary containing file path and metadata

    Raises:
        RuntimeError: If download fails or no data is retrieved
    """
    if output_dir is None:
        output_dir = "data/raw"

    ensure_directories("data")

    # Load the real dataset
    dataset = load_dataset_subset(language, split, dataset_id)

    output_file = Path(output_dir) / f"codesearchnet_{language}_{split}.json"

    data_records = []
    count = 0

    try:
        # Iterate through the dataset records
        # ir_datasets yields objects with attributes like 'doc_id', 'code', 'query', etc.
        # The exact attributes depend on the specific dataset version
        for record in dataset:
            # Convert record to dictionary
            record_dict = {}
            for attr in dir(record):
                if not attr.startswith('_'):
                    try:
                        val = getattr(record, attr)
                        if not callable(val):
                            record_dict[attr] = val
                    except Exception:
                        pass

            if record_dict:
                data_records.append(record_dict)
                count += 1

    except Exception as e:
        raise RuntimeError(f"Failed to iterate or process real dataset records: {str(e)}") from e

    if count == 0:
        raise RuntimeError(f"No records retrieved from real dataset for {language}/{split}")

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_records, f, indent=2, default=str)

    return {
        "file_path": str(output_file),
        "record_count": count,
        "language": language,
        "split": split
    }


def verify_download(file_path: str) -> bool:
    """
    Verify the integrity of a downloaded file.

    Args:
        file_path: Path to the file to verify

    Returns:
        True if file exists and is valid JSON
    """
    path = Path(file_path)
    if not path.exists():
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, IOError):
        return False


def main() -> None:
    """
    Main entry point to download and verify CodeSearchNet subsets.

    This function downloads Python and Java test sets by default.
    """
    languages = ["python", "java"]
    split = "test"

    print("Starting CodeSearchNet download process...")

    for lang in languages:
        print(f"Processing {lang}/{split}...")
        try:
            result = download_and_save_subset(
                language=lang,
                split=split,
                output_dir="data/raw"
            )
            print(f"  Downloaded {result['record_count']} records to {result['file_path']}")

            if not verify_download(result['file_path']):
                raise RuntimeError(f"Verification failed for {result['file_path']}")

            print(f"  Verification passed for {lang}")

        except Exception as e:
            print(f"  ERROR: Failed to process {lang}: {str(e)}")
            raise

    print("All downloads completed successfully.")


if __name__ == "__main__":
    main()