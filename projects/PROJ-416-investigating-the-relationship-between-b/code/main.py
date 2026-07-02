"""
Main orchestration entry point for the Brain Network Dynamics pipeline.

This script initializes the configuration, validates the environment,
and triggers the appropriate pipeline stages based on command-line arguments.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import Config
from code.utils.logging import setup_logging

def parse_args():
    parser = argparse.ArgumentParser(
        description="Brain Network Dynamics & VR Therapy Response Pipeline"
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=["download", "preprocess", "analyze", "report", "all"],
        default="all",
        help="Pipeline stage to execute.",
    )
    parser.add_argument(
        "--openneuro-id",
        type=str,
        default=None,
        help="OpenNeuro dataset ID (e.g., ds000000).",
    )
    parser.add_argument(
        "--n-subjects",
        type=int,
        default=10,
        help="Number of subjects to process (subset for CI/Feasibility).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup logging
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    logger = setup_logging(
        level=getattr(logging, args.log_level.upper()),
        log_file=log_dir / "pipeline.log",
    )

    logger.info(f"Starting pipeline execution for stage: {args.stage}")
    logger.info(f"Project root: {project_root}")

    # Initialize configuration
    config = Config(
        openneuro_id=args.openneuro_id,
        n_subjects=args.n_subjects,
        stage=args.stage,
    )

    # Validate critical configuration
    if not config.openneuro_id:
        logger.error("Missing verified dataset source (OpenNeuro ID). Halting.")
        logger.error("Please provide --openneuro-id or set OPENNEURO_ID env var.")
        sys.exit(1)

    logger.info(f"Configuration loaded. Targeting dataset: {config.openneuro_id}")

    # Stage dispatch logic
    if args.stage == "download":
        logger.info("Stage 'download' selected. Importing download module...")
        try:
            from code.data.download import run_download
            run_download(config)
        except ImportError as e:
            logger.error(f"Download module not yet implemented: {e}")
            sys.exit(1)
    elif args.stage == "preprocess":
        logger.info("Stage 'preprocess' selected. Importing preprocess module...")
        try:
            from code.data.preprocess import run_preprocessing
            run_preprocessing(config)
        except ImportError as e:
            logger.error(f"Preprocessing module not yet implemented: {e}")
            sys.exit(1)
    elif args.stage == "analyze":
        logger.info("Stage 'analyze' selected. Importing network analysis module...")
        try:
            from code.analysis.network import run_analysis
            run_analysis(config)
        except ImportError as e:
            logger.error(f"Analysis module not yet implemented: {e}")
            sys.exit(1)
    elif args.stage == "report":
        logger.info("Stage 'report' selected. Importing stats/reporting module...")
        try:
            from code.analysis.stats import run_reporting
            run_reporting(config)
        except ImportError as e:
            logger.error(f"Reporting module not yet implemented: {e}")
            sys.exit(1)
    elif args.stage == "all":
        logger.info("Stage 'all' selected. Executing full pipeline...")
        # Execute in order
        stages = ["download", "preprocess", "analyze", "report"]
        for stage in stages:
            logger.info(f"--- Executing stage: {stage} ---")
            if stage == "download":
                try:
                    from code.data.download import run_download
                    run_download(config)
                except ImportError:
                    logger.warning("Download not implemented, skipping.")
            elif stage == "preprocess":
                try:
                    from code.data.preprocess import run_preprocessing
                    run_preprocessing(config)
                except ImportError:
                    logger.warning("Preprocessing not implemented, skipping.")
            elif stage == "analyze":
                try:
                    from code.analysis.network import run_analysis
                    run_analysis(config)
                except ImportError:
                    logger.warning("Analysis not implemented, skipping.")
            elif stage == "report":
                try:
                    from code.analysis.stats import run_reporting
                    run_reporting(config)
                except ImportError:
                    logger.warning("Reporting not implemented, skipping.")
    else:
        logger.error(f"Unknown stage: {args.stage}")
        sys.exit(1)
    
    logger.info(f"Pipeline stage '{args.stage}' executed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
