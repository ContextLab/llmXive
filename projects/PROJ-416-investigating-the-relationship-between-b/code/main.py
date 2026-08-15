import argparse
import logging
import sys
from pathlib import Path

from code.config import Config
from code.utils.logging import setup_logging
from code.data.download import run_download
from code.data.validate import run_validation
from code.data.preprocess import run_preprocessing
from code.data.save_metadata import run_save_metadata
from code.analysis.network import run_analysis as run_network_analysis
from code.analysis.validate_metrics import run_validation as run_metrics_validation
from code.analysis.stats import run_analysis as run_stats_analysis
from code.analysis.report import run_analysis as run_report_generation
from code.analysis.save_stats_results import run_save_stats_results
from code.scripts.run_quickstart_validation import main as run_quickstart_validation

def parse_args():
    parser = argparse.ArgumentParser(description="Brain Network Dynamics Pipeline")
    parser.add_argument("--stage", type=str, required=True,
                        choices=["download", "validate", "preprocess", "save_metadata", 
                                 "compute", "validate_metrics", "analyze", "report", 
                                 "save_stats", "quickstart"],
                        help="Pipeline stage to execute")
    parser.add_argument("--config", type=str, default="code/.env",
                        help="Path to configuration file")
    return parser.parse_args()

def run_stage(stage: str):
    logging.info(f"Executing stage: {stage}")
    Config.ensure_directories()
    
    if stage == "download":
        run_download()
    elif stage == "validate":
        run_validation()
    elif stage == "preprocess":
        run_preprocessing()
    elif stage == "save_metadata":
        run_save_metadata()
    elif stage == "compute":
        run_network_analysis()
    elif stage == "validate_metrics":
        run_metrics_validation()
    elif stage == "analyze":
        run_stats_analysis()
    elif stage == "report":
        run_report_generation()
    elif stage == "save_stats":
        run_save_stats_results()
    elif stage == "quickstart":
        run_quickstart_validation()
    
    logging.info(f"Stage {stage} completed successfully.")

def main():
    args = parse_args()
    setup_logging()
    run_stage(args.stage)

if __name__ == "__main__":
    main()