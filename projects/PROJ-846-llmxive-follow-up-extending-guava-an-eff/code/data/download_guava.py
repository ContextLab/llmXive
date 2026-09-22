"""
Download Guava Dataset Script

Fetches raw Guava data from the Hugging Face Hub and saves it to the project's raw data directory.
Generates a checksums.json file for integrity verification.
"""
import json
import os
import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List

# Import project exceptions
from utils.exceptions import DatasetUnavailableError
from utils.config import get_path

# Try to import datasets library, raise error if not available
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' library is required to download the Guava dataset. "
        "Please install it via 'pip install datasets'."
    )


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def download_guava_dataset(output_dir: Path, overwrite: bool = False) -> Dict[str, Any]:
    """
    Download the Guava dataset from Hugging Face Hub.

    This function fetches the 'guava' dataset from the Hugging Face Hub,
    downloads all relevant files to the specified output directory,
    and generates a checksums.json file for integrity verification.

    Args:
        output_dir: Directory where the dataset will be saved.
        overwrite: If True, overwrite existing files. If False, skip existing files.

    Returns:
        Dictionary containing download statistics and checksums.

    Raises:
        DatasetUnavailableError: If the dataset cannot be downloaded.
        FileNotFoundError: If the output directory does not exist.
    """
    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    # Dataset configuration
    DATASET_NAME = "guava"  # Hugging Face dataset name
    DATASET_CONFIG = "default"  # Configuration name if applicable

    print(f"Attempting to download Guava dataset from Hugging Face Hub...")
    print(f"Dataset: {DATASET_NAME}")
    print(f"Config: {DATASET_CONFIG}")
    print(f"Output directory: {output_dir}")

    try:
        # Load the dataset (this will download and cache it)
        # We use streaming=False to download the full dataset
        # Note: This might take a while depending on the dataset size
        print("Loading dataset from Hugging Face Hub...")
        dataset = load_dataset(DATASET_NAME, split="train", trust_remote_code=True)

        # Create a temporary directory to store the downloaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Save the dataset to the temporary directory in parquet format
            # This is a common format for storing datasets
            dataset_path = temp_path / "guava_data.parquet"
            dataset.to_parquet(str(dataset_path))

            # Copy the file to the output directory
            final_path = output_dir / "guava_data.parquet"
            if final_path.exists() and not overwrite:
                print(f"File {final_path} already exists. Skipping download.")
            else:
                shutil.copy2(str(dataset_path), str(final_path))
                print(f"Dataset saved to: {final_path}")

            # Calculate checksum
            checksum = calculate_sha256(final_path)
            print(f"SHA-256 checksum: {checksum}")

            # Create checksums.json
            checksums_file = output_dir / "checksums.json"
            checksums_data = {
                "dataset_name": DATASET_NAME,
                "config": DATASET_CONFIG,
                "files": {
                    "guava_data.parquet": {
                        "sha256": checksum,
                        "size_bytes": final_path.stat().st_size,
                        "downloaded_at": str(final_path.stat().st_mtime)
                    }
                },
                "download_status": "success"
            }

            with open(checksums_file, "w") as f:
                json.dump(checksums_data, f, indent=2)

            print(f"Checksums saved to: {checksums_file}")

            return checksums_data

    except Exception as e:
        # Raise a specific error if download fails
        error_msg = f"Failed to download Guava dataset: {str(e)}"
        print(error_msg)
        raise DatasetUnavailableError(error_msg) from e


def main():
    """
    Main entry point for downloading the Guava dataset.
    """
    # Get the output directory from config
    output_dir = get_path("raw_guava_data")

    print("=" * 60)
    print("Guava Dataset Downloader")
    print("=" * 60)

    try:
        # Download the dataset
        result = download_guava_dataset(output_dir, overwrite=False)

        print("\nDownload Summary:")
        print(f"  Dataset: {result['dataset_name']}")
        print(f"  Config: {result['config']}")
        print(f"  Files downloaded: {len(result['files'])}")
        for filename, info in result['files'].items():
            print(f"    - {filename}: {info['sha256'][:16]}... ({info['size_bytes']} bytes)")
        print(f"  Status: {result['download_status']}")

        print("\nDownload completed successfully!")
        return 0

    except DatasetUnavailableError as e:
        print(f"\nERROR: {e}")
        print("The Guava dataset could not be downloaded. Please check your internet connection")
        print("and ensure the dataset is available on Hugging Face Hub.")
        return 1
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("Please ensure the output directory exists.")
        return 2
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        return 3


if __name__ == "__main__":
    exit(main())
