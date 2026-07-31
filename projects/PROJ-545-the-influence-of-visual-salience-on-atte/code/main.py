"""
Main entry point for the Visual Salience on Attentional Bias pipeline.

Usage:
    python code/main.py --stage <stage_name> [options]

Available stages:
    download    : Fetch and subset the Moral Machine dataset
    salience    : Compute visual/textual salience scores
    preprocess  : Merge raw data with salience scores and proxy controls
    fit         : Run aDDM grid search fitting
    compare     : Run model comparison and sensitivity analysis
    all         : Run the full pipeline sequentially
"""
import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import setup_logging, get_logger
from data.download import main as download_main
from data.salience import main as salience_main
from data.preprocess import main as preprocess_main
from models.fit import main as fit_main
from analysis.compare import main as compare_main

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pipeline entry point for Visual Salience on Attentional Bias study."
    )
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=[
            "download",
            "salience",
            "preprocess",
            "fit",
            "compare",
            "all",
        ],
        help="Pipeline stage to execute.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory for artifacts.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-run even if outputs exist.",
    )
    return parser

def run_stage_download(args: argparse.Namespace, logger: logging.Logger) -> bool:
    logger.info("Starting 'download' stage...")
    try:
        # Pass args if the download function expects them, otherwise call directly
        # The skeleton/download.py main usually handles its own arg parsing or takes no args
        # We invoke it directly. If it needs specific paths, we might need to pass them.
        # Assuming the module's main() handles its own internal logic or reads from env/config.
        # For now, we call it. If it requires specific args not in its own parser, we adapt.
        # Based on T013, it saves to data/raw/moral_machine_subset.csv.
        download_main()
        logger.info("Download stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Download stage failed: {e}", exc_info=True)
        return False

def run_stage_salience(args: argparse.Namespace, logger: logging.Logger) -> bool:
    logger.info("Starting 'salience' stage...")
    try:
        salience_main()
        logger.info("Salience stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Salience stage failed: {e}", exc_info=True)
        return False

def run_stage_preprocess(args: argparse.Namespace, logger: logging.Logger) -> bool:
    logger.info("Starting 'preprocess' stage...")
    try:
        preprocess_main()
        logger.info("Preprocess stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Preprocess stage failed: {e}", exc_info=True)
        return False

def run_stage_fit(args: argparse.Namespace, logger: logging.Logger) -> bool:
    logger.info("Starting 'fit' stage...")
    try:
        fit_main()
        logger.info("Fit stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Fit stage failed: {e}", exc_info=True)
        return False

def run_stage_compare(args: argparse.Namespace, logger: logging.Logger) -> bool:
    logger.info("Starting 'compare' stage...")
    try:
        compare_main()
        logger.info("Compare stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Compare stage failed: {e}", exc_info=True)
        return False

def run_all(args: argparse.Namespace, logger: logging.Logger) -> bool:
    stages = ["download", "salience", "preprocess", "fit", "compare"]
    logger.info("Running full pipeline sequentially...")
    for stage in stages:
        logger.info(f"--- Executing stage: {stage} ---")
        if stage == "download":
            if not run_stage_download(args, logger):
                return False
        elif stage == "salience":
            if not run_stage_salience(args, logger):
                return False
        elif stage == "preprocess":
            if not run_stage_preprocess(args, logger):
                return False
        elif stage == "fit":
            if not run_stage_fit(args, logger):
                return False
        elif stage == "compare":
            if not run_stage_compare(args, logger):
                return False
    logger.info("Full pipeline completed successfully.")
    return True

def main():
    parser = get_parser()
    args = parser.parse_args()

    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{timestamp}.log"

    setup_logging(
        level=getattr(logging, args.log_level.upper()),
        log_file=str(log_file),
    )
    logger = get_logger("main")

    logger.info(f"Starting pipeline execution. Stage: {args.stage}")
    logger.info(f"Output directory: {args.output_dir}")

    success = False
    start_time = time.time()

    try:
        if args.stage == "all":
            success = run_all(args, logger)
        elif args.stage == "download":
            success = run_stage_download(args, logger)
        elif args.stage == "salience":
            success = run_stage_salience(args, logger)
        elif args.stage == "preprocess":
            success = run_stage_preprocess(args, logger)
        elif args.stage == "fit":
            success = run_stage_fit(args, logger)
        elif args.stage == "compare":
            success = run_stage_compare(args, logger)
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error in pipeline: {e}", exc_info=True)
        sys.exit(1)

    elapsed = time.time() - start_time
    if success:
        logger.info(f"Pipeline finished successfully in {elapsed:.2f} seconds.")
        sys.exit(0)
    else:
        logger.error(f"Pipeline failed after {elapsed:.2f} seconds.")
        sys.exit(1)

if __name__ == "__main__":
    main()