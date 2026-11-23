"""
Main orchestrator for the biomarker discovery pipeline.
Coordinates data acquisition, preprocessing, and downstream analysis stages.
"""
import sys
import argparse
import json
import logging
import time
from pathlib import Path

from .config import get_project_root, ensure_directories
from .utils import setup_logging, check_limits, resource_monitor, ResourceLimitExceeded

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Biomarker Discovery Pipeline Orchestrator"
    )
    parser.add_argument(
        "--mode",
        choices=["real", "test"],
        default="real",
        help="Execution mode: 'real' for production data, 'test' for minimal subset",
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=None,
        help="Limit number of samples per tumor type for testing (optional)",
    )
    parser.add_argument(
        "--stage",
        choices=["all", "acquisition", "preprocessing", "de", "meta", "modeling", "validation"],
        default="all",
        help="Specific stage to execute",
    )
    return parser.parse_args()


def run_acquisition_stage(args):
    """Execute data acquisition and feasibility gate."""
    logger.info("Starting Data Acquisition Stage...")
    from .data_acquisition import main as acquisition_main

    # Prepare args for the acquisition module
    acq_args = argparse.Namespace(
        mode=args.mode,
        subset_size=args.subset_size,
    )
    try:
        acquisition_main(acq_args)
        logger.info("Data Acquisition Stage completed successfully.")
    except Exception as e:
        logger.error(f"Data Acquisition Stage failed: {e}")
        raise


def run_preprocessing_stage(args):
    """Execute preprocessing: filtering, normalization, batch correction, splitting."""
    logger.info("Starting Preprocessing Stage...")
    from .preprocessing import main as preprocessing_main

    try:
        preprocessing_main()
        logger.info("Preprocessing Stage completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing Stage failed: {e}")
        raise


def run_de_stage(args):
    """Execute differential expression analysis."""
    logger.info("Starting Differential Expression Stage...")
    from .differential_expression import main as de_main

    try:
        de_main()
        logger.info("Differential Expression Stage completed successfully.")
    except Exception as e:
        logger.error(f"Differential Expression Stage failed: {e}")
        raise


def run_meta_analysis_stage(args):
    """Execute meta-analysis and gene panel selection."""
    logger.info("Starting Meta-Analysis Stage...")
    from .meta_analysis import main as meta_main

    try:
        meta_main()
        logger.info("Meta-Analysis Stage completed successfully.")
    except Exception as e:
        logger.error(f"Meta-Analysis Stage failed: {e}")
        raise


def run_modeling_stage(args):
    """Execute model training and validation."""
    logger.info("Starting Modeling Stage...")
    # Note: The specific modeling controller is imported dynamically if it exists
    # or we assume the main entry point handles the full flow if split differently.
    # Based on tasks.md, T031-T043 cover modeling.
    try:
        # Placeholder for specific modeling orchestrator if it exists separately
        # Currently, we assume the main flow might handle it or it's called here.
        # If a specific file like modeling.py exists, import it.
        from .model_training import main as modeling_main
        modeling_main()
        logger.info("Modeling Stage completed successfully.")
    except ImportError:
        logger.warning("Modeling module not found or not fully implemented yet.")
    except Exception as e:
        logger.error(f"Modeling Stage failed: {e}")
        raise


def run_validation_stage(args):
    """Execute LOO and external validation."""
    logger.info("Starting Validation Stage...")
    # Placeholder for validation logic
    try:
        # If a specific validation controller exists
        from .validation_controller import main as validation_main
        validation_main()
        logger.info("Validation Stage completed successfully.")
    except ImportError:
        logger.warning("Validation module not found or not fully implemented yet.")
    except Exception as e:
        logger.error(f"Validation Stage failed: {e}")
        raise


def main():
    """Main entry point for the pipeline."""
    args = parse_args()
    root = get_project_root()
    ensure_directories(root)

    # Setup logging
    log_file = root / "results" / "pipeline.log"
    setup_logging(log_file)

    logger.info(f"Pipeline started in mode: {args.mode}")
    logger.info(f"Project root: {root}")

    start_time = time.time()

    try:
        if args.stage in ["all", "acquisition"]:
            run_acquisition_stage(args)

        if args.stage in ["all", "preprocessing"]:
            run_preprocessing_stage(args)

        if args.stage in ["all", "de"]:
            run_de_stage(args)

        if args.stage in ["all", "meta"]:
            run_meta_analysis_stage(args)

        if args.stage in ["all", "modeling"]:
            run_modeling_stage(args)

        if args.stage in ["all", "validation"]:
            run_validation_stage(args)

        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds.")

    except ResourceLimitExceeded as e:
        logger.critical(f"Resource limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()