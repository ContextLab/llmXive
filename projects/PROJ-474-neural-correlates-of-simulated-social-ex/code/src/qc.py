import os
import json
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Dict, Any, Set

from src.config import load_config
from src.utils import get_logger, InsufficientDataError

# Re-using the custom error defined in utils or local scope if preferred
# The API surface shows InsufficientDataError is available from src.utils
# We will import it from there to be consistent.

def load_motion_parameters(subject_dir: Path) -> np.ndarray:
    """
    Load motion parameters (6 columns) from a subject's confounds file.
    Expects a .tsv file named 'confounds.tsv' or similar in the subject directory.
    """
    confounds_file = subject_dir / "confounds.tsv"
    if not confounds_file.exists():
        # Fallback: look for specific OpenNeuro naming conventions if needed
        # For now, raise if missing as per strict QC
        raise FileNotFoundError(f"Confounds file not found for {subject_dir}")
    
    # Read TSV manually to avoid pandas dependency if strictly avoiding it, 
    # but standard python csv is safer for raw dependencies.
    # However, the API surface imports numpy and nibabel. 
    # Let's use numpy to load the TSV as it's robust for numeric data.
    try:
        data = np.genfromtxt(confounds_file, delimiter='\t', skip_header=1, usecols=(1,2,3,4,5,6)) # Assuming first col is time
        if data.ndim == 1:
            data = data.reshape(-1, 6)
        return data
    except Exception as e:
        raise IOError(f"Failed to load motion parameters from {confounds_file}: {e}")

def calculate_framewise_displacement(motion_params: np.ndarray) -> np.ndarray:
    """
    Calculate Framewise Displacement (FD) from 6 motion parameters.
    FD = sum of absolute differences of each parameter.
    """
    if motion_params.shape[1] < 6:
        raise ValueError("Motion parameters must have at least 6 columns.")
    
    # Calculate differences
    diffs = np.abs(np.diff(motion_params, axis=0))
    # Sum absolute differences
    fd = np.sum(diffs, axis=1)
    return fd

def calculate_subject_motion_metrics(subject_dir: Path) -> Dict[str, float]:
    """
    Calculate max displacement and mean FD for a subject.
    """
    motion_params = load_motion_parameters(subject_dir)
    fd = calculate_framewise_displacement(motion_params)
    
    return {
        "max_displacement": float(np.max(fd)),
        "mean_fd": float(np.mean(fd))
    }

def process_subject(subject_dir: Path, threshold: float) -> Dict[str, Any]:
    """
    Process a single subject directory to calculate metrics and determine retention.
    """
    metrics = calculate_subject_motion_metrics(subject_dir)
    retained = metrics["max_displacement"] <= threshold
    
    return {
        "subject_id": subject_dir.name,
        "motion_metric": metrics["max_displacement"],
        "condition_status": "PASS" if retained else "FAIL",
        "retained": retained
    }

def filter_by_motion_threshold(
    subject_dirs: List[Path], 
    threshold: float = 3.0, 
    output_path: Path = None
) -> List[Dict[str, Any]]:
    """
    Filter subjects based on motion threshold.
    Writes results to subject_qc_list.json if output_path is provided.
    """
    results = []
    for subj_dir in subject_dirs:
        try:
            result = process_subject(subj_dir, threshold)
            results.append(result)
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Error processing {subj_dir}: {e}")
            # Exclude on error
            results.append({
                "subject_id": subj_dir.name,
                "motion_metric": None,
                "condition_status": "ERROR",
                "retained": False
            })
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
    
    return results

def check_subject_count(filtered_results: List[Dict[str, Any]], min_count: int = 10):
    """
    Verify that enough subjects passed QC.
    Raises InsufficientDataError if count < min_count.
    """
    retained_count = sum(1 for r in filtered_results if r.get("retained", False))
    if retained_count < min_count:
        raise InsufficientDataError(
            f"Insufficient subjects retained: {retained_count} < {min_count}. "
            "Global halt logic triggered (FR-009)."
        )
    return retained_count

def verify_conditions(
    subject_dirs: List[Path], 
    retained_subject_ids: List[str], 
    config: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Verify each subject has valid time-series data for BOTH Inclusion and Exclusion conditions.
    Excludes subjects if missing (FR-010).
    
    Args:
        subject_dirs: List of all subject directories processed.
        retained_subject_ids: List of subject IDs that passed motion QC (from T014).
        config: Optional config dict to read expected condition names.
    
    Returns:
        List of subjects that passed condition verification.
    """
    logger = get_logger(__name__)
    if config is None:
        config = load_config()
    
    # Expected conditions from config or defaults
    expected_conditions = config.get("analysis", {}).get("conditions", ["Inclusion", "Exclusion"])
    
    final_retained = []
    
    for subj_path in subject_dirs:
        subj_id = subj_path.name
        
        # Only check subjects that were retained by motion filter
        if subj_id not in retained_subject_ids:
            continue
        
        # Check for events.tsv or similar metadata that defines conditions
        # OpenNeuro typically has events.tsv in the subject/task folder
        # We need to look for the functional runs and their associated events
        
        # Strategy: Look for events.tsv files in the subject directory
        # and verify that all expected conditions are present in the 'trial_type' column.
        
        events_files = list(subj_path.rglob("events.tsv"))
        if not events_files:
            logger.warning(f"No events.tsv found for {subj_id}. Excluding.")
            continue
        
        # Aggregate conditions found across all events files for this subject
        found_conditions: Set[str] = set()
        
        for ev_file in events_files:
            try:
                # Read TSV
                import csv
                with open(ev_file, 'r') as f:
                    reader = csv.DictReader(f, delimiter='\t')
                    for row in reader:
                        if 'trial_type' in row and row['trial_type']:
                            found_conditions.add(row['trial_type'])
            except Exception as e:
                logger.warning(f"Could not parse events file {ev_file}: {e}")
        
        # Check if all expected conditions are present
        missing_conditions = set(expected_conditions) - found_conditions
        
        if missing_conditions:
            logger.warning(
                f"Subject {subj_id} missing conditions: {missing_conditions}. "
                f"Found: {found_conditions}. Excluding per FR-010."
            )
            # Do not add to final_retained
            continue
        
        # If we reach here, conditions are valid
        final_retained.append({
            "subject_id": subj_id,
            "conditions_verified": list(found_conditions),
            "retained": True
        })
    
    logger.info(f"Condition verification complete. {len(final_retained)} subjects retained.")
    return final_retained

def run_qc_pipeline(
    data_dir: Path, 
    output_dir: Path = None,
    motion_threshold: float = 3.0,
    min_subjects: int = 10
) -> List[Dict[str, Any]]:
    """
    Run the full QC pipeline: Motion -> Count -> Conditions.
    """
    logger = get_logger(__name__)
    config = load_config()
    
    if output_dir is None:
        output_dir = data_dir / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Identify subject directories
    subject_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')])
    logger.info(f"Found {len(subject_dirs)} subjects.")
    
    if not subject_dirs:
        raise InsufficientDataError("No subject directories found.")
    
    # 2. Motion Filtering (T013, T014)
    qc_list_path = output_dir / "subject_qc_list.json"
    motion_results = filter_by_motion_threshold(subject_dirs, motion_threshold, qc_list_path)
    
    # 3. Count Check (T015)
    check_subject_count(motion_results, min_subjects)
    
    # 4. Condition Verification (T016)
    retained_ids = [r["subject_id"] for r in motion_results if r.get("retained", False)]
    condition_results = verify_conditions(subject_dirs, retained_ids, config)
    
    # 5. Update the QC list with condition status or create a final list
    # The task asks to exclude if missing. We return the final list.
    return condition_results

def main():
    """
    Entry point for QC pipeline execution.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run QC pipeline on fMRI data.")
    parser.add_argument("--data-dir", type=str, required=True, help="Path to raw data directory")
    parser.add_argument("--output-dir", type=str, default=None, help="Path to output directory")
    parser.add_argument("--threshold", type=float, default=3.0, help="Motion threshold in mm")
    parser.add_argument("--min-subjects", type=int, default=10, help="Minimum subjects required")
    
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info(f"Starting QC pipeline on {args.data_dir}")
    
    try:
        final_subjects = run_qc_pipeline(
            data_dir=Path(args.data_dir),
            output_dir=Path(args.output_dir) if args.output_dir else None,
            motion_threshold=args.threshold,
            min_subjects=args.min_subjects
        )
        logger.info(f"QC Pipeline complete. {len(final_subjects)} subjects passed all checks.")
    except InsufficientDataError as e:
        logger.error(f"QC Pipeline failed due to insufficient data: {e}")
        raise
    except Exception as e:
        logger.error(f"QC Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()

# Helper to ensure setup_logging is available if not imported from utils correctly
# The API surface says src.utils has setup_logging
from src.utils import setup_logging