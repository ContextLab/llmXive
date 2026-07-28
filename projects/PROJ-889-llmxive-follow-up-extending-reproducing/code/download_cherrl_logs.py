"""
Download CHERRL trajectory logs from the verified Hugging Face dataset repository.

This script implements a 'fail loud' strategy: it fetches real data from the
arXiv:2606.04923 linked repository. If the source is unreachable or the
metadata does not match the expected arXiv ID, it exits with code 2.
NO synthetic fallback is allowed.
"""
import os
import sys
import hashlib
import shutil
from pathlib import Path
import requests

# Import project config and utils to ensure path consistency and validation
from config import get_project_root, ensure_paths_exist
from utils.io_utils import ensure_dir
from utils.validator import validate_cherrl_source

# Constants
EXPECTED_ARXIV_ID = "2606.04923"
DATASET_REPO_ID = "cherrl/cherrl-trajectories"  # Standard naming convention for CHERRL
DATA_RAW_DIR = "data/raw"
LOG_FILE_NAME = "cherrl_trajectories_raw.csv"

def verify_arxiv_source(expected_id: str) -> bool:
    """
    Verifies that the data source corresponds to the expected arXiv paper.
    This checks the dataset metadata on Hugging Face.

    Args:
        expected_id: The arXiv ID string (e.g., "2606.04923").

    Returns:
        True if the source is verified, False otherwise.
    """
    try:
        # Use the Hugging Face Hub API to check dataset metadata
        # URL structure: https://huggingface.co/api/datasets/{repo_id}
        api_url = f"https://huggingface.co/api/datasets/{DATASET_REPO_ID}"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            print(f"ERROR: Could not reach Hugging Face API for {DATASET_REPO_ID}. Status: {response.status_code}")
            return False

        data = response.json()
        
        # Check if 'arxiv' or 'paper' tag contains the expected ID
        # Hugging Face datasets often store paper info in 'tags' or 'cardData'
        tags = data.get('tags', [])
        card_data = data.get('cardData', {})
        
        paper_id_found = False
        
        # Check tags
        for tag in tags:
            if isinstance(tag, str) and expected_id in tag:
                paper_id_found = True
                break
        
        # Check cardData if not found in tags
        if not paper_id_found:
            paper_info = card_data.get('paper', '')
            if isinstance(paper_info, str) and expected_id in paper_info:
                paper_id_found = True
            elif isinstance(paper_info, list):
                for p in paper_info:
                    if isinstance(p, str) and expected_id in p:
                        paper_id_found = True
                        break

        if not paper_id_found:
            print(f"ERROR: Source metadata does not contain arXiv ID {expected_id}.")
            print(f"Found metadata tags: {tags[:5]}...") # Log partial tags for debugging
            return False

        return True

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error while verifying source: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during source verification: {e}")
        return False

def download_from_huggingface(output_dir: Path) -> bool:
    """
    Downloads the CHERRL dataset using the `datasets` library.
    
    This function fetches the real data. It does NOT fall back to synthetic data.
    If the download fails, it raises an exception to be caught by main().

    Args:
        output_dir: The directory where data will be saved.

    Returns:
        True if download was successful.
    """
    try:
        # Dynamically import datasets to avoid hard dependency if not installed,
        # but the project requires it per requirements.txt.
        from datasets import load_dataset

        print(f"Loading dataset '{DATASET_REPO_ID}' from Hugging Face...")
        
        # Load the dataset. We assume 'train' split exists or default to all.
        # Streaming is used to avoid loading massive datasets into memory immediately,
        # but we will materialize the specific CSV we need.
        dataset = load_dataset(DATASET_REPO_ID, split="train", streaming=True)
        
        # Convert to pandas for easier CSV export and validation
        # Since we are streaming, we might need to collect it.
        # For a robust implementation that handles large data, we iterate and save chunks
        # or convert to a single dataframe if it fits. 
        # Given the task is to produce a CSV, we assume the dataset is manageable or we sample.
        # However, the instruction says "Real data only". We will try to convert.
        
        df = dataset.to_pandas()
        
        if df.empty:
            print("ERROR: Downloaded dataset is empty.")
            return False

        output_path = output_dir / LOG_FILE_NAME
        print(f"Saving {len(df)} rows to {output_path}...")
        df.to_csv(output_path, index=False)
        
        # Verify checksum (simple integrity check)
        file_hash = hashlib.sha256()
        with open(output_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        
        print(f"Downloaded file SHA256: {file_hash.hexdigest()[:16]}...")
        return True

    except ImportError:
        print("ERROR: 'datasets' library not found. Please install it: pip install datasets")
        return False
    except Exception as e:
        print(f"ERROR: Failed to download dataset: {e}")
        return False

def main():
    """
    Main entry point for the download script.
    
    1. Verify the source is the correct arXiv paper.
    2. Ensure data directories exist.
    3. Download the real data.
    4. Exit with code 2 on failure.
    """
    print(f"Starting CHERRL Log Download for arXiv:{EXPECTED_ARXIV_ID}")
    
    # 1. Verify Source
    print("Verifying data source...")
    if not verify_arxiv_source(EXPECTED_ARXIV_ID):
        print("ERROR: Data source unreachable or mismatch")
        sys.exit(2)
    print("Source verified successfully.")

    # 2. Setup Paths
    project_root = get_project_root()
    raw_dir = project_root / DATA_RAW_DIR
    ensure_dir(raw_dir)

    # 3. Download Data
    print("Downloading real data...")
    success = download_from_huggingface(raw_dir)

    if not success:
        print("ERROR: Data source unreachable or mismatch")
        sys.exit(2)

    print("Download completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()