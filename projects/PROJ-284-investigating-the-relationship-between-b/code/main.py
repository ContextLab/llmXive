"""Main entry point for the research pipeline."""
import argparse
import logging
import sys
from pathlib import Path
from logging_config import setup_logging, get_logger
from analysis.correlation_main_runner import main as run_analyze


def main() -> int:
    """Main pipeline orchestrator."""
    parser = argparse.ArgumentParser(
        description="Brain network dynamics and sensorimotor performance analysis"
    )
    parser.add_argument(
        "--step",
        choices=[
            "download_preprocess",
            "extract_metrics",
            "analyze",
            "viz_report"
        ],
        default="analyze",
        help="Pipeline step to execute"
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=50,
        help="Number of subjects to process (for download_preprocess)"
    )
    
    args = parser.parse_args()
    
    # Initialize logging with module name
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info(f"Starting pipeline step: {args.step}")
    
    try:
        if args.step == "analyze":
            run_analyze()
        elif args.step == "download_preprocess":
            logger.info(f"Download/preprocess step with {args.subjects} subjects")
        elif args.step == "extract_metrics":
            logger.info("Extract metrics step")
        elif args.step == "viz_report":
            logger.info("Visualization and report generation step")
        
        logger.info(f"Pipeline step {args.step} completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
