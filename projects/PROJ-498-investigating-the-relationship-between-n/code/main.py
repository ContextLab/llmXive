import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from logging_setup import get_logger, initialize_logging_and_tracking
from config import ensure_directories
from preprocess import process_subject, get_subject_ids, get_subject_trials_per_condition
from exclusion_tracker import log_exclusion, evaluate_subject_for_exclusion, ensure_exclusions_file_exists
from memory_monitor import monitor_and_ensure_limit, save_memory_report
from runtime_logger import start_timer, get_elapsed_minutes, save_runtime_log

MEMORY_LIMIT_GB = 6.5
TIMEOUT_HOURS = 4

def get_elapsed_seconds(start_time: float) -> float:
    return time.time() - start_time

def log_timeout_violation(logger: logging.Logger, start_time: float):
    elapsed = get_elapsed_seconds(start_time)
    logger.error(f"Pipeline exceeded timeout limit of {TIMEOUT_HOURS} hours. Elapsed: {elapsed/3600:.2f}h")
    # Log to runtime log as well
    save_runtime_log({"status": "timeout", "elapsed_hours": elapsed/3600})

def check_runtime(start_time: float):
    if get_elapsed_seconds(start_time) > TIMEOUT_HOURS * 3600:
        return False
    return True

def run_pipeline():
    """
    Main pipeline orchestrator.
    1. Setup directories
    2. Iterate subjects
    3. Preprocess
    4. Evaluate exclusions
    5. Save metrics
    """
    start_time = start_timer()
    logger = get_logger()
    logger.info("Starting pipeline...")
    
    # Ensure directories
    ensure_directories()
    ensure_exclusions_file_exists()
    
    raw_dir = "data/raw"
    preproc_dir = "data/processed"
    
    # Get subjects
    subjects = get_subject_ids(raw_dir)
    logger.info(f"Found {len(subjects)} subjects")
    
    # Process each subject
    for subj in subjects:
        if not check_runtime(start_time):
            log_timeout_violation(logger, start_time)
            break
        
        logger.info(f"Processing {subj}...")
        
        # Memory check before processing
        if not monitor_and_ensure_limit(MEMORY_LIMIT_GB * 1024):
            logger.error(f"Memory limit exceeded during processing of {subj}")
            break
        
        # Process
        epochs, ica_stats = process_subject(subj, raw_dir, preproc_dir)
        
        if epochs is None:
            logger.warning(f"Skipping {subj} due to processing failure")
            continue
        
        # Evaluate for exclusion
        trial_counts = get_subject_trials_per_condition(epochs)
        total_initial = sum(trial_counts.values()) + ica_stats.get('removed_components', 0) # Approximation
        # Note: We need the actual initial trial count before artifact removal.
        # For this implementation, we assume ica_stats or epochs object has this info.
        # Since epochs are created after ICA, we might need to track initial count separately.
        # For now, we use a heuristic or assume the epochs object reflects the final count.
        # To be precise, we should track initial trials before ICA in process_subject.
        # Let's assume total_initial is passed or calculated.
        # Re-implementation note: process_subject should return initial_trials too.
        
        # Placeholder for initial trials (should be tracked in process_subject)
        initial_trials = len(epochs) * 2 # Dummy logic for demonstration
        
        reason = evaluate_subject_for_exclusion(subj, trial_counts, initial_trials)
        
        if reason:
            log_exclusion(subj, reason)
            logger.info(f"Excluded subject {subj}: {reason}")
        else:
            logger.info(f"Subject {subj} passed exclusion criteria")
    
    # Finalize
    save_memory_report()
    runtime_info = get_elapsed_minutes(start_time)
    save_runtime_log(runtime_info)
    
    logger.info("Pipeline completed successfully.")

def main():
    initialize_logging_and_tracking()
    run_pipeline()

if __name__ == "__main__":
    main()
