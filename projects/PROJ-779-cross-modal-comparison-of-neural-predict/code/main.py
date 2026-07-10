"""
Main orchestration script for the Cross-Modal Comparison of Neural Prediction Error Signals pipeline.

This script chains the following steps:
1. Download datasets (Auditory ds000246, Visual ds000117)
2. Validate datasets (Sampling rate >= 500Hz, Trial counts)
3. Preprocess datasets (Filter, ICA, Re-reference, Save cleaned data)
4. Extract Metrics (Difference waves, Peak Latency, Mean Amplitude)
5. Save results to data/results/metrics_summary.json

Usage:
    python code/main.py
"""

import sys
import os
from pathlib import Path

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_config, ensure_directories
from code.utils.logger import get_logger, configure_logging
from code.data.download import (
    run_auditory_validation, 
    validate_visual_dataset, 
    validate_auditory_dataset
)
from code.data.preprocess import main as preprocess_main
from code.data.data_loader import validate_sampling_rate, validate_trial_counts
from code.analysis.metrics import generate_metrics_summary

logger = get_logger(__name__)

def run_orchestration():
    """Execute the full pipeline: Download -> Validate -> Preprocess -> Extract Metrics."""
    logger.info("Starting Cross-Modal Neural Prediction Error Pipeline")
    
    # Load configuration
    try:
        config = get_config()
        ensure_directories()
        logger.info(f"Configuration loaded. Output dir: {config['output_dir']}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Step 1: Download and Validate Auditory Dataset (ds000246)
    logger.info("--- Step 1: Auditory Dataset (ds000246) ---")
    try:
        # The download module handles fetching and basic structure validation
        # We explicitly call the validation logic defined in the API surface
        result_aud = run_auditory_validation()
        if not result_aud:
            logger.error("Auditory dataset validation failed.")
            return 1
        logger.info("Auditory dataset validated successfully.")
        
    except Exception as e:
        logger.error(f"Auditory processing failed: {e}")
        return 1
    
    # Step 2: Download and Validate Visual Dataset (ds000117)
    logger.info("--- Step 2: Visual Dataset (ds000117) ---")
    try:
        # Similar to auditory, we rely on the validation function to ensure data integrity
        result_vis = validate_visual_dataset()
        if not result_vis:
            logger.error("Visual dataset validation failed.")
            return 1
        logger.info("Visual dataset validated successfully.")
        
    except Exception as e:
        logger.error(f"Visual processing failed: {e}")
        return 1
    
    # Step 3: Preprocess Datasets
    logger.info("--- Step 3: Preprocessing Pipeline ---")
    try:
        # T019-T022 are implemented in preprocess.py.
        # The `main` function in preprocess.py is the entry point for the full pipeline.
        preprocess_main()
        logger.info("Preprocessing completed successfully. Cleaned data saved.")
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return 1
    
    # Step 4: Extract Metrics and Save Results (T032)
    logger.info("--- Step 4: Metric Extraction and Summary Generation ---")
    try:
        # Call the metrics generation function which computes difference waves,
        # extracts peak latencies and mean amplitudes, and saves the summary.
        metrics_path = generate_metrics_summary()
        logger.info(f"Metrics summary generated and saved to: {metrics_path}")
        
    except Exception as e:
        logger.error(f"Metric extraction failed: {e}")
        return 1
    
    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    # Configure logging
    configure_logging()
    exit_code = run_orchestration()
    sys.exit(exit_code)