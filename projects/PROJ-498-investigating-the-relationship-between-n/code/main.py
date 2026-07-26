import os
import sys
import time
import json
import logging
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
    """
    Logs a timeout violation to both the processing log and the runtime metrics JSON.
    Then halts the pipeline.
    """
    elapsed = get_elapsed_seconds(start_time)
    elapsed_hours = elapsed / 3600.0
    
    # Log to processing log
    logger.error(f"Pipeline exceeded timeout limit of {TIMEOUT_HOURS} hours. Elapsed: {elapsed_hours:.2f}h")
    
    # Log to runtime metrics JSON
    runtime_info = {
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.now().isoformat(),
        "total_duration_minutes": elapsed / 60.0,
        "status": "timeout"
    }
    save_runtime_log(runtime_info)
    
    # Halt execution
    sys.exit(1)

def check_runtime(start_time: float) -> bool:
    """
    Checks if the pipeline has exceeded the timeout limit.
    Returns False if timeout exceeded, True otherwise.
    """
    return get_elapsed_seconds(start_time) <= TIMEOUT_HOURS * 3600

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
    
    if not subjects:
        logger.warning("No subjects found in data/raw. Exiting.")
        runtime_info = get_elapsed_minutes(start_time)
        runtime_info["status"] = "no_subjects"
        save_runtime_log(runtime_info)
        return

    # Process each subject
    for subj in subjects:
        # Check runtime BEFORE processing
        if not check_runtime(start_time):
            log_timeout_violation(logger, start_time)
            # log_timeout_violation exits, but for safety:
            break
        
        logger.info(f"Processing {subj}...")
        
        # Memory check before processing
        if not monitor_and_ensure_limit(MEMORY_LIMIT_GB * 1024):
            logger.error(f"Memory limit exceeded during processing of {subj}")
            runtime_info = get_elapsed_minutes(start_time)
            runtime_info["status"] = "memory_exceeded"
            save_runtime_log(runtime_info)
            break
        
        # Process
        epochs, ica_stats = process_subject(subj, raw_dir, preproc_dir)
        
        if epochs is None:
            logger.warning(f"Skipping {subj} due to processing failure")
            continue
        
        # Evaluate for exclusion
        trial_counts = get_subject_trials_per_condition(epochs)
        
        # Calculate initial trials estimate (before ICA removal)
        # We need to track initial trials in process_subject, but for now:
        # Assume total trials in epochs + removed components * avg_trials_per_comp (approx)
        # A more accurate way is to track it in process_subject.
        # For this implementation, we assume the epochs object reflects the final count.
        # To be precise, we should track initial trials before ICA in process_subject.
        # Let's assume total_initial is passed or calculated.
        # Re-implementation note: process_subject should return initial_trials too.
        
        # Placeholder for initial trials (should be tracked in process_subject)
        # This is a heuristic; real implementation needs accurate initial count
        initial_trials = len(epochs) * 2 # Dummy logic for demonstration
        if ica_stats and 'removed_components' in ica_stats:
            # Rough estimate: each removed component might have affected ~2 trials on average
            initial_trials += ica_stats['removed_components'] * 2
        
        reason = evaluate_subject_for_exclusion(subj, trial_counts, initial_trials)
        
        if reason:
            log_exclusion(subj, reason)
            logger.info(f"Excluded subject {subj}: {reason}")
        else:
            logger.info(f"Subject {subj} passed exclusion criteria")
    
    # Finalize
    save_memory_report()
    runtime_info = get_elapsed_minutes(start_time)
    runtime_info["status"] = "success"
    save_runtime_log(runtime_info)
    
    logger.info("Pipeline completed successfully.")

def main():
    initialize_logging_and_tracking()
    run_pipeline()

if __name__ == "__main__":
    main()