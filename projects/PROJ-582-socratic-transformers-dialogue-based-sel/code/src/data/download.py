"""
Dataset Downloader for Socratic Transformers Project.

Downloads GSM8K and MATH datasets from HuggingFace, computes SHA-256 checksums
of the cached parquet files, and writes a manifest to state/artifact_hashes.yaml.

Real Data Requirement: This script fetches actual data from the HuggingFace Hub.
It will fail loudly if the datasets cannot be downloaded.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path to ensure imports work regardless of execution context
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from datasets import load_dataset
import yaml

# Configuration for datasets
DATASET_CONFIGS = [
    {
        "name": "gsm8k",
        "hf_id": "openai/gsm8k",
        "config": "main",
        "split": "train",
        "output_file": "gsm8k_train.parquet"
    },
    {
        "name": "math",
        "hf_id": "hendrycks/math",
        "config": "prealgebra", # Using a subset to keep download manageable for initial run
        "split": "train",
        "output_file": "math_train.parquet"
    }
]

# Paths relative to project root
RAW_DATA_DIR = project_root / "data" / "raw"
STATE_DIR = project_root / "state"
MANIFEST_FILE = STATE_DIR / "artifact_hashes.yaml"

def ensure_data_dirs() -> None:
    """Ensure raw data and state directories exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest() -> Dict[str, Any]:
    """Load existing manifest if it exists."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save manifest to YAML file."""
    with open(MANIFEST_FILE, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

def download_dataset(dataset_config: Dict[str, Any]) -> Optional[Path]:
    """
    Download a dataset from HuggingFace and return the path to the cached parquet file.
    
    This function forces a download by specifying the cache_dir to our raw data directory
    and then locating the parquet file that was created.
    """
    hf_id = dataset_config["hf_id"]
    config_name = dataset_config["config"]
    split = dataset_config["split"]
    output_file_name = dataset_config["output_file"]
    
    print(f"Downloading {hf_id} ({config_name}, split={split})...")
    
    try:
        # Load dataset with streaming=False to ensure it's fully downloaded to cache
        # We point cache_dir to our raw data directory to keep artifacts organized
        dataset = load_dataset(
            hf_id, 
            config_name, 
            split=split,
            cache_dir=str(RAW_DATA_DIR / "hf_cache"),
            trust_remote_code=True
        )
        
        # The datasets library caches data in a specific structure.
        # We need to find the actual parquet file to hash it.
        # Since we are using the standard loader, the data is stored in:
        # cache_dir/hf_id/config_name/split/0.parquet (or similar)
        
        # However, for the purpose of this task, we need to produce a stable artifact.
        # The 'datasets' library doesn't always expose the local file path directly 
        # in a simple way without digging into the cache structure.
        # To ensure we have a hashable file, we will write the dataset to a parquet file
        # explicitly in our raw data directory. This is a standard practice for 
        # creating stable data artifacts in research pipelines.
        
        output_path = RAW_DATA_DIR / output_file_name
        
        # Export to parquet to create a stable, hashable file
        # Using to_pandas() might be memory intensive for full datasets, 
        # but for GSM8K and a subset of MATH it is acceptable.
        # For very large datasets, we would stream and write in chunks.
        # Given the constraints of this specific task (GSM8K + Math prealgebra),
        # loading to pandas is feasible.
        
        df = dataset.to_pandas()
        df.to_parquet(output_path, index=False)
        
        print(f"Successfully saved {output_path}")
        return output_path

    except Exception as e:
        print(f"Failed to download {hf_id}: {e}", file=sys.stderr)
        raise

def download_all_datasets() -> List[Path]:
    """Download all configured datasets and return list of file paths."""
    ensure_data_dirs()
    paths = []
    for config in DATASET_CONFIGS:
        path = download_dataset(config)
        if path:
            paths.append(path)
    return paths

def main() -> None:
    """Main entry point for the dataset downloader."""
    print("Starting dataset download process...")
    
    try:
        downloaded_files = download_all_datasets()
        
        if not downloaded_files:
            print("No datasets were downloaded.", file=sys.stderr)
            sys.exit(1)
        
        # Load existing manifest
        manifest = load_manifest()
        
        # Update manifest with new hashes
        for file_path in downloaded_files:
            file_hash = compute_file_hash(file_path)
            # Store relative path for portability
            rel_path = str(file_path.relative_to(project_root))
            manifest[rel_path] = {
                "hash": file_hash,
                "algorithm": "sha256",
                "size_bytes": file_path.stat().st_size
            }
            print(f"Hashed {rel_path}: {file_hash}")
        
        # Save manifest
        save_manifest(manifest)
        print(f"Manifest saved to {MANIFEST_FILE}")
        
    except Exception as e:
        print(f"Critical error during download process: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
