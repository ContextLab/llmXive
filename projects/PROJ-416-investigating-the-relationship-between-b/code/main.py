"""
Main entry point for the pipeline orchestration.
"""
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
from code.analysis.stats import run_analysis as run_stats_analysis
from code.analysis.save_stats_results import run_save_stats_results
from code.analysis.report import run_analysis as run_report_analysis

def parse_args():
    parser = argparse.ArgumentParser(description="Brain Network Dynamics Pipeline")
    parser.add_argument("--stage", type=str, required=True,
                        choices=["download", "validate", "preprocess", "compute", "analyze", "report", "all"],
                        help="Which stage of the pipeline to run")
    parser.add_argument("--config", type=str, default="code/.env",
                        help="Path to configuration file")
    return parser.parse_args()

def main():
    args = parse_args()
    config = Config()
    
    # Setup logging
    log_file = config.LOGS_DIR / "pipeline.log"
    setup_logging(log_file)
    logger = logging.getLogger(__name__)

    logger.info(f"Starting pipeline stage: {args.stage}")

    try:
        if args.stage == "download":
            run_download(config)
        elif args.stage == "validate":
            run_validation(config)
        elif args.stage == "preprocess":
            run_preprocessing(config)
        elif args.stage == "compute":
            # Run network analysis (US2)
            run_network_analysis(config)
        elif args.stage == "analyze":
            # Run statistical analysis (US3)
            stats_results = run_stats_analysis(config)
            # Save stats results to CSV (T035)
            run_save_stats_results(stats_results, config)
        elif args.stage == "report":
            # Generate final report
            run_report_analysis(config)
        elif args.stage == "all":
            # Run full pipeline
            run_download(config)
            run_validation(config)
            run_preprocessing(config)
            run_network_analysis(config)
            stats_results = run_stats_analysis(config)
            run_save_stats_results(stats_results, config)
            run_report_analysis(config)
        
        logger.info(f"Stage {args.stage} completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed at stage {args.stage}: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()