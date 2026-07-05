"""
Main Orchestrator for the Chemo-Biomarker Discovery Pipeline.

This script serves as the entry point for the entire research pipeline.
It initializes configuration, sets up logging, and executes the phases
defined in the project plan.
"""
import sys
import argparse
import json
from pathlib import Path

# Import project components
# Note: Using relative imports assuming execution via `python -m` or proper PYTHONPATH
# Fallback to absolute imports if executed directly in code/src
try:
    from .config import get_config
    from .utils import setup_logging, watchdog, ensure_path_exists
    from .data_acquisition import run_acquisition
    from .preprocessing import run_preprocessing
    from .differential_expression import run_differential_expression
    from .meta_analysis import run_meta_analysis
    from .modeling import run_modeling
    from .validation import run_validation
except ImportError:
    # Fallback for direct execution if PYTHONPATH is not set correctly
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.config import get_config
    from src.utils import setup_logging, watchdog, ensure_path_exists
    from src.data_acquisition import run_acquisition
    from src.preprocessing import run_preprocessing
    from src.differential_expression import run_differential_expression
    from src.meta_analysis import run_meta_analysis
    from src.modeling import run_modeling
    from src.validation import run_validation

def main():
    parser = argparse.ArgumentParser(description="Chemo-Biomarker Discovery Pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--phase",
        type=str,
        choices=["all", "acquisition", "preprocessing", "de", "meta", "modeling", "validation"],
        default="all",
        help="Specific phase to run (default: all)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    # Initialize Configuration
    config = get_config(args.config)
    
    # Ensure output directories exist
    for dir_path in [
        config.get("paths", {}).get("raw_data"),
        config.get("paths", {}).get("processed_data"),
        config.get("paths", {}).get("results"),
        config.get("paths", {}).get("figures"),
    ]:
        if dir_path:
            ensure_path_exists(dir_path)

    # Setup Logging
    logger = setup_logging(
        level="DEBUG" if args.debug else "INFO",
        log_file=config.get("paths", {}).get("log_file") or "results/pipeline.log"
    )
    logger.info("Starting Chemo-Biomarker Discovery Pipeline")
    logger.info(f"Configuration loaded from: {args.config}")

    try:
        # Phase 2: Data Acquisition (US1)
        if args.phase in ["all", "acquisition"]:
            logger.info("Phase 1: Data Acquisition")
            # Placeholder for actual acquisition logic
            # run_acquisition(config, logger)
            logger.warning("Data Acquisition phase skipped (T012-T019 not implemented yet)")

        # Phase 3: Preprocessing (US1)
        if args.phase in ["all", "preprocessing"]:
            logger.info("Phase 2: Preprocessing")
            # Placeholder for actual preprocessing logic
            # run_preprocessing(config, logger)
            logger.warning("Preprocessing phase skipped (T015-T020 not implemented yet)")

        # Phase 4: Differential Expression (US2)
        if args.phase in ["all", "de"]:
            logger.info("Phase 3: Differential Expression")
            # Placeholder for DE logic
            # run_differential_expression(config, logger)
            logger.warning("Differential Expression phase skipped (T023-T024 not implemented yet)")

        # Phase 5: Meta Analysis (US2)
        if args.phase in ["all", "meta"]:
            logger.info("Phase 4: Meta Analysis")
            # Placeholder for Meta Analysis logic
            # run_meta_analysis(config, logger)
            logger.warning("Meta Analysis phase skipped (T025-T028 not implemented yet)")

        # Phase 6: Modeling (US3)
        if args.phase in ["all", "modeling"]:
            logger.info("Phase 5: Modeling")
            # Placeholder for Modeling logic
            # run_modeling(config, logger)
            logger.warning("Modeling phase skipped (T031-T033 not implemented yet)")

        # Phase 7: Validation (US3)
        if args.phase in ["all", "validation"]:
            logger.info("Phase 6: Validation")
            # Placeholder for Validation logic
            # run_validation(config, logger)
            logger.warning("Validation phase skipped (T034-T040 not implemented yet)")

        logger.info("Pipeline execution completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()