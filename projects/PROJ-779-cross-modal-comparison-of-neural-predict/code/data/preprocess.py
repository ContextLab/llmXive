import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import mne

from code.config import get_config, ensure_directories
from code.utils.logger import get_logger
from code.data.data_loader import BaseDataLoader, validate_sampling_rate, validate_trial_counts

# Ensure the logger is configured before use
logger = get_logger(__name__)

def apply_bandpass_filter(raw_data: mne.io.Raw, config: Dict[str, Any]) -> mne.io.Raw:
    """
    Apply bandpass filter to the raw data.
    
    Args:
        raw_data: MNE Raw object
        config: Configuration dictionary containing filter parameters
    
    Returns:
        Filtered MNE Raw object
    """
    if raw_data is None:
        raise ValueError("Raw data cannot be None")
    
    logger.info(f"Applying bandpass filter: {config['filter_low_freq']} Hz to {config['filter_high_freq']} Hz")
    
    raw_filtered = raw_data.copy().filter(
        l_freq=config['filter_low_freq'],
        h_freq=config['filter_high_freq'],
        method='fir',
        fir_window='hamming',
        fir_design='firwin',
        skip_by_annotation='bad',
        n_jobs=1
    )
    
    return raw_filtered

def run_ica_artifact_removal(raw_data: mne.io.Raw, config: Dict[str, Any]) -> mne.io.Raw:
    """
    Apply ICA for artifact removal.
    
    Args:
        raw_data: MNE Raw object
        config: Configuration dictionary containing ICA parameters
    
    Returns:
        Cleaned MNE Raw object with artifacts removed
    """
    if raw_data is None:
        raise ValueError("Raw data cannot be None")
    
    logger.info("Running ICA artifact removal")
    
    # Set up ICA
    ica = mne.preprocessing.ICA(
        n_components=config.get('ica_n_components', 0.95),
        method='fastica',
        random_state=config.get('random_seed', 42),
        max_iter=config.get('ica_max_iter', 500),
        n_jobs=1
    )
    
    # Fit ICA
    logger.info("Fitting ICA components...")
    ica.fit(raw_data)
    
    # Identify and exclude EOG/ECG artifacts
    # For this implementation, we use automatic detection based on correlation
    eog_indices, eog_scores = ica.find_bads_eog(raw_data, ch_name=config.get('eog_ch_name', 'EOG'))
    ecg_indices, ecg_scores = ica.find_bads_ecg(raw_data, ch_name=config.get('ecg_ch_name', 'ECG'))
    
    exclude_indices = list(set(eog_indices + ecg_indices))
    
    if exclude_indices:
        logger.info(f"Excluding {len(exclude_indices)} ICA components (EOG: {len(eog_indices)}, ECG: {len(ecg_indices)})")
        ica.exclude = exclude_indices
    else:
        logger.info("No significant EOG/ECG artifacts detected for exclusion")
    
    # Apply ICA
    logger.info("Applying ICA reconstruction...")
    raw_cleaned = ica.apply(raw_data)
    
    return raw_cleaned

def apply_re_reference(raw_data: mne.io.Raw, config: Dict[str, Any]) -> mne.io.Raw:
    """
    Apply common average re-referencing.
    
    Args:
        raw_data: MNE Raw object
        config: Configuration dictionary
    
    Returns:
        Re-referenced MNE Raw object
    """
    if raw_data is None:
        raise ValueError("Raw data cannot be None")
    
    logger.info("Applying common average re-referencing")
    
    # Get all EEG channels
    eeg_channels = [ch for ch in raw_data.ch_names if raw_data.get_channel_types([ch])[0] == 'eeg']
    
    if not eeg_channels:
        logger.warning("No EEG channels found for re-referencing")
        return raw_data
    
    # Apply common average reference
    raw_referred = raw_data.copy()
    raw_referred.set_eeg_reference(ref_channels=eeg_channels, projection=False)
    
    return raw_referred

def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for integrity verification."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def preprocess_dataset(
    input_path: Path,
    output_path: Path,
    config: Dict[str, Any],
    dataset_id: str
) -> Tuple[Path, Dict[str, Any]]:
    """
    Full preprocessing pipeline: filter -> ICA -> re-reference -> save.
    
    Args:
        input_path: Path to input raw data file
        output_path: Path to save cleaned data
        config: Configuration dictionary
        dataset_id: Identifier for the dataset (auditory/visual)
    
    Returns:
        Tuple of (output_path, metadata_dict)
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    ensure_directories([output_path.parent])
    
    logger.info(f"Starting preprocessing for {dataset_id}")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Load raw data
    logger.info("Loading raw data...")
    raw = mne.io.read_raw_fif(input_path, preload=True)
    
    # Validate sampling rate
    validate_sampling_rate(raw, config)
    
    # Step 1: Bandpass Filter
    logger.info("Step 1: Applying bandpass filter")
    raw = apply_bandpass_filter(raw, config)
    
    # Step 2: ICA Artifact Removal
    logger.info("Step 2: Running ICA artifact removal")
    raw = run_ica_artifact_removal(raw, config)
    
    # Step 3: Re-referencing
    logger.info("Step 3: Applying common average re-referencing")
    raw = apply_re_reference(raw, config)
    
    # Step 4: Save Cleaned Data
    logger.info(f"Step 4: Saving cleaned data to {output_path}")
    raw.save(output_path, overwrite=True)
    
    # Generate metadata and rejection log
    metadata = {
        "dataset_id": dataset_id,
        "input_file": str(input_path),
        "output_file": str(output_path),
        "input_checksum": _compute_file_hash(input_path),
        "output_checksum": _compute_file_hash(output_path),
        "sampling_rate": raw.info['sfreq'],
        "n_channels": len(raw.ch_names),
        "n_times": raw.n_times,
        "duration_seconds": raw.times[-1],
        "processing_steps": [
            "bandpass_filter",
            "ica_artifact_removal",
            "common_average_re_reference"
        ],
        "ica_components_total": raw.info['proc_history'][0]['ica']['n_components'] if raw.info.get('proc_history') else None,
        "ica_components_excluded": raw.info['proc_history'][0]['ica']['exclude'] if raw.info.get('proc_history') else [],
        "timestamp": str(mne.utils._get_time()),
        "config_snapshot": {
            "filter_low_freq": config['filter_low_freq'],
            "filter_high_freq": config['filter_high_freq'],
            "ica_n_components": config.get('ica_n_components', 0.95),
            "random_seed": config.get('random_seed', 42)
        }
    }
    
    # Trial rejection logging (if available in raw annotation)
    rejection_log = {
        "total_epochs": 0,
        "rejected_epochs": 0,
        "rejection_reasons": {}
    }
    
    if raw.annotations:
        bad_annotations = [ann for ann in raw.annotations if 'bad' in ann['description'].lower()]
        rejection_log['rejected_epochs'] = len(bad_annotations)
        rejection_log['rejection_reasons'] = {
            "bad_annotations": len(bad_annotations),
            "descriptions": list(set([ann['description'] for ann in bad_annotations]))
        }
    
    # Save rejection log
    rejection_log_path = output_path.parent / f"{output_path.stem}_rejection_log.json"
    with open(rejection_log_path, 'w') as f:
        json.dump(rejection_log, f, indent=2)
    
    # Save metadata
    metadata_path = output_path.parent / f"{output_path.stem}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Preprocessing complete. Output saved to {output_path}")
    logger.info(f"Rejection log saved to {rejection_log_path}")
    logger.info(f"Metadata saved to {metadata_path}")
    
    return output_path, metadata

def main():
    """Main entry point for preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    
    config = get_config()
    
    # Define paths
    data_dir = Path(config['data_dir'])
    processed_dir = data_dir / 'processed'
    
    # Process Auditory Dataset (ds000246)
    auditory_input = data_dir / 'raw' / 'ds000246' / 'sub-01' / 'eeg' / 'sub-01_task-auditory_eeg.fif'
    auditory_output = processed_dir / 'cleaned_data_auditory.fif'
    
    if auditory_input.exists():
        logger.info("Processing Auditory dataset...")
        try:
            preprocess_dataset(
                input_path=auditory_input,
                output_path=auditory_output,
                config=config,
                dataset_id='auditory'
            )
        except Exception as e:
            logger.error(f"Failed to process auditory dataset: {e}")
            raise
    else:
        logger.warning(f"Auditory input file not found: {auditory_input}. Skipping.")
    
    # Process Visual Dataset (ds000117)
    visual_input = data_dir / 'raw' / 'ds000117' / 'sub-01' / 'eeg' / 'sub-01_task-visual_eeg.fif'
    visual_output = processed_dir / 'cleaned_data_visual.fif'
    
    if visual_input.exists():
        logger.info("Processing Visual dataset...")
        try:
            preprocess_dataset(
                input_path=visual_input,
                output_path=visual_output,
                config=config,
                dataset_id='visual'
            )
        except Exception as e:
            logger.error(f"Failed to process visual dataset: {e}")
            raise
    else:
        logger.warning(f"Visual input file not found: {visual_input}. Skipping.")
    
    logger.info("Preprocessing pipeline finished")

if __name__ == '__main__':
    main()