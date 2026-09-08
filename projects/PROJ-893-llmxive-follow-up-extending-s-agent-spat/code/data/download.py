import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional
from huggingface_hub import hf_hub_download, HfApi, RepositoryNotFoundError
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

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify file checksum."""
    return compute_sha256(file_path) == expected_hash

def download_dataset(sample_size: int = 1000, repo_id: str = "llmXive/s-agent-300k", filename: str = "s-agent-300k.jsonl"):
    """
    Download dataset from HuggingFace Hub.
    FAIL LOUD: Raises error if dataset not found or download fails.
    """
    output_dir = config.DATA_RAW
    ensure_directory(output_dir)
    
    output_file = output_dir / filename
    
    if output_file.exists():
        print(f"Dataset already exists at {output_file}. Skipping download.")
        return output_file

    print(f"Downloading {filename} from {repo_id}...")
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset"
        )
        # Move to project directory
        import shutil
        shutil.move(downloaded_path, output_file)
        print(f"Downloaded to {output_file}")
        
        # Generate manifest
        file_hash = compute_sha256(output_file)
        manifest = {filename: file_hash}
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Manifest saved to {manifest_path}")
        
        return output_file
    except RepositoryNotFoundError:
        raise RuntimeError(f"Repository {repo_id} not found. Please check the repo_id.")
    except Exception as e:
        raise RuntimeError(f"Failed to download dataset: {e}")

def main():
    parser = argparse.ArgumentParser(description="Download dataset")
    parser.add_argument("--sample-size", type=int, default=1000, help="Sample size (not used for download, just for pipeline)")
    args = parser.parse_args()

    try:
        download_dataset(sample_size=args.sample_size)
        print("Download successful.")
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
