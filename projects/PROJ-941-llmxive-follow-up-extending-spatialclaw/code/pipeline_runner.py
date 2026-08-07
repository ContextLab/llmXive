"""
T052: Full Pipeline Execution Orchestrator

Executes the complete SpatialClaw restriction pipeline:
1. Data Generation (T006a/b)
2. 3D Baseline Execution (T023b)
3. 2D Agent Execution (T017)
4. Statistical Analysis (T029, T031b)

Produces: results/logs/pipeline_run.log
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.generator import main as generate_dataset_main
from agents.baseline_3d import main as baseline_3d_main
from agents.agent_2d import main as agent_2d_main
from stats.tests import main as stats_tests_main
from stats.sensitivity import main as stats_sensitivity_main
from utils.budget_check import check_budget, ConfigurationError
from utils.verify_run import main as verify_run_main
from utils.logging import setup_logging

# Configure logger for this module
logger = logging.getLogger("pipeline_runner")

def run_step(step_name: str, func, *args, **kwargs) -> bool:
    """Run a pipeline step with timing and error handling."""
    logger.info(f"--- Starting Step: {step_name} ---")
    start_time = time.time()
    try:
        func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"--- Completed Step: {step_name} in {elapsed:.2f}s ---")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"--- FAILED Step: {step_name} after {elapsed:.2f}s ---")
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(description="Run the full SpatialClaw pipeline")
    parser.add_argument("--config", type=str, default="data/power_config.yaml",
                        help="Path to power configuration file")
    parser.add_argument("--skip-data-gen", action="store_true",
                        help="Skip data generation step")
    parser.add_argument("--skip-baseline", action="store_true",
                        help="Skip 3D baseline execution")
    parser.add_argument("--skip-agent", action="store_true",
                        help="Skip 2D agent execution")
    parser.add_argument("--skip-stats", action="store_true",
                        help="Skip statistical analysis")
    parser.add_argument("--skip-verify", action="store_true",
                        help="Skip run verification")
    args = parser.parse_args()

    # Setup logging to file and console
    log_dir = "results/logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pipeline_run.log")
    
    # Create file handler with specific format for this log
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("=" * 60)
    logger.info("SPATIALCLAW FULL PIPELINE EXECUTION")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # 1. Budget Check (T044)
    logger.info("Checking budget constraints...")
    try:
        check_budget(args.config)
        logger.info("Budget check passed.")
    except ConfigurationError as e:
        logger.error(f"BUDGET CHECK FAILED: {e}")
        logger.info("Aborting pipeline execution.")
        return 1
    except Exception as e:
        logger.warning(f"Could not perform budget check: {e}")
        logger.info("Continuing with caution...")

    success = True

    # 2. Data Generation (T006a/b)
    if not args.skip_data_gen:
        # Generate dataset
        if not run_step("Data Generation", generate_dataset_main):
            success = False
            logger.error("Data generation failed. Aborting.")
            return 1
    else:
        logger.info("Skipping Data Generation (flag set).")

    # 3. 3D Baseline Execution (T023b)
    if not args.skip_baseline:
        # Run baseline on the generated dataset
        baseline_args = [
            "baseline_3d",
            "--input", "data/raw/synthetic_spatialclaw_v1.json",
            "--output", "results/logs/baseline_run.json"
        ]
        # Parse args manually to match expected interface
        import argparse as ap
        bas_parser = ap.ArgumentParser()
        bas_parser.add_argument("--input", required=True)
        bas_parser.add_argument("--output", required=True)
        bas_args = bas_parser.parse_args(baseline_args[1:])
        
        if not run_step("3D Baseline Execution", baseline_3d_main, bas_args):
            success = False
            logger.error("3D Baseline execution failed. Aborting.")
            return 1
    else:
        logger.info("Skipping 3D Baseline Execution (flag set).")

    # 4. 2D Agent Execution (T017)
    if not args.skip_agent:
        # Run 2D agent on the generated dataset
        agent_args = [
            "agent_2d",
            "--input", "data/raw/synthetic_spatialclaw_v1.json",
            "--output-dir", "results/runs"
        ]
        import argparse as ap
        agent_parser = ap.ArgumentParser()
        agent_parser.add_argument("--input", required=True)
        agent_parser.add_argument("--output-dir", required=True)
        agent_parsed = agent_parser.parse_args(agent_args[1:])
        
        if not run_step("2D Agent Execution", agent_2d_main, agent_parsed):
            success = False
            logger.error("2D Agent execution failed. Aborting.")
            return 1
    else:
        logger.info("Skipping 2D Agent Execution (flag set).")

    # 5. Verification (T046)
    if not args.skip_verify:
        if not run_step("Run Integrity Verification", verify_run_main):
            logger.warning("Run verification completed with warnings.")
    else:
        logger.info("Skipping Run Verification (flag set).")

    # 6. Statistical Analysis (T029, T031b)
    if not args.skip_stats:
        # Run statistical tests
        if not run_step("Statistical Tests (T029/T030)", stats_tests_main):
            success = False
            logger.error("Statistical tests failed.")
        
        # Run sensitivity analysis
        if not run_step("Sensitivity Analysis (T031b)", stats_sensitivity_main):
            success = False
            logger.error("Sensitivity analysis failed.")
    else:
        logger.info("Skipping Statistical Analysis (flag set).")

    # Final Status
    logger.info("=" * 60)
    logger.info("PIPELINE EXECUTION FINISHED")
    logger.info(f"End Time: {datetime.now().isoformat()}")
    if success:
        logger.info("Status: SUCCESS")
    else:
        logger.info("Status: COMPLETED WITH ERRORS")
    logger.info("=" * 60)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
