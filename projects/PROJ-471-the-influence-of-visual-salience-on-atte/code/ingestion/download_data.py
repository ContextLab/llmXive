import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset
from huggingface_hub import snapshot_download

from config import get_paths, get_hyperparams
from utils.logging import get_logger, log_error_context
from utils.versioning import register_artifact

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_dataset(dataset_id: str, local_dir: Path, revision: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch a dataset from Hugging Face Hub using snapshot_download.
    
    Args:
        dataset_id: The Hugging Face dataset identifier (e.g., 'openneuro/ds000001').
        local_dir: The local directory to cache the dataset.
        revision: Optional specific revision/tag to download.
        
    Returns:
        A dictionary containing metadata about the downloaded dataset.
        
    Raises:
        Exception: If the download fails or the dataset cannot be found.
    """
    logger.info(f"Fetching dataset '{dataset_id}' to '{local_dir}'")
    
    try:
        # Use snapshot_download to get the full dataset locally
        # This caches the data in the local_dir
        downloaded_path = snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            local_dir=str(local_dir),
            revision=revision,
            allow_patterns=["*.png", "*.jpg", "*.jpeg", "*.nii", "*.json", "*.tsv", "*.txt"],
            max_workers=4
        )
        
        logger.info(f"Dataset downloaded successfully to: {downloaded_path}")
        
        return {
            "dataset_id": dataset_id,
            "local_path": str(downloaded_path),
            "revision": revision,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to download dataset '{dataset_id}': {e}")
        raise e

def validate_and_cache_images(source_dir: Path, cache_dir: Path, checksum_manifest_path: Path) -> List[Dict[str, Any]]:
    """
    Validate downloaded images against a manifest (if exists) or generate a new manifest.
    Copies valid images to the cache directory.
    
    Args:
        source_dir: Directory containing the raw downloaded dataset.
        cache_dir: Directory to store validated and cached images.
        checksum_manifest_path: Path to the JSON file containing expected checksums.
        
    Returns:
        List of dictionaries containing validation results for each image.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing manifest if it exists
    expected_checksums = {}
    if checksum_manifest_path.exists():
        logger.info(f"Loading existing checksum manifest from {checksum_manifest_path}")
        with open(checksum_manifest_path, 'r') as f:
            manifest_data = json.load(f)
            expected_checksums = {item['filename']: item['sha256'] for item in manifest_data.get('files', [])}
    else:
        logger.info("No existing checksum manifest found. Will generate new one.")
    
    # Find all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(source_dir.rglob(f'*{ext}'))
        image_files.extend(source_dir.rglob(f'*{ext.upper()}'))
    
    if not image_files:
        logger.warning(f"No image files found in {source_dir}")
        return []
    
    logger.info(f"Found {len(image_files)} image files to validate")
    
    validation_results = []
    valid_count = 0
    invalid_count = 0
    new_files = []
    
    for img_path in image_files:
        filename = img_path.name
        try:
            # Compute checksum
            actual_checksum = compute_sha256(img_path)
            
            # Check if we have an expected checksum
            if filename in expected_checksums:
                expected = expected_checksums[filename]
                is_valid = actual_checksum == expected
                status = "valid" if is_valid else "checksum_mismatch"
            else:
                # New file - mark as valid but add to new_files
                is_valid = True
                status = "new"
                new_files.append({
                    "filename": filename,
                    "sha256": actual_checksum
                })
            
            # Copy valid files to cache
            if is_valid:
                dest_path = cache_dir / filename
                # Handle potential filename collisions by adding a hash suffix if needed
                if dest_path.exists():
                    dest_path = cache_dir / f"{filename.split('.')[0]}_{actual_checksum[:8]}.{filename.split('.')[-1]}"
                
                with open(img_path, 'rb') as src, open(dest_path, 'wb') as dst:
                    dst.write(src.read())
                
                valid_count += 1
            else:
                invalid_count += 1
                logger.warning(f"Checksum mismatch for {filename}: expected {expected_checksums[filename]}, got {actual_checksum}")
            
            validation_results.append({
                "filename": filename,
                "source_path": str(img_path),
                "cache_path": str(dest_path) if is_valid else None,
                "sha256": actual_checksum,
                "status": status,
                "size_bytes": img_path.stat().st_size
            })
            
        except Exception as e:
            logger.error(f"Error processing {img_path}: {e}")
            validation_results.append({
                "filename": filename,
                "source_path": str(img_path),
                "cache_path": None,
                "sha256": None,
                "status": "error",
                "error": str(e)
            })
            invalid_count += 1
    
    # Update manifest with new files
    if new_files or checksum_manifest_path.exists():
        all_files = list(expected_checksums.keys()) + [f['filename'] for f in new_files]
        updated_manifest = {
            "dataset_id": source_dir.parent.name,
            "generated_at": str(datetime.now()),
            "files": validation_results
        }
        
        with open(checksum_manifest_path, 'w') as f:
            json.dump(updated_manifest, f, indent=2)
        
        logger.info(f"Updated checksum manifest saved to {checksum_manifest_path}")
    
    logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid/errors")
    
    # Register the manifest as an artifact
    if checksum_manifest_path.exists():
        register_artifact(checksum_manifest_path)
    
    return validation_results

def main():
    """
    Main entry point for the data ingestion pipeline.
    Downloads a dataset, validates checksums, and caches images.
    """
    paths = get_paths()
    hyperparams = get_hyperparams()
    
    # Configuration
    dataset_id = hyperparams.get('dataset_id', 'openneuro/ds000224')  # Default to a known dataset
    revision = hyperparams.get('dataset_revision', None)
    
    raw_data_dir = paths.data / "raw" / dataset_id.split('/')[-1]
    cache_dir = paths.data / "processed" / "images"
    manifest_path = paths.data / "interim" / "dataset_checksums.json"
    
    # Ensure directories exist
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    (paths.data / "interim").mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting data ingestion for dataset: {dataset_id}")
    
    try:
        # Step 1: Fetch dataset
        fetch_result = fetch_dataset(dataset_id, raw_data_dir, revision)
        
        if fetch_result['status'] != 'success':
            raise RuntimeError(f"Dataset fetch failed: {fetch_result}")
        
        # Step 2: Validate and cache images
        validation_results = validate_and_cache_images(raw_data_dir, cache_dir, manifest_path)
        
        if not validation_results:
            logger.warning("No images were validated. Check the dataset contents.")
            return {"status": "warning", "message": "No images found"}
        
        # Step 3: Log summary
        valid_count = sum(1 for r in validation_results if r['status'] in ['valid', 'new'])
        invalid_count = len(validation_results) - valid_count
        
        summary = {
            "status": "success",
            "dataset_id": dataset_id,
            "total_files": len(validation_results),
            "valid_files": valid_count,
            "invalid_files": invalid_count,
            "cache_dir": str(cache_dir),
            "manifest_path": str(manifest_path)
        }
        
        logger.info(f"Ingestion summary: {json.dumps(summary)}")
        
        # Register the final summary as an artifact
        summary_path = paths.data / "interim" / "ingestion_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        register_artifact(summary_path)
        
        return summary
        
    except Exception as e:
        log_error_context(e, "Data ingestion failed")
        raise

if __name__ == "__main__":
    main()
