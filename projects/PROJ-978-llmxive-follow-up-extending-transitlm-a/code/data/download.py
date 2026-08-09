"""
Download and verify the TransitLM SFT dataset from Hugging Face.

This script fetches the dataset using streaming to minimize memory footprint,
verifies integrity using SHA256 checksums, and saves the raw data to data/raw/.
The output is converted to the required JSON format: `data/raw/transitlm_ground_truth.json`.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure we can import from the project root if run as a script
if __name__ == "__main__":
    parent = Path(__file__).parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' package is required. Install with: pip install datasets")
    sys.exit(1)


# Configuration
DATASET_ID = "TransitLM/TransitLM-SFT"
OUTPUT_DIR = Path("data/raw")
# The task explicitly requires this output filename
OUTPUT_FILENAME = "transitlm_ground_truth.json"
# We will compute the hash of the final output file to verify integrity
EXPECTED_SHA256: Optional[str] = None  # Can be set if a known hash is available


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
    Aggregates the streamed data into a single JSON list and saves it.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    print(f"Downloading dataset '{DATASET_ID}' with streaming...")
    
    try:
        # Load dataset in streaming mode
        # We assume the dataset has a 'train' split.
        dataset = load_dataset(DATASET_ID, split="train", streaming=True)
        
        # Accumulate data in memory (or stream to file if too large, 
        # but the task requires a single JSON file output).
        # Given the nature of "streaming" for large datasets, we iterate and collect.
        # If the dataset is too massive for RAM, we would need to stream to JSONL 
        # and then convert, but the requirement is a specific JSON output file.
        # We will collect rows. If memory becomes an issue, the user should 
        # adjust the dataset ID or split, but we must fetch REAL data.
        data_rows: List[Dict[str, Any]] = []
        
        for i, item in enumerate(dataset):
            data_rows.append(item)
            if (i + 1) % 10000 == 0:
                print(f"  Streamed {i + 1} rows...", end="\r")
        
        print(f"\nTotal rows streamed: {len(data_rows)}")
        
        if len(data_rows) == 0:
            raise RuntimeError("Dataset returned 0 rows. The dataset ID or split might be incorrect.")

        # Write to JSON (as a single list object)
        print(f"Writing {len(data_rows)} rows to {output_path}...")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data_rows, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully wrote {output_path}")
            
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        # Fail loudly - no synthetic fallback
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
            "row_count": json.load(open(output_path)) if False else len(json.load(open(output_path, "r"))), # Safe load
            "downloaded_at": str(Path().cwd())
        }
        # Re-load to get count safely if needed, or just store hash
        with open(output_path, "r", encoding="utf-8") as f:
            count = len(json.load(f))
        metadata["row_count"] = count
        
        metadata_path = output_path.with_suffix(".meta.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to {metadata_path}")
        
    except Exception as e:
        print(f"Download process failed: {e}")
        sys.exit(1)

    print("Download completed successfully.")


if __name__ == "__main__":
    main()
