import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional

# Import huggingface_hub components safely
try:
    from huggingface_hub import hf_hub_download, HfApi, RepositoryNotFoundError, RevisionNotFoundError
except ImportError:
    # Fallback for older versions or missing specific exceptions
    from huggingface_hub import hf_hub_download, HfApi
    RepositoryNotFoundError = Exception
    RevisionNotFoundError = Exception

from config import config

def ensure_directory(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def download_dataset(dataset_id: str, filename: str, output_dir: Path, expected_checksum: str):
    """
    Download dataset from HuggingFace Hub.
    FAIL LOUD: Raises FileNotFoundError if dataset not found.
    """
    try:
        api = HfApi()
        # Check if repo exists
        api.repo_info(repo_id=dataset_id)
        
        # Download file
        local_path = hf_hub_download(
            repo_id=dataset_id,
            filename=filename,
            local_dir=output_dir
        )
        
        # Verify checksum
        if not verify_checksum(Path(local_path), expected_checksum):
            raise ValueError(f"Checksum mismatch for {filename}")
        
        print(f"Successfully downloaded and verified {filename}")
        
    except RepositoryNotFoundError:
        raise FileNotFoundError(f"Dataset {dataset_id} not found at HuggingFace Hub")
    except RevisionNotFoundError:
        raise FileNotFoundError(f"Revision not found for dataset {dataset_id}")
    except Exception as e:
        raise FileNotFoundError(f"Failed to download dataset: {str(e)}")

def main():
    """Main entry point for dataset download."""
    import argparse
    parser = argparse.ArgumentParser(description="Download S-AgentK dataset")
    parser.add_argument("--sample-size", type=int, default=config.SAMPLE_SIZE, help="Sample size")
    args = parser.parse_args()

    # Configuration for S-AgentK
    DATASET_ID = "llmXive/S-AgentK"
    FILENAME = "s_agent_k_subset.jsonl"
    CHECKSUM = "placeholder_checksum" # To be updated with real checksum

    output_dir = config.DATA_RAW
    ensure_directory(output_dir)

    try:
        download_dataset(DATASET_ID, FILENAME, output_dir, CHECKSUM)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
