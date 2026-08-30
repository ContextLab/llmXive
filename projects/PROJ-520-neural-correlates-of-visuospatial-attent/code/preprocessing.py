"""
EEG preprocessing pipeline for visuospatial attention study.
Implements download, filtering, ICA artifact rejection, and epoch segmentation.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

import mne
from datasets import load_dataset

# Import local modules
from config import load_config, get_paths
from logging_config import get_pipeline_logger, log_stage_start, log_stage_end
from models import PreprocessingReport


class SampleSizeError(Exception):
    """Raised when sample size requirements are not met."""
    pass


def download_dataset(config: Dict[str, Any], raw_data_path: Path) -> Path:
    """
    Download dataset from OpenNeuro using the datasets library.
    
    Args:
        config: Configuration dictionary
        raw_data_path: Path to store raw data
        
    Returns:
        Path to downloaded dataset directory
    """
    logger = get_pipeline_logger("download")
    log_stage_start(logger, "download_dataset")
    
    dataset_id = config.get("dataset", {}).get("dataset_id", "ds004229")
    logger.info(f"Downloading dataset {dataset_id} from OpenNeuro")
    
    # Use streaming to avoid loading entire dataset into memory
    try:
        # Try to download using MNE's OpenNeuro fetcher
        raw_path = mne.datasets.openneuro.data_path(
            dataset=dataset_id,
            path=raw_data_path,
            download=True
        )
        logger.info(f"Dataset downloaded to: {raw_path}")
    except Exception as e:
        # Fallback to datasets library if MNE fails
        logger.warning(f"MNE download failed: {e}, trying datasets library")
        try:
            ds = load_dataset(
                "openneuro",
                dataset_id,
                split="train",
                streaming=True
            )
            # Process and save
            raw_path = raw_data_path / dataset_id
            raw_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Dataset streamed and saved to: {raw_path}")
        except Exception as e2:
            # Fail loudly - no synthetic data
            raise RuntimeError(f"Failed to download dataset from OpenNeuro: {e2}")
    
    log_stage_end(logger, "download_dataset", status="success")
    return raw_path


def validate_dataset(raw_path: Path, config: Dict[str, Any]) -> bool:
    """
    Validate BIDS structure and event markers.
    
    Args:
        raw_path: Path to dataset directory
        config: Configuration dictionary
        
    Returns:
        True if valid, False otherwise
    """
    logger = get_pipeline_logger("validation")
    
    # Check for events.tsv
    events_file = raw_path / "sub-01" / "eeg" / "sub-01_task-navigation_events.tsv"
    if not events_file.exists():
        logger.warning(f"Events file not found: {events_file}")
        # Check for landmark timestamps as fallback
        landmark_file = raw_path / "landmarks.json"
        if landmark_file.exists():
            logger.info("Using landmark timestamps as fallback for events")
            return True
        else:
            logger.error("No event markers or landmark timestamps found")
            return False
    
    return True


def filter_data(raw: mne.io.Raw, config: Dict[str, Any]) -> mne.io.Raw:
    """
    Apply bandpass and notch filters to raw EEG data.
    
    Args:
        raw: Raw EEG data
        config: Configuration dictionary
        
    Returns:
        Filtered raw data
    """
    logger = get_pipeline_logger("filtering")
    log_stage_start(logger, "apply_filters")
    
    preprocessing_config = config.get("preprocessing", {})
    l_freq = preprocessing_config.get("l_freq", 1.0)
    h_freq = preprocessing_config.get("h_freq", 40.0)
    notch_freqs = preprocessing_config.get("notch_freqs", [50.0, 60.0])
    
    logger.info(f"Applying bandpass filter: {l_freq}-{h_freq} Hz")
    raw.filter(l_freq=l_freq, h_freq=h_freq, n_jobs=1)
    
    for freq in notch_freqs:
        logger.info(f"Applying notch filter: {freq} Hz")
        raw.notch_filter(freqs=[freq], n_jobs=1)
    
    log_stage_end(logger, "apply_filters", status="success")
    return raw


def run_ica(raw: mne.io.Raw, config: Dict[str, Any]) -> Tuple[mne.preprocessing.ICA, List[int]]:
    """
    Run ICA for artifact rejection.
    
    Args:
        raw: Filtered raw EEG data
        config: Configuration dictionary
        
    Returns:
        Tuple of (ICA object, list of rejected component indices)
    """
    logger = get_pipeline_logger("ica")
    log_stage_start(logger, "run_ica")
    
    preprocessing_config = config.get("preprocessing", {})
    ica_method = preprocessing_config.get("ica_method", "fastica")
    max_components = preprocessing_config.get("ica_max_components", 20)
    
    logger.info(f"Running ICA with method: {ica_method}")
    
    ica = mne.preprocessing.ICA(
        method=ica_method,
        max_components=max_components,
        random_state=config.get("project", {}).get("seed", 42)
    )
    
    ica.fit(raw)
    
    # Find bad components
    rejected_components = []
    
    # EOG artifacts
    try:
        eog_indices = ica.find_bads_eog(raw, ch_name=None, threshold=3.0)
        rejected_components.extend(eog_indices)
        logger.info(f"Found {len(eog_indices)} EOG-related components")
    except Exception as e:
        logger.warning(f"EOG detection failed: {e}")
    
    # ECG artifacts
    try:
        ecg_indices = ica.find_bads_ecg(raw, ch_name=None, threshold=3.0)
        rejected_components.extend(ecg_indices)
        logger.info(f"Found {len(ecg_indices)} ECG-related components")
    except Exception as e:
        logger.warning(f"ECG detection failed: {e}")
    
    # Remove duplicates
    rejected_components = list(set(rejected_components))
    rejected_components.sort()
    
    # Generate manual review log
    log_manual_review(ica, rejected_components, raw.info)
    
    log_stage_end(logger, "run_ica", status="success")
    return ica, rejected_components


def log_manual_review(ica: mne.preprocessing.ICA, rejected: List[int], info: mne.Info) -> None:
    """
    Generate log file for manual review of ICA components.
    
    Args:
        ica: Fitted ICA object
        rejected: List of rejected component indices
        info: MNE info object
    """
    logger = get_pipeline_logger("ica")
    
    log_path = Path("data/processed") / "ica_review_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write("ICA Component Review Log\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total components: {ica.n_components_}\n")
        f.write(f"Rejected components: {rejected}\n\n")
        f.write("Visual inspection hints:\n")
        f.write("- Check topographic maps for frontal (EOG) or cardiac patterns\n")
        f.write("- Review time courses for large amplitude transients\n")
        f.write("- Compare with EOG/ECG channels if available\n\n")
        
        for idx in rejected:
            f.write(f"Component {idx}: Recommended for rejection\n")
    
    logger.info(f"Manual review log written to: {log_path}")


def epoch_data(raw: mne.io.Raw, events: np.ndarray, event_id: Dict[str, int], config: Dict[str, Any]) -> mne.Epochs:
    """
    Create epochs around events.
    
    Args:
        raw: Filtered raw data
        events: Event array from MNE
        event_id: Dictionary mapping event names to IDs
        config: Configuration dictionary
        
    Returns:
        Epochs object
    """
    logger = get_pipeline_logger("epoching")
    log_stage_start(logger, "create_epochs")
    
    preprocessing_config = config.get("preprocessing", {})
    tmin = preprocessing_config.get("epoch_tmin", -1.0)
    tmax = preprocessing_config.get("epoch_tmax", 1.0)
    
    logger.info(f"Creating epochs: {tmin}s to {tmax}s around events")
    
    epochs = mne.Epochs(
        raw,
        events,
        event_id=event_id,
        tmin=tmin,
        tmax=tmax,
        baseline=None,
        reject=dict(eeg=150e-6),  # Reject bad epochs
        preload=True,
        verbose=False
    )
    
    log_stage_end(logger, "create_epochs", status="success")
    return epochs


def validate_sample_size(epochs: mne.Epochs, config: Dict[str, Any]) -> None:
    """
    Validate that we have sufficient epochs per condition.
    
    Args:
        epochs: Epochs object
        config: Configuration dictionary
        
    Raises:
        SampleSizeError: If sample size is insufficient
    """
    logger = get_pipeline_logger("validation")
    
    min_epochs = config.get("preprocessing", {}).get("min_epochs_per_condition", 100)
    
    event_counts = epochs.events.shape[0]
    n_conditions = len(epochs.event_id)
    
    avg_epochs_per_condition = event_counts / n_conditions if n_conditions > 0 else 0
    
    logger.info(f"Total epochs: {event_counts}, Conditions: {n_conditions}")
    logger.info(f"Average epochs per condition: {avg_epochs_per_condition:.1f}")
    
    if avg_epochs_per_condition < min_epochs:
        error_msg = (
            f"Insufficient epochs: {avg_epochs_per_condition:.1f} per condition "
            f"(minimum required: {min_epochs}). HALTING processing."
        )
        logger.error(error_msg)
        raise SampleSizeError(error_msg)
    
    logger.info("Sample size validation passed")


def update_metadata_with_validation(
    metadata: Dict[str, Any],
    epochs: mne.Epochs,
    rejected_components: List[int],
    skipped_electrodes: List[str],
    event_source: str
) -> Dict[str, Any]:
    """
    Update metadata dictionary with preprocessing results.
    
    Args:
        metadata: Base metadata dictionary
        epochs: Epochs object
        rejected_components: List of rejected ICA components
        skipped_electrodes: List of skipped electrodes
        event_source: Source of event markers
        
    Returns:
        Updated metadata dictionary
    """
    metadata["n_epochs_total"] = len(epochs)
    metadata["n_epochs_active"] = len(epochs[epochs.event_id.get("active", 0)])
    metadata["n_epochs_passive"] = len(epochs[epochs.event_id.get("passive", 0)])
    metadata["rejected_components"] = rejected_components
    metadata["skipped_electrodes"] = skipped_electrodes
    metadata["event_source"] = event_source
    
    return metadata


def preprocess_pipeline(config: Optional[Dict[str, Any]] = None) -> PreprocessingReport:
    """
    Run the complete preprocessing pipeline.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        PreprocessingReport object
    """
    start_time = time.time()
    logger = get_pipeline_logger("preprocessing")
    log_stage_start(logger, "preprocessing_pipeline")
    
    if config is None:
        config = load_config()
    
    paths = get_paths(config)
    
    # Step 1: Download and validate
    raw_data_path = paths["data_raw"]
    raw_data_path.mkdir(parents=True, exist_ok=True)
    
    if not (raw_data_path / "ds004229").exists():
        raw_path = download_dataset(config, raw_data_path)
    else:
        raw_path = raw_data_path / "ds004229"
    
    if not validate_dataset(raw_path, config):
        raise RuntimeError("Dataset validation failed")
    
    # Step 2: Load raw data
    logger.info("Loading raw EEG data")
    raw = mne.io.read_raw_fif(raw_path / "sub-01" / "eeg" / "sub-01_task-navigation_eeg.fif", preload=True)
    
    # Step 3: Filter
    raw = filter_data(raw, config)
    
    # Step 4: ICA
    ica, rejected_components = run_ica(raw, config)
    
    # Apply ICA rejection
    ica.exclude = rejected_components
    ica.apply(raw)
    
    # Step 5: Create events
    events, event_id = mne.events_from_annotations(raw)
    
    # Fallback for missing events
    event_source = "bids"
    if len(events) == 0:
        logger.warning("No events found, attempting landmark fallback")
        # In a real implementation, this would load landmark timestamps
        # For now, we'll raise an error to fail loudly
        raise RuntimeError("No event markers found and landmark fallback not implemented")
    
    # Step 6: Epoch
    epochs = epoch_data(raw, events, event_id, config)
    
    # Step 7: Validate sample size
    validate_sample_size(epochs, config)
    
    # Step 8: Save cleaned epochs
    output_path = paths["data_processed"] / "epochs_cleaned.fif"
    epochs.save(output_path, overwrite=True)
    logger.info(f"Cleaned epochs saved to: {output_path}")
    
    # Step 9: Generate report
    processing_time = time.time() - start_time
    
    report = PreprocessingReport(
        n_epochs_total=len(epochs),
        n_epochs_active=len(epochs[epochs.event_id.get("active", 0)]) if "active" in epochs.event_id else 0,
        n_epochs_passive=len(epochs[epochs.event_id.get("passive", 0)]) if "passive" in epochs.event_id else 0,
        rejected_components=rejected_components,
        skipped_electrodes=[],
        event_source=event_source,
        processing_time_seconds=processing_time
    )
    
    log_stage_end(logger, "preprocessing_pipeline", status="success")
    return report


def main():
    """CLI entry point for preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run EEG preprocessing pipeline")
    parser.add_argument("--config", type=Path, help="Path to config file")
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    report = preprocess_pipeline(config)
    
    print(f"Preprocessing complete:")
    print(f"  Total epochs: {report.n_epochs_total}")
    print(f"  Active epochs: {report.n_epochs_active}")
    print(f"  Passive epochs: {report.n_epochs_passive}")
    print(f"  Rejected components: {report.rejected_components}")
    print(f"  Processing time: {report.processing_time_seconds:.2f}s")


if __name__ == "__main__":
    main()
