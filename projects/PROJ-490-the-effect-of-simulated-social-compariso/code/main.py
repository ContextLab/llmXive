"""
Main entry point for the llmXive pipeline.

Supports actions: download, preprocess, analyze, validate
"""
import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import json
from datetime import datetime

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from utils.logger import get_logger, log_execution_start, log_execution_end
from data.config import get_config
from data.download import main as download_main, load_or_generate_data
from data.preprocess import run_preprocess
from data.validate_raw import run_validation as validate_raw
from data.validate_imputed import run_validation as validate_imputed
from analysis.regression import run_regression_analysis
from analysis.bootstrap import run_bootstrap_analysis
from analysis.sensitivity import run_sensitivity_analysis
from analysis.report_generator import run_report_generation
from analysis.export_results import run_export
from data.state_manager import update_project_state

logger = get_logger(__name__)

def action_download():
    """Download or generate data."""
    log_execution_start(logger, "download")
    try:
        df, data_type = download_main()
        log_execution_end(logger, "download", status="success")
        return df, data_type
    except Exception as e:
        logger.error(f"Download failed: {e}")
        log_execution_end(logger, "download", status="failed")
        raise

def action_preprocess():
    """Preprocess data (imputation, validation)."""
    log_execution_start(logger, "preprocess")
    try:
        # Run raw validation
        validate_raw()
        
        # Run preprocessing (imputation)
        df = run_preprocess()
        
        # Run imputed validation
        validate_imputed()
        
        log_execution_end(logger, "preprocess", status="success")
        return df
    except Exception as e:
        logger.error(f"Preprocess failed: {e}")
        log_execution_end(logger, "preprocess", status="failed")
        raise

def action_analyze():
    """Run full analysis pipeline."""
    log_execution_start(logger, "analyze")
    try:
        # Regression
        run_regression_analysis()
        
        # Bootstrap
        run_bootstrap_analysis()
        
        # Sensitivity
        run_sensitivity_analysis()
        
        # Export results
        run_export()
        
        # Generate report
        run_report_generation()
        
        log_execution_end(logger, "analyze", status="success")
    except Exception as e:
        logger.error(f"Analyze failed: {e}")
        log_execution_end(logger, "analyze", status="failed")
        raise

def action_validate():
    """Run validation checks."""
    log_execution_start(logger, "validate")
    try:
        validate_raw()
        validate_imputed()
        log_execution_end(logger, "validate", status="success")
    except Exception as e:
        logger.error(f"Validate failed: {e}")
        log_execution_end(logger, "validate", status="failed")
        raise

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Runner")
    parser.add_argument("--action", type=str, required=True, 
                      choices=["download", "preprocess", "analyze", "validate"],
                      help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "download":
        action_download()
    elif args.action == "preprocess":
        action_preprocess()
    elif args.action == "analyze":
        action_analyze()
    elif args.action == "validate":
        action_validate()

if __name__ == "__main__":
    main()
