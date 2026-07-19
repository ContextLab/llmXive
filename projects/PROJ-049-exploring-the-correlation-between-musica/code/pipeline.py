"""
Pipeline Orchestration Script.

This script orchestrates the end-to-end execution of the music-personality correlation
research pipeline. It handles directory setup, data ingestion, analysis, and reporting.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils import setup_logging, load_config
from setup_directories import create_directory_structure
from ingest import run_orchestration
from analysis import run_analysis
from verify_schema import verify_schema_integrity

logger = setup_logging(__name__)

def run_pipeline():
    """
    Execute the full research pipeline:
    1. Setup directories
    2. Ingest and preprocess data
    3. Perform statistical analysis
    4. Generate reports and visualizations
    5. Verify output schemas
    """
    start_time = time.time()
    logger.info("Starting pipeline execution...")

    # 1. Setup
    logger.info("Setting up directory structure...")
    create_directory_structure()

    # 2. Data Ingestion
    logger.info("Running data ingestion and preprocessing...")
    merged_data_path = run_orchestration()
    if not merged_data_path or not merged_data_path.exists():
        logger.error("Data ingestion failed. Aborting pipeline.")
        return False

    # 3. Analysis
    logger.info("Running statistical analysis...")
    analysis_results_path = run_analysis()
    if not analysis_results_path or not analysis_results_path.exists():
        logger.error("Analysis failed. Aborting pipeline.")
        return False

    # 4. Schema Verification
    logger.info("Verifying output schemas...")
    verify_schema_integrity()

    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
    
    # Log timing to file
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    with open(logs_dir / "timing.log", "a") as f:
        f.write(f"Pipeline run: {time.strftime('%Y-%m-%d %H:%M:%S')} | Duration: {duration:.2f}s\n")
    
    return True

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
