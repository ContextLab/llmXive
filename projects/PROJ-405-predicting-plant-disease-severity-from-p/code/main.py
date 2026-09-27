"""
Main Orchestration Script for the Plant Disease Severity Prediction Pipeline.

Executes the full pipeline:
1. Data Stage (Download, Extract, Link, Merge)
2. Model Stage (Baseline, Augmented, Permutation Test)
3. Visual Stage (PDP, Sensitivity)
4. Final Reporting (T040)
"""
import os
import sys
import gc
import logging
import traceback
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_dirs, get_path
from utils.logging_config import setup_logging, get_logger
from utils.state_manager import batch_update_state, compute_file_hash
from data_ingestion import main as run_data_stage
from modeling import main as run_model_stage
from visualization import main as run_visual_stage
from utils.final_report import generate_final_report

logger = get_logger(__name__)


def check_memory_usage() -> Dict[str, Any]:
    """
    Checks current memory usage.
    Note: Actual peak tracking requires T044 instrumentation.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return {
            "max_rss_mb": usage.ru_maxrss, # In KB on Linux, MB on macOS usually, check platform
            "timestamp": "current"
        }
    except ImportError:
        return {"error": "resource module not available"}


def run_full_pipeline() -> None:
    """
    Orchestrates the execution of all pipeline stages in order.
    """
    logger.info("="*60)
    logger.info("Starting Full Pipeline Execution")
    logger.info("="*60)

    try:
        # 1. Setup Directories
        ensure_dirs()
        logger.info("Directory structure ensured.")

        # 2. Data Stage
        logger.info(">>> Stage 1: Data Ingestion & Feature Extraction")
        run_data_stage()
        logger.info(">>> Stage 1 Complete.")
        gc.collect()

        # 3. Model Stage
        logger.info(">>> Stage 2: Modeling & Hypothesis Testing")
        run_model_stage()
        logger.info(">>> Stage 2 Complete.")
        gc.collect()

        # 4. Visual Stage
        logger.info(">>> Stage 3: Visualization & Sensitivity Analysis")
        run_visual_stage()
        logger.info(">>> Stage 3 Complete.")
        gc.collect()

        # 5. Final Report Generation (T040)
        logger.info(">>> Stage 4: Final Report Generation (T040)")
        generate_final_report()
        logger.info(">>> Stage 4 Complete.")

        logger.info("="*60)
        logger.info("Pipeline Execution Finished Successfully")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        logger.error(traceback.format_exc())
        raise


def main() -> None:
    """
    Main entry point.
    """
    setup_logging()
    run_full_pipeline()


if __name__ == "__main__":
    main()
