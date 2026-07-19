import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List

from src.config import load_config
from src.utils import setup_logging, get_logger, log_exception
from src.exceptions import DataUnavailableError, InsufficientDataError, PipelineError
from src.integrity import update_hashes, get_state_path, load_hashes
from src.data_loader import load_openneuro_dataset, main as data_loader_main
from src.qc import (
    calculate_subject_motion_metrics,
    verify_conditions,
    filter_by_motion_threshold,
    check_subject_count,
    run_qc_pipeline,
    main as qc_main
)
from src.preprocessing import preprocess_all_subjects, main as preprocessing_main
from src.extraction import run_extraction_pipeline, main as extraction_main
from src.connectivity import compute_connectivity_metrics, main as connectivity_main
from src.stats import run_statistical_analysis, generate_sensitivity_curve, main as stats_main
from src.visualization import generate_final_report, main as viz_main

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
STATE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-474-neural-correlates-social-ex.yaml"

def run_download_qc_step(config: Dict[str, Any], logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Executes the data download and QC pipeline (T012-T016).
    Returns the list of retained subjects.
    """
    logger.info("Starting Download and QC Step...")
    
    try:
        # 1. Download Data (T012)
        # The main function of data_loader handles the download and checksum update
        data_loader_main(config, logger)
        
        # 2. Run QC Pipeline (T013, T014, T016)
        # This function calculates motion, verifies conditions, filters, and writes subject_qc_list.json
        # It also updates the state file for the output JSON
        qc_results = run_qc_pipeline(config, logger)
        
        # 3. Check Subject Count (T015)
        # This function raises InsufficientDataError if count < 10
        check_subject_count(qc_results, config, logger)
        
        logger.info("Download and QC Step completed successfully.")
        return qc_results
        
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        log_exception(logger, e)
        sys.exit(1)
    except InsufficientDataError as e:
        logger.error(f"Insufficient subjects: {e}")
        log_exception(logger, e)
        # Return specific exit code for insufficient subjects as per T017
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error in Download/QC step: {e}")
        log_exception(logger, e)
        sys.exit(1)

def run_extract_connectivity_step(config: Dict[str, Any], logger: logging.Logger, retained_subjects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Executes preprocessing, extraction, and connectivity (T023-T027).
    """
    logger.info("Starting Connectivity Extraction Step...")
    
    try:
        # Filter retained subjects
        subject_ids = [s['subject_id'] for s in retained_subjects if s.get('retained', False)]
        
        if not subject_ids:
            raise PipelineError("No retained subjects found for connectivity analysis.")

        # 1. Preprocessing (T023)
        logger.info(f"Preprocessing {len(subject_ids)} subjects...")
        preprocess_all_subjects(subject_ids, config, logger)

        # 2. Extraction (T024)
        logger.info("Extracting ROI time-series...")
        run_extraction_pipeline(subject_ids, config, logger)

        # 3. Connectivity (T025-T027)
        logger.info("Computing connectivity metrics...")
        metrics = compute_connectivity_metrics(subject_ids, config, logger)
        
        # Save metrics to file (T028 logic integrated here as it's the output of this step)
        output_path = config.get('paths', {}).get('connectivity_metrics', 'data/processed/connectivity_metrics.json')
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Update integrity for this output
        update_hashes([output_path], config, logger)

        logger.info("Connectivity Extraction Step completed successfully.")
        return metrics

    except Exception as e:
        logger.error(f"Error in Connectivity step: {e}")
        log_exception(logger, e)
        sys.exit(1)

def run_stats_viz_step(config: Dict[str, Any], logger: logging.Logger, metrics: Dict[str, Any]) -> None:
    """
    Executes statistical testing and visualization (T033-T039).
    """
    logger.info("Starting Statistical Analysis and Visualization Step...")
    
    try:
        # 1. Sensitivity Curve (T036) - Must run before final halt logic if applicable
        # This re-calculates metrics for different thresholds
        generate_sensitivity_curve(config, logger)

        # 2. Statistical Testing (T033, T034, T035)
        run_statistical_analysis(config, logger)

        # 3. Visualization and Report (T038, T039)
        generate_final_report(config, logger)

        logger.info("Statistical Analysis and Visualization Step completed successfully.")

    except Exception as e:
        logger.error(f"Error in Stats/Viz step: {e}")
        log_exception(logger, e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Neural Correlates Pipeline Orchestrator")
    parser.add_argument('--step', type=str, choices=['download_qc', 'extract_connectivity', 'stats_viz', 'all'],
                        help='Pipeline step to execute')
    parser.add_argument('--config', type=str, default=str(CONFIG_PATH), help='Path to config.yaml')
    
    args = parser.parse_args()
    
    # Setup Logging
    logger = setup_logging()
    
    # Load Config
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    step = args.step
    
    if step == 'all' or step == 'download_qc':
        retained_subjects = run_download_qc_step(config, logger)
        if step == 'download_qc':
            return

    if step == 'all' or step == 'extract_connectivity':
        # Ensure we have subjects to process
        try:
            # Read the definitive list of retained subjects from the QC step output
            qc_list_path = Path(config.get('paths', {}).get('subject_qc_list', 'data/processed/subject_qc_list.json'))
            if not qc_list_path.exists():
                # If running in isolation without prior step, try to infer or fail
                logger.warning("QC List not found. Attempting to read from metadata if available.")
                # Fallback to metadata if list is missing but we are in 'all' mode and previous step failed silently?
                # Strictly, we should have the list from download_qc.
                # For robustness in 'all' mode, we assume download_qc ran.
                retained_subjects = [] # Should not happen if 'all' is used correctly
            else:
                with open(qc_list_path, 'r') as f:
                    retained_subjects = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load subject list: {e}")
            sys.exit(1)

        run_extract_connectivity_step(config, logger, retained_subjects)
        if step == 'extract_connectivity':
            return

    if step == 'all' or step == 'stats_viz':
        # Load metrics from previous step
        metrics_path = Path(config.get('paths', {}).get('connectivity_metrics', 'data/processed/connectivity_metrics.json'))
        if not metrics_path.exists():
            logger.error("Connectivity metrics not found. Cannot run stats.")
            sys.exit(1)
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
            
        run_stats_viz_step(config, logger, metrics)

    logger.info("Pipeline execution finished.")

if __name__ == "__main__":
    main()
