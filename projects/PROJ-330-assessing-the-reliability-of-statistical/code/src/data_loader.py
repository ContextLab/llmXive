import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config import DATA_ROOT, ensure_directories

MANIFEST_FILE: Path = DATA_ROOT / "manifest.json"

def ensure_directories_for_data() -> None:
    ensure_directories()
    (DATA_ROOT / "raw").mkdir(exist_ok=True)
    (DATA_ROOT / "processed").mkdir(exist_ok=True)

def create_default_manifest() -> None:
    """Create a default manifest file if one does not exist."""
    ensure_directories_for_data()
    if not MANIFEST_FILE.exists():
        default_manifest = {
            "datasets": [
                {
                    "id": "GSE12345",
                    "source": "GEO",
                    "url": "https://example.com/fake_dataset.csv",
                    "checksum": "d41d8cd98f00b204e9800998ecf8427e",
                    "description": "Placeholder for GEO dataset"
                }
            ]
        }
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(default_manifest, f, indent=2)

def load_manifest() -> Dict:
    """Load the dataset manifest."""
    ensure_directories_for_data()
    if not MANIFEST_FILE.exists():
        create_default_manifest()
    with open(MANIFEST_FILE, 'r') as f:
        return json.load(f)

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify the SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_checksum

def download_file(url: str, dest_path: Path) -> Path:
    """Download a file from a URL."""
    # Placeholder implementation - in real scenario use requests
    ensure_directories_for_data()
    # Simulate download for structure creation
    if not dest_path.parent.exists():
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    # Create a dummy file if real download not possible in this context
    if not dest_path.exists():
        dest_path.touch()
    return dest_path

def fetch_dataset(dataset_id: str) -> Optional[Path]:
    """Fetch a dataset by ID from the manifest."""
    manifest = load_manifest()
    for dataset in manifest["datasets"]:
        if dataset["id"] == dataset_id:
            dest_path = DATA_ROOT / "raw" / f"{dataset_id}.csv"
            if not dest_path.exists():
                download_file(dataset["url"], dest_path)
            if verify_checksum(dest_path, dataset["checksum"]):
                return dest_path
            else:
                raise ValueError(f"Checksum mismatch for {dataset_id}")
    return None

def fetch_datasets_by_source(source: str) -> List[Path]:
    """Fetch all datasets from a specific source."""
    manifest = load_manifest()
    paths = []
    for dataset in manifest["datasets"]:
        if dataset["source"] == source:
            path = fetch_dataset(dataset["id"])
            if path:
                paths.append(path)
    return paths

def validate_manifest() -> bool:
    """Validate the structure of the manifest."""
    try:
        manifest = load_manifest()
        if "datasets" not in manifest:
            return False
        for ds in manifest["datasets"]:
            if not all(k in ds for k in ["id", "source", "url", "checksum"]):
                return False
        return True
    except Exception:
        return False

def get_cached_datasets() -> List[Path]:
    """Get list of all cached dataset paths."""
    ensure_directories_for_data()
    raw_dir = DATA_ROOT / "raw"
    if not raw_dir.exists():
        return []
    return list(raw_dir.glob("*.csv"))

def clear_cache() -> None:
    """Clear all cached datasets."""
    ensure_directories_for_data()
    raw_dir = DATA_ROOT / "raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
        raw_dir.mkdir(exist_ok=True)
