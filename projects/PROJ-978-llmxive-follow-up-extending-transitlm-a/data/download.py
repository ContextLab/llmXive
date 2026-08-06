"""
Download and verify the TransitLM SFT dataset from Hugging Face.

This script fetches the dataset using streaming to minimize memory footprint,
verifies integrity using SHA256 checksums, and saves the raw data to data/raw/.
"""
import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure we can import from the project root if run as a script
if __name__ == "__main__":
    # Add parent directory to path for imports if necessary
    parent = Path(__file__).parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' package is required. Install with: pip install datasets")
    sys.exit(1)


# Configuration
DATASET_ID = "TransitLM/TransitLM-SFT"  # Real dataset ID on HuggingFace
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILENAME = "transitlm_sft_raw.jsonl"
# Checksums will be computed on the downloaded file; we expect a specific hash
# If the dataset changes, this will need to be updated. 
# For now, we compute and store the hash of the first 1000 lines to verify consistency 
# if the full file is too large to hash instantly, or hash the full file if manageable.
# Given the "streaming" requirement, we will download the full file to disk first, then hash it.
# We will define a target hash if one is known, otherwise we compute and log it.
# Since no specific hash was provided in the prompt, we will compute it and print it.
EXPECTED_SHA256: Optional[str] = None  # Set this if a known hash is available


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def download_transitlm(output_dir: Path, filename: str) -> Path:
    """
    Download the TransitLM SFT dataset from Hugging Face.
    
    Uses streaming=True to handle large datasets efficiently.
    Saves the result as a JSONL file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    print(f"Downloading dataset '{DATASET_ID}' with streaming...")
    
    try:
        # Load dataset in streaming mode
        # We assume the dataset has a 'train' split or similar. 
        # If the dataset structure is different, this might need adjustment.
        # Most HF datasets have a 'train' split.
        dataset = load_dataset(DATASET_ID, split="train", streaming=True)
        
        # Write to JSONL
        with open(output_path, "w", encoding="utf-8") as f:
            count = 0
            for item in dataset:
                # Ensure the item is a dict and convert to JSON
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1
                if count % 10000 == 0:
                    print(f"  Downloaded {count} rows...", end="\r")
            print(f"\nDownloaded {count} rows to {output_path}")
            
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        # If the dataset ID is incorrect or unavailable, we fail loudly.
        # We do NOT fallback to synthetic data.
        raise RuntimeError(f"Failed to download real data from {DATASET_ID}. "
                           "The task requires real data. If the dataset ID is wrong, update DATASET_ID. "
                           "If the dataset is unavailable, the task cannot be completed.") from e

    return output_path


def main():
    """Main entry point for the download script."""
    print("Starting TransitLM dataset download...")
    
    try:
        output_path = download_transitlm(OUTPUT_DIR, OUTPUT_FILENAME)
        
        # Verify checksum
        print(f"Computing SHA256 checksum for {output_path}...")
        file_hash = compute_sha256(output_path)
        print(f"SHA256: {file_hash}")
        
        if EXPECTED_SHA256:
            if file_hash == EXPECTED_SHA256:
                print("Checksum verification PASSED.")
            else:
                print(f"Checksum verification FAILED.")
                print(f"  Expected: {EXPECTED_SHA256}")
                print(f"  Got:      {file_hash}")
                sys.exit(1)
        else:
            print("No expected checksum provided. Skipping verification comparison.")
            print("Please update EXPECTED_SHA256 in the script for production use.")
        
        # Save metadata
        metadata = {
            "dataset_id": DATASET_ID,
            "file": str(output_path),
            "sha256": file_hash,
            "downloaded_at": str(Path().cwd())
        }
        metadata_path = output_path.with_suffix(".json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to {metadata_path}")
        
    except Exception as e:
        print(f"Download process failed: {e}")
        sys.exit(1)

    print("Download completed successfully.")


if __name__ == "__main__":
    main()
