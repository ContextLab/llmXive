"""
Pipeline Execution Orchestrator for PROJ-294.

This script serves as the entry point for the automated research pipeline.
It enforces the execution order defined in the project plan, specifically
starting with the Citation Validation Gate (T007a) before proceeding to
data acquisition and analysis tasks.

Execution Order:
1. T007b Gate: Run validate_citations.py. Abort if non-zero.
2. T008/T009: Ensure directory structures (via setup scripts).
3. T010: Download Data.
4. T011-T017: Generate and Analyze Metrics.
5. T018-T046: Statistical Analysis and Reporting.

Usage:
    python code/run_pipeline.py
"""

import os
import sys
import subprocess
import logging

# Import logging setup from utils to ensure consistent formatting
from utils import setup_logging, get_logger, set_task_id, get_task_id

# Project root relative to this script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
STATE_DIR = os.path.join(PROJECT_ROOT, "state")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

def ensure_directories():
    """
    Ensures all required directory structures exist before pipeline execution.
    Corresponds to T008 and T009.
    """
    logger = logging.getLogger(__name__)
    directories = [
        os.path.join(DATA_DIR, "raw"),
        os.path.join(DATA_DIR, "generated"),
        os.path.join(DATA_DIR, "analysis"),
        os.path.join(RESULTS_DIR, "figures"),
        STATE_DIR
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
        else:
            logger.debug(f"Directory exists: {directory}")

def run_pipeline_stage(script_name: str, args: list = None) -> int:
    """
    Executes a specific pipeline stage script.

    Args:
        script_name: Name of the python script in the code/ directory.
        args: Optional list of command-line arguments.

    Returns:
        Exit code of the subprocess.
    """
    logger = logging.getLogger(__name__)
    script_path = os.path.join(CODE_DIR, script_name)

    if not os.path.exists(script_path):
        logger.error(f"Pipeline script not found: {script_path}")
        return 1

    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    logger.info(f"Executing stage: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=False,  # We handle exit codes manually
            capture_output=False,  # Stream output to main log
            text=True
        )
        return result.returncode
    except Exception as e:
        logger.critical(f"Failed to execute stage {script_name}: {e}")
        return 1

def main():
    """
    Main pipeline orchestration logic.
    """
    # Initialize logging
    set_task_id("PIPELINE-MAIN")
    logger = setup_logging()
    logger.info("Starting Pipeline Execution for PROJ-294")
    logger.info(f"Project Root: {PROJECT_ROOT}")

    # Step 0: Ensure Directory Structure (T008, T009)
    logger.info("Verifying directory structure...")
    ensure_directories()

    # Step 1: T007b - Pipeline Gate (Citation Validation)
    # Constraint: If validate_citations.py returns non-zero, abort immediately.
    logger.info("Executing Pipeline Gate: Citation Validation (T007a/T007b)...")
    gate_exit_code = run_pipeline_stage("validate_citations.py")

    if gate_exit_code != 0:
        logger.critical(f"Pipeline Gate FAILED (Exit Code: {gate_exit_code}). Aborting pipeline.")
        logger.critical("Citation validation failed. Please check state/citations.yaml and fix issues.")
        sys.exit(1)

    logger.info("Pipeline Gate PASSED. Proceeding to data acquisition.")

    # Step 2: Data Download (T010)
    logger.info("Stage 2: Downloading Data (T010)...")
    exit_code = run_pipeline_stage("download_data.py")
    if exit_code != 0:
        logger.error(f"Data download failed with code {exit_code}. Stopping.")
        sys.exit(exit_code)

    # Step 3: Code Generation (T012, T013)
    logger.info("Stage 3: Generating Code (T012)...")
    exit_code = run_pipeline_stage("generate_code.py")
    if exit_code != 0:
        logger.error(f"Code generation failed with code {exit_code}. Stopping.")
        sys.exit(exit_code)

    # Step 4: Metrics Analysis (T014a, T014b, T015, T042, T017)
    logger.info("Stage 4: Analyzing Metrics (T014-T017)...")
    exit_code = run_pipeline_stage("analyze_metrics.py")
    if exit_code != 0:
        logger.error(f"Metrics analysis failed with code {exit_code}. Stopping.")
        sys.exit(exit_code)

    # Step 5: Sensitivity Analysis Merge (T041a-T041c)
    # Note: Assuming sensitivity generation was handled in generate_code or separate step.
    # This stage merges if new data exists.
    logger.info("Stage 5: Merging Sensitivity Metrics (T041c)...")
    # If merge_sensitivity_metrics.py exists and is needed here, run it.
    # Based on tasks.md, T041c is a distinct step after T017.
    merge_script = os.path.join(CODE_DIR, "merge_sensitivity_metrics.py")
    if os.path.exists(merge_script):
        exit_code = run_pipeline_stage("merge_sensitivity_metrics.py")
        if exit_code != 0:
            logger.warning(f"Sensitivity merge failed with code {exit_code}. Continuing...")
            # Not a hard stop for the whole pipeline, but a warning.
    else:
        logger.debug("Merge script not found or not needed.")

    # Step 6: Statistical Analysis (T020-T024, T040, T045, T046)
    logger.info("Stage 6: Running Statistical Tests (T020-T024, T040, T045, T046)...")
    exit_code = run_pipeline_stage("statistical_tests.py")
    if exit_code != 0:
        logger.error(f"Statistical analysis failed with code {exit_code}. Stopping.")
        sys.exit(exit_code)

    # Step 7: Report Generation (T030-T032)
    logger.info("Stage 7: Generating Report (T030-T032)...")
    exit_code = run_pipeline_stage("report_generator.py")
    if exit_code != 0:
        logger.error(f"Report generation failed with code {exit_code}. Stopping.")
        sys.exit(exit_code)

    logger.info("Pipeline Execution Completed Successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()