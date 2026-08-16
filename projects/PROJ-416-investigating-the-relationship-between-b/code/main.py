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
from code.analysis.report import run_analysis as run_report_analysis
from code.analysis.save_stats_results import run_save_stats_results

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestrator")
    parser.add_argument(
        "--stage",
        required=True,
        choices=[
            "download",
            "validate",
            "preprocess",
            "save_metadata",
            "compute",
            "analyze",
            "report",
            "save_stats",
            "all",
        ],
        help="Pipeline stage to execute",
    )
    return parser.parse_args()

def run_stage(stage: str, config: Config):
    logger = logging.getLogger(__name__)
    logger.info(f"Starting stage: {stage}")

    try:
        if stage == "download":
            run_download(config)
        elif stage == "validate":
            run_validation(config)
        elif stage == "preprocess":
            run_preprocessing(config)
        elif stage == "save_metadata":
            run_save_metadata(config)
        elif stage == "compute":
            run_network_analysis(config)
        elif stage == "analyze":
            run_stats_analysis(config)
        elif stage == "save_stats":
            run_save_stats_results(config)
        elif stage == "report":
            run_report_analysis(config)
        elif stage == "all":
            # Execute full pipeline sequentially
            run_download(config)
            run_validation(config)
            run_preprocessing(config)
            run_save_metadata(config)
            run_network_analysis(config)
            run_stats_analysis(config)
            run_save_stats_results(config)
            run_report_analysis(config)
        else:
            logger.error(f"Unknown stage: {stage}")
            sys.exit(1)

        logger.info(f"Stage {stage} completed successfully.")
    except Exception as e:
        logger.error(f"Stage {stage} failed with error: {e}")
        raise

def main():
    args = parse_args()
    config = Config()
    setup_logging(config)
    run_stage(args.stage, config)

if __name__ == "__main__":
    main()
