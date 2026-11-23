"""
Data loading module for genomic datasets.
Fetches from GEO, TCGA, ENCODE via manifest and verifies checksums.
"""
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from src.config import ensure_directories, DATA_DIR

def ensure_directories_for_data() -> None:
    """Ensure data directory structure exists."""
    ensure_directories()

def create_default_manifest() -> Path:
    """Create a default manifest file if one doesn't exist."""
    manifest_path = DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        default_manifest = {
            "datasets": [
                {
                    "id": "GSE12345",
                    "source": "GEO",
                    "url": "https://example.com/GSE12345.tar.gz",
                    "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "description": "Example RNA-seq dataset"
                }
            ]
        }
        with open(manifest_path, "w") as f:
            json.dump(default_manifest, f, indent=2)
    return manifest_path

def load_manifest(manifest_path: Optional[Path] = None) -> dict:
    """Load the dataset manifest."""
    if manifest_path is None:
        manifest_path = DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        create_default_manifest()
    with open(manifest_path, "r") as f:
        return json.load(f)

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify the SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_checksum

def download_file(url: str, dest_path: Path) -> Path:
    """Download a file from a URL to a destination path."""
    import requests
    ensure_directories_for_data()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return dest_path

def fetch_dataset(dataset_id: str) -> Path:
    """Fetch a specific dataset by ID from the manifest."""
    manifest = load_manifest()
    dataset_info = None
    for ds in manifest.get("datasets", []):
        if ds["id"] == dataset_id:
            dataset_info = ds
            break
    
    if not dataset_info:
        raise ValueError(f"Dataset {dataset_id} not found in manifest")
    
    local_path = DATA_DIR / f"{dataset_id}.tar.gz"
    if not local_path.exists():
        download_file(dataset_info["url"], local_path)
        if not verify_checksum(local_path, dataset_info["checksum"]):
            raise RuntimeError(f"Checksum verification failed for {dataset_id}")
    return local_path

def fetch_datasets_by_source(source: str) -> list:
    """Fetch all datasets from a specific source (GEO, TCGA, ENCODE)."""
    manifest = load_manifest()
    return [ds for ds in manifest.get("datasets", []) if ds.get("source") == source]

def validate_manifest(manifest_path: Optional[Path] = None) -> bool:
    """Validate the manifest structure."""
    try:
        data = load_manifest(manifest_path)
        if "datasets" not in data:
            return False
        for ds in data["datasets"]:
            if not all(k in ds for k in ["id", "source", "url", "checksum"]):
                return False
        return True
    except Exception:
        return False

def get_cached_datasets() -> list:
    """List all cached datasets in the data directory."""
    ensure_directories_for_data()
    return [f.name for f in DATA_DIR.glob("*.tar.gz") if f.is_file()]

def clear_cache() -> int:
    """Remove all cached datasets. Returns count of removed files."""
    ensure_directories_for_data()
    files = list(DATA_DIR.glob("*.tar.gz"))
    for f in files:
        f.unlink()
    return len(files)
