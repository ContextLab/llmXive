"""
Preprocessing module for EEG data.
Implements artifact rejection, underpowered dataset flagging, and data cleaning.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from ..utils.logging import get_logger, log_event, log_error
from ..utils.config import get_config

logger = get_logger(__name__)

# Constants for artifact rejection
MAX_ARTIFACT_REJECTION_RATE = 0.05  # 5%
MIN_SUBJECTS_FOR_POWER = 20

def load_preprocessed_data(data_dir: Path) -> Dict[str, Any]:
    """
    Load preprocessed EEG data from disk.
    Assumes data is stored in a standard format (e.g., MNE-Python .fif or .edf).
    """
    # This is a placeholder for the actual loading logic.
    # In a real implementation, this would load the data using MNE-Python or similar.
    logger.info(f"Loading preprocessed data from {data_dir}")
    # Placeholder return structure
    return {
        "subjects": {},
        "metadata": {}
    }

def detect_artifacts(epochs_data: np.ndarray, threshold: float = 100e-6) -> np.ndarray:
    """
    Detect artifacts in EEG epochs based on amplitude threshold.

    Args:
        epochs_data: Array of shape (n_epochs, n_channels, n_times)
        threshold: Amplitude threshold in Volts (default 100 microvolts)

    Returns:
        Boolean array of shape (n_epochs,) indicating if epoch is bad
    """
    # Calculate peak-to-peak amplitude for each epoch
    ptp = np.ptp(epochs_data, axis=2)
    # Check if any channel exceeds threshold
    bad_epochs = np.any(ptp > threshold, axis=1)
    return bad_epochs

def reject_artifacts(epochs_data: np.ndarray, bad_epochs: np.ndarray) -> Tuple[np.ndarray, int]:
    """
    Remove bad epochs from the data.

    Args:
        epochs_data: Array of shape (n_epochs, n_channels, n_times)
        bad_epochs: Boolean array of shape (n_epochs,)

    Returns:
        Tuple of (cleaned_epochs_data, number_of_rejected_epochs)
    """
    cleaned_data = epochs_data[~bad_epochs]
    num_rejected = np.sum(bad_epochs)
    return cleaned_data, int(num_rejected)

def check_trial_count_loss(total_epochs: int, rejected_epochs: int) -> bool:
    """
    Check if the trial count loss is within acceptable limits.

    Args:
        total_epochs: Total number of epochs before rejection
        rejected_epochs: Number of epochs rejected

    Returns:
        True if loss is <= 5%, False otherwise
    """
    if total_epochs == 0:
        return False
    loss_rate = rejected_epochs / total_epochs
    is_acceptable = loss_rate <= MAX_ARTIFACT_REJECTION_RATE
    if not is_acceptable:
        logger.warning(f"Trial count loss {loss_rate:.2%} exceeds limit {MAX_ARTIFACT_REJECTION_RATE:.2%}")
    return is_acceptable

def flag_underpowered_subjects(subject_data: Dict[str, Any]) -> List[str]:
    """
    Flag subjects from datasets with fewer than MIN_SUBJECTS_FOR_POWER subjects.

    Args:
        subject_data: Dictionary mapping subject_id to their data

    Returns:
        List of subject_ids to be excluded
    """
    if len(subject_data) < MIN_SUBJECTS_FOR_POWER:
        logger.warning(f"Dataset has only {len(subject_data)} subjects, which is underpowered (< {MIN_SUBJECTS_FOR_POWER}). Flagging all subjects.")
        return list(subject_data.keys())
    return []

def write_excluded_subjects_csv(excluded_subjects: List[Tuple[str, str]], output_path: Path) -> None:
    """
    Write excluded subject IDs to a CSV file.

    Args:
        excluded_subjects: List of tuples (subject_id, reason)
        output_path: Path to the output CSV file
    """
    df = pd.DataFrame(excluded_subjects, columns=["subject_id", "reason"])
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(excluded_subjects)} excluded subjects to {output_path}")

def update_validation_report(data_dir: Path, excluded_subjects: List[Tuple[str, str]], analysis_mode: str) -> None:
    """
    Update the validation report JSON with exclusion information.

    Args:
        data_dir: Path to the data directory
        excluded_subjects: List of tuples (subject_id, reason)
        analysis_mode: The determined analysis mode ("error_signal" or "stimulus_driven")
    """
    report_path = data_dir / "validation_report.json"
    if not report_path.exists():
        logger.error(f"Validation report not found at {report_path}. Cannot update.")
        return

    with open(report_path, 'r') as f:
        report = json.load(f)

    report["excluded_subjects"] = [
        {"subject_id": sid, "reason": reason}
        for sid, reason in excluded_subjects
    ]
    report["exclusion_summary"] = {
        "total_excluded": len(excluded_subjects),
        "reasons": list(set(reason for _, reason in excluded_subjects))
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Updated validation report at {report_path}")

def preprocess_dataset(subject_data: Dict[str, Any], data_dir: Path, analysis_mode: str) -> Tuple[Dict[str, Any], List[Tuple[str, str]]]:
    """
    Main preprocessing pipeline for a subject's data.
    Includes artifact rejection and underpowered dataset flagging.

    Args:
        subject_data: Dictionary containing subject's EEG data and metadata
        data_dir: Path to the data directory
        analysis_mode: The determined analysis mode

    Returns:
        Tuple of (processed_data, list_of_excluded_subjects_with_reasons)
    """
    subject_id = subject_data.get("subject_id", "unknown")
    epochs_data = subject_data.get("epochs", None)

    if epochs_data is None:
        logger.error(f"No epochs data found for subject {subject_id}")
        return subject_data, [(subject_id, "missing_epochs_data")]

    total_epochs = epochs_data.shape[0]
    bad_epochs = detect_artifacts(epochs_data)
    cleaned_epochs, num_rejected = reject_artifacts(epochs_data, bad_epochs)

    is_acceptable = check_trial_count_loss(total_epochs, num_rejected)

    if not is_acceptable:
        logger.warning(f"Subject {subject_id} rejected due to excessive artifact loss.")
        return subject_data, [(subject_id, "excessive_artifact_rejection")]

    subject_data["epochs"] = cleaned_epochs
    subject_data["num_rejected_epochs"] = num_rejected
    subject_data["final_epoch_count"] = cleaned_epochs.shape[0]

    return subject_data, []

def run_preprocessing_pipeline(data_dir: Path, analysis_mode: str) -> None:
    """
    Run the full preprocessing pipeline including artifact rejection and exclusion logic.

    Args:
        data_dir: Path to the data directory
        analysis_mode: The determined analysis mode
    """
    logger.info("Starting preprocessing pipeline")

    # Load all subject data (placeholder logic)
    all_subjects_data = {}
    # In a real implementation, this would iterate over subjects in data_dir
    # For now, we assume a single subject for demonstration
    sample_subject = {
        "subject_id": "sub-001",
        "epochs": np.random.randn(100, 64, 500)  # Placeholder data
    }
    all_subjects_data["sub-001"] = sample_subject

    # Check for underpowered dataset
    excluded_subjects = flag_underpowered_subjects(all_subjects_data)
    excluded_list = [(sid, "underpowered_dataset") for sid in excluded_subjects]

    # Process each subject
    final_subjects = {}
    for subject_id, data in all_subjects_data.items():
        if subject_id in excluded_subjects:
            continue
        processed_data, subject_exclusions = preprocess_dataset(data, data_dir, analysis_mode)
        excluded_list.extend(subject_exclusions)
        if not subject_exclusions:
            final_subjects[subject_id] = processed_data

    # Write excluded subjects to CSV
    excluded_csv_path = data_dir / "excluded_subjects.csv"
    write_excluded_subjects_csv(excluded_list, excluded_csv_path)

    # Update validation report
    update_validation_report(data_dir, excluded_list, analysis_mode)

    logger.info("Preprocessing pipeline completed")

def main():
    """
    Entry point for the preprocessing script.
    """
    config = get_config()
    data_dir = Path(config.get("DATA_DIR", "./data"))
    analysis_mode = "error_signal"  # This would come from T003 validation report

    run_preprocessing_pipeline(data_dir, analysis_mode)

if __name__ == "__main__":
    main()
