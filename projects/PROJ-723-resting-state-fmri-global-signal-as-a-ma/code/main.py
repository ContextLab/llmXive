"""
Main entry point for the Resting-State fMRI Global Signal analysis pipeline.

This script orchestrates the full pipeline:
1. Data Ingestion (download, validate, clean)
2. Modeling (Ridge regression, null distribution)
3. Robustness Analysis
4. Reporting & Visualization

Usage:
    python code/main.py
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils import get_logger, setup_logging

# Import pipeline steps
from run_ingestion_pipeline import main as run_ingestion
from modeling import main as run_modeling
from diagnostics import main as run_diagnostics
from robustness import main as run_robustness
from visualizations import main as run_visualizations
from run_final_report import main as run_final_report

def main():
    """Execute the full analysis pipeline."""
    logger = get_logger("main")
    
    logger.info("Starting Resting-State fMRI Global Signal Analysis Pipeline")
    logger.info("=" * 60)
    
    # Ensure directories exist
    ensure_directories()
    logger.info("Project directories verified/created")
    
    # Step 1: Data Ingestion
    logger.info("Step 1: Running data ingestion pipeline...")
    try:
        run_ingestion()
        logger.info("✓ Data ingestion complete")
    except Exception as e:
        logger.error(f"✗ Data ingestion failed: {e}")
        sys.exit(1)
    
    # Step 2: Modeling
    logger.info("Step 2: Running modeling pipeline...")
    try:
        run_modeling()
        logger.info("✓ Modeling complete")
    except Exception as e:
        logger.error(f"✗ Modeling failed: {e}")
        sys.exit(1)
    
    # Step 3: Diagnostics
    logger.info("Step 3: Running collinearity diagnostics...")
    try:
        run_diagnostics()
        logger.info("✓ Diagnostics complete")
    except Exception as e:
        logger.error(f"✗ Diagnostics failed: {e}")
        sys.exit(1)
    
    # Step 4: Robustness Analysis
    logger.info("Step 4: Running robustness analysis...")
    try:
        run_robustness()
        logger.info("✓ Robustness analysis complete")
    except Exception as e:
        logger.error(f"✗ Robustness analysis failed: {e}")
        sys.exit(1)
    
    # Step 5: Visualizations
    logger.info("Step 5: Generating visualizations...")
    try:
        run_visualizations()
        logger.info("✓ Visualizations complete")
    except Exception as e:
        logger.error(f"✗ Visualizations failed: {e}")
        sys.exit(1)
    
    # Step 6: Final Report
    logger.info("Step 6: Generating final report...")
    try:
        run_final_report()
        logger.info("✓ Final report complete")
    except Exception as e:
        logger.error(f"✗ Final report failed: {e}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Pipeline execution completed successfully!")
    logger.info("Results are available in data/results/")

if __name__ == "__main__":
    main()
