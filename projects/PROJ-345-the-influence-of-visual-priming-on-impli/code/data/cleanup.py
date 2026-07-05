"""
Data module cleanup and refactoring utilities.

This module consolidates data integrity checks, validation logic,
and preprocessing helper functions to improve maintainability and reduce redundancy.
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import hashlib
import json

from config import get_path
from data.ingest import load_iat_csv, validate_trial_data
from data.models import Trial, Stimulus
from data.preprocess import check_confounding

logger = logging.getLogger(__name__)


def normalize_stimulus_path(stimulus_id: str, base_dir: Path) -> Optional[Path]:
    """
    Normalize a stimulus ID to a full path, checking existence.
    
    Args:
        stimulus_id: The ID or relative path of the stimulus.
        base_dir: The base directory to check against (e.g., data/primes or data/targets).
        
    Returns:
        The absolute Path if found, None otherwise.
    """
    if not stimulus_id:
        return None
        
    # If it's already an absolute path, check it
    if os.path.isabs(stimulus_id):
        p = Path(stimulus_id)
        if p.exists():
            return p
        return None
        
    # Try relative to base_dir
    candidate = base_dir / stimulus_id
    if candidate.exists():
        return candidate
        
    # Try with common extensions if missing
    for ext in ['.jpg', '.png', '.jpeg', '.bmp', '.tiff']:
        if not stimulus_id.lower().endswith(ext):
            candidate_ext = base_dir / f"{stimulus_id}{ext}"
            if candidate_ext.exists():
                return candidate_ext
                
    return None


def validate_stimulus_integrity(
    stimuli_list: List[Stimulus], 
    prime_dir: Path, 
    target_dir: Path
) -> Tuple[int, List[str]]:
    """
    Validate that all referenced stimuli exist on disk.
    
    Args:
        stimuli_list: List of Stimulus objects to validate.
        prime_dir: Path to the primes directory.
        target_dir: Path to the targets directory.
        
    Returns:
        Tuple of (count_valid, list_of_missing_stimulus_ids)
    """
    missing = []
    valid_count = 0
    
    for stim in stimuli_list:
        if stim.stimulus_type == 'prime':
            resolved = normalize_stimulus_path(stim.stimulus_id, prime_dir)
        elif stim.stimulus_type == 'target':
            resolved = normalize_stimulus_path(stim.stimulus_id, target_dir)
        else:
            logger.warning(f"Unknown stimulus type for {stim.stimulus_id}")
            missing.append(stim.stimulus_id)
            continue
            
        if resolved:
            valid_count += 1
        else:
            missing.append(stim.stimulus_id)
            
    return valid_count, missing


def clean_duplicate_trials(
    trials: List[Trial]
) -> List[Trial]:
    """
    Remove duplicate trials based on trial_id and participant_id.
    Keeps the first occurrence.
    
    Args:
        trials: List of Trial objects.
        
    Returns:
        Deduplicated list of trials.
    """
    seen = set()
    unique_trials = []
    duplicates = 0
    
    for trial in trials:
        key = (trial.trial_id, trial.participant_id)
        if key not in seen:
            seen.add(key)
            unique_trials.append(trial)
        else:
            duplicates += 1
            logger.debug(f"Removing duplicate trial: {key}")
            
    if duplicates > 0:
        logger.info(f"Removed {duplicates} duplicate trials.")
        
    return unique_trials


def clean_missing_response_times(
    trials: List[Trial],
    threshold_ms: int = 100
) -> List[Trial]:
    """
    Remove trials with missing or implausibly low response times.
    
    Args:
        trials: List of Trial objects.
        threshold_ms: Minimum valid response time in milliseconds.
        
    Returns:
        Filtered list of trials.
    """
    original_count = len(trials)
    filtered_trials = []
    
    for trial in trials:
        if trial.response_time is None:
            logger.debug(f"Removing trial {trial.trial_id}: missing response time")
            continue
            
        if trial.response_time < threshold_ms:
            logger.debug(f"Removing trial {trial.trial_id}: response time {trial.response_time}ms < {threshold_ms}ms")
            continue
            
        filtered_trials.append(trial)
        
    removed = original_count - len(filtered_trials)
    if removed > 0:
        logger.info(f"Removed {removed} trials with missing or invalid response times.")
        
    return filtered_trials


def generate_data_quality_report(
    output_path: Path,
    total_trials: int,
    valid_trials: int,
    missing_stimuli: List[str],
    confounding_report: Optional[Dict[str, Any]] = None
) -> None:
    """
    Generate a JSON report summarizing data quality metrics.
    
    Args:
        output_path: Where to write the report.
        total_trials: Total number of trials processed.
        valid_trials: Number of trials passing quality checks.
        missing_stimuli: List of missing stimulus IDs.
        confounding_report: Optional confounding analysis results.
    """
    report = {
        "total_trials": total_trials,
        "valid_trials": valid_trials,
        "retention_rate": valid_trials / total_trials if total_trials > 0 else 0.0,
        "missing_stimuli_count": len(missing_stimuli),
        "missing_stimuli_sample": missing_stimuli[:10],  # First 10 only
        "confounding_check": confounding_report
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Data quality report written to {output_path}")


def run_data_cleanup_pipeline(
    trials_path: Optional[Path] = None,
    output_quality_report: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full data cleanup pipeline on processed trials.
    
    Args:
        trials_path: Path to the linked_trials.csv file. If None, uses default.
        output_quality_report: Path to write the quality report. If None, skips.
        
    Returns:
        Dictionary with cleanup statistics.
    """
    if trials_path is None:
        trials_path = get_path("processed", "linked_trials.csv")
        
    if not trials_path.exists():
        logger.error(f"Trials file not found: {trials_path}")
        return {"error": "File not found"}
        
    logger.info(f"Starting data cleanup pipeline on {trials_path}")
    
    # Load trials
    trials = []
    with open(trials_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rt = float(row['response_time']) if row['response_time'] else None
                trial = Trial(
                    trial_id=row['trial_id'],
                    participant_id=row['participant_id'],
                    response_time=rt,
                    stimulus_id=row.get('stimulus_id'),
                    prime_condition=row.get('prime_condition')
                )
                trials.append(trial)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed row: {row} - {e}")
                
    total_before = len(trials)
    logger.info(f"Loaded {total_before} trials")
    
    # Step 1: Clean duplicates
    trials = clean_duplicate_trials(trials)
    after_dedup = len(trials)
    logger.info(f"After deduplication: {after_dedup} trials")
    
    # Step 2: Clean invalid response times
    trials = clean_missing_response_times(trials)
    after_rt_clean = len(trials)
    logger.info(f"After response time cleaning: {after_rt_clean} trials")
    
    # Step 3: Check confounding
    confounding_result = None
    try:
        confounding_result = check_confounding(trials)
    except Exception as e:
        logger.warning(f"Confounding check failed: {e}")
        
    # Step 4: Validate stimuli (simplified for this pipeline)
    prime_dir = get_path("primes")
    target_dir = get_path("targets")
    missing_stimuli = []
    
    # Collect unique stimulus IDs
    unique_stim_ids = set(t.stimulus_id for t in trials if t.stimulus_id)
    for stim_id in unique_stim_ids:
        # Try both dirs
        if not normalize_stimulus_path(stim_id, prime_dir) and \
           not normalize_stimulus_path(stim_id, target_dir):
            missing_stimuli.append(stim_id)
            
    # Generate report
    if output_quality_report:
        generate_data_quality_report(
            output_quality_report,
            total_before,
            after_rt_clean,
            missing_stimuli,
            confounding_result
        )
        
    return {
        "original_count": total_before,
        "after_dedup": after_dedup,
        "final_count": after_rt_clean,
        "missing_stimuli_count": len(missing_stimuli),
        "confounding_check_passed": confounding_result.get("passed", False) if confounding_result else None
    }


def main():
    """Entry point for running the cleanup pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    output_report = get_path("processed", "data_quality_report.json")
    results = run_data_cleanup_pipeline(output_quality_report=output_report)
    
    print("Data Cleanup Results:")
    for k, v in results.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
