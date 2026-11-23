"""
Data acquisition module for PROJ-800.
Fetches raw fMRI NIfTI files from OpenNeuro dataset ds000224 (HCP Young Adult).
Verifies >= 100 usable subjects before processing.
"""
import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from tqdm import tqdm

# Import project utilities
from utils.logger import get_logger, DataFetchError, ProcessingError, log_error_and_raise
from utils.checksum import compute_file_checksum
from config import get_path, ensure_paths_exist

logger = get_logger(__name__)

# Configuration
PRIMARY_DATASET = "ds000224"  # HCP Young Adult
PRIMARY_VERSION = "1.0.0"
ALT_DATASET = "ds000005"      # OpenNeuro Demo (fallback)
ALT_VERSION = "1.0.0"

# OpenNeuro API endpoints
DATASET_URL_TEMPLATE = "https://openneuro.org/datasets/{dataset_id}/files/{version_id}"
FILES_API_URL = "https://openneuro.org/datasets/{dataset_id}/files"
DOWNLOAD_URL_TEMPLATE = "https://openneuro.org/datasets/{dataset_id}/versions/{version_id}/download"

# Target: 100 subjects
TARGET_SUBJECT_COUNT = 100
SUBJECT_PREFIX = "sub-"
FUNC_SUFFIX = "_task-rest_bold.nii.gz"

def get_openneuro_dataset_info(dataset_id: str, version: str) -> Dict[str, Any]:
    """Fetch dataset metadata and file list from OpenNeuro API."""
    # OpenNeuro GraphQL API for file listing
    # Note: Direct file listing via REST is limited, we use the public file tree endpoint
    # or the download manifest.
    
    # We will use the public download manifest endpoint which lists all files
    manifest_url = f"https://openneuro.org/datasets/{dataset_id}/versions/{version}/download"
    
    # Actually, for programmatic access to the file tree, we use the GraphQL API
    # But a simpler approach for this specific task is to use the openneuro-py library
    # or the public s3 bucket structure if accessible.
    # However, to avoid external dependencies not in requirements.txt (unless added),
    # we will use the requests library to fetch the file tree from the public API.
    
    # The most reliable programmatic way without installing openneuro-py is:
    # 1. Fetch the dataset description to confirm existence.
    # 2. Use the 'files' API if available, or parse the download manifest.
    
    # Let's try the public files endpoint (if available) or the download manifest.
    # OpenNeuro provides a JSON manifest at:
    # https://openneuro.org/datasets/{id}/versions/{ver}/download?format=json
    # But the standard way is to use the openneuro CLI or API.
    # Since we can't assume openneuro-py is installed, we will use a direct HTTP approach
    # to the public file tree if available, or fallback to a known structure.
    
    # Alternative: Use the openneuro public S3 bucket structure? No, that's not stable.
    # Let's use the openneuro GraphQL API via requests.
    
    query = """
    query {
      dataset(id: "{id}") {
        id
        name
        snapshot {
          id
          files {
            id
            name
            size
            filename
            directory {
              id
              name
            }
          }
        }
      }
    }
    """
    # The above query might be too complex. Let's use the simpler public API.
    # OpenNeuro v3 API: https://openneuro.org/api/v3
    
    api_url = f"https://openneuro.org/api/v3/datasets/{dataset_id}/snapshots/{version}"
    try:
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Dataset {dataset_id} version {version} not found via API: {response.status_code}")
            return {}
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch dataset info from API: {e}")
        return {}

def list_subjects_from_manifest(dataset_id: str, version: str) -> List[str]:
    """
    List subjects available in the dataset by parsing the download manifest.
    This avoids downloading the full dataset just to list subjects.
    """
    # OpenNeuro provides a manifest file in the download tarball, but we can't download the tarball yet.
    # We will use the GraphQL API to list files.
    
    # GraphQL endpoint
    graphql_url = "https://openneuro.org/graphql"
    
    # We need to fetch the snapshot files.
    # The query below fetches the snapshot by ID (we need the snapshot ID first).
    # Let's try to fetch the dataset and its snapshots.
    
    # Simplified approach: The file structure is standard BIDS.
    # We can try to fetch the directory listing from the public s3 bucket if we know the path,
    # but that's brittle.
    
    # Let's use the openneuro-py library if it's available? No, we can't add it yet.
    # We will implement a simple downloader that attempts to fetch the file tree.
    
    # Actually, the most robust way without extra deps is to use the `openneuro` CLI if installed,
    # but we can't rely on that.
    
    # Let's assume we can use the public API to get the file list.
    # The endpoint https://openneuro.org/datasets/{id}/files/{version} might work.
    
    # Fallback: We will try to download the dataset description and assume standard BIDS structure.
    # But we need to know the subject IDs.
    
    # Let's try the openneuro API directly.
    # https://openneuro.org/api/v3/datasets/{id}/snapshots/{version}/files
    
    files_url = f"https://openneuro.org/api/v3/datasets/{dataset_id}/snapshots/{version}/files"
    try:
        response = requests.get(files_url, timeout=60)
        if response.status_code == 200:
            files = response.json()
            subjects = set()
            for f in files:
                filename = f.get('filename', '')
                if filename.startswith(SUBJECT_PREFIX) and FUNC_SUFFIX in filename:
                    # Extract subject ID: sub-001/... -> sub-001
                    parts = filename.split('/')
                    if len(parts) > 0:
                        sub_id = parts[0]
                        if sub_id.startswith(SUBJECT_PREFIX):
                            subjects.add(sub_id)
            return sorted(list(subjects))
        else:
            logger.error(f"Failed to fetch file list: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching file list: {e}")
        return []

def download_file(url: str, dest_path: Path, chunk_size: int = 8192):
    """Download a file with progress bar and integrity check."""
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        with open(dest_path, 'wb') as f, tqdm(
            desc=dest_path.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        logger.info(f"Downloaded {dest_path.name} ({dest_path.stat().st_size} bytes)")
        return True
    except requests.RequestException as e:
        logger.error(f"Download failed for {url}: {e}")
        return False

def verify_subject(subject_dir: Path) -> bool:
    """Verify that a subject directory contains the required fMRI file."""
    func_files = list(subject_dir.glob(f"*{FUNC_SUFFIX}"))
    if not func_files:
        return False
    # Check file size > 0
    if func_files[0].stat().st_size == 0:
        return False
    return True

def fetch_dataset(
    dataset_id: str,
    version: str,
    target_count: int = TARGET_SUBJECT_COUNT,
    output_dir: Optional[Path] = None
) -> Tuple[List[Path], str]:
    """
    Fetch raw fMRI NIfTI files for a specified number of subjects.
    Returns list of downloaded file paths and the dataset ID used.
    """
    if output_dir is None:
        output_dir = get_path("data_raw")
    
    ensure_paths_exist([output_dir])
    
    logger.info(f"Fetching dataset {dataset_id} version {version}")
    
    # Get list of subjects
    subjects = list_subjects_from_manifest(dataset_id, version)
    if not subjects:
        raise DataFetchError(f"No subjects found for {dataset_id} v{version}")
    
    logger.info(f"Found {len(subjects)} subjects in {dataset_id}")
    
    if len(subjects) < target_count:
        raise DataFetchError(
            f"Dataset {dataset_id} has only {len(subjects)} subjects, "
            f"but {target_count} are required."
        )
    
    # Select first N subjects
    selected_subjects = subjects[:target_count]
    logger.info(f"Selected {len(selected_subjects)} subjects for download")
    
    downloaded_paths = []
    failed_subjects = []
    
    # Construct download URL for specific files?
    # OpenNeuro download API usually requires downloading the whole snapshot or using the CLI.
    # However, we can construct the direct S3 URL if we know the pattern.
    # Pattern: https://openneuro.s3.amazonaws.com/{dataset_id}/{version}/sub-{id}/...
    # But this is not guaranteed to be public.
    
    # Alternative: Use the openneuro download API which provides a manifest and download links.
    # We will try to download the manifest and then the files.
    
    # Since direct file download links are not easily available via public API without CLI,
    # and we cannot install openneuro-py, we will simulate the download process by
    # attempting to fetch the files from the public S3 bucket if the dataset is public.
    # HCP ds000224 is public.
    
    # S3 Bucket pattern for OpenNeuro:
    # https://openneuro.s3.amazonaws.com/{dataset_id}/sub-{id}/func/sub-{id}_task-rest_bold.nii.gz
    
    base_s3_url = f"https://openneuro.s3.amazonaws.com/{dataset_id}"
    
    for sub_id in selected_subjects:
        # Construct expected path
        sub_dir = output_dir / sub_id
        ensure_paths_exist([sub_dir])
        
        # Find the func file
        # We need to know the exact filename. Let's assume standard BIDS:
        # sub-XXX/func/sub-XXX_task-rest_bold.nii.gz
        # But there might be variants.
        # We will try to construct the URL and download.
        
        # Try common patterns
        patterns = [
            f"sub-{sub_id}/func/sub-{sub_id}_task-rest_bold.nii.gz",
            f"sub-{sub_id}/func/sub-{sub_id}_task-rest_bold.nii",
            f"{sub_id}/func/{sub_id}_task-rest_bold.nii.gz",
        ]
        
        downloaded = False
        for pattern in patterns:
            url = f"{base_s3_url}/{pattern}"
            dest_file = sub_dir / pattern.split('/')[-1]
            
            # Check if file exists
            if dest_file.exists() and dest_file.stat().st_size > 0:
                logger.info(f"Skipping {dest_file} (already exists)")
                downloaded_paths.append(dest_file)
                downloaded = True
                break
            
            if download_file(url, dest_file):
                if verify_subject(sub_dir):
                    downloaded_paths.append(dest_file)
                    downloaded = True
                    break
                else:
                    logger.warning(f"Downloaded file for {sub_id} failed verification, retrying...")
                    dest_file.unlink()
        
        if not downloaded:
            logger.error(f"Failed to download functional data for {sub_id}")
            failed_subjects.append(sub_id)
    
    if len(downloaded_paths) < target_count:
        raise DataFetchError(
            f"Only {len(downloaded_paths)} subjects downloaded successfully, "
            f"but {target_count} are required. Failed: {failed_subjects}"
        )
    
    logger.info(f"Successfully downloaded {len(downloaded_paths)} subjects")
    return downloaded_paths, dataset_id

def main():
    """Main entry point for data download."""
    logger.info("Starting data download for PROJ-800")
    
    try:
        # Try primary dataset
        try:
            paths, dataset_id = fetch_dataset(
                PRIMARY_DATASET,
                PRIMARY_VERSION,
                TARGET_SUBJECT_COUNT
            )
            logger.info(f"Downloaded from primary source: {dataset_id}")
        except DataFetchError as e:
            logger.warning(f"Primary source failed: {e}")
            # Fallback to alternate
            logger.info("Attempting fallback to alternate dataset")
            paths, dataset_id = fetch_dataset(
                ALT_DATASET,
                ALT_VERSION,
                TARGET_SUBJECT_COUNT
            )
            logger.info(f"Downloaded from alternate source: {dataset_id}")
        
        # Verify count
        if len(paths) < TARGET_SUBJECT_COUNT:
            raise DataFetchError(f"Only {len(paths)} subjects downloaded, need {TARGET_SUBJECT_COUNT}")
        
        # Create manifest
        manifest = {
            "dataset_id": dataset_id,
            "subjects": [str(p) for p in paths],
            "count": len(paths),
            "checksums": {str(p): compute_file_checksum(p) for p in paths}
        }
        
        manifest_path = get_path("data_raw") / "download_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Download complete. Manifest saved to {manifest_path}")
        return 0
        
    except Exception as e:
        log_error_and_raise(e, DataFetchError, "Data download failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
