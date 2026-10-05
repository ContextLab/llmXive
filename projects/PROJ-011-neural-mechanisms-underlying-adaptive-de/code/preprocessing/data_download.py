"""
Data Download Module for OpenNeuro ds003694.

Fetches the specified dataset using the openneuro-py library.
Implements strict fail-loudly safety: no synthetic fallbacks.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import yaml

# Attempt to import openneuro. If missing, we raise a clear ImportError
# that prevents the script from running, rather than falling back to mocks.
try:
    import openneuro
    from openneuro import download
except ImportError:
    raise ImportError(
        "The 'openneuro-py' package is required for data download. "
        "Please install it via: pip install openneuro-py"
    )

from utils.io import ensure_dir, file_exists, save_yaml, load_yaml
from utils.logger import get_logger

logger = get_logger(__name__)

DATASET_ID = "ds003694"
EXCLUSIONS_FILE = "state/exclusions.yaml"
DATASET_MANIFEST = "state/dataset_manifest.json"

class DataDownloadError(Exception):
    """Custom exception for data download failures."""
    pass

def get_dataset_client() -> Any:
    """
    Initialize the OpenNeuro client.
    Since we are using the download function which handles the API internally,
    we ensure the environment is ready.
    """
    logger.info(f"Initializing OpenNeuro client for dataset {DATASET_ID}...")
    # The openneuro-py library handles authentication and API connection
    # implicitly during download. We verify connectivity by attempting a dry-run
    # or simply proceeding if the download function is available.
    return download

def get_participant_list(dataset_id: str) -> List[str]:
    """
    Retrieve the list of participants (subjects) in the dataset.
    We use the openneuro library to list subjects.
    """
    logger.info(f"Fetching participant list for {dataset_id}...")
    try:
        # openneuro-py does not have a direct 'list_subjects' function in the high-level API
        # exposed as easily as the download function. We will rely on the download
        # process to discover participants or use a local directory scan if data exists.
        # However, for the purpose of this task, we assume the download will fetch
        # the dataset structure. We will return a placeholder list if we can't fetch
        # dynamically without downloading, but the main logic is in download_participant_data.
        #
        # To strictly follow "real data only", we attempt to get the structure.
        # If the dataset is not downloaded yet, we cannot list subjects without downloading.
        # We will proceed to download the whole dataset structure first, then parse it.
        return []
    except Exception as e:
        logger.warning(f"Could not fetch participant list remotely: {e}")
        return []

def check_participant_assets(participant_id: str, raw_dir: Path) -> Tuple[bool, Optional[str]]:
    """
    Verify that a participant has the required assets (NIfTI, behavioral logs).
    Returns (is_valid, reason_if_invalid).
    """
    sub_dir = raw_dir / participant_id
    if not sub_dir.exists():
        return False, "Participant directory missing"

    # Required files based on ds003694 structure
    func_dir = sub_dir / "func"
    beh_dir = sub_dir / "beh"

    # Check for NIfTI
    nii_pattern = f"{participant_id}_task-social_bold.nii.gz"
    nii_found = False
    if func_dir.exists():
        for f in func_dir.glob(nii_pattern):
            if f.is_file():
                nii_found = True
                break

    if not nii_found:
        return False, f"Missing NIfTI ({nii_pattern})"

    # Check for behavioral logs
    beh_pattern = f"{participant_id}_task-social_beh.tsv"
    beh_found = False
    if beh_dir.exists():
        for f in beh_dir.glob(beh_pattern):
            if f.is_file():
                beh_found = True
                break

    if not beh_found:
        return False, f"Missing behavioral logs ({beh_pattern})"

    return True, None

def download_participant_data(dataset_id: str, target_dir: Path) -> Set[str]:
    """
    Download the dataset using openneuro-py.
    This function handles the full download of ds003694.
    """
    logger.info(f"Starting download of {dataset_id} to {target_dir}...")

    # Ensure target directory exists
    ensure_dir(target_dir)

    try:
        # openneuro-py download function
        # dataset_id: e.g., "ds003694"
        # output_dir: Path to download to
        # update: False to skip if exists, True to re-download
        # ds_version: Optional specific version
        download.download(
            dataset=dataset_id,
            output_dir=str(target_dir),
            update=False,
            delete=False
        )
        logger.info(f"Download of {dataset_id} completed successfully.")
    except Exception as e:
        # CRITICAL SAFETY: Fail loudly. Do not catch and return empty or synthetic.
        raise DataDownloadError(f"Failed to download dataset {dataset_id}: {e}")

    return set() # Return empty set, we will scan later

def write_exclusions(exclusions: Dict[str, str], exclusions_path: Path):
    """
    Write the exclusion list to state/exclusions.yaml.
    """
    ensure_dir(exclusions_path.parent)
    data = {
        "excluded_participants": exclusions
    }
    save_yaml(data, exclusions_path)
    logger.info(f"Wrote exclusions to {exclusions_path}")

def scan_participants(raw_dir: Path) -> Dict[str, str]:
    """
    Scan the downloaded raw directory for valid participants.
    Returns a dict of {participant_id: reason} for excluded ones.
    """
    exclusions = {}
    valid_participants = []

    if not raw_dir.exists():
        raise DataDownloadError(f"Raw data directory {raw_dir} does not exist after download.")

    # Look for sub-* directories
    for item in raw_dir.iterdir():
        if item.is_dir() and item.name.startswith("sub-"):
            is_valid, reason = check_participant_assets(item.name, raw_dir)
            if is_valid:
                valid_participants.append(item.name)
            else:
                exclusions[item.name] = reason

    logger.info(f"Scanned {len(valid_participants) + len(exclusions)} participants.")
    logger.info(f"Valid: {len(valid_participants)}, Excluded: {len(exclusions)}")
    for sub, reason in exclusions.items():
        logger.warning(f"Excluding {sub}: {reason}")

    return exclusions

def main(args: Optional[argparse.Namespace] = None):
    """
    Main entry point for data download.
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Download OpenNeuro ds003694")
        parser.add_argument("--dataset", type=str, default=DATASET_ID, help="Dataset ID")
        parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory")
        parser.add_argument("--state-dir", type=str, default="state", help="State directory")
        args = parser.parse_args()

    raw_dir = Path(args.output_dir)
    state_dir = Path(args.state_dir)

    logger.info(f"Configured: dataset={args.dataset}, raw_dir={raw_dir}, state_dir={state_dir}")

    # 1. Download the dataset
    try:
        download_participant_data(args.dataset, raw_dir)
    except DataDownloadError as e:
        logger.error(str(e))
        # Fail loudly as per constraint
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

    # 2. Scan for valid participants and exclusions
    exclusions = scan_participants(raw_dir)

    # 3. Write exclusions to state/exclusions.yaml
    exclusions_path = state_dir / EXCLUSIONS_FILE
    write_exclusions(exclusions, exclusions_path)

    # 4. Write dataset manifest
    manifest_path = state_dir / "dataset_manifest.json"
    ensure_dir(manifest_path.parent)
    manifest = {
        "dataset_id": args.dataset,
        "download_path": str(raw_dir),
        "downloaded": True
    }
    # Using json for manifest as per T012 requirement
    import json
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info("Data download and validation complete.")

if __name__ == "__main__":
    main()
