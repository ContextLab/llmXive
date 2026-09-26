"""
Preprocess OpenNeuro EEG dataset ds000248 to extract alpha power features.

This script:
1. Downloads the OpenNeuro ds000248 dataset (or verifies local copy).
2. Loads EEG data, applies filtering (high-pass 1Hz, low-pass 45Hz).
3. Runs FastICA to remove artifacts.
4. Epochs data around events.
5. Computes alpha power (8-13Hz) using Welch's method.
6. Filters subjects with <80% valid epochs.
7. Outputs data/processed/eeg_features.csv with subject demographics and alpha power.

Dependencies: mne, numpy, pandas, scipy, pyyaml, openneuro-dataset (via datalad or curl)
"""

import os
import sys
import logging
import warnings
import subprocess
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import mne
from scipy import signal

# Local imports
from config import get_project_root
from config_loader import load_preprocess_config
from checksum_utils import compute_checksum, verify_checksums, update_checksum_for_file
from seed_manager import set_seed, get_random_state
from logging_config import get_preprocess_logger

# Suppress MNE warnings for cleaner logs
warnings.filterwarnings("ignore", category=RuntimeWarning, module="mne")
os.environ["OMP_NUM_THREADS"] = "1"  # Avoid threading issues in MNE

# Constants
DATASET_ID = "ds000248"
OPENNEURO_URL = f"https://openneuro.org/datasets/{DATASET_ID}/versions/3.0.0/download"
DOWNLOAD_DIR = "data/raw/openneuro_eeg"
PROCESSED_DIR = "data/processed"
CHECKSUM_FILE = "artifacts/checksums.txt"
SUBJECT_MIN_EPOCHS_RATIO = 0.80
ALPHA_BAND = (8, 13)  # Hz
FILTER_BAND = (1, 45)  # Hz (High-pass 1Hz, Low-pass 45Hz)
ICA_MAX_ITER = 200
EPOCH_TMIN = -0.2
EPOCH_TMAX = 0.8
BASELINE = (-0.2, 0)

logger = get_preprocess_logger("preprocess_eeg")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def download_openneuro_dataset() -> Path:
    """
    Download OpenNeuro dataset ds000248.
    Tries datalad first, then curl.
    Raises FileNotFoundError if download fails and no local copy exists.
    """
    project_root = get_project_root()
    download_path = project_root / DOWNLOAD_DIR
    ensure_directory(download_path)

    # Check for local copy first
    local_data_path = download_path / DATASET_ID
    if local_data_path.exists() and (local_data_path / "dataset_description.json").exists():
        logger.info(f"Local copy of {DATASET_ID} found at {local_data_path}. Verifying checksum...")
        # Verify checksum if available
        checksum_file = project_root / CHECKSUM_FILE
        if checksum_file.exists():
            if verify_checksums(str(checksum_file), str(local_data_path)):
                logger.info("Local checksum verification passed.")
                return local_data_path
            else:
                logger.warning("Local checksum verification failed. Re-downloading.")
                shutil.rmtree(local_data_path)
        else:
            logger.warning("No checksum file found. Proceeding with local copy.")
            return local_data_path

    # Try datalad
    try:
        logger.info(f"Attempting to download {DATASET_ID} using datalad...")
        subprocess.run(
            ["datalad", "get", "-d", str(download_path), str(DATASET_ID)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Datalad download successful.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning(f"Datalad failed: {e}. Trying curl...")
        # Fallback to curl
        try:
            logger.info(f"Downloading {DATASET_ID} using curl...")
            output_file = download_path / f"{DATASET_ID}.tar.gz"
            subprocess.run(
                ["curl", "-L", "-o", str(output_file), OPENNEURO_URL],
                check=True,
                capture_output=True,
                text=True
            )
            # Extract
            logger.info("Extracting downloaded archive...")
            subprocess.run(
                ["tar", "-xzf", str(output_file), "-C", str(download_path)],
                check=True,
                capture_output=True,
                text=True
            )
            # Remove archive
            output_file.unlink()
            logger.info("Extraction complete.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e2:
            logger.error(f"Failed to download dataset: {e2}")
            raise FileNotFoundError(f"Could not download OpenNeuro dataset {DATASET_ID}. "
                                    "Please download manually from {OPENNEURO_URL} and place in {download_path}.")

    # Verify download
    if not (download_path / DATASET_ID).exists():
        raise FileNotFoundError(f"Downloaded data not found at {download_path / DATASET_ID}")

    # Update checksums
    checksum_file = project_root / CHECKSUM_FILE
    update_checksum_for_file(str(checksum_file), str(download_path / DATASET_ID))

    return download_path / DATASET_ID


def load_eeg_data(dataset_path: Path) -> List[mne.io.BaseRaw]:
    """
    Load all EEG raw files from the dataset.
    Returns a list of Raw objects.
    """
    raw_files = list(dataset_path.rglob("*.fif"))
    if not raw_files:
        raise FileNotFoundError(f"No .fif files found in {dataset_path}")

    raw_objects = []
    for f in raw_files:
        try:
            raw = mne.io.read_raw_fif(f, preload=True)
            raw_objects.append(raw)
            logger.info(f"Loaded {f.name}: {raw.info['nchan']} channels, {raw.times[-1]:.2f}s duration.")
        except Exception as e:
            logger.warning(f"Failed to load {f.name}: {e}")

    return raw_objects


def preprocess_eeg(raw: mne.io.BaseRaw, config: Dict[str, Any]) -> mne.io.BaseRaw:
    """
    Apply filtering and ICA to raw EEG data.
    """
    # Set montage (if available)
    # Assuming standard 10-20 or similar for OpenNeuro ds000248
    try:
        raw.set_montage('standard_1005', match_case=False, match_alias=True)
    except Exception:
        logger.warning("Could not set montage. Proceeding without.")

    # Filter
    l_freq, h_freq = config.get('filter_bands', FILTER_BAND)
    raw.filter(l_freq, h_freq, fir_design='firwin')
    logger.info(f"Applied filter: {l_freq}-{h_freq} Hz")

    # ICA
    ica_settings = config.get('ica_settings', {})
    n_components = ica_settings.get('n_components', 0.99)
    max_iter = ica_settings.get('max_iter', ICA_MAX_ITER)

    ica = mne.preprocessing.ICA(n_components=n_components, method='fastica', max_iter=max_iter, random_state=get_random_state())
    ica.fit(raw)

    # Find and remove eye-blink components (based on EOG channel or correlation)
    # For ds000248, we assume EOG channels are present or use correlation with frontal channels
    try:
        eog_indices, eog_scores = mne.preprocessing.find_eog_components(ica, raw)
        if eog_indices:
            ica.exclude = eog_indices
            logger.info(f"Excluding {len(eog_indices)} ICA components (EOG).")
        else:
            logger.warning("No EOG components found. Skipping ICA exclusion.")
    except Exception as e:
        logger.warning(f"EOG component detection failed: {e}. Skipping ICA exclusion.")

    raw_clean = ica.apply(raw)
    return raw_clean


def epoch_and_compute_alpha(raw: mne.io.BaseRaw, config: Dict[str, Any]) -> Tuple[float, int, int]:
    """
    Epoch data and compute alpha power using Welch's method.
    Returns (mean_alpha_power, n_valid_epochs, n_total_epochs).
    """
    # Epoching
    event_id, events = mne.find_events(raw, stim_channel='STI 014')
    if not events.size:
        logger.warning("No events found in raw data. Skipping epoching.")
        return np.nan, 0, 0

    epochs = mne.Epochs(
        raw, events, event_id=event_id, tmin=EPOCH_TMIN, tmax=EPOCH_TMAX,
        baseline=BASELINE, reject=dict(eeg=150e-6), preload=True, verbose=False
    )

    n_total = len(epochs)
    if n_total == 0:
        return np.nan, 0, 0

    # Compute alpha power
    # Use Welch's method on the average of all channels
    data = epochs.get_data()  # (n_epochs, n_channels, n_times)
    sfreq = raw.info['sfreq']

    # Average across channels for each epoch
    data_avg = data.mean(axis=1)  # (n_epochs, n_times)

    # Compute power spectral density for each epoch
    psd_list = []
    for epoch_data in data_avg:
        freqs, psd = signal.welch(epoch_data, fs=sfreq, nperseg=256, scaling='density')
        # Extract alpha band power
        alpha_mask = (freqs >= ALPHA_BAND[0]) & (freqs <= ALPHA_BAND[1])
        if np.any(alpha_mask):
            alpha_power = np.mean(psd[alpha_mask])
            psd_list.append(alpha_power)
        else:
            psd_list.append(np.nan)

    psd_list = np.array(psd_list)
    valid_psd = psd_list[~np.isnan(psd_list)]

    if len(valid_psd) == 0:
        return np.nan, 0, n_total

    mean_alpha_power = np.mean(valid_psd)
    n_valid = len(valid_psd)

    return mean_alpha_power, n_valid, n_total


def extract_demographics(raw: mne.io.BaseRaw, dataset_path: Path) -> Dict[str, Any]:
    """
    Extract demographic information from the dataset.
    For ds000248, demographics are in participants.tsv.
    """
    participants_file = dataset_path / "participants.tsv"
    if not participants_file.exists():
        logger.warning("participants.tsv not found. Returning empty demographics.")
        return {}

    try:
        df = pd.read_csv(participants_file, sep='\t')
        # Find subject ID in raw filename
        subject_id = raw.filenames[0].split('/')[-1].split('_')[1]  # e.g., sub-01_ses-01...
        if subject_id in df['participant_id'].values:
            row = df[df['participant_id'] == subject_id].iloc[0]
            return {
                'age': row.get('age', np.nan),
                'sex': row.get('sex', np.nan),
                'bmi': row.get('bmi', np.nan),
                'diet': row.get('diet', np.nan)  # Optional
            }
        else:
            logger.warning(f"Subject {subject_id} not found in participants.tsv.")
            return {}
    except Exception as e:
        logger.warning(f"Failed to extract demographics: {e}")
        return {}


def main():
    """Main entry point for EEG preprocessing."""
    set_seed(42)
    logger.info("Starting EEG preprocessing for OpenNeuro ds000248.")

    project_root = get_project_root()
    ensure_directory(project_root / PROCESSED_DIR)

    # Load config
    config = load_preprocess_config()

    # Download dataset
    try:
        dataset_path = download_openneuro_dataset()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Load EEG data
    raw_objects = load_eeg_data(dataset_path)
    if not raw_objects:
        logger.error("No valid EEG files found.")
        sys.exit(1)

    # Process each subject
    results = []
    for raw in raw_objects:
        logger.info(f"Processing subject: {raw.filenames[0]}")

        # Preprocess
        raw_clean = preprocess_eeg(raw, config)

        # Epoch and compute alpha
        alpha_power, n_valid, n_total = epoch_and_compute_alpha(raw_clean, config)

        # Extract demographics
        demographics = extract_demographics(raw, dataset_path)

        # Filter subjects with <80% valid epochs
        if n_total > 0 and (n_valid / n_total) < SUBJECT_MIN_EPOCHS_RATIO:
            logger.warning(f"Subject {demographics.get('participant_id', 'unknown')} has <80% valid epochs. Excluding.")
            continue

        # Record results
        subject_id = raw.filenames[0].split('/')[-1].split('_')[1]
        results.append({
            'subject_id': subject_id,
            'alpha_power': alpha_power,
            'n_valid_epochs': n_valid,
            'n_total_epochs': n_total,
            'age': demographics.get('age', np.nan),
            'sex': demographics.get('sex', np.nan),
            'bmi': demographics.get('bmi', np.nan),
            'diet': demographics.get('diet', np.nan)
        })

    # Save results
    output_file = project_root / PROCESSED_DIR / "eeg_features.csv"
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved EEG features to {output_file}")

    # Update checksums
    checksum_file = project_root / CHECKSUM_FILE
    update_checksum_for_file(str(checksum_file), str(output_file))

    logger.info("EEG preprocessing completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()