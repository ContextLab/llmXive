"""
Download and verify the TransitLM SFT dataset from Hugging Face.

This script fetches the dataset using streaming to minimize memory footprint,
verifies integrity using SHA256 checksums, and saves the raw data to data/raw/.

Output: data/raw/transitlm_ground_truth.json
"""
import hashlib
import json
import os
import sys
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
# The specific dataset ID for TransitLM SFT
DATASET_ID = "TransitLM/TransitLM-SFT"
OUTPUT_DIR = Path("data/raw")
# The task explicitly requests this output filename
OUTPUT_FILENAME = "transitlm_ground_truth.json"

# We do not have a pre-computed hash for the full dataset yet.
# We will compute it after download. If the dataset is stable,
# we can update this value in future runs to verify integrity.
EXPECTED_SHA256: Optional[str] = None


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
    Saves the result as a JSON file containing the list of items.
    
    Note: The task requires saving to `data/raw/transitlm_ground_truth.json`.
    We will accumulate the streaming data into a list and write it as JSON.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    print(f"Downloading dataset '{DATASET_ID}' with streaming...")
    
    try:
        # Load dataset in streaming mode
        # Most HF datasets have a 'train' split.
        dataset = load_dataset(DATASET_ID, split="train", streaming=True)
        
        # Accumulate data to write as a single JSON file as requested
        # Streaming allows us to iterate without loading everything into RAM at once,
        # but we need to write the final file. If the dataset is massive, 
        # writing a single huge JSON might be memory intensive during write.
        # However, the task specifies a .json output.
        # We will write line-by-line JSON (JSONL) internally but rename/structure
        # it to match the requested .json if it implies a list, or keep as JSONL 
        # if the extension is loose. 
        # Strictly, "transitlm_ground_truth.json" usually implies a JSON list.
        # Given the streaming nature, writing a JSON list requires wrapping in []
        # and handling commas.
        
        # To be safe with memory, we will write a JSONL file but name it .json 
        # if the downstream expects line-delimited, OR we write a proper JSON list.
        # The task says "save to data/raw/transitlm_ground_truth.json".
        # Let's write a valid JSON list.
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("[\n")
            count = 0
            first = True
            for item in dataset:
                if not first:
                    f.write(",\n")
                first = False
                f.write(json.dumps(item, ensure_ascii=False))
                count += 1
                if count % 10000 == 0:
                    print(f"  Downloaded {count} rows...", end="\r")
            f.write("\n]")
            print(f"\nDownloaded {count} rows to {output_path}")
        
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        # Fail loudly: do not fallback to synthetic data
        raise RuntimeError(
            f"Failed to download real data from {DATASET_ID}. "
            "The task requires real data. If the dataset ID is wrong, update DATASET_ID. "
            "If the dataset is unavailable, the task cannot be completed."
        ) from e

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
        metadata_path = output_path.with_suffix(".json.meta")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to {metadata_path}")
        
    except Exception as e:
        print(f"Download process failed: {e}")
        sys.exit(1)

    print("Download completed successfully.")


if __name__ == "__main__":
    main()