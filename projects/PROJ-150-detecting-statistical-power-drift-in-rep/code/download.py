"""
Download real data for the Reproducibility Project.

This script fetches the 'data.csv' file from the Hugging Face dataset
  'osf/reproducibility_project' and saves it to 'data/raw/reproducibility_project.csv'.

It strictly adheres to the 'fail loudly' constraint:
- No synthetic data generation.
- No fallback to mock data if the download fails.
- Explicit error handling that raises exceptions on failure.
"""

import os
import sys
import hashlib
from pathlib import Path

# Ensure the project root is in the path if running as a script
# but rely on standard imports for the package structure
try:
    from huggingface_hub import hf_hub_download, HfApi
except ImportError:
    print("ERROR: huggingface_hub is not installed. "
          "Please run: pip install huggingface_hub", file=sys.stderr)
    sys.exit(1)

# Constants
DATASET_ID = "osf/reproducibility_project"
FILENAME = "data.csv"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "reproducibility_project.csv"

# Verification: Ensure we are targeting the specific file
# The reproducibility project on OSF/HuggingFace usually contains a single main CSV
# or a specific file named 'data.csv' or 'reproducibility_project.csv'.
# We attempt to fetch 'data.csv' as per the task description.
# If that specific file doesn't exist in the repo root, we might need to list files.
# However, the task specifically asks for 'data.csv'.

def get_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point to download the real dataset.
    """
    print(f"Starting download for dataset: {DATASET_ID}")
    print(f"Target file: {FILENAME}")
    print(f"Output path: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check if file already exists to avoid redundant downloads (optional optimization)
    # But for a pipeline step, we usually want to ensure freshness or verify hash.
    # For this task, we just fetch.
    
    try:
        # Attempt to download the file
        # repo_type defaults to 'dataset'
        local_path = hf_hub_download(
            repo_id=DATASET_ID,
            filename=FILENAME,
            repo_type="dataset",
            force_download=False, # Set to True if we want to always re-download
        )
        
        if local_path is None:
            raise FileNotFoundError(f"Failed to download {FILENAME} from {DATASET_ID}. "
                                    "The file might not exist or the dataset is empty.")

        # Move/Rename to our standard output path if the download location is different
        # hf_hub_download usually returns the path to the cached file.
        # We copy/move it to our data/derived or data/raw structure as required.
        # The task says: save to data/raw (implied by standard structure) or specifically data/raw/reproducibility_project.csv
        
        import shutil
        shutil.copy2(local_path, OUTPUT_FILE)
        
        # Verify the file was written
        if not OUTPUT_FILE.exists():
            raise RuntimeError(f"Downloaded file not found at expected location: {OUTPUT_FILE}")

        file_hash = get_file_hash(OUTPUT_FILE)
        file_size = OUTPUT_FILE.stat().st_size
        
        print(f"SUCCESS: File downloaded and saved to {OUTPUT_FILE}")
        print(f"File size: {file_size} bytes")
        print(f"SHA-256: {file_hash}")
        
        return 0

    except Exception as e:
        # Fail loudly: print the error and exit with non-zero status
        # Do NOT catch and return a mock/synthetic file
        print(f"ERROR: Failed to download real data from {DATASET_ID}/{FILENAME}", file=sys.stderr)
        print(f"Reason: {str(e)}", file=sys.stderr)
        print("This script requires a real, reachable data source. "
              "No synthetic fallback is implemented.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main() or 0)
