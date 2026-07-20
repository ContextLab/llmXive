import os
import sys
import logging
from pathlib import Path
import json
from utils import setup_logging, get_logger, set_deterministic_seed

# Ensure project root is in path for imports if run as script
if __name__ == "__main__" and __package__ is None:
    root_dir = Path(__file__).resolve().parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from ingest import main as ingest_main
from embeddings import main as embeddings_main
from similarity import main as similarity_main
from similarity_save import main as similarity_save_main
from viz import main as viz_main
from regression import main as regression_main

def log_section_header(logger: logging.Logger, title: str):
    logger.info("=" * 60)
    logger.info(f"  {title}")
    logger.info("=" * 60)

def log_section_footer(logger: logging.Logger, status: str):
    logger.info(f"  Status: {status}")
    logger.info("=" * 60)
    logger.info("")

def validate_outputs(logger: logging.Logger) -> bool:
    """
    Validates that all expected output files from the pipeline exist.
    Returns True if all checks pass, False otherwise.
    """
    base_path = Path("data/derived")
    embeddings_path = Path("yearly_embeddings")
    figures_path = Path("figures")

    required_files = [
        base_path / "metadata_mpd.parquet",
        base_path / "low_coverage_years.json",
        base_path / "excluded_years.json",
        base_path / "yearly_similarity.csv",
        base_path / "regression_results.json",
        base_path / "cooks_distance_report.csv",
        base_path / "sensitivity_report.csv",
    ]

    required_dirs = [
        embeddings_path,
        figures_path,
    ]

    required_figures = [
        figures_path / "similarity_trend.png",
        figures_path / "genre_similarity_heatmap.html",
    ]

    all_valid = True

    # Check derived files
    for f in required_files:
        if not f.exists():
            logger.error(f"MISSING: {f}")
            all_valid = False
        else:
            logger.info(f"FOUND: {f}")

    # Check directories
    for d in required_dirs:
        if not d.exists():
            logger.error(f"MISSING DIR: {d}")
            all_valid = False
        else:
            logger.info(f"FOUND DIR: {d}")

    # Check figures
    for f in required_figures:
        if not f.exists():
            logger.error(f"MISSING FIGURE: {f}")
            all_valid = False
        else:
            logger.info(f"FOUND FIGURE: {f}")

    # Check embeddings directory contents
    if embeddings_path.exists():
        npy_files = list(embeddings_path.glob("*.npy"))
        if len(npy_files) == 0:
            logger.error(f"MISSING EMBEDDINGS: No .npy files in {embeddings_path}")
            all_valid = False
        else:
            logger.info(f"FOUND EMBEDDINGS: {len(npy_files)} files in {embeddings_path}")
    else:
        all_valid = False

    return all_valid

def main():
    """
    Executes the full pipeline stages and validates outputs.
    This script acts as the quickstart validation runner.
    """
    logger = setup_logging("pipeline_log.txt")
    set_deterministic_seed(42)

    logger.info("Starting Quickstart Validation Pipeline...")

    try:
        # Stage 1: Ingestion
        log_section_header(logger, "STAGE 1: Ingestion (T010-T012)")
        # Note: ingest_main handles its own logic, including MPD download and MB fetch
        # We assume the previous tasks (T010-T012) have been implemented to run main()
        # If run in isolation, this might fail if data is missing, but the task
        # implies validating the end-to-end flow.
        try:
            ingest_main()
            log_section_footer(logger, "SUCCESS")
        except Exception as e:
            logger.error(f"INGESTION FAILED: {e}")
            log_section_footer(logger, "FAILED")
            # Depending on strictness, we might stop here.
            # For validation, we note the failure but continue to check what exists.

        # Stage 2: Embeddings
        log_section_header(logger, "STAGE 2: Embeddings (T013-T014)")
        try:
            embeddings_main()
            log_section_footer(logger, "SUCCESS")
        except Exception as e:
            logger.error(f"EMBEDDINGS FAILED: {e}")
            log_section_footer(logger, "FAILED")

        # Stage 3: Similarity
        log_section_header(logger, "STAGE 3: Similarity (T019-T020)")
        try:
            similarity_main()
            similarity_save_main() # Ensure save is called if split
            log_section_footer(logger, "SUCCESS")
        except Exception as e:
            logger.error(f"SIMILARITY FAILED: {e}")
            log_section_footer(logger, "FAILED")

        # Stage 4: Visualization
        log_section_header(logger, "STAGE 4: Visualization (T021-T022)")
        try:
            viz_main()
            log_section_footer(logger, "SUCCESS")
        except Exception as e:
            logger.error(f"VISUALIZATION FAILED: {e}")
            log_section_footer(logger, "FAILED")

        # Stage 5: Regression
        log_section_header(logger, "STAGE 5: Regression (T026-T036b)")
        try:
            regression_main()
            log_section_footer(logger, "SUCCESS")
        except Exception as e:
            logger.error(f"REGRESSION FAILED: {e}")
            log_section_footer(logger, "FAILED")

        # Validation
        log_section_header(logger, "VALIDATION: Checking Outputs")
        is_valid = validate_outputs(logger)

        if is_valid:
            logger.info("VALIDATION PASSED: All required artifacts generated.")
            return 0
        else:
            logger.error("VALIDATION FAILED: Missing required artifacts.")
            return 1

    except Exception as e:
        logger.critical(f"Pipeline crashed unexpectedly: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
