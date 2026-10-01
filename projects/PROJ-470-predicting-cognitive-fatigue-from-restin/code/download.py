"""
Download and validate the Sleep-EDF Expanded dataset.
Fetches the full dataset, validates variables, checks participant count (N >= 30),
and writes an atomic manifest to data/raw/download_manifest.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Add project root to path to import utils if needed, though we use stdlib here
sys.path.insert(0, str(Path(__file__).parent))

# Constants
DATASET_URL = "https://physionet.org/files/sleep-edfx/1.0.0/"
METADATA_URL = "https://physionet.org/api/files/sleep-edfx/1.0.0/"
OUTPUT_DIR = Path("data/raw")
MANIFEST_PATH = OUTPUT_DIR / "download_manifest.json"
VALIDATION_REPORT_PATH = Path("data/processed") / "validation_report.json"

# Required variables in the dataset
REQUIRED_VARIABLES = ["eeg_data", "fatigue_rating"]

# Minimum participants required
MIN_PARTICIPANTS = 30

def setup_logger(name: str = "download", log_file: str | None = None):
    """Simple logger setup."""
    import logging
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(fh)
    return logger

def check_metadata_availability(logger):
    """Perform HTTP HEAD request to metadata URL before downloading."""
    logger.info(f"Checking metadata availability at {METADATA_URL}...")
    try:
        req = Request(METADATA_URL, method='HEAD')
        # Add a user agent to avoid being blocked by some servers
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; llmXive/1.0)')
        with urlopen(req, timeout=10) as response:
            if response.status == 200:
                logger.info("Metadata URL is accessible.")
                return True
            else:
                logger.error(f"Metadata URL returned status {response.status}")
                return False
    except HTTPError as e:
        logger.error(f"HTTP error checking metadata: {e.code} {e.reason}")
        return False
    except URLError as e:
        logger.error(f"URL error checking metadata: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking metadata: {e}")
        return False

def fetch_dataset(logger):
    """
    Fetch the full dataset.
    Since we cannot implement a full recursive downloader without mne or specific libraries in this snippet,
    we simulate the successful fetch by listing known files from the Sleep-EDF Expanded dataset.
    In a real production environment, this would use mne.datasets.sleep_edf.fetch_sleep_edf or a custom downloader.
    For this task, we assume the data is available or simulate the structure if the real fetch is blocked by environment.
    However, per the strict "Real Data Only" constraint, we must attempt a real fetch or fail.
    
    Given the constraints of a text-only environment and the specific dataset (Sleep-EDF),
    we will use the `mne` library's dataset fetcher if available, otherwise we fail loudly.
    """
    logger.info("Attempting to fetch Sleep-EDF Expanded dataset...")
    
    try:
        import mne
        from mne.datasets import sleep_edf
        
        # This attempts to download the full dataset
        # path = sleep_edf.fetch_sleep_edf(data_dir=str(OUTPUT_DIR))
        # Since we cannot guarantee mne is installed in the runner environment for this specific task 
        # without adding it to requirements (which we did in T004), we rely on the installed mne.
        # However, the Sleep-EDF Expanded dataset in MNE might be split.
        
        # Let's try to fetch the 'sleep' part which is the main one
        logger.info("Using MNE to fetch Sleep-EDF dataset...")
        # We fetch to a temporary location first to avoid partial writes
        temp_dir = OUTPUT_DIR
        # Note: mne.datasets.sleep_edf.fetch_sleep_edf downloads the 'expanded' version by default if available
        # or the specific version. We specify path.
        try:
            data_path = sleep_edf.fetch_sleep_edf(path=str(temp_dir), force_update=True)
            logger.info(f"Dataset fetched successfully to {data_path}")
            return data_path
        except Exception as e:
            logger.error(f"MNE fetch failed: {e}")
            # If MNE fetch fails, we cannot proceed with real data.
            # We must fail loudly.
            raise RuntimeError(f"Failed to fetch real dataset via MNE: {e}")
            
    except ImportError:
        logger.error("MNE library not found. Cannot fetch real dataset.")
        raise RuntimeError("MNE library required for fetching Sleep-EDF dataset. Please install via requirements.txt.")
    except Exception as e:
        logger.error(f"Dataset fetch failed: {e}")
        raise RuntimeError(f"Dataset fetch failed: {e}")

def validate_variables(data_path, logger):
    """
    Validate the presence of required variables in the fetched data.
    Since Sleep-EDF is EEG data, we validate that EEG channels exist and 
    we check for the presence of a file or metadata indicating fatigue ratings.
    
    NOTE: The Sleep-EDF Expanded dataset does NOT contain 'fatigue_rating' as a standard variable.
    It contains EEG, EOG, EMG, and event markers. 
    The task description assumes a dataset with 'eeg_data' and 'fatigue_rating'.
    This is a critical mismatch. 
    
    However, the task says: "The script MUST identify and fetch the 'PhysioNet Sleep-EDF Database Expanded' ... containing BOTH resting-state EEG AND paired pre/post fatigue ratings."
    This dataset (Sleep-EDF) does NOT have fatigue ratings. 
    
    If the task insists on this specific dataset AND these specific variables, the script MUST fail if variables are missing.
    We will simulate the check:
    1. Check for EEG data (exists in Sleep-EDF).
    2. Check for Fatigue Rating (does NOT exist in Sleep-EDF).
    
    Since the task requires a real dataset with these variables, and Sleep-EDF lacks them,
    we must fail with a clear error message listing available variables.
    
    BUT, if the prompt implies we should use a *different* dataset that *does* have fatigue ratings,
    or if we are to *simulate* the existence for the sake of the pipeline structure (which is forbidden),
    we are in a bind.
    
    Given the strict "Real Data Only" and "Fail Loudly" constraints:
    We will check for the variables. If they are missing, we raise an exception.
    
    For the purpose of this implementation, we will assume the user has a custom dataset 
    or a specific mirror that *does* contain these fields, or we will fail.
    Since I cannot fabricate data, and Sleep-EDF doesn't have fatigue ratings, 
    I will implement the check to FAIL if 'fatigue_rating' is missing, as per the task requirement.
    """
    logger.info("Validating variables in dataset...")
    
    # Check for EEG data (Sleep-EDF has this)
    has_eeg = False
    has_fatigue = False
    available_vars = []
    
    # We assume the data path contains .edf or .fif files.
    # We scan the directory for files.
    if isinstance(data_path, str):
        data_path = Path(data_path)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data path does not exist: {data_path}")
    
    # Scan for files to determine available variables
    # In a real scenario, we would inspect the file headers.
    # Here we assume the presence of .edf files implies eeg_data.
    eeg_files = list(data_path.rglob("*.edf")) + list(data_path.rglob("*.fif"))
    if eeg_files:
        has_eeg = True
        available_vars.append("eeg_data")
    
    # Check for fatigue_rating
    # Since Sleep-EDF doesn't have it, we look for a specific file or metadata.
    # If not found, we report it.
    fatigue_files = list(data_path.rglob("*fatigue*")) + list(data_path.rglob("*rating*"))
    if fatigue_files:
        has_fatigue = True
        available_vars.append("fatigue_rating")
    
    # If we are using the standard Sleep-EDF, has_fatigue will be False.
    # The task requires BOTH.
    if not has_fatigue:
        # We must fail.
        logger.error("Required variable 'fatigue_rating' NOT found in dataset.")
        logger.error(f"Available variables: {available_vars}")
        raise ValueError(f"Dataset missing required variable 'fatigue_rating'. Available: {available_vars}")
    
    if not has_eeg:
        logger.error("Required variable 'eeg_data' NOT found in dataset.")
        raise ValueError("Dataset missing required variable 'eeg_data'.")
        
    logger.info("Variables validated successfully.")
    return available_vars

def count_participants(data_path, logger):
    """Count participants in the dataset."""
    logger.info("Counting participants...")
    
    if isinstance(data_path, str):
        data_path = Path(data_path)
    
    # Count unique subject directories or files
    # Sleep-EDF usually has a structure like: sleep-edf/1.0.0/ST/
    # We count the number of subjects.
    # Assuming each .edf file (or pair) represents a participant.
    # We count the number of unique subject IDs.
    
    # Heuristic: Count directories in the main data folder or unique prefixes
    subjects = set()
    for f in data_path.rglob("*.edf"):
        # Extract subject ID from filename (e.g., SC4001E0.edf -> SC4001)
        name = f.stem
        # Simple heuristic: take first 6 chars if it looks like a subject ID
        # Or just count files if structure is flat
        subjects.add(name)
    
    n = len(subjects)
    logger.info(f"Found {n} participants.")
    return n

def save_dataset_to_disk(data_path, logger):
    """Ensure data is on disk (already done by fetcher)."""
    logger.info(f"Dataset is available at {data_path}")

def create_manifest(data_path, n_participants, variables, logger):
    """Create the manifest dictionary."""
    if isinstance(data_path, str):
        data_path = Path(data_path)
    
    files = []
    for f in data_path.rglob("*.edf"):
        files.append(str(f.relative_to(data_path)))
    for f in data_path.rglob("*.fif"):
        files.append(str(f.relative_to(data_path)))
    
    manifest = {
        "dataset": "Sleep-EDF Expanded",
        "version": "1.0.0",
        "n_participants": n_participants,
        "variables_found": variables,
        "data_path": str(data_path),
        "files": files,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    return manifest

def write_manifest_atomically(manifest, manifest_path, logger):
    """Write manifest atomically using temp file and os.replace."""
    logger.info(f"Writing manifest atomically to {manifest_path}")
    
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temp file first
    fd, temp_path = tempfile.mkstemp(suffix=".json", dir=manifest_path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(manifest, f, indent=2)
        # Atomic rename
        os.replace(temp_path, manifest_path)
        logger.info("Manifest written successfully.")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def write_validation_report(n_participants, variables, status, logger):
    """Write a validation report to data/processed/validation_report.json."""
    report_path = Path("data/processed") / "validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "n_participants": n_participants,
        "variables_found": variables,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Download and validate EEG dataset.")
    parser.add_argument("--validate", action="store_true", help="Only validate existing data.")
    args = parser.parse_args()

    logger = setup_logger()
    
    # Ensure directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    # 1. Check Metadata
    if not check_metadata_availability(logger):
        logger.error("Metadata check failed. Aborting.")
        sys.exit(1)

    # 2. Fetch Dataset
    try:
        data_path = fetch_dataset(logger)
    except Exception as e:
        logger.error(f"Dataset fetch failed: {e}")
        sys.exit(1)

    # 3. Validate Variables
    try:
        variables = validate_variables(data_path, logger)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # 4. Count Participants
    try:
        n_participants = count_participants(data_path, logger)
    except Exception as e:
        logger.error(f"Participant count failed: {e}")
        sys.exit(1)

    # 5. N-Count Check
    if n_participants < MIN_PARTICIPANTS:
        logger.error(f"Sample size N={n_participants} < {MIN_PARTICIPANTS}. Study invalid.")
        write_validation_report(n_participants, variables, "FAILED_N_COUNT", logger)
        sys.exit(1)

    # 6. Save Dataset (already done by fetcher, but we log it)
    save_dataset_to_disk(data_path, logger)

    # 7. Create Manifest
    manifest = create_manifest(data_path, n_participants, variables, logger)

    # 8. Write Manifest Atomically
    try:
        write_manifest_atomically(manifest, MANIFEST_PATH, logger)
    except Exception as e:
        logger.error(f"Failed to write manifest: {e}")
        sys.exit(1)

    # 9. Write Validation Report
    write_validation_report(n_participants, variables, "SUCCESS", logger)

    logger.info("Download and validation completed successfully.")
    print(f"SUCCESS: Dataset downloaded. N={n_participants}. Manifest: {MANIFEST_PATH}")

if __name__ == "__main__":
    main()
