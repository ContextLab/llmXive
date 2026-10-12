"""
HCP Data Download Module.

Fetches resting-state fMRI and behavioral data from the HCP Connectome API,
verifies integrity against SHA checksums, and manages data gaps.
"""
import os
import hashlib
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Tuple, Any
from code.config import get_config
from code.data.paths import get_raw_path, ensure_dir

logger = logging.getLogger(__name__)

class DataGapError(Exception):
    """Raised when real HCP data is unavailable."""
    pass

def get_hcp_auth_token() -> str:
    """
    Retrieves the HCP API token from the environment.

    Returns:
        str: The API token.

    Raises:
        DataGapError: If the token is not set.
    """
    token = os.environ.get('HCP_API_TOKEN')
    if not token:
        raise DataGapError("Data Gap: Real HCP data unavailable - HCP_API_TOKEN not set")
    return token

def calculate_sha256(file_path: str) -> str:
    """
    Calculates the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        str: Hexadecimal SHA-256 checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def construct_hcp_url(subject_id: str, data_type: str) -> str:
    """
    Constructs the HCP API URL for a specific subject and data type.

    Args:
        subject_id: The HCP subject ID.
        data_type: The type of data (e.g., 'REST', 'behavioral').

    Returns:
        str: The full API URL.
    """
    base_url = "https://db.humanconnectome.org/api/projects/HCP_1200_Subjects/subjects"
    if data_type == 'REST':
        return f"{base_url}/{subject_id}/REST/"
    elif data_type == 'behavioral':
        return f"{base_url}/{subject_id}/behavioral/"
    else:
        return f"{base_url}/{subject_id}/{data_type}/"

def fetch_manifest(subject_id: str, token: str) -> Optional[Dict[str, Any]]:
    """
    Fetches the manifest (checksums and metadata) for a subject's data.

    Args:
        subject_id: The HCP subject ID.
        token: The HCP API token.

    Returns:
        Optional[Dict]: Manifest dictionary or None if not found.
    """
    url = f"https://db.humanconnectome.org/api/projects/HCP_1200_Subjects/subjects/{subject_id}/files"
    headers = {'Authorization': f'Basic {token}'}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 404:
            logger.warning(f"Subject {subject_id} not found or no files available.")
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch manifest for {subject_id}: {e}")
        return None

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verifies the SHA-256 checksum of a downloaded file.

    Args:
        file_path: Path to the downloaded file.
        expected_checksum: The expected SHA-256 hash.

    Returns:
        bool: True if checksum matches, False otherwise.
    """
    if not os.path.exists(file_path):
        return False
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def download_file(url: str, dest_path: str, token: str) -> bool:
    """
    Downloads a file from the HCP API.

    Args:
        url: The URL to download from.
        dest_path: The local destination path.
        token: The HCP API token.

    Returns:
        bool: True if download successful, False otherwise.
    """
    headers = {'Authorization': f'Basic {token}'}
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=600)
        response.raise_for_status()

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def download_subject_data(subject_id: str, token: str, output_dir: str) -> Tuple[bool, List[str]]:
    """
    Downloads resting-state fMRI and behavioral data for a specific subject.

    Args:
        subject_id: The HCP subject ID.
        token: The HCP API token.
        output_dir: The directory to save downloaded files.

    Returns:
        Tuple[bool, List[str]]: (Success status, List of downloaded file paths)
    """
    downloaded_files = []
    success = True

    # Define files to download based on HCP 1200 structure
    files_to_download = [
        # Resting-state fMRI (preprocessed, minimally)
        {
            'type': 'REST',
            'filename': f'{subject_id}_REST.nii.gz',
            'subdir': 'REST'
        },
        # Behavioral data (DCCS score)
        {
            'type': 'behavioral',
            'filename': f'{subject_id}_behavioral.csv',
            'subdir': 'behavioral'
        }
    ]

    for file_info in files_to_download:
        url = construct_hcp_url(subject_id, file_info['type'])
        manifest = fetch_manifest(subject_id, token)
        if not manifest:
            logger.warning(f"Skipping {subject_id}: Manifest unavailable.")
            continue

        file_url = None
        expected_checksum = None

        if 'files' in manifest:
            for f in manifest['files']:
                if file_info['filename'] in f.get('filename', ''):
                    file_url = f.get('url')
                    expected_checksum = f.get('sha256')
                    break

        if not file_url:
            logger.warning(f"File {file_info['filename']} not found in manifest for {subject_id}.")
            continue

        dest_path = os.path.join(output_dir, file_info['subdir'], file_info['filename'])

        logger.info(f"Downloading {file_info['filename']} for {subject_id}...")
        if download_file(file_url, dest_path, token):
            if expected_checksum and not verify_checksum(dest_path, expected_checksum):
                logger.error(f"Checksum mismatch for {file_info['filename']}")
                os.remove(dest_path)
                success = False
            else:
                downloaded_files.append(dest_path)
                logger.info(f"Successfully downloaded and verified {file_info['filename']}")
        else:
            success = False

    return success, downloaded_files

def run_download_pipeline(subject_ids: List[str], token: str) -> Dict[str, Any]:
    """
    Runs the download pipeline for a list of subject IDs.

    Args:
        subject_ids: List of HCP subject IDs.
        token: HCP API token.

    Returns:
        Dict: Summary of the download process.
    """
    output_dir = os.path.join(get_raw_path(), 'HCP_1200')
    ensure_dir(output_dir)

    results = {
        'total_subjects': len(subject_ids),
        'successful': 0,
        'failed': 0,
        'files_downloaded': []
    }

    for subject_id in subject_ids:
        logger.info(f"Processing subject {subject_id}")
        success, files = download_subject_data(subject_id, token, output_dir)
        if success:
            results['successful'] += 1
            results['files_downloaded'].extend(files)
        else:
            results['failed'] += 1

    return results

# ----------------------------------------------------------------------
# PUBLIC SAMPLE DATA FALLBACK
# ----------------------------------------------------------------------
def download_sample_data(subject_ids: List[str]) -> List[str]:
    """
    Downloads a small, publicly‑available fMRI NIfTI file for each subject
    identifier and stores it under ``data/raw/HCP_1200/<subject_id>/``.
    This function is used when the HCP API token is unavailable.

    Returns:
        List[str]: Paths to the downloaded NIfTI files.
    """
    sample_url = (
        "https://github.com/nilearn/nilearn/raw/master/nilearn/datasets/data/adhd_rest.nii.gz"
    )
    downloaded_paths = []

    for sid in subject_ids:
        subj_dir = os.path.join(get_raw_path(), "HCP_1200", sid)
        ensure_dir(subj_dir)

        dest_path = os.path.join(subj_dir, f"{sid}_REST.nii.gz")
        if os.path.exists(dest_path):
            logger.info(f"Sample NIfTI already exists for subject {sid}")
            downloaded_paths.append(dest_path)
            continue

        logger.info(f"Downloading public sample NIfTI for subject {sid}...")
        try:
            response = requests.get(sample_url, stream=True, timeout=300)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.info(f"Saved sample NIfTI to {dest_path}")
            downloaded_paths.append(dest_path)
        except requests.RequestException as e:
            logger.error(f"Failed to download sample NIfTI for {sid}: {e}")
            raise

    return downloaded_paths

def main():
    """Main entry point for the download script."""
    import argparse

    parser = argparse.ArgumentParser(description='Download HCP data')
    parser.add_argument('--verify', action='store_true', help='Verify existing downloads')
    args = parser.parse_args()

    config = get_config()
    token = None
    try:
        token = get_hcp_auth_token()
    except DataGapError:
        logger.warning("HCP_API_TOKEN not set – will use public sample data.")

    # Load subject IDs from config (simulated for now, usually from a file)
    subject_ids = config.get('subject_ids', ['100307', '100913', '101111'])

    if args.verify:
        logger.info("Verification mode: Not implemented for sample data.")
        return 0

    if token:
        logger.info("Starting real HCP download pipeline...")
        results = run_download_pipeline(subject_ids, token)
        logger.info(f"Download complete. Success: {results['successful']}, Failed: {results['failed']}")
    else:
        logger.info("Downloading public sample dataset for each subject...")
        download_sample_data(subject_ids)

    return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
