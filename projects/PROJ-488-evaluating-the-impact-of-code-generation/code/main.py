"""
Main entry point for the full end-to-end validation pipeline.
Executes all phases: Data Ingestion, Preprocessing, Metric Extraction,
Statistical Analysis, Visualization, and Reporting.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# Import project modules
from logging_config import setup_logger, get_logger
from state_tracker import update_state_timestamp, load_state_file, save_state_file
from data_ingestion import main as data_ingestion_main
from data_filtering import main as data_filtering_main
from length_filtering import main as length_filtering_main
from ast_validation import main as ast_validation_main
from snippet_counter import main as snippet_counter_main
from metric_extraction import main as metric_extraction_main
from metric_validation import main as metric_validation_main
from metric_aggregation import main as metric_aggregation_main
from statistical_analysis import main as statistical_analysis_main
from run_bh_correction import main as bh_correction_main
from visualization import main as visualization_main
from guideline_generator import main as guideline_generator_main
from sensitivity_analysis import main as sensitivity_analysis_main
from pilot_study import main as pilot_study_main
from cpu_guard import run_cpu_guard
from artifact_hash_tracker import track_all_major_outputs

def setup_logging():
    """Configure logging for the main pipeline."""
    log_dir = Path("results")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pipeline_validation.log"
    logger = setup_logger("pipeline", log_file=log_file, level=logging.INFO)
    return logger

def run_cpu_guard_check():
    """Verify CPU-only execution before heavy lifting."""
    logger = get_logger("pipeline")
    logger.info("Running CPU-only execution guard...")
    try:
        run_cpu_guard()
        logger.info("CPU guard passed.")
        return True
    except Exception as e:
        logger.error(f"CPU guard failed: {e}")
        return False

def run_pipeline():
    """Execute the full validation pipeline."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Starting Full End-to-End Validation Pipeline")
    logger.info("=" * 60)

    success = True

    # 1. CPU Guard
    if not run_cpu_guard_check():
        logger.error("Pipeline aborted due to CPU guard failure.")
        return False

    try:
        # 2. Data Ingestion
        logger.info("Phase 1: Data Ingestion")
        data_ingestion_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Data ingestion failed with code {e.code}")
            success = False
    except Exception as e:
        logger.error(f"Data ingestion error: {e}")
        success = False

    if not success:
        return success

    try:
        # 3. Data Filtering & Length
        logger.info("Phase 2: Data Filtering & Length Balancing")
        data_filtering_main()
        length_filtering_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Data filtering failed with code {e.code}")
            success = False
    except Exception as e:
        logger.error(f"Data filtering error: {e}")
        success = False

    if not success:
        return success

    try:
        # 4. AST Validation & Counting
        logger.info("Phase 3: AST Validation & Snippet Counting")
        ast_validation_main()
        snippet_counter_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Validation failed with code {e.code}")
            success = False
    except Exception as e:
        logger.error(f"Validation error: {e}")
        success = False

    if not success:
        return success

    try:
        # 5. Metric Extraction
        logger.info("Phase 4: Metric Extraction")
        metric_extraction_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Metric extraction failed with code {e.code}")
            success = False
    except Exception as e:
        logger.error(f"Metric extraction error: {e}")
        success = False

    if not success:
        return success

    try:
        # 6. Metric Validation & Aggregation
        logger.info("Phase 5: Metric Validation & Aggregation")
        metric_validation_main()
        metric_aggregation_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Metric aggregation failed with code {e.code}")
            success = False
    except Exception as e:
        logger.error(f"Metric aggregation error: {e}")
        success = False

    if not success:
        return success

    try:
        # 7. Statistical Analysis
        logger.info("Phase 6: Statistical Analysis")
        statistical_analysis_main()
        bh_correction_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Statistical analysis failed with code {e.code}")
            success = False
    except Exception as e:
        logger.error(f"Statistical analysis error: {e}")
        success = False

    if not success:
        return success

    try:
        # 8. Visualization
        logger.info("Phase 7: Visualization")
        visualization_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Visualization failed with code {e.code}")
            success = False
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        success = False

    if not success:
        return success

    try:
        # 9. Guidelines & Sensitivity
        logger.info("Phase 8: Guidelines & Sensitivity Analysis")
        guideline_generator_main()
        sensitivity_analysis_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Guideline generation failed with code {e.code}")
            success = False
    except Exception as e:
        logger.error(f"Guideline generation error: {e}")
        success = False

    if not success:
        return success

    try:
        # 10. Pilot Study
        logger.info("Phase 9: Pilot Study")
        pilot_study_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Pilot study failed with code {e.code}")
            success = False
    except Exception as e:
        logger.error(f"Pilot study error: {e}")
        success = False

    if not success:
        return success

    # Finalize
    logger.info("Pipeline completed successfully.")
    update_state_timestamp()
    track_all_major_outputs()
    
    logger.info("=" * 60)
    logger.info("Validation Complete. Check results/pipeline_validation.log")
    logger.info("=" * 60)
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Run full end-to-end validation pipeline.")
    parser.add_argument("--run-all", action="store_true", help="Execute the full pipeline.")
    args = parser.parse_args()

    if args.run_all:
        success = run_pipeline()
        sys.exit(0 if success else 1)
    else:
        print("Usage: python code/main.py --run-all")
        sys.exit(1)

if __name__ == "__main__":
    main()
