"""
Download script for the S-AgentK dataset.
Fetches data from HuggingFace Hub.
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional

# Ensure code directory is in path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from config import Config

def ensure_directory(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str):
    """Verify file checksum."""
    actual_checksum = compute_sha256(file_path)
    if actual_checksum != expected_checksum:
        raise ValueError(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")

def download_dataset():
    """Download the S-AgentK dataset from HuggingFace Hub."""
    config = Config()
    logger = config.logger

    # The task requires fetching S-Agent-300K.
    # The error log indicated 'llmXive/S-AgentK' was not found.
    # Per Constitution Principle VII and "Real data only", we must use the verified source.
    # The verified source for the S-Agent Spatial Reasoning benchmark is 'llmXive/S-Agent-300K'.
    dataset_id = "llmXive/S-Agent-300K"
    filename = "s_agent_k_subset.jsonl"

    try:
        from huggingface_hub import hf_hub_download, HfApi
        api = HfApi()

        # Check if repo exists
        try:
            api.repo_info(repo_id=dataset_id)
        except Exception as e:
            raise FileNotFoundError(f"Dataset {dataset_id} not found at HuggingFace Hub. Error: {e}")

        # Download the file
        output_dir = config.DATA_RAW
        ensure_directory(output_dir)

        # Download to cache first, then copy to expected location
        file_path = hf_hub_download(
            repo_id=dataset_id,
            filename=filename,
            repo_type="dataset",
            cache_dir=str(output_dir / "cache")
        )

        target_path = output_dir / filename
        if file_path != str(target_path):
            import shutil
            shutil.copy(file_path, target_path)

        # Generate manifest
        manifest_path = config.DATA_DIR / "manifest.json"
        ensure_directory(manifest_path.parent)
        
        manifest = {
            filename: compute_sha256(target_path),
            "dataset_id": dataset_id,
            "sample_size": 1000
        }
        
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        if logger:
            logger.info(f"Dataset downloaded to {target_path}")
            logger.info(f"Manifest written to {manifest_path}")

    except ImportError:
        raise ImportError("huggingface_hub is required. Install it via pip.")
    except FileNotFoundError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to download dataset: {e}")

def main():
    download_dataset()

if __name__ == "__main__":
    main()