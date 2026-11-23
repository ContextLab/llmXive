"""
Download and validation module for OpenNeuro datasets.
Handles fetching and validating both Auditory (ds000246) and Visual (ds000117) datasets.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import mne
from code.config import get_config
from code.utils.logger import get_logger

# Error codes as per specification
ERR_SAMPLING_RATE_LOW = "FR-008"
ERR_ODDBALL_TRIALS_LOW = "FR-009"
ERR_STANDARD_TRIALS_LOW = "FR-011"
ERR_DOWNLOAD_FAILED = "FR-007"

class DownloadValidationError(Exception):
    """Custom exception for dataset validation failures."""
    def __init__(self, message: str, error_code: str):
        super().__init__(f"[{error_code}] {message}")
        self.error_code = error_code

def fetch_visual_dataset() -> str:
    """
    Fetch the Visual dataset (ds000117) from OpenNeuro.
    
    Returns:
        str: Path to the downloaded dataset directory.
        
    Raises:
        DownloadValidationError: If download fails or dataset is not found.
    """
    logger = get_logger(__name__)
    config = get_config()
    dataset_id = "ds000117"
    data_dir = Path(config.data_raw_dir)
    
    logger.info(f"Fetching Visual dataset: {dataset_id}")
    
    try:
        # Use mne to fetch the dataset
        # mne.datasets.openneuro_dataset returns the path to the dataset
        dataset_path = mne.datasets.openneuro_dataset(
            dataset_id=dataset_id,
            data_path=data_dir,
            update_path=False
        )
        
        if not dataset_path or not os.path.exists(dataset_path):
            raise DownloadValidationError(
                f"Dataset {dataset_id} was not found after fetch attempt.",
                ERR_DOWNLOAD_FAILED
            )
        
        logger.info(f"Visual dataset fetched successfully to: {dataset_path}")
        return dataset_path
        
    except Exception as e:
        logger.error(f"Failed to fetch Visual dataset {dataset_id}: {str(e)}")
        raise DownloadValidationError(
            f"Failed to fetch Visual dataset {dataset_id}: {str(e)}",
            ERR_DOWNLOAD_FAILED
        ) from e

def validate_visual_dataset(dataset_path: str) -> Dict[str, Any]:
    """
    Validate the Visual dataset (ds000117) for sampling rate and trial counts.
    
    Checks:
        - Sampling rate >= 500 Hz (FR-008)
        - Oddball trials >= 100 (FR-009)
        - Standard trials >= 300 (FR-011)
        
    Args:
        dataset_path (str): Path to the downloaded dataset.
        
    Returns:
        Dict[str, Any]: Dictionary containing validation results and metadata.
        
    Raises:
        DownloadValidationError: If any validation check fails.
    """
    logger = get_logger(__name__)
    config = get_config()
    
    logger.info(f"Validating Visual dataset at: {dataset_path}")
    
    # Look for raw EEG data files in the dataset
    # OpenNeuro ds000117 structure typically has BIDS format
    raw_file_path = None
    for root, dirs, files in os.walk(dataset_path):
        for file in files:
            if file.endswith(('.fif', '.edf', '.vhdr', '.set')):
                # Look for task-stimulus files (visual oddball)
                if 'stimulus' in file.lower() or 'visual' in file.lower() or 'task' in file.lower():
                    raw_file_path = os.path.join(root, file)
                    break
        if raw_file_path:
            break
    
    if not raw_file_path:
        # Fallback: look for any raw file if specific naming not found
        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                if file.endswith(('.fif', '.edf', '.vhdr', '.set')):
                    raw_file_path = os.path.join(root, file)
                    break
            if raw_file_path:
                break
    
    if not raw_file_path:
        raise DownloadValidationError(
            "No raw EEG data files found in the Visual dataset.",
            ERR_DOWNLOAD_FAILED
        )
    
    logger.info(f"Found raw data file: {raw_file_path}")
    
    # Load the raw data
    try:
        # Determine file type and load accordingly
        if raw_file_path.endswith('.fif'):
            raw = mne.io.read_raw_fif(raw_file_path, preload=False)
        elif raw_file_path.endswith('.edf'):
            raw = mne.io.read_raw_edf(raw_file_path, preload=False)
        elif raw_file_path.endswith('.vhdr'):
            raw = mne.io.read_raw_brainvision(raw_file_path, preload=False)
        elif raw_file_path.endswith('.set'):
            # EEGLAB format requires loading the whole file usually
            raw = mne.io.read_raw_eeglab(raw_file_path, preload=False)
        else:
            raise DownloadValidationError(
                f"Unsupported file format: {raw_file_path}",
                ERR_DOWNLOAD_FAILED
            )
        
        # Preload for analysis if necessary, but be careful with memory
        # For validation, we might not need full preload if we can get metadata
        raw.load_data()
        
    except Exception as e:
        logger.error(f"Failed to load raw data from {raw_file_path}: {str(e)}")
        raise DownloadValidationError(
            f"Failed to load raw data: {str(e)}",
            ERR_DOWNLOAD_FAILED
        ) from e
    
    # Validation 1: Sampling Rate
    sfreq = raw.info['sfreq']
    logger.info(f"Dataset sampling rate: {sfreq} Hz")
    
    if sfreq < config.min_sampling_rate:
        error_msg = (
            f"Sampling rate {sfreq} Hz is below minimum threshold "
            f"{config.min_sampling_rate} Hz. "
            f"Required: >= {config.min_sampling_rate} Hz."
        )
        logger.error(error_msg)
        raise DownloadValidationError(error_msg, ERR_SAMPLING_RATE_LOW)
    
    # Validation 2 & 3: Trial Counts
    # We need to identify oddball and standard conditions from events
    events = mne.find_events(raw, stim_channel='STI 014')  # Default stim channel
    
    if len(events) == 0:
        # Try alternative stim channel names
        for stim_ch in raw.ch_names:
            if 'stim' in stim_ch.lower() or 'trigger' in stim_ch.lower():
                events = mne.find_events(raw, stim_channel=stim_ch)
                if len(events) > 0:
                    break
    
    if len(events) == 0:
        raise DownloadValidationError(
            "No events found in the dataset. Cannot validate trial counts.",
            ERR_DOWNLOAD_FAILED
        )
    
    # Count trials by event type
    # In ds000117, we expect specific event codes for oddball and standard
    # We'll count unique event types and try to infer which are oddball/standard
    event_ids = {}
    for event in events:
        event_type = event[2]
        if event_type not in event_ids:
            event_ids[event_type] = 0
        event_ids[event_type] += 1
    
    logger.info(f"Event counts: {event_ids}")
    
    # For ds000117 (Visual Oddball), we need to identify the specific conditions
    # Typically, there are target (oddball) and non-target (standard) stimuli
    # We'll assume the most frequent event is standard and the less frequent is oddball
    # This is a heuristic; in practice, we'd use the dataset documentation
    
    sorted_events = sorted(event_ids.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_events) < 2:
        logger.warning("Dataset has fewer than 2 event types. Using all events as standard.")
        # If only one type, we assume it's the standard condition
        # and we don't have an oddball condition
        standard_count = sorted_events[0][1] if sorted_events else 0
        oddball_count = 0
    else:
        # Assume the most frequent is standard, second most is oddball
        # This is a reasonable heuristic for oddball paradigms
        standard_count = sorted_events[0][1]
        oddball_count = sorted_events[1][1]
    
    logger.info(f"Estimated trial counts - Oddball: {oddball_count}, Standard: {standard_count}")
    
    # Check Oddball trials
    if oddball_count < config.min_oddball_trials:
        error_msg = (
            f"Oddball trial count {oddball_count} is below minimum threshold "
            f"{config.min_oddball_trials}. "
            f"Required: >= {config.min_oddball_trials}."
        )
        logger.error(error_msg)
        raise DownloadValidationError(error_msg, ERR_ODDBALL_TRIALS_LOW)
    
    # Check Standard trials
    if standard_count < config.min_standard_trials:
        error_msg = (
            f"Standard trial count {standard_count} is below minimum threshold "
            f"{config.min_standard_trials}. "
            f"Required: >= {config.min_standard_trials}."
        )
        logger.error(error_msg)
        raise DownloadValidationError(error_msg, ERR_STANDARD_TRIALS_LOW)
    
    validation_result = {
        'dataset_id': 'ds000117',
        'dataset_path': dataset_path,
        'raw_file': raw_file_path,
        'sampling_rate': sfreq,
        'min_sampling_rate': config.min_sampling_rate,
        'oddball_trials': oddball_count,
        'min_oddball_trials': config.min_oddball_trials,
        'standard_trials': standard_count,
        'min_standard_trials': config.min_standard_trials,
        'validation_status': 'PASSED'
    }
    
    logger.info("Visual dataset validation PASSED.")
    return validation_result

def run_visual_validation() -> Dict[str, Any]:
    """
    Run the complete pipeline for Visual dataset: fetch and validate.
    
    Returns:
        Dict[str, Any]: Validation results dictionary.
        
    Raises:
        DownloadValidationError: If fetch or validation fails.
    """
    logger = get_logger(__name__)
    
    try:
        # Fetch the dataset
        dataset_path = fetch_visual_dataset()
        
        # Validate the dataset
        validation_result = validate_visual_dataset(dataset_path)
        
        return validation_result
        
    except DownloadValidationError as e:
        logger.error(f"Visual dataset validation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Visual dataset validation: {str(e)}")
        raise DownloadValidationError(
            f"Unexpected error: {str(e)}",
            ERR_DOWNLOAD_FAILED
        ) from e

def main():
    """
    Main entry point for Visual dataset download and validation.
    """
    logger = get_logger(__name__)
    logger.info("Starting Visual dataset download and validation (T018)...")
    
    try:
        result = run_visual_validation()
        logger.info(f"Validation result: {result}")
        
        # Save validation result to a JSON file for downstream tasks
        output_path = Path(get_config().data_processed_dir) / "visual_validation.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Validation result saved to: {output_path}")
        return 0
        
    except DownloadValidationError as e:
        logger.error(f"Validation failed with error: {e}")
        # Exit with specific error code based on the error
        if e.error_code == ERR_SAMPLING_RATE_LOW:
            return 101
        elif e.error_code == ERR_ODDBALL_TRIALS_LOW:
            return 102
        elif e.error_code == ERR_STANDARD_TRIALS_LOW:
            return 103
        else:
            return 100
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 100

if __name__ == "__main__":
    sys.exit(main())