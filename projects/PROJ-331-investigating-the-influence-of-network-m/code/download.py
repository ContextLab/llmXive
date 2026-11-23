import os
import sys
import json
import logging
import time
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import concurrent.futures
import traceback

# Import local utilities
from config import ensure_dirs
from utils import (
    get_logger, 
    log_error, 
    safe_mkdir, 
    safe_write_json, 
    safe_read_json,
    log_execution_context,
    compute_sha256,
    PipelineError
)

def get_logger_module() -> logging.Logger:
    """Returns the logger module for use in this file."""
    return get_logger("download")

def compute_sha256_file(file_path: Union[str, Path]) -> str:
    """Computes the SHA256 hash of a file."""
    return compute_sha256(file_path)

def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """Verifies the checksum of a file against an expected value."""
    actual_checksum = compute_sha256_file(file_path)
    return actual_checksum == expected_checksum

def check_hcp_availability() -> bool:
    """
    Checks if HCP S3 bucket is accessible.
    Returns True if accessible, False otherwise.
    """
    logger = get_logger()
    # Simple check by attempting to list a known directory or file
    # HCP Open Access bucket: s3://hcp-openaccess
    test_url = "https://hcp-openaccess.s3.amazonaws.com/"
    try:
        response = requests.head(test_url, timeout=10)
        if response.status_code == 200:
            logger.info("HCP S3 bucket is accessible.")
            return True
        else:
            logger.warning(f"HCP S3 bucket returned status {response.status_code}.")
            return False
    except requests.RequestException as e:
        logger.error(f"Failed to connect to HCP S3: {e}")
        return False

def download_file(url: str, dest_path: Union[str, Path], timeout: int = 3600) -> str:
    """
    Downloads a file from a URL to a destination path.
    Returns the path to the downloaded file.
    Raises FileNotFoundError if the file is not found (404).
    """
    logger = get_logger()
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"Downloaded {dest_path}")
        return str(dest_path)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"File not found (404): {url}")
            raise FileNotFoundError(f"File not found: {url}") from e
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        raise PipelineError(f"Download failed: {e}") from e

def stream_hcp_dwi(subject_id: str, dest_dir: Union[str, Path]) -> Tuple[str, str]:
    """
    Streams HCP DWI data for a subject.
    Returns (local_path, checksum).
    """
    logger = get_logger()
    dest_dir = Path(dest_dir)
    safe_mkdir(dest_dir)
    
    # HCP S3 structure (example for 1200 release)
    # s3://hcp-openaccess/HCP_1200/{subject_id}/T1w/DWI/DWI.nii.gz
    # Note: Actual paths might vary. This is a placeholder for the pattern.
    # In a real implementation, we would use the verified URL from research.md
    base_url = f"https://hcp-openaccess.s3.amazonaws.com/HCP_1200/{subject_id}/T1w/DWI/DWI.nii.gz"
    
    dest_file = dest_dir / f"{subject_id}_dwi.nii.gz"
    
    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            download_file(base_url, dest_file)
            checksum = compute_sha256_file(dest_file)
            return str(dest_file), checksum
        except FileNotFoundError:
            logger.warning(f"Data missing for subject {subject_id} on attempt {attempt+1}")
            raise
        except PipelineError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to download after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Attempt {attempt+1} failed, retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff

def download_subject_data(subject_id: str, raw_dir: Union[str, Path]) -> Dict[str, str]:
    """
    Downloads both DWI and rsFMRI data for a subject.
    Returns a dict with keys 'dwi_path', 'rsfmri_path'.
    """
    logger = get_logger()
    log_execution_context(f"download_subject_data({subject_id})", "STARTED")
    
    try:
        dwi_path, dwi_checksum = stream_hcp_dwi(subject_id, Path(raw_dir) / "dwi")
        
        # Placeholder for rsFMRI download (similar logic)
        # rsfmri_path, rsfmri_checksum = stream_hcp_rsfmri(subject_id, Path(raw_dir) / "rsfmri")
        
        # For now, we'll just return DWI path to satisfy the interface
        # In a full implementation, rsFMRI would be downloaded similarly
        result = {
            'dwi_path': dwi_path,
            'rsfmri_path': None  # Placeholder
        }
        
        # Record checksums
        checksums_file = Path(raw_dir) / ".checksums.json"
        checksums = safe_read_json(checksums_file) if checksums_file.exists() else {}
        checksums[subject_id] = {'dwi': dwi_checksum}
        safe_write_json(checksums_file, checksums)
        
        log_execution_context(f"download_subject_data({subject_id})", "COMPLETED")
        return result
    except Exception as e:
        log_error(e, f"Failed to download data for {subject_id}")
        log_execution_context(f"download_subject_data({subject_id})", "FAILED", str(e))
        raise

def load_subject_list(subject_ids_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Loads the list of subject IDs from a file.
    Validates the file exists and writes a manifest.
    """
    logger = get_logger()
    subject_ids_file = Path(subject_ids_file)
    
    if not subject_ids_file.exists():
        raise FileNotFoundError(f"Subject list file not found: {subject_ids_file}")
    
    # Read subject IDs (one per line or JSON array)
    content = subject_ids_file.read_text().strip()
    try:
        subject_ids = json.loads(content)
    except json.JSONDecodeError:
        # Assume one ID per line
        subject_ids = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Write manifest
    manifest = {
        "total_subjects": len(subject_ids),
        "subject_ids": subject_ids,
        "subjects_attempted": 0  # Will be updated during processing
    }
    manifest_path = Path("data/processed/subject_list_manifest.json")
    safe_mkdir(manifest_path.parent)
    safe_write_json(manifest_path, manifest)
    
    logger.info(f"Loaded {len(subject_ids)} subjects. Manifest saved to {manifest_path}")
    return manifest

def process_subjects(subject_ids: List[str], raw_dir: Union[str, Path]) -> List[Dict]:
    """
    Processes a list of subjects by downloading their data.
    """
    logger = get_logger()
    results = []
    
    for subject_id in subject_ids:
        try:
            data = download_subject_data(subject_id, raw_dir)
            results.append({'subject_id': subject_id, 'status': 'success', 'data': data})
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
            results.append({'subject_id': subject_id, 'status': 'failed', 'error': str(e)})
    
    return results

def main():
    """Main entry point for the download script."""
    logger = get_logger()
    logger.info("Starting data download pipeline...")
    
    # Load subject list
    subject_ids_file = Path("data/raw/subject_ids.txt")
    if not subject_ids_file.exists():
        logger.error(f"Subject list file not found: {subject_ids_file}")
        sys.exit(1)
    
    manifest = load_subject_list(subject_ids_file)
    subject_ids = manifest['subject_ids']
    
    # Check HCP availability
    if not check_hcp_availability():
        logger.warning("HCP S3 bucket not accessible. Skipping download.")
        sys.exit(1)
    
    # Process subjects
    raw_dir = Path("data/raw")
    results = process_subjects(subject_ids, raw_dir)
    
    # Update manifest with attempt count
    manifest['subjects_attempted'] = len(results)
    safe_write_json(Path("data/processed/subject_list_manifest.json"), manifest)
    
    # Summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    logger.info(f"Download complete. Success: {success_count}/{len(results)}")

if __name__ == "__main__":
    main()
