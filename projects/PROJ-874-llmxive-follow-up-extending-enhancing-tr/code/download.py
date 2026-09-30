"""
Dataset download and verification module.
Handles fetching datasets from HuggingFace and verifying checksums.
"""
import os
import sys
import hashlib
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import config for paths and errors
try:
    from config import (
        get_raw_dir, 
        get_dataset_paths, 
        DatasetNotFoundError, 
        ValidationError,
        calculate_hash
    )
except ImportError:
    # Fallback for standalone execution or if config not yet loaded
    sys.path.insert(0, str(Path(__file__).parent))
    from config import (
        get_raw_dir, 
        get_dataset_paths, 
        DatasetNotFoundError, 
        ValidationError,
        calculate_hash
    )

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm ('md5' or 'sha256')
        
    Returns:
        Hex digest of the file hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is unsupported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def verify_checksums(manifest_path: Path) -> bool:
    """
    Verify file checksums against a manifest.
    
    Args:
        manifest_path: Path to the JSON manifest file
        
    Returns:
        True if all checksums match, False otherwise
        
    Raises:
        FileNotFoundError: If manifest or data files are missing
        ValidationError: If checksums do not match
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    dataset_name = manifest.get('dataset_name')
    files = manifest.get('files', [])
    checksums = manifest.get('checksums', {})
    
    all_valid = True
    missing_files = []
    
    for file_info in files:
        relative_path = file_info.get('relative_path')
        full_path = manifest_path.parent / relative_path
        
        if not full_path.exists():
            logger.error(f"File missing: {full_path}")
            missing_files.append(relative_path)
            all_valid = False
            continue
        
        # Verify MD5
        if 'md5' in checksums.get(relative_path, {}):
            expected_md5 = checksums[relative_path]['md5']
            actual_md5 = calculate_file_hash(full_path, 'md5')
            if actual_md5 != expected_md5:
                logger.error(f"MD5 mismatch for {relative_path}: expected {expected_md5}, got {actual_md5}")
                all_valid = False
        
        # Verify SHA256
        if 'sha256' in checksums.get(relative_path, {}):
            expected_sha256 = checksums[relative_path]['sha256']
            actual_sha256 = calculate_file_hash(full_path, 'sha256')
            if actual_sha256 != expected_sha256:
                logger.error(f"SHA256 mismatch for {relative_path}: expected {expected_sha256}, got {actual_sha256}")
                all_valid = False
    
    if missing_files:
        raise DatasetNotFoundError(f"Missing files in {dataset_name}: {missing_files}")
    
    if not all_valid:
        raise ValidationError(f"Checksum verification failed for {dataset_name}")
    
    logger.info(f"Checksum verification passed for {dataset_name}")
    return True

def download_dataset(dataset_name: str, force: bool = False) -> Path:
    """
    Download a dataset from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset to download
        force: If True, re-download even if already present
        
    Returns:
        Path to the downloaded dataset directory
        
    Raises:
        RuntimeError: If download fails
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("The 'datasets' library is required. Install with: pip install datasets")
    
    raw_dir = get_raw_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_path = raw_dir / dataset_name
    
    if dataset_path.exists() and not force:
        logger.info(f"Dataset {dataset_name} already exists at {dataset_path}")
        # Verify checksums if manifest exists
        manifest_path = dataset_path / "manifest.json"
        if manifest_path.exists():
            try:
                verify_checksums(manifest_path)
                return dataset_path
            except (DatasetNotFoundError, ValidationError) as e:
                logger.warning(f"Existing dataset verification failed: {e}. Re-downloading...")
                force = True
        else:
            logger.warning(f"No manifest found for {dataset_name}. Re-downloading...")
            force = True
    
    if force and dataset_path.exists():
        import shutil
        logger.info(f"Removing existing dataset at {dataset_path}")
        shutil.rmtree(dataset_path)
    
    logger.info(f"Downloading dataset: {dataset_name}")
    
    # Map dataset names to HuggingFace IDs
    # These are placeholders; in a real scenario, these would be actual HF dataset IDs
    hf_dataset_map = {
        "NarrLV": "llmXive/NarrLV",
        "VBench": "llmXive/VBench"
    }
    
    if dataset_name not in hf_dataset_map:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    hf_id = hf_dataset_map[dataset_name]
    
    try:
        dataset = load_dataset(hf_id, split="train")
        dataset.save_to_disk(str(dataset_path))
        
        # Create manifest
        manifest = {
            "dataset_name": dataset_name,
            "version": "1.0.0",
            "source": hf_id,
            "created_at": None, # Would be set to datetime.now().isoformat()
            "files": [],
            "checksums": {}
        }
        
        # Iterate over files to compute hashes and build manifest
        # Note: This assumes the saved dataset structure has accessible files
        # In practice, we might need to inspect the dataset object or the directory structure
        for file_path in dataset_path.rglob("*"):
            if file_path.is_file() and "state" not in str(file_path): # Skip internal state files
                rel_path = file_path.relative_to(dataset_path)
                file_size = file_path.stat().st_size
                
                manifest["files"].append({
                    "path": str(file_path),
                    "relative_path": str(rel_path),
                    "size_bytes": file_size
                })
                
                # Compute hashes
                md5_hash = calculate_file_hash(file_path, 'md5')
                sha256_hash = calculate_file_hash(file_path, 'sha256')
                
                manifest["checksums"][str(rel_path)] = {
                    "md5": md5_hash,
                    "sha256": sha256_hash
                }
        
        # Save manifest
        manifest_path = dataset_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Dataset {dataset_name} downloaded and manifest created at {dataset_path}")
        return dataset_path
        
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_name}: {e}")
        raise RuntimeError(f"Download failed for {dataset_name}: {e}")

def download_all_datasets(force: bool = False) -> List[Path]:
    """
    Download all required datasets.
    
    Args:
        force: If True, re-download all datasets
        
    Returns:
        List of paths to downloaded datasets
    """
    dataset_names = ["NarrLV", "VBench"]
    downloaded_paths = []
    
    for name in dataset_names:
        try:
            path = download_dataset(name, force=force)
            downloaded_paths.append(path)
        except Exception as e:
            logger.error(f"Skipping {name} due to error: {e}")
            # Continue with other datasets
    
    return downloaded_paths

def check_preflight_requirements() -> Dict[str, bool]:
    """
    Check if all required dataset files exist.
    
    Returns:
        Dictionary mapping dataset names to existence status
    """
    raw_dir = get_raw_dir()
    dataset_names = ["NarrLV", "VBench"]
    status = {}
    
    for name in dataset_names:
        dataset_path = raw_dir / name
        manifest_path = dataset_path / "manifest.json"
        
        if not dataset_path.exists():
            status[name] = False
            logger.warning(f"Dataset {name} not found at {dataset_path}")
        elif not manifest_path.exists():
            status[name] = False
            logger.warning(f"Manifest for {name} not found at {manifest_path}")
        else:
            # Verify checksums
            try:
                verify_checksums(manifest_path)
                status[name] = True
            except (DatasetNotFoundError, ValidationError) as e:
                status[name] = False
                logger.error(f"Verification failed for {name}: {e}")
    
    return status

def abort_on_missing_files(status: Dict[str, bool]) -> None:
    """
    Abort execution if any required files are missing.
    
    Args:
        status: Dictionary from check_preflight_requirements
        
    Raises:
        DatasetNotFoundError: If any dataset is missing or invalid
    """
    missing = [name for name, exists in status.items() if not exists]
    
    if missing:
        error_msg = (
            f"CRITICAL: Required datasets are missing or invalid: {missing}\n"
            "Please run `python code/download.py` to download the datasets.\n"
            "If the issue persists, check your internet connection and HuggingFace access."
        )
        logger.error(error_msg)
        raise DatasetNotFoundError(error_msg)

def main():
    """Main entry point for the download script."""
    parser = argparse.ArgumentParser(description="Download and verify llmXive datasets")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force re-download of datasets even if they exist"
    )
    parser.add_argument(
        "--verify-only", 
        action="store_true", 
        help="Only verify existing datasets, do not download"
    )
    
    args = parser.parse_args()
    
    if args.verify_only:
        logger.info("Verifying existing datasets...")
        status = check_preflight_requirements()
        if all(status.values()):
            logger.info("All datasets verified successfully.")
            return 0
        else:
            missing = [name for name, exists in status.items() if not exists]
            logger.error(f"Verification failed for: {missing}")
            return 1
    
    logger.info("Starting dataset download...")
    try:
        paths = download_all_datasets(force=args.force)
        if paths:
            logger.info(f"Successfully downloaded {len(paths)} datasets.")
            return 0
        else:
            logger.error("No datasets were downloaded.")
            return 1
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
