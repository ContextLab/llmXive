"""
Data Download and Validation Module.

Handles fetching OpenNeuro datasets (Auditory and Visual) and performing
strict validation checks on sampling rates and trial counts.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import mne
import numpy as np
from huggingface_hub import snapshot_download
from tqdm import tqdm

# Project imports based on API surface
from code.config.env_config import get_env_config, ConfigError
from code.data.data_loader import (
    DataLoaderError, 
    validate_sampling_rate, 
    validate_trial_counts
)
from code.utils.logger import get_logger

# Error Codes
ERR_SAMPLING_RATE_LOW = "FR-008"
ERR_ODDBALL_TRIALS_LOW = "FR-009"
ERR_STANDARD_TRIALS_LOW = "FR-011"

logger = get_logger(__name__)

class DownloadValidationError(DataLoaderError):
    """Custom exception for validation failures during download."""
    def __init__(self, message: str, error_code: str):
        super().__init__(f"[{error_code}] {message}")
        self.error_code = error_code

def _load_raw_data_from_path(raw_path: Path, modality: str) -> mne.io.Raw:
    """
    Helper to load raw data from a directory or file.
    Handles both .fif files and directories containing raw data.
    """
    if raw_path.is_dir():
        # Try to find a .fif file or use mne.read_raw_bids if available
        # For OpenNeuro ds000246, data is typically in sub-*/eeg/*.fif
        fif_files = list(raw_path.rglob("*.fif"))
        if not fif_files:
            raise DataLoaderError(f"No .fif files found in {raw_path}")
        # Load the first found file (assuming single session per modality for this task)
        raw_path = fif_files[0]
        logger.info(f"Loading raw data from: {raw_path}")
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Data path does not exist: {raw_path}")

    # Determine extension and reader
    ext = raw_path.suffix.lower()
    if ext == '.fif':
        raw = mne.io.read_raw_fif(raw_path, preload=False)
    elif ext == '.edf':
        raw = mne.io.read_raw_edf(raw_path, preload=False)
    elif ext == '.bdf':
        raw = mne.io.read_raw_bdf(raw_path, preload=False)
    else:
        # Fallback: try generic reader or raise error
        raise DataLoaderError(f"Unsupported file format: {ext} for {raw_path}")
    
    # Set montage if available (optional but good practice)
    # For ds000246, standard 10-20 montage is often appropriate
    try:
        raw.set_montage('standard_1020', match_case=False, match_alias=True, on_missing='ignore')
    except Exception as e:
        logger.warning(f"Could not set montage: {e}")

    return raw

def _count_trials(raw: mne.io.Raw, event_id: Dict[str, int], condition: str) -> int:
    """
    Count trials for a specific condition based on event IDs.
    """
    events, _ = mne.events_from_annotations(raw)
    if events.size == 0:
        # Try to find events in raw.info if annotations are missing
        # This is a fallback for some OpenNeuro datasets
        logger.warning("No annotations found, attempting to infer events from raw info if possible.")
        return 0
    
    # Map condition name to ID
    target_id = event_id.get(condition)
    if target_id is None:
        raise ValueError(f"Condition '{condition}' not found in event_id map: {event_id}")
    
    count = np.sum(events[:, 2] == target_id)
    return int(count)

def validate_auditory_dataset(data_path: Path) -> Dict[str, Any]:
    """
    Validate the Auditory dataset (ds000246).
    
    Checks:
    1. Sampling rate >= 500 Hz (FR-008)
    2. Oddball trials >= 100 (FR-009)
    3. Standard trials >= 300 (FR-011)
    
    Args:
        data_path: Path to the downloaded dataset directory.
        
    Returns:
        Dict containing validation results and metadata.
        
    Raises:
        DownloadValidationError: If any validation check fails.
    """
    logger.info(f"Validating Auditory dataset at: {data_path}")
    
    # Load raw data
    try:
        raw = _load_raw_data_from_path(data_path, modality="auditory")
    except Exception as e:
        raise DataLoaderError(f"Failed to load auditory data: {e}")

    # Check Sampling Rate
    sfreq = raw.info['sfreq']
    logger.info(f"Auditory sampling rate: {sfreq} Hz")
    
    if not validate_sampling_rate(sfreq, threshold=500):
        raise DownloadValidationError(
            f"Auditory sampling rate ({sfreq} Hz) is below threshold (500 Hz).",
            ERR_SAMPLING_RATE_LOW
        )

    # Define Event IDs for ds000246 (Typical Oddball Paradigm)
    # Standard: 1, Oddball (Target): 2
    # Note: These IDs are typical for ds000246. If annotations differ, 
    # mne.events_from_annotations will map them.
    # We rely on the 'description' or 'trial_type' in annotations if available.
    # For this implementation, we assume standard OpenNeuro event mapping.
    # If specific IDs are not in annotations, we scan for unique codes.
    
    events, event_id_map = mne.events_from_annotations(raw)
    
    if events.size == 0:
        raise DownloadValidationError(
            "No events found in auditory dataset annotations.",
            "FR-000" # Generic no events
        )

    # Identify standard and oddball events
    # In ds000246, 'Standard' is usually code 1, 'Target' (Oddball) is code 2
    # We look for these in the event_id_map keys or values
    standard_id = None
    oddball_id = None
    
    # Heuristic: Look for 'standard' or '1' and 'target'/'oddball' or '2'
    for k, v in event_id_map.items():
        k_lower = str(k).lower()
        if 'standard' in k_lower or k_lower == '1':
            standard_id = v
        if 'target' in k_lower or 'oddball' in k_lower or k_lower == '2':
            oddball_id = v

    if standard_id is None or oddball_id is None:
        # Fallback: If we can't map by name, assume the most frequent is standard, least is oddball?
        # Or raise error. Let's raise error for strict validation.
        raise DownloadValidationError(
            f"Could not identify Standard or Oddball event IDs. Found: {event_id_map}",
            "FR-000"
        )

    # Count Trials
    n_standard = _count_trials(raw, event_id_map, standard_id)
    n_oddball = _count_trials(raw, event_id_map, oddball_id)
    
    logger.info(f"Auditory Trial Counts - Standard: {n_standard}, Oddball: {n_oddball}")

    # Validate Trial Counts
    if not validate_trial_counts(n_oddball, n_standard, min_oddball=100, min_standard=300):
        errors = []
        if n_oddball < 100:
            errors.append(f"Oddball trials ({n_oddball}) < 100 (FR-009)")
        if n_standard < 300:
            errors.append(f"Standard trials ({n_standard}) < 300 (FR-011)")
        
        raise DownloadValidationError(
            "Auditory trial count validation failed: " + "; ".join(errors),
            ERR_ODDBALL_TRIALS_LOW if n_oddball < 100 else ERR_STANDARD_TRIALS_LOW
        )

    return {
        "modality": "auditory",
        "path": str(data_path),
        "sfreq": sfreq,
        "n_standard": n_standard,
        "n_oddball": n_oddball,
        "valid": True
    }

def validate_visual_dataset(data_path: Path) -> Dict[str, Any]:
    """
    Validate the Visual dataset.
    
    Checks:
    1. Sampling rate >= 500 Hz (FR-008)
    2. Oddball trials >= 100 (FR-009)
    3. Standard trials >= 300 (FR-011)
    
    Args:
        data_path: Path to the downloaded dataset directory.
        
    Returns:
        Dict containing validation results and metadata.
        
    Raises:
        DownloadValidationError: If any validation check fails.
    """
    logger.info(f"Validating Visual dataset at: {data_path}")
    
    # Load raw data
    try:
        raw = _load_raw_data_from_path(data_path, modality="visual")
    except Exception as e:
        raise DataLoaderError(f"Failed to load visual data: {e}")

    # Check Sampling Rate
    sfreq = raw.info['sfreq']
    logger.info(f"Visual sampling rate: {sfreq} Hz")
    
    if not validate_sampling_rate(sfreq, threshold=500):
        raise DownloadValidationError(
            f"Visual sampling rate ({sfreq} Hz) is below threshold (500 Hz).",
            ERR_SAMPLING_RATE_LOW
        )

    # Event mapping for Visual (Similar logic, IDs might differ)
    events, event_id_map = mne.events_from_annotations(raw)
    
    if events.size == 0:
        raise DownloadValidationError(
            "No events found in visual dataset annotations.",
            "FR-000"
        )

    standard_id = None
    oddball_id = None
    
    for k, v in event_id_map.items():
        k_lower = str(k).lower()
        if 'standard' in k_lower or k_lower == '1':
            standard_id = v
        if 'target' in k_lower or 'oddball' in k_lower or k_lower == '2':
            oddball_id = v

    if standard_id is None or oddball_id is None:
        raise DownloadValidationError(
            f"Could not identify Standard or Oddball event IDs in visual data. Found: {event_id_map}",
            "FR-000"
        )

    n_standard = _count_trials(raw, event_id_map, standard_id)
    n_oddball = _count_trials(raw, event_id_map, oddball_id)
    
    logger.info(f"Visual Trial Counts - Standard: {n_standard}, Oddball: {n_oddball}")

    if not validate_trial_counts(n_oddball, n_standard, min_oddball=100, min_standard=300):
        errors = []
        if n_oddball < 100:
            errors.append(f"Oddball trials ({n_oddball}) < 100 (FR-009)")
        if n_standard < 300:
            errors.append(f"Standard trials ({n_standard}) < 300 (FR-011)")
        
        raise DownloadValidationError(
            "Visual trial count validation failed: " + "; ".join(errors),
            ERR_ODDBALL_TRIALS_LOW if n_oddball < 100 else ERR_STANDARD_TRIALS_LOW
        )

    return {
        "modality": "visual",
        "path": str(data_path),
        "sfreq": sfreq,
        "n_standard": n_standard,
        "n_oddball": n_oddball,
        "valid": True
    }

def run_auditory_validation() -> None:
    """
    Entry point for T017: Run validation on the Auditory dataset.
    This function assumes T015 has already downloaded the data to the configured path.
    """
    config = get_env_config()
    auditory_path = config.auditory_data_path
    
    if not auditory_path.exists():
        raise FileNotFoundError(f"Auditory data path not found: {auditory_path}. Did T015 run?")
    
    try:
        result = validate_auditory_dataset(auditory_path)
        logger.info("Auditory validation PASSED.")
        logger.info(f"Results: {result}")
        # Optionally save result to a log file
        with open(config.logs_path / "auditory_validation.json", "w") as f:
            import json
            json.dump(result, f, indent=2)
    except DownloadValidationError as e:
        logger.error(f"Auditory validation FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during auditory validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_auditory_validation()
