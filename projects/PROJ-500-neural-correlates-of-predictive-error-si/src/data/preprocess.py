"""
Preprocessing module for EEG data.
Implements artifact rejection, underpowered subject flagging, and data hygiene.
"""
import os
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Import project utilities
from src.utils.logging import get_logger, log_event, log_error
from src.utils.config import get_config
from src.utils.checksum import compute_file_sha256

logger = get_logger(__name__)

# Constants
MAX_TRIAL_LOSS_PERCENT = 5.0  # Maximum allowed trial loss due to artifact rejection
UNDERPOWERED_SUBJECT_THRESHOLD = 20  # Minimum number of subjects required

def calculate_artifact_rejection_rate(
    original_trials: int,
    rejected_trials: int
) -> float:
    """
    Calculate the percentage of trials rejected due to artifacts.

    Args:
        original_trials: Total number of trials before rejection
        rejected_trials: Number of trials removed due to artifacts

    Returns:
        Percentage of trials rejected
    """
    if original_trials == 0:
        return 0.0
    return (rejected_trials / original_trials) * 100.0

def validate_trial_count_loss(
    original_count: int,
    final_count: int,
    max_loss_percent: float = MAX_TRIAL_LOSS_PERCENT
) -> Tuple[bool, float]:
    """
    Validate that trial count loss is within acceptable limits.

    Args:
        original_count: Number of trials before rejection
        final_count: Number of trials after rejection
        max_loss_percent: Maximum allowed loss percentage

    Returns:
        Tuple of (is_valid, actual_loss_percent)
    """
    lost_trials = original_count - final_count
    loss_percent = calculate_artifact_rejection_rate(original_count, lost_trials)
    return loss_percent <= max_loss_percent, loss_percent

def identify_underpowered_subjects(
    subject_trial_counts: Dict[str, int],
    threshold: int = UNDERPOWERED_SUBJECT_THRESHOLD
) -> List[str]:
    """
    Identify subjects with insufficient trials (underpowered).

    Args:
        subject_trial_counts: Dictionary mapping subject_id to trial count
        threshold: Minimum required trials per subject

    Returns:
        List of subject IDs that are underpowered
    """
    underpowered = []
    for subject_id, count in subject_trial_counts.items():
        if count < threshold:
            underpowered.append(subject_id)
    return underpowered

def write_excluded_subjects_csv(
    excluded_subjects: List[str],
    output_path: Path
) -> None:
    """
    Write excluded subject IDs to a CSV file.

    Args:
        excluded_subjects: List of subject IDs to exclude
        output_path: Path to the output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['subject_id', 'reason'])
        for subject_id in excluded_subjects:
            writer.writerow([subject_id, 'underpowered'])
    logger.info(f"Wrote {len(excluded_subjects)} excluded subjects to {output_path}")

def update_validation_report(
    validation_report_path: Path,
    underpowered_subjects: List[str]
) -> None:
    """
    Update the validation report JSON with underpowered subjects list.

    Args:
        validation_report_path: Path to the validation report JSON file
        underpowered_subjects: List of subject IDs to add to the report
    """
    if not validation_report_path.exists():
        report = {
            "analysis_mode": "error_signal",
            "underpowered_subjects": [],
            "validation_status": "passed"
        }
    else:
        with open(validation_report_path, 'r') as f:
            report = json.load(f)

    # Update underpowered subjects list
    report['underpowered_subjects'] = underpowered_subjects
    report['underpowered_count'] = len(underpowered_subjects)

    # Update validation status if underpowered subjects exist
    if underpowered_subjects:
        report['validation_status'] = 'warning'
        log_event(
            event_type="validation_warning",
            message=f"Found {len(underpowered_subjects)} underpowered subjects",
            subjects=underpowered_subjects
        )

    with open(validation_report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Updated validation report at {validation_report_path}")

def preprocess_dataset(
    data_dir: Path,
    output_dir: Path,
    validation_report_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main preprocessing pipeline that includes artifact rejection and
    underpowered subject flagging.

    Args:
        data_dir: Directory containing preprocessed EEG data (from T015)
        output_dir: Directory to write output artifacts
        validation_report_path: Path to validation report JSON (optional)

    Returns:
        Dictionary with preprocessing results and statistics
    """
    logger.info(f"Starting preprocessing pipeline for {data_dir}")

    # Initialize results
    results = {
        "total_subjects": 0,
        "excluded_subjects": [],
        "trial_stats": {},
        "artifact_rejection_valid": True
    }

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load subject trial counts (simulated from T015 output or metadata)
    # In a real pipeline, this would come from the epoching step
    subject_trial_counts = {}
    total_original_trials = 0
    total_final_trials = 0

    # Scan for subject data files
    subject_files = list(data_dir.glob("subject_*.json"))
    if not subject_files:
        # Fallback: scan for any JSON files that might contain trial counts
        subject_files = list(data_dir.glob("*.json"))

    for subject_file in subject_files:
        try:
            with open(subject_file, 'r') as f:
                subject_data = json.load(f)

            subject_id = subject_data.get('subject_id', subject_file.stem)
            original_trials = subject_data.get('original_trial_count', 0)
            final_trials = subject_data.get('final_trial_count', 0)

            if original_trials > 0:
                subject_trial_counts[subject_id] = final_trials
                total_original_trials += original_trials
                total_final_trials += final_trials

                # Check artifact rejection rate for this subject
                is_valid, loss_percent = validate_trial_count_loss(
                    original_trials, final_trials
                )

                if not is_valid:
                    logger.warning(
                        f"Subject {subject_id} exceeded artifact rejection "
                        f"threshold: {loss_percent:.2f}% loss"
                    )
                    results['artifact_rejection_valid'] = False

                results['trial_stats'][subject_id] = {
                    'original': original_trials,
                    'final': final_trials,
                    'loss_percent': loss_percent
                }

        except (json.JSONDecodeError, KeyError) as e:
            log_error(f"Error processing {subject_file}: {e}")
            continue

    results['total_subjects'] = len(subject_trial_counts)

    # Identify underpowered subjects
    underpowered_subjects = identify_underpowered_subjects(subject_trial_counts)
    results['excluded_subjects'] = underpowered_subjects

    # Write excluded subjects CSV
    excluded_csv_path = output_dir / "excluded_subjects.csv"
    write_excluded_subjects_csv(underpowered_subjects, excluded_csv_path)

    # Update validation report
    if validation_report_path is None:
        validation_report_path = output_dir.parent / "data" / "validation_report.json"

    if validation_report_path:
        update_validation_report(validation_report_path, underpowered_subjects)

    # Log summary
    log_event(
        event_type="preprocessing_complete",
        message="Artifact rejection and underpowered subject flagging complete",
        total_subjects=results['total_subjects'],
        excluded_count=len(underpowered_subjects),
        total_original_trials=total_original_trials,
        total_final_trials=total_final_trials,
        avg_loss_percent=(
            ((total_original_trials - total_final_trials) / total_original_trials * 100)
            if total_original_trials > 0 else 0
        )
    )

    logger.info(
        f"Preprocessing complete: {results['total_subjects']} subjects, "
        f"{len(underpowered_subjects)} excluded as underpowered"
    )

    return results

def run_preprocessing_pipeline(
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Entry point for running the full preprocessing pipeline with artifact
    rejection and underpowered subject flagging.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Dictionary with pipeline results
    """
    config = get_config(config_path)

    data_dir = Path(config['data_dir'])
    output_dir = Path(config['output_dir'])
    validation_report_path = Path(config.get('validation_report_path', 
                                             output_dir.parent / "data" / "validation_report.json"))

    return preprocess_dataset(data_dir, output_dir, validation_report_path)

if __name__ == "__main__":
    # Run pipeline with default configuration
    results = run_preprocessing_pipeline()
    print(json.dumps(results, indent=2))
