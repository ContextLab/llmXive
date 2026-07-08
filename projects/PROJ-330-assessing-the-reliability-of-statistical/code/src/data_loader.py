"""
Data loader module for fetching genomic datasets from verified sources (GEO, TCGA, ENCODE).

This module handles:
- Manifest file parsing
- Downloading datasets from verified URLs
- Checksum verification (SHA256)
- Caching downloaded files
"""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse
import requests
from tqdm import tqdm

from src.config import ensure_directories, PROJECT_ROOT
from src.versioning import compute_sha256, load_state, save_state, update_artifact_state


# Constants
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.json"
DOWNLOAD_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUMS_PATH = PROJECT_ROOT / "data" / "checksums.json"

# Verified source configurations
VERIFIED_SOURCES = {
    "GEO": {
        "name": "Gene Expression Omnibus",
        "base_url": "https://ftp.ncbi.nlm.nih.gov/geo/",
        "description": "NCBI GEO repository for gene expression data"
    },
    "TCGA": {
        "name": "The Cancer Genome Atlas",
        "base_url": "https://gdc.cancer.gov/about-data/publications/",
        "description": "TCGA cancer genomics data"
    },
    "ENCODE": {
        "name": "ENCODE Project",
        "base_url": "https://www.encodeproject.org/",
        "description": "ENCODE functional genomics data"
    }
}

def ensure_directories_for_data() -> None:
    """Ensure data directories exist."""
    ensure_directories([DOWNLOAD_DIR, PROJECT_ROOT / "data"])

def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the dataset manifest file.
    
    Args:
        manifest_path: Path to manifest file. Defaults to MANIFEST_PATH.
        
    Returns:
        Dictionary containing dataset definitions.
        
    Raises:
        FileNotFoundError: If manifest file doesn't exist.
        json.JSONDecodeError: If manifest file is invalid JSON.
    """
    if manifest_path is None:
        manifest_path = MANIFEST_PATH
        
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
        
    with open(manifest_path, 'r') as f:
        return json.load(f)

def create_default_manifest() -> Path:
    """
    Create a default manifest file with example datasets from verified sources.
    
    Returns:
        Path to the created manifest file.
    """
    ensure_directories_for_data()
    
    default_manifest = {
        "version": "1.0.0",
        "datasets": [
            {
                "id": "GSE12345",
                "name": "Example RNA-seq Dataset",
                "source": "GEO",
                "url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE123nnn/GSE12345/suppl/GSE12345_RAW.tar",
                "checksum": "placeholder",
                "checksum_algorithm": "sha256",
                "description": "Example dataset for testing data loader",
                "metadata": {
                    "platform": "Illumina HiSeq",
                    "organism": "Homo sapiens",
                    "assay_type": "RNA-seq"
                }
            },
            {
                "id": "TCGA-BRCA",
                "name": "TCGA Breast Cancer RNA-seq",
                "source": "TCGA",
                "url": "https://gdc.cancer.gov/about-data/publications/BRCA-2020/TCGA_BRCA_RNAseq_counts.csv",
                "checksum": "placeholder",
                "checksum_algorithm": "sha256",
                "description": "TCGA breast cancer RNA-seq count data",
                "metadata": {
                    "platform": "Illumina HiSeq 2000",
                    "organism": "Homo sapiens",
                    "assay_type": "RNA-seq",
                    "sample_count": 1000
                }
            },
            {
                "id": "ENCODE-K562",
                "name": "ENCODE K562 RNA-seq",
                "source": "ENCODE",
                "url": "https://www.encodeproject.org/files/ENCFF001TDO/@@download/ENCFF001TDO.bed.gz",
                "checksum": "placeholder",
                "checksum_algorithm": "sha256",
                "description": "ENCODE K562 cell line RNA-seq data",
                "metadata": {
                    "platform": "Illumina",
                    "organism": "Homo sapiens",
                    "cell_line": "K562",
                    "assay_type": "RNA-seq"
                }
            }
        ]
    }
    
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(default_manifest, f, indent=2)
        
    return MANIFEST_PATH

def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify the checksum of a downloaded file.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum value.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        True if checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If unsupported algorithm is specified.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if algorithm not in ["sha256", "md5", "sha1"]:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use sha256, md5, or sha1.")
        
    actual_checksum = compute_sha256(file_path) if algorithm == "sha256" else None
    
    if algorithm == "sha256":
        return actual_checksum == expected_checksum
    elif algorithm == "md5":
        # For MD5, we'd need a separate function
        with open(file_path, 'rb') as f:
            actual_checksum = hashlib.md5(f.read()).hexdigest()
        return actual_checksum == expected_checksum
    elif algorithm == "sha1":
        with open(file_path, 'rb') as f:
            actual_checksum = hashlib.sha1(f.read()).hexdigest()
        return actual_checksum == expected_checksum
        
    return False

def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> Path:
    """
    Download a file from a URL with progress tracking.
    
    Args:
        url: URL to download from.
        dest_path: Destination path for the downloaded file.
        chunk_size: Size of chunks to download.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        requests.RequestException: If download fails.
        ValueError: If URL is invalid.
    """
    ensure_directories_for_data()
    
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError(f"Invalid URL: {url}")
        
    # Create parent directories if needed
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file already exists and is complete
    if dest_path.exists():
        # Verify if file is complete by checking if it matches expected size
        # For now, we'll re-download to ensure integrity
        pass
        
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f, tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=dest_path.name
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
                    
    except requests.RequestException as e:
        # Clean up partial download
        if dest_path.exists():
            dest_path.unlink()
        raise requests.RequestException(f"Failed to download {url}: {e}")
        
    return dest_path

def fetch_dataset(dataset_id: str, manifest: Optional[Dict[str, Any]] = None) -> Tuple[Path, Dict[str, Any]]:
    """
    Fetch a dataset by ID from the manifest.
    
    Args:
        dataset_id: ID of the dataset to fetch.
        manifest: Optional pre-loaded manifest. If None, loads from default path.
        
    Returns:
        Tuple of (path to downloaded file, dataset metadata).
        
    Raises:
        ValueError: If dataset_id not found in manifest.
        FileNotFoundError: If manifest file not found.
        RuntimeError: If checksum verification fails.
    """
    if manifest is None:
        manifest = load_manifest()
        
    # Find dataset in manifest
    dataset_info = None
    for dataset in manifest.get("datasets", []):
        if dataset.get("id") == dataset_id:
            dataset_info = dataset
            break
            
    if dataset_info is None:
        raise ValueError(f"Dataset ID '{dataset_id}' not found in manifest")
        
    # Validate source
    source = dataset_info.get("source", "").upper()
    if source not in VERIFIED_SOURCES:
        raise ValueError(f"Unsupported source: {source}. Must be one of {list(VERIFIED_SOURCES.keys())}")
        
    url = dataset_info.get("url")
    if not url:
        raise ValueError(f"Dataset '{dataset_id}' has no URL specified")
        
    checksum = dataset_info.get("checksum")
    checksum_algorithm = dataset_info.get("checksum_algorithm", "sha256")
    
    # Determine destination path
    filename = Path(url).name
    dest_path = DOWNLOAD_DIR / f"{dataset_id}_{filename}"
    
    # Download if needed
    if not dest_path.exists():
        print(f"Downloading {dataset_id} from {source}...")
        dest_path = download_file(url, dest_path)
        
    # Verify checksum if provided
    if checksum and checksum != "placeholder":
        print(f"Verifying checksum for {dataset_id}...")
        if not verify_checksum(dest_path, checksum, checksum_algorithm):
            raise RuntimeError(
                f"Checksum verification failed for {dataset_id}. "
                f"Expected: {checksum}, Algorithm: {checksum_algorithm}"
            )
        print(f"Checksum verified successfully for {dataset_id}")
    else:
        print(f"Warning: No checksum provided for {dataset_id}, skipping verification")
        
    # Update state
    state = load_state()
    update_artifact_state(
        state, 
        "data_loader", 
        str(dest_path), 
        compute_sha256(dest_path)
    )
    save_state(state)
    
    return dest_path, dataset_info

def fetch_datasets_by_source(source: str, manifest: Optional[Dict[str, Any]] = None) -> List[Tuple[Path, Dict[str, Any]]]:
    """
    Fetch all datasets from a specific source.
    
    Args:
        source: Source name (GEO, TCGA, ENCODE).
        manifest: Optional pre-loaded manifest.
        
    Returns:
        List of tuples (path, metadata) for each fetched dataset.
        
    Raises:
        ValueError: If source is invalid.
    """
    source = source.upper()
    if source not in VERIFIED_SOURCES:
        raise ValueError(f"Invalid source: {source}. Must be one of {list(VERIFIED_SOURCES.keys())}")
        
    if manifest is None:
        manifest = load_manifest()
        
    results = []
    for dataset in manifest.get("datasets", []):
        if dataset.get("source", "").upper() == source:
            try:
                path, metadata = fetch_dataset(dataset["id"], manifest)
                results.append((path, metadata))
            except Exception as e:
                print(f"Warning: Failed to fetch {dataset['id']}: {e}")
                
    return results

def validate_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Validate a manifest file for correctness.
    
    Args:
        manifest_path: Path to manifest file.
        
    Returns:
        Dictionary with validation results.
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    try:
        manifest = load_manifest(manifest_path)
    except FileNotFoundError as e:
        results["valid"] = False
        results["errors"].append(str(e))
        return results
    except json.JSONDecodeError as e:
        results["valid"] = False
        results["errors"].append(f"Invalid JSON: {e}")
        return results
        
    # Check required fields
    if "datasets" not in manifest:
        results["valid"] = False
        results["errors"].append("Missing 'datasets' field")
    else:
        for i, dataset in enumerate(manifest["datasets"]):
            dataset_id = dataset.get("id", f"dataset_{i}")
            
            # Required fields
            required_fields = ["url", "source"]
            for field in required_fields:
                if field not in dataset:
                    results["valid"] = False
                    results["errors"].append(f"Dataset '{dataset_id}' missing required field: {field}")
                    
            # Validate source
            source = dataset.get("source", "").upper()
            if source and source not in VERIFIED_SOURCES:
                results["warnings"].append(
                    f"Dataset '{dataset_id}' has unverified source: {source}"
                )
                
            # Check for checksum
            if "checksum" not in dataset:
                results["warnings"].append(
                    f"Dataset '{dataset_id}' missing checksum"
                )
                
    return results

def get_cached_datasets() -> List[Path]:
    """
    Get list of all cached datasets.
    
    Returns:
        List of paths to cached dataset files.
    """
    ensure_directories_for_data()
    if not DOWNLOAD_DIR.exists():
        return []
        
    return list(DOWNLOAD_DIR.glob("*"))

def clear_cache(dataset_id: Optional[str] = None) -> int:
    """
    Clear cached datasets.
    
    Args:
        dataset_id: Optional specific dataset ID to clear. If None, clears all.
        
    Returns:
        Number of files deleted.
    """
    ensure_directories_for_data()
    if not DOWNLOAD_DIR.exists():
        return 0
        
    count = 0
    for file_path in DOWNLOAD_DIR.glob("*"):
        if dataset_id is None or dataset_id in file_path.name:
            file_path.unlink()
            count += 1
            
    return count

if __name__ == "__main__":
    # Example usage: Create default manifest and validate it
    print("Creating default manifest...")
    manifest_path = create_default_manifest()
    print(f"Manifest created at: {manifest_path}")
    
    print("\nValidating manifest...")
    validation_results = validate_manifest(manifest_path)
    print(f"Valid: {validation_results['valid']}")
    if validation_results['errors']:
        print("Errors:", validation_results['errors'])
    if validation_results['warnings']:
        print("Warnings:", validation_results['warnings'])
        
    # Example: Fetch a dataset (this would require actual URLs to work)
    # Uncomment to test with real URLs:
    # try:
    #     manifest = load_manifest()
    #     if manifest['datasets']:
    #         sample_dataset = manifest['datasets'][0]['id']
    #         print(f"\nAttempting to fetch dataset: {sample_dataset}")
    #         path, metadata = fetch_dataset(sample_dataset, manifest)
    #         print(f"Successfully fetched: {path}")
    # except Exception as e:
    #     print(f"Error fetching dataset: {e}")
