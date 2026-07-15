import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Local imports from project structure
from logging_config import setup_logger, get_logger
from cpu_guard import run_cpu_guard
from data_ingestion import main as ingest_main
from metric_extraction import main as metric_main
from statistical_analysis import main as stat_main
from visualization import main as viz_main
from guideline_generator import main as guide_main
from sensitivity_analysis import main as sens_main
from pilot_study import main as pilot_main
from run_bh_correction import main as bh_main
from cliff_delta_analysis import main as cliff_main
from state_tracker import update_state_after_pipeline_stage, load_state_file, save_state_file

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
LOG_FILE = RESULTS_DIR / "pipeline_validation.log"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"

def setup_logging():
    """Configure logging to both console and the validation log file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(
        name="pipeline_validation",
        log_file=str(LOG_FILE),
        level=logging.INFO
    )
    return logger

def run_cpu_guard_check(logger):
    """Verify CPU-only execution constraints before proceeding."""
    logger.info("Running CPU guard check...")
    try:
        run_cpu_guard()
        logger.info("CPU guard check passed.")
        return True
    except Exception as e:
        logger.error(f"CPU guard check failed: {e}")
        return False

def run_pipeline(logger):
    """Execute the full end-to-end pipeline stages."""
    stages = [
        ("Data Ingestion", ingest_main),
        ("Metric Extraction", metric_main),
        ("Statistical Analysis", stat_main),
        ("Mann-Whitney U & BH Correction", bh_main),
        ("Cliff's Delta Analysis", cliff_main),
        ("Visualization", viz_main),
        ("Guideline Generation", guide_main),
        ("Sensitivity Analysis", sens_main),
        ("Pilot Study", pilot_main),
    ]

    results = {}
    success = True

    for stage_name, stage_func in stages:
        logger.info(f"--- Starting Stage: {stage_name} ---")
        try:
            # We assume each stage function handles its own logging and state updates
            # We call it with sys.argv if it expects args, but for validation we run it directly
            # If the stage function expects arguments, we might need to parse them.
            # However, standard pattern in this project is `main()` handling sys.argv or no args.
            stage_func()
            logger.info(f"--- Stage {stage_name} completed successfully. ---")
            results[stage_name] = "PASS"
        except SystemExit as e:
            if e.code == 0:
                results[stage_name] = "PASS"
            else:
                results[stage_name] = f"FAIL (exit code {e.code})"
                success = False
                logger.error(f"Stage {stage_name} exited with code {e.code}")
        except Exception as e:
            results[stage_name] = f"FAIL ({str(e)})"
            success = False
            logger.error(f"Stage {stage_name} failed with exception: {e}", exc_info=True)

    return success, results

def log_validation_results(logger, success, results):
    """Log the final validation summary to the log file and console."""
    logger.info("=" * 50)
    logger.info("PIPELINE VALIDATION SUMMARY")
    logger.info("=" * 50)
    
    for stage, status in results.items():
        status_icon = "✓" if status == "PASS" else "✗"
        logger.info(f"{status_icon} {stage}: {status}")
    
    logger.info("=" * 50)
    if success:
        logger.info("OVERALL RESULT: ALL TESTS PASSED")
    else:
        logger.info("OVERALL RESULT: SOME TESTS FAILED")
    logger.info("=" * 50)

    # Update state file with validation result
    try:
        state = load_state_file(STATE_FILE)
        if "pipeline_validation" not in state:
            state["pipeline_validation"] = {}
        
        state["pipeline_validation"]["last_run"] = datetime.now().isoformat()
        state["pipeline_validation"]["overall_status"] = "PASSED" if success else "FAILED"
        state["pipeline_validation"]["stages"] = results
        
        save_state_file(state, STATE_FILE)
        logger.info("State file updated with validation results.")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")

def main():
    """Entry point for the full end-to-end validation script."""
    parser = argparse.ArgumentParser(description="Run full end-to-end validation for PROJ-488")
    parser.add_argument("--run-all", action="store_true", help="Execute the full pipeline validation")
    args = parser.parse_args()

    if not args.run_all:
        print("Usage: python code/main.py --run-all")
        print("This script runs the full pipeline validation and logs results to results/pipeline_validation.log")
        sys.exit(1)

    # Setup logging
    logger = setup_logging()
    logger.info("Starting full end-to-end validation pipeline...")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Log File: {LOG_FILE}")

    # 1. CPU Guard Check
    if not run_cpu_guard_check(logger):
        logger.critical("Aborting due to CPU guard failure.")
        sys.exit(1)

    # 2. Run Pipeline
    success, results = run_pipeline(logger)

    # 3. Log Results
    log_validation_results(logger, success, results)

    # 4. Exit with appropriate code
    if success:
        logger.info("Validation completed successfully.")
        sys.exit(0)
    else:
        logger.critical("Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
