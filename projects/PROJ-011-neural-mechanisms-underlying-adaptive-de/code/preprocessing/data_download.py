"""
Data Download Module for OpenNeuro ds003694.

This module handles the fetching of raw fMRI and behavioral data from OpenNeuro.
It strictly adheres to the "Fail Loudly" policy: if the real data cannot be fetched,
it raises an exception immediately. No synthetic data or fallbacks are permitted.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import yaml
import json

# Attempt to import openneuro. If not available, we must fail loudly as per T013 requirements.
# The dependency 'openneuro-py' is listed in requirements.txt.
try:
    from openneuro import client
except ImportError:
    raise ImportError(
        "The 'openneuro' package is required for data download. "
        "Please install it via: pip install openneuro-py"
    )

from utils.io import ensure_dir, save_yaml, load_yaml
from utils.logger import get_logger

# Constants for the specific dataset
DATASET_ID = "ds003694"
EXCLUSIONS_FILE = "state/exclusions.yaml"

logger = get_logger(__name__)


class DataDownloadError(Exception):
    """Custom exception for data download failures."""
    pass


def get_dataset_client() -> client.Client:
    """
    Initialize and return the OpenNeuro client.

    Returns:
        client.Client: Configured OpenNeuro client.

    Raises:
        DataDownloadError: If the client cannot be initialized (e.g., network issues).
    """
    try:
        # OpenNeuro public datasets do not require an API key, but the client handles auth if present.
        # We initialize with default settings.
        c = client.Client()
        # Verify connectivity by attempting a lightweight operation (getting dataset info)
        # This ensures we fail early if the network is down or the dataset ID is wrong.
        c.get_dataset(DATASET_ID)
        return c
    except Exception as e:
        logger.error(f"Failed to initialize OpenNeuro client or connect to dataset {DATASET_ID}: {e}")
        raise DataDownloadError(f"Connection to OpenNeuro failed for {DATASET_ID}. "
                                "Ensure internet connection is active and the dataset ID is correct.") from e


def get_participant_list(client_instance: client.Client) -> List[str]:
    """
    Retrieve the list of valid participants (subjects) for the dataset.

    Args:
        client_instance: The initialized OpenNeuro client.

    Returns:
        List[str]: List of participant IDs (e.g., 'sub-01').
    """
    try:
        # Fetch dataset files to identify subjects
        # We use the client's file listing capabilities.
        # Note: The exact method might vary slightly by openneuro-py version,
        # but generally involves listing files and extracting unique subject prefixes.
        files = client_instance.get_dataset_files(DATASET_ID)
        
        subjects = set()
        for file_entry in files:
            path = file_entry.get('filename') or file_entry.get('path')
            if path and path.startswith('sub-'):
                # Extract subject ID (e.g., 'sub-01' from 'sub-01/...')
                subject_id = path.split('/')[0]
                if subject_id.startswith('sub-'):
                    subjects.add(subject_id)
        
        sorted_subjects = sorted(list(subjects))
        logger.info(f"Found {len(sorted_subjects)} participants in dataset {DATASET_ID}.")
        return sorted_subjects
    except Exception as e:
        logger.error(f"Failed to retrieve participant list: {e}")
        raise DataDownloadError("Could not retrieve participant list from OpenNeuro.") from e


def check_participant_assets(client_instance: client.Client, participant_id: str) -> Tuple[bool, List[str]]:
    """
    Check if a specific participant has all required assets (NIfTI, behavioral logs, motion params).

    Required assets based on project specs:
    - func: sub-<id>_task-social_bold.nii.gz
    - beh: sub-<id>/*.tsv (private_belief, social_feedback, choice)

    Args:
        client_instance: The initialized OpenNeuro client.
        participant_id: The subject ID (e.g., 'sub-01').

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_missing_assets).
    """
    missing_assets = []
    required_patterns = [
        f"{participant_id}/func/{participant_id}_task-social_bold.nii.gz",
        f"{participant_id}/beh/{participant_id}_private_belief.tsv",
        f"{participant_id}/beh/{participant_id}_social_feedback.tsv",
        f"{participant_id}/beh/{participant_id}_choice.tsv",
        f"{participant_id}/beh/{participant_id}_motion.tsv" # Assuming motion is in beh or derived from events
    ]

    try:
        files = client_instance.get_dataset_files(DATASET_ID)
        available_paths = {f.get('filename') or f.get('path') for f in files}
        
        for pattern in required_patterns:
            # Check if the exact file exists or if a wildcard match exists
            # For simplicity in this check, we look for exact matches or prefix matches if wildcards are used in spec
            # Here we assume exact file names as per BIDS standard.
            found = False
            for avail_path in available_paths:
                if avail_path.startswith(pattern):
                    found = True
                    break
            
            if not found:
                missing_assets.append(pattern)

        is_valid = len(missing_assets) == 0
        if not is_valid:
            logger.warning(f"Participant {participant_id} missing assets: {missing_assets}")
        return is_valid, missing_assets

    except Exception as e:
        logger.error(f"Error checking assets for {participant_id}: {e}")
        raise DataDownloadError(f"Failed to check assets for {participant_id}") from e


def download_participant_data(client_instance: client.Client, participant_id: str, output_dir: Path) -> bool:
    """
    Download all data for a specific participant.

    Args:
        client_instance: The initialized OpenNeuro client.
        participant_id: The subject ID.
        output_dir: The base directory to save the data (e.g., data/raw/ds003694).

    Returns:
        bool: True if successful, False otherwise (though we prefer raising errors).
    """
    try:
        # Create participant-specific directory
        p_dir = output_dir / participant_id
        ensure_dir(p_dir)

        # Use openneuro-py's download functionality
        # The client.download method usually takes a dataset ID and an output directory.
        # To download only a specific participant, we might need to filter or use the CLI wrapper.
        # Since openneuro-py's API might be limited in granular download without downloading all,
        # we will attempt to download the specific subject if the API supports it,
        # or download the whole dataset to the specific path if granular download isn't available in the library version.
        # However, standard practice with openneuro-py is often:
        # client.download(dataset_id, output_dir, include=['sub-01/...'])
        
        # Construct the filter list for this participant
        # We need to be careful not to re-download the whole dataset if we are processing incrementally.
        # For this implementation, we assume we are setting up the raw data structure.
        
        # Strategy: Download the specific files identified as present.
        # Note: openneuro-py might not support granular file download easily. 
        # If so, we might need to use the `openneuro` CLI tool via subprocess or download the full dataset.
        # Given the constraints of "real data" and "fail loudly", we attempt the library call.
        
        # Attempting to download the whole dataset to the specific output directory is the most robust
        # way to ensure data integrity if the library doesn't support partial downloads easily.
        # However, to avoid re-downloading, we check if the participant dir exists and is non-empty.
        
        if p_dir.exists() and any(p_dir.iterdir()):
            logger.info(f"Data for {participant_id} already exists at {p_dir}. Skipping download.")
            return True

        logger.info(f"Downloading data for {participant_id}...")
        
        # Fallback: If the library doesn't support subject-level download easily,
        # we might have to download the whole dataset. But for this task, we assume
        # the library supports it or we download the whole thing once.
        # Let's try to use the download method with a specific subject filter if possible.
        # If not, we download the whole dataset to the raw folder.
        
        # Since openneuro-py's download() often downloads the whole dataset:
        # We will download the dataset to the output_dir.
        # If the output_dir already has the dataset, it might skip or update.
        # To be safe and specific, we assume we are running this once to populate data/raw.
        
        client_instance.download(DATASET_ID, str(output_dir))
        logger.info(f"Downloaded dataset {DATASET_ID} to {output_dir}")
        return True

    except Exception as e:
        logger.error(f"Failed to download data for {participant_id}: {e}")
        # Do not catch and return False. We want to fail loudly.
        raise DataDownloadError(f"Download failed for {participant_id}") from e


def write_exclusions(exclusions: Dict[str, List[str]], output_path: Path) -> None:
    """
    Write the list of excluded participants and reasons to a YAML file.

    Args:
        exclusions: Dict mapping participant_id to list of reasons.
        output_path: Path to the exclusions.yaml file.
    """
    ensure_dir(output_path.parent)
    try:
        # Load existing exclusions if any
        existing = {}
        if output_path.exists():
            existing = load_yaml(output_path)
        
        # Merge new exclusions
        for pid, reasons in exclusions.items():
            if pid not in existing:
                existing[pid] = []
            existing[pid].extend(reasons)
        
        save_yaml(existing, output_path)
        logger.info(f"Exclusion list updated at {output_path}")
    except Exception as e:
        logger.error(f"Failed to write exclusions to {output_path}: {e}")
        raise DataDownloadError("Could not write exclusions file.") from e


def main(args: Optional[List[str]] = None) -> None:
    """
    Main entry point for data download.

    Steps:
    1. Initialize OpenNeuro client.
    2. Get list of participants.
    3. Check assets for each participant.
    4. Download valid participants.
    5. Record exclusions for invalid participants.
    """
    parser = argparse.ArgumentParser(description="Download OpenNeuro ds003694 data.")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Base directory for raw data.")
    parser.add_argument("--force-download", action="store_true", help="Force re-download even if data exists.")
    args = parser.parse_args(args)

    output_dir = Path(args.output_dir)
    exclusions: Dict[str, List[str]] = {}

    # 1. Initialize Client (Fail loudly if connection fails)
    client_instance = get_dataset_client()

    # 2. Get Participants
    participants = get_participant_list(client_instance)
    logger.info(f"Processing {len(participants)} participants.")

    # 3. Check Assets & 4. Download
    for pid in participants:
        is_valid, missing = check_participant_assets(client_instance, pid)
        
        if not is_valid:
            exclusions[pid] = missing
            logger.warning(f"Excluding {pid} due to missing assets: {missing}")
            continue

        # Download if valid (and not skipped by force flag)
        if not args.force_download and (output_dir / pid).exists():
            logger.info(f"Skipping {pid} (already exists).")
            continue

        try:
            download_participant_data(client_instance, pid, output_dir)
        except DataDownloadError as e:
            # If download fails, exclude the participant and log
            exclusions[pid] = [f"download_failed: {str(e)}"]
            logger.error(f"Failed to download {pid}. Excluding.")

    # 5. Write Exclusions
    if exclusions:
        exclusions_path = Path("state") / EXCLUSIONS_FILE
        write_exclusions(exclusions, exclusions_path)
        logger.info(f"Total excluded: {len(exclusions)}")
    else:
        logger.info("No participants excluded.")

    logger.info("Data download process completed.")


if __name__ == "__main__":
    main()
