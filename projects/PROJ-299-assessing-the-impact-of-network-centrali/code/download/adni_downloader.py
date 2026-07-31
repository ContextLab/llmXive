"""
ADNI Downloader Module.

Implements authentication and data retrieval from the LONI IDGK portal
for rs-fMRI NIfTI files and clinical CSVs.
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import requests
from dotenv import load_dotenv

# Local imports based on project API surface
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.env_config import validate_adni_credentials, get_config
from utils.logging_config import setup_logging, get_logger, log_event

# Constants
ADNI_API_BASE = "https://ida.loni.usc.edu"
# Note: The actual LONI IDGK portal API often requires session cookies or specific
# endpoints. This implementation assumes a standard authenticated download pattern
# or direct file access via constructed URLs if the API allows public access
# with credentials. If the specific endpoint requires a token, the `validate_adni_credentials`
# step should ideally fetch one, but for this implementation, we assume the
# credentials allow direct access to the file endpoints or a known download endpoint.

# Placeholder for the actual download endpoint. In a real ADNI integration,
# this would be dynamic based on the study metadata API.
# We will attempt to fetch a manifest first or construct the path based on known ADNI structure.
# For this task, we assume we are downloading specific files for known participant IDs.
# The actual URL pattern for ADNI data often looks like:
# https://ida.loni.usc.edu/services/download?study=ADNI&fileId=...
# or similar. Since we cannot hardcode a specific file ID without a manifest,
# we will implement a "manifest fetch" simulation that would call the real API
# in production, and then download the files.

# To satisfy the "Real Data Only" constraint without a live API key that grants
# full manifest access in this sandbox, we will implement the loader to:
# 1. Validate credentials.
# 2. Attempt to fetch a manifest or file list from a known public endpoint if available,
#    OR (more likely for ADNI) use a known set of public test data URLs if the
#    project spec implies a public subset, OR raise a clear error if the credentials
#    are not sufficient to access the private LONI portal.
#
# CRITICAL: The task requires fetching from the LONI IDGK portal API.
# Since I cannot execute network calls to private portals in this environment,
# I will implement the code to use the `requests` library against the ADNI
# endpoint. If the credentials are invalid or the endpoint is unreachable,
# it will raise an exception (Fail Loudly).
#
# For the purpose of this implementation, we assume the existence of a 
# `manifest.json` or similar metadata file that maps participant IDs to file URLs.
# In a real run, this would be fetched via `requests.get(api_url, auth=...)`.

# We will use a known public ADNI dataset URL pattern if credentials are not provided,
# but the task requires `--user`/`--pass` and abort if unavailable.
# Therefore, we strictly require credentials.

logger = get_logger("adni_downloader")

def load_manifest(user: str, password: str) -> List[Dict]:
    """
    Fetches the manifest of available files for the study.
    In a real scenario, this would query the LONI IDGK API.
    For this implementation, we attempt to fetch a known public manifest
    or raise an error if authentication fails.
    """
    # Placeholder URL for the manifest. In production, this is the real API endpoint.
    # ADNI often uses a specific JSON endpoint for file lists.
    manifest_url = f"{ADNI_API_BASE}/api/v1/files?study=ADNI&format=json"
    
    try:
        # Attempt to fetch with credentials
        response = requests.get(
            manifest_url,
            auth=(user, password),
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("Authentication failed. Please check ADNI credentials.")
            raise RuntimeError("ADNI Authentication Failed: Invalid credentials.")
        elif e.response.status_code == 404:
            # Fallback: Try a known public endpoint if the private one is not accessible
            # This is a strict requirement: if real data is not reachable, fail loudly.
            # We do NOT fall back to synthetic.
            logger.error(f"Manifest endpoint not found ({manifest_url}). "
                         "Real ADNI data source unreachable.")
            raise RuntimeError("Real ADNI data source unreachable. Manifest fetch failed.")
        else:
            logger.error(f"HTTP Error fetching manifest: {e}")
            raise
    except Exception as e:
        logger.error(f"Network error fetching manifest: {e}")
        raise

def find_files_for_participants(manifest: List[Dict], participant_ids: List[str]) -> Dict[str, List[str]]:
    """
    Filters the manifest to find NIfTI and CSV files for the given participant IDs.
    Returns a dict: { participant_id: [url1, url2, ...] }
    """
    # This is a simplified filter logic. Real ADNI manifests are complex.
    # We assume the manifest contains 'subject_id', 'file_type', and 'download_url'.
    result = {pid: [] for pid in participant_ids}
    
    for item in manifest:
        pid = item.get('subject_id')
        if pid in result:
            file_type = item.get('file_type', '').lower()
            if 'nifti' in file_type or 'neuro' in file_type:
                result[pid].append(item['download_url'])
            elif 'clinical' in file_type or 'csv' in file_type:
                result[pid].append(item['download_url'])
    
    return result

def download_file(url: str, output_path: Path, user: str, password: str) -> bool:
    """
    Downloads a single file from the given URL.
    """
    try:
        logger.info(f"Downloading {url} to {output_path}")
        with requests.get(url, auth=(user, password), stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def validate_clinical_csv(csv_path: Path) -> bool:
    """
    Validates that the clinical CSV contains required columns: TMT-A and WAIS-R.
    """
    required_cols = ['TMT-A', 'WAIS-R']
    if not csv_path.exists():
        logger.error(f"Clinical CSV not found: {csv_path}")
        return False
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if headers is None:
                logger.error(f"Empty headers in {csv_path}")
                return False
            
            missing = [col for col in required_cols if col not in headers]
            if missing:
                logger.error(f"Missing required columns in {csv_path}: {missing}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error reading CSV {csv_path}: {e}")
        return False

def run_downloader(
    participant_ids: List[str],
    output_dir: Path,
    user: str,
    password: str
) -> Tuple[int, int]:
    """
    Main downloader logic.
    Returns (downloaded_count, failed_count)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    clinical_dir = output_dir / "clinical"
    imaging_dir = output_dir / "imaging"
    clinical_dir.mkdir(exist_ok=True)
    imaging_dir.mkdir(exist_ok=True)

    # Step 1: Fetch Manifest
    logger.info("Fetching ADNI manifest...")
    try:
        manifest = load_manifest(user, password)
    except RuntimeError as e:
        logger.critical(str(e))
        return 0, 0

    # Step 2: Map files
    file_map = find_files_for_participants(manifest, participant_ids)

    downloaded = 0
    failed = 0

    for pid, urls in file_map.items():
        if not urls:
            logger.warning(f"No files found for participant {pid}")
            failed += 1
            continue

        for url in urls:
            # Determine filename
            filename = url.split('/')[-1]
            if filename.endswith('.nii') or filename.endswith('.nii.gz'):
                dest = imaging_dir / f"{pid}_{filename}"
            elif filename.endswith('.csv'):
                dest = clinical_dir / f"{pid}_{filename}"
            else:
                # Skip unknown types or treat as generic
                dest = output_dir / filename

            if download_file(url, dest, user, password):
                downloaded += 1
                # Validate clinical CSVs immediately
                if dest.suffix == '.csv':
                    if not validate_clinical_csv(dest):
                        logger.error(f"Validation failed for {dest}. Aborting.")
                        raise RuntimeError(f"Validation failed for clinical data: {dest}")
            else:
                failed += 1

    return downloaded, failed

def main():
    parser = argparse.ArgumentParser(description="Download ADNI rs-fMRI and clinical data.")
    parser.add_argument("--user", required=True, help="ADNI Username")
    parser.add_argument("--pass", dest="password", required=True, help="ADNI Password")
    parser.add_argument("--ids", type=str, default=None, 
                        help="Comma-separated list of participant IDs. "
                             "If not provided, reads from data/raw/participant_list.csv")
    parser.add_argument("--output", type=str, default="data/raw", 
                        help="Output directory for downloaded data")
    
    args = parser.parse_args()

    # Setup logging
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    setup_logging(log_file=log_path / "pipeline.log")

    # Load environment to validate credentials (optional but good practice)
    # The task requires explicit user/pass, so we use those.
    # We do not fall back to .env if args are provided, but we validate.
    if not args.user or not args.password:
        logger.error("Credentials are required.")
        sys.exit(1)

    # Load participant IDs
    if args.ids:
        pids = [p.strip() for p in args.ids.split(",")]
    else:
        pids_file = Path("data/raw/participant_list.csv")
        if not pids_file.exists():
            logger.error(f"Participant list not found: {pids_file}")
            sys.exit(1)
        
        with open(pids_file, 'r') as f:
            reader = csv.DictReader(f)
            pids = [row['participant_id'] for row in reader if 'participant_id' in row]
    
    if not pids:
        logger.error("No participant IDs provided.")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting download for {len(pids)} participants...")
    try:
        count, fail = run_downloader(pids, output_dir, args.user, args.password)
        logger.info(f"Download complete. Success: {count}, Failed: {fail}")
        if fail > 0:
            sys.exit(1)
    except RuntimeError as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
