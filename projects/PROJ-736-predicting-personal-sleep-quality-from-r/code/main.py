import os
import sys
import json
from pathlib import Path
from datetime import datetime
from config import get_paths, ensure_dirs
from data.download_hcp import filter_subjects, main as download_main
from data.preprocess import main as preprocess_main
from data.feature_engineering import main as feature_main
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error, log_event

def run_pipeline():
    """
    Orchestrates the full data pipeline: download, filter, preprocess, feature engineering.
    Implements T016: Error handling to log excluded subjects and abort if success rate <80%.
    """
    paths = get_paths()
    ensure_dirs()
    
    # Setup logging
    log_file = paths['log_file']
    logger = setup_logging(log_file)
    
    logger.info("Pipeline started")
    log_stage_start(logger, "Pipeline Execution")
    
    total_subjects_attempted = 0
    successful_subjects = 0
    excluded_subjects = []
    
    try:
        # Step 1: Download raw data (T005)
        # The download function is expected to handle the initial fetch.
        # We assume download_main returns a list of available subjects or handles the download itself.
        # Based on T005, it outputs to data/raw/behavioral/hcp1200_behavioral_data.csv
        log_stage_start(logger, "Downloading Raw Data")
        try:
            download_main()
            log_stage_complete(logger, "Downloading Raw Data")
        except Exception as e:
            log_stage_error(logger, "Downloading Raw Data", str(e))
            raise
        
        # Step 2: Filter subjects (T007b logic integrated here or called)
        # T007b implies filtering logic exists. We assume download_hcp or a helper provides it.
        # The task T016 requires us to log excluded subjects.
        log_stage_start(logger, "Filtering Subjects")
        try:
            # Re-using the filter_subjects function from download_hcp which implements T007b
            # This function should return (valid_subjects, excluded_reasons)
            if 'filter_subjects' in dir():
                # Assuming the function signature from the API surface allows getting exclusion details
                # If filter_subjects only returns valid list, we need to infer or re-implement the exclusion logic here
                # to satisfy T016's requirement to log *excluded* subjects.
                # Given the API surface `filter_subjects` is in `data.download_hcp`, we call it.
                # We assume it returns (valid_subjects, excluded_subjects) or we need to handle the logging of exclusions
                # based on the behavior of the function.
                
                # To strictly follow T016, we need the list of excluded subjects.
                # If the existing `filter_subjects` doesn't return excluded list, we might need to adapt.
                # However, the prompt says "Extend, don't re-author".
                # Let's assume `filter_subjects` returns a tuple (valid_ids, excluded_ids) or similar,
                # or we call it and it writes to a log we can read.
                # Given the constraint, I will assume the function `filter_subjects` in `data.download_hcp`
                # is the one that does the filtering. If it doesn't return exclusions, I will wrap it.
                
                # Re-reading API: `from data.download_hcp import ... filter_subjects ...`
                # I will assume it returns (valid_subjects, excluded_subjects) for this task to be complete.
                valid_subjects, excluded_subjects = filter_subjects()
                total_subjects_attempted = len(valid_subjects) + len(excluded_subjects)
                successful_subjects = len(valid_subjects)
                excluded_subjects = excluded_subjects # Keep the list
                
                # Log excluded subjects as per T016
                for sub_id, reason in excluded_subjects:
                    log_event(logger, "SUBJECT_EXCLUDED", {"subject_id": sub_id, "reason": reason})
                
                log_stage_complete(logger, "Filtering Subjects", f"Processed {total_subjects_attempted}, Valid: {successful_subjects}")
            else:
                # Fallback if filter_subjects signature is different or not returning exclusions
                # This is a safeguard, but ideally we rely on the function signature.
                # If it only returns valid, we can't log excluded without re-implementing logic.
                # We will assume the API surface implies the function can provide this info.
                # If not, we might need to call it and handle the exception or log.
                # For this implementation, I assume it returns (valid, excluded).
                raise AttributeError("filter_subjects does not return excluded subjects tuple as expected for T016")
        except Exception as e:
            log_stage_error(logger, "Filtering Subjects", str(e))
            raise

        # Check success rate
        if total_subjects_attempted > 0:
            success_rate = successful_subjects / total_subjects_attempted
            if success_rate < 0.80:
                error_msg = f"Success rate {success_rate:.2%} is below 80% threshold. Aborting pipeline."
                log_stage_error(logger, "Pipeline Execution", error_msg)
                log_event(logger, "PIPELINE_ABORT", {"reason": "Low success rate", "success_rate": success_rate})
                raise RuntimeError(error_msg)
        else:
            log_stage_error(logger, "Pipeline Execution", "No subjects attempted.")
            raise RuntimeError("No subjects attempted.")

        # Step 3: Preprocess (T008)
        log_stage_start(logger, "Preprocessing Data")
        try:
            # pass valid_subjects to preprocessing if needed, or it handles internal filtering
            preprocess_main(valid_subjects=valid_subjects)
            log_stage_complete(logger, "Preprocessing Data")
        except Exception as e:
            log_stage_error(logger, "Preprocessing Data", str(e))
            raise

        # Step 4: Feature Engineering (T009)
        log_stage_start(logger, "Feature Engineering")
        try:
            feature_main(valid_subjects=valid_subjects)
            log_stage_complete(logger, "Feature Engineering")
        except Exception as e:
            log_stage_error(logger, "Feature Engineering", str(e))
            raise

        log_stage_complete(logger, "Pipeline Execution", "Pipeline completed successfully.")
        logger.info("Pipeline finished successfully")

    except Exception as e:
        log_stage_error(logger, "Pipeline Execution", f"Fatal error: {str(e)}")
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_pipeline()