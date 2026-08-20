"""
Full Pipeline Execution Runner for T052.
Orchestrates: Data Gen -> Baseline -> 2D Agent -> Stats -> Reporting.
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.generator import main as generate_data_main
from agents.baseline_3d import main as baseline_3d_main
from agents.agent_2d import main as agent_2d_main
from stats.tests import main as stats_tests_main
from stats.sensitivity import main as sensitivity_main
from stats.report_generator import main as report_gen_main
from utils.budget_check import check_budget, ConfigurationError
from utils.verify_run import verify_integrity, main as verify_run_main
from analysis.assemble_paired_dataset import main as assemble_paired_main
from utils.logging import setup_logging

# Configure logging for the pipeline run
LOG_DIR = "results/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "pipeline_run.log")

def setup_pipeline_logger():
    """Setup a logger that writes to the pipeline log file and stdout."""
    logger = logging.getLogger("pipeline_runner")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers = []

    # File handler
    fh = logging.FileHandler(LOG_FILE, mode='w')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def run_step(step_name, func, *args, **kwargs):
    """Execute a pipeline step with timing and error handling."""
    logger = logging.getLogger("pipeline_runner")
    logger.info(f"--- STARTING STEP: {step_name} ---")
    start_time = time.time()
    try:
        func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"--- COMPLETED STEP: {step_name} in {elapsed:.2f}s ---")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"--- FAILED STEP: {step_name} after {elapsed:.2f}s ---")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def execute_data_generation():
    """Execute T006a/b: Generate the Synthetic SpatialClaw Proxy dataset."""
    # We invoke the generator's main function which handles reading config and writing output
    # The generator is expected to read data/power_config.yaml and output to data/raw/
    generate_data_main()

def execute_baseline():
    """Execute T023b: Run 3D Baseline on the generated dataset."""
    # The baseline expects input from data/raw/synthetic_spatialclaw_v1.json
    # and writes to results/logs/baseline_run.json
    baseline_3d_main()

def execute_agent_2d():
    """Execute T017: Run 2D Agent on the generated dataset."""
    # The agent expects input from data/raw/synthetic_spatialclaw_v1.json
    # and writes multiple run files to results/runs/
    agent_2d_main()

def execute_stats():
    """Execute T029/T031b: Run statistical tests and sensitivity analysis."""
    stats_tests_main()
    sensitivity_main()

def execute_assemble_paired():
    """Execute T047: Assemble the final paired dataset."""
    assemble_paired_main()

def execute_report_generation():
    """Execute T048: Generate the final statistical report."""
    report_gen_main()

def main():
    parser = argparse.ArgumentParser(description="Run the full SpatialClaw Restriction Pipeline (T052)")
    parser.add_argument("--skip-budget-check", action="store_true", help="Skip the initial budget check")
    args = parser.parse_args()

    logger = setup_pipeline_logger()
    logger.info("Starting Full Pipeline Execution (T052)")
    
    # 1. Budget Check (Optional but recommended)
    if not args.skip_budget_check:
        try:
            logger.info("Performing budget check...")
            check_budget()
            logger.info("Budget check passed.")
        except ConfigurationError as e:
            logger.error(f"BUDGET CHECK FAILED: {str(e)}")
            sys.exit(1)
        except Exception as e:
            logger.warning(f"Budget check encountered an issue (non-fatal): {str(e)}")

    # 2. Data Generation
    if not run_step("Data Generation", execute_data_generation):
        logger.error("Pipeline aborted: Data Generation failed.")
        sys.exit(1)

    # 3. Baseline Execution
    if not run_step("Baseline Execution", execute_baseline):
        logger.error("Pipeline aborted: Baseline Execution failed.")
        sys.exit(1)

    # 4. 2D Agent Execution
    if not run_step("2D Agent Execution", execute_agent_2d):
        logger.error("Pipeline aborted: 2D Agent Execution failed.")
        sys.exit(1)

    # 5. Integrity Check (T046)
    logger.info("Running integrity check (T046)...")
    # We call the verify_run logic directly here to ensure integrity before stats
    # The verify_run_main function is expected to handle this
    verify_run_main() 
    # Note: verify_run_main might exit on failure, which is desired behavior

    # 6. Assemble Paired Dataset (T047)
    if not run_step("Assemble Paired Dataset", execute_assemble_paired):
        logger.error("Pipeline aborted: Assembling Paired Dataset failed.")
        sys.exit(1)

    # 7. Statistical Tests & Sensitivity (T029, T031b)
    if not run_step("Statistical Tests", execute_stats):
        logger.error("Pipeline aborted: Statistical Tests failed.")
        sys.exit(1)

    # 8. Report Generation (T048)
    if not run_step("Report Generation", execute_report_generation):
        logger.error("Pipeline aborted: Report Generation failed.")
        sys.exit(1)

    logger.info("========================================")
    logger.info("PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
    logger.info("========================================")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Final Report: results/analysis/final_statistical_report.md")

if __name__ == "__main__":
    main()