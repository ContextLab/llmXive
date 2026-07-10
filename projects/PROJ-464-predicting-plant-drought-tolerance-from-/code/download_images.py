"""
Download root images from the NPPN Plant Phenome Pipeline on HuggingFace Hub.

This script fetches images from the 'nppn/root-phenotyping' repository.
It enforces a strict halt if the repository is missing, inaccessible, or empty.
No GPU is required; CPU-optimized download is used.
"""

import os
import sys
from pathlib import Path

from huggingface_hub import snapshot_download, RepositoryNotFoundError, LocalEntryNotFoundError
from requests.exceptions import RequestException

# Import config for paths and seeds if available, otherwise define defaults
try:
    from config import DATA_RAW_DIR
except ImportError:
    # Fallback if config.py is not yet imported in this specific execution context
    # but relies on T004 creating code/config.py. We will use standard paths.
    DATA_RAW_DIR = Path("data/raw")

REPO_ID = "nppn/root-phenotyping"
OUTPUT_DIR = DATA_RAW_DIR / "nppn_images"


def main():
    """
    Main entry point to download NPPN root images.
    """
    print(f"Starting download of root images from HuggingFace Hub: {REPO_ID}")
    print(f"Target directory: {OUTPUT_DIR}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Download the entire repository (or specific subfolder if needed, 
        # but task implies fetching the dataset generally).
        # allow_patterns can be used to filter if specific extensions are needed,
        # but we fetch all to be safe unless specified otherwise.
        downloaded_path = snapshot_download(
            repo_id=REPO_ID,
            repo_type="dataset",
            local_dir=OUTPUT_DIR,
            local_dir_use_symlinks=False, # Force copy to ensure files are actually there
            force_download=False,
            resume_download=True
        )

        print(f"Download completed. Content path: {downloaded_path}")

        # Validate that the directory is not empty
        files = list(OUTPUT_DIR.glob("**/*"))
        # Filter out directories to count actual files
        actual_files = [f for f in files if f.is_file()]

        if not actual_files:
            print("ERROR: Downloaded directory is empty.")
            print("No real NPPN root images found. Pipeline cannot proceed.")
            sys.exit(1)

        print(f"Successfully downloaded {len(actual_files)} files.")
        print("Validation passed: Real data exists.")

    except RepositoryNotFoundError:
        print("CRITICAL ERROR: Repository 'nppn/root-phenotyping' not found on HuggingFace Hub.")
        print("No real NPPN root images found. Pipeline cannot proceed.")
        sys.exit(1)
    except LocalEntryNotFoundError:
        print("CRITICAL ERROR: Local entry not found after download attempt.")
        print("No real NPPN root images found. Pipeline cannot proceed.")
        sys.exit(1)
    except RequestException as e:
        print(f"CRITICAL ERROR: Network request failed while fetching images: {e}")
        print("No real NPPN root images found. Pipeline cannot proceed.")
        sys.exit(1)
    except Exception as e:
        print(f"CRITICAL ERROR: Unexpected failure during download: {type(e).__name__}: {e}")
        print("No real NPPN root images found. Pipeline cannot proceed.")
        sys.exit(1)


if __name__ == "__main__":
    main()