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
import json
from pathlib import Path

# Ensure the project root is in the path if running as a script
try:
    from huggingface_hub import hf_hub_download, HfApi
    import datasets
except ImportError:
    print("ERROR: huggingface_hub or datasets is not installed. "
          "Please run: pip install huggingface_hub datasets", file=sys.stderr)
    sys.exit(1)

# Constants
DATASET_ID = "osf/reproducibility_project"
FILENAME = "data.csv"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "data.csv"
METADATA_FILE = OUTPUT_DIR / "download_metadata.json"

# Verification: Ensure we are targeting the specific file
# The reproducibility project on OSF/HuggingFace usually contains a single main CSV
# or a specific file named 'data.csv' or 'reproducibility_project.csv'.
# We attempt to fetch 'data.csv' as per the task description.

def get_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_title_token_overlap(title1: str, title2: str) -> float:
    """
    Calculate cosine similarity of tokenized titles.
    Returns overlap score between 0.0 and 1.0.
    """
    import re
    from math import sqrt

    def tokenize(text: str):
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return set(tokens)

    tokens1 = tokenize(title1)
    tokens2 = tokenize(title2)

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union)

def main():
    """
    Main entry point to download the real dataset.
    Implements T006 logic:
    1. Attempt fetch (streaming if large, else direct).
    2. Verify metadata (title-token-overlap >= 0.7).
    3. Fail loudly on any error.
    """
    print(f"Starting download for dataset: {DATASET_ID}")
    print(f"Target file: {FILENAME}")
    print(f"Output path: {OUTPUT_FILE}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Attempt to fetch using datasets.load_dataset (streaming if large)
        # We first try to get the dataset info to check size, or just attempt streaming load.
        # The task specifies: if file size > 100MB, use streaming, else read_csv.
        # Since we are using the HuggingFace datasets library, we can stream the dataset
        # and then write it to disk, or download the raw file if it exists in the repo.
        
        # Strategy: Use hf_hub_download to get the raw file if it exists in the repo root.
        # If the dataset is structured as a HuggingFace Dataset (parquet/csv shards),
        # we use datasets.load_dataset.
        
        # Let's try to list the repo files first to see if 'data.csv' is a raw file.
        api = HfApi()
        try:
            files = api.list_repo_files(repo_id=DATASET_ID, repo_type="dataset")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to HuggingFace Hub for {DATASET_ID}: {e}")

        if FILENAME in files:
            # Raw file exists, download it directly
            print(f"Found {FILENAME} in repo. Downloading directly...")
            local_path = hf_hub_download(
                repo_id=DATASET_ID,
                filename=FILENAME,
                repo_type="dataset",
                force_download=False,
            )
            
            if local_path is None:
                raise FileNotFoundError(f"Failed to download {FILENAME} from {DATASET_ID}.")
            
            import shutil
            shutil.copy2(local_path, OUTPUT_FILE)
            
            # Get file size to decide on streaming logic (though we already downloaded)
            file_size = OUTPUT_FILE.stat().st_size
            print(f"Downloaded raw file. Size: {file_size} bytes")
            
            # Load into pandas to verify content and get metadata
            import pandas as pd
            df = pd.read_csv(OUTPUT_FILE)
            
        else:
            # File not in root, assume it's a HuggingFace Dataset structure (parquet/csv shards)
            print(f"{FILENAME} not found in repo root. Loading via datasets library...")
            
            # Check if we need streaming based on estimated size or just stream to be safe
            # The task says: if > 100MB, stream. We'll try to load normally first, 
            # but if it fails or is huge, we stream.
            # For robustness, we'll use streaming=True to handle large datasets gracefully.
            try:
                ds = datasets.load_dataset(DATASET_ID, split="train", streaming=True)
                
                # Convert to CSV to save
                # Since streaming returns an iterator of dicts, we write row by row
                # to avoid loading everything into memory if it's huge.
                # However, we need to know the columns first.
                # We'll take the first row to infer schema.
                
                first_row = next(iter(ds))
                columns = list(first_row.keys())
                
                with open(OUTPUT_FILE, 'w') as f:
                    # Write header
                    f.write(','.join(columns) + '\n')
                    # Write first row
                    f.write(','.join(str(v) for v in first_row.values()) + '\n')
                    
                    # Write rest
                    for row in ds:
                        f.write(','.join(str(v) for v in row.values()) + '\n')
                
                print("Dataset streamed and saved to CSV.")
                df = pd.read_csv(OUTPUT_FILE) # Load for metadata check
                
            except Exception as e:
                raise RuntimeError(f"Failed to load dataset {DATASET_ID} via datasets library: {e}")

        # 2. Verify dataset metadata by calculating title-token-overlap
        # We need a title. The dataset description or name is used.
        # The task requires overlap >= 0.7 with "OSF Reproducibility Project".
        # We'll use the dataset_id itself or try to fetch the dataset info.
        
        target_title = "OSF Reproducibility Project"
        
        # Try to get dataset info for a title
        try:
            dataset_info = api.dataset_info(DATASET_ID)
            dataset_title = dataset_info.id or dataset_info.description or DATASET_ID
        except:
            dataset_title = DATASET_ID

        overlap = calculate_title_token_overlap(dataset_title, target_title)
        print(f"Dataset title: {dataset_title}")
        print(f"Target title: {target_title}")
        print(f"Token overlap score: {overlap:.4f}")

        if overlap < 0.7:
            raise ValueError(f"Title token overlap ({overlap:.4f}) is less than 0.7. "
                             f"Source verification failed for {DATASET_ID}.")

        # 3. Verification: Ensure the loader yields rows correctly
        if len(df) == 0:
            raise ValueError("Downloaded dataset is empty.")
        
        print(f"Verification: Dataset contains {len(df)} rows.")

        # Save metadata
        metadata = {
            "dataset_id": DATASET_ID,
            "filename": FILENAME,
            "output_file": str(OUTPUT_FILE),
            "file_size_bytes": OUTPUT_FILE.stat().st_size,
            "sha256": get_file_hash(OUTPUT_FILE),
            "row_count": len(df),
            "title_token_overlap": overlap,
            "verification_status": "passed"
        }

        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"SUCCESS: File downloaded and saved to {OUTPUT_FILE}")
        print(f"Metadata saved to {METADATA_FILE}")
        
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