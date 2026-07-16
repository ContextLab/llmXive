"""
Main entry point for the Personality-AI Feedback analysis pipeline.

This script orchestrates the full pipeline:
1. Data Ingestion (fetch real data or handle synthetic fallback)
2. Statistical Analysis (correlations, regression, BH correction)
3. Visualization and Reporting

Usage:
    python code/main.py
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data_ingestion import run_ingestion_pipeline
from code.analysis import run_analysis_pipeline
from code.visualization import run_visualization_pipeline
from code.report import generate_final_report
from code.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    config = get_config()
    logger.info(f"Starting pipeline with seed: {config['seed']}")
    
    # Phase 1: Data Ingestion
    logger.info("Phase 1: Running data ingestion pipeline...")
    try:
        data_path = run_ingestion_pipeline()
        logger.info(f"Data ingestion complete. Output: {data_path}")
    except SystemExit as e:
        if e.code == 0:
            logger.info("Ingestion completed with synthetic fallback.")
        else:
            logger.error("Ingestion failed. Aborting pipeline.")
            raise
    
    # Phase 2: Statistical Analysis
    logger.info("Phase 2: Running statistical analysis...")
    try:
        stats_path = run_analysis_pipeline()
        logger.info(f"Analysis complete. Output: {stats_path}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise
    
    # Phase 3: Visualization and Reporting
    logger.info("Phase 3: Running visualization and reporting...")
    try:
        report_path, plots_dir = run_visualization_pipeline()
        logger.info(f"Visualizations complete. Plots: {plots_dir}")
        
        final_report = generate_final_report(report_path)
        logger.info(f"Final report generated: {final_report}")
    except Exception as e:
        logger.error(f"Reporting failed: {e}")
        raise
    
    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
