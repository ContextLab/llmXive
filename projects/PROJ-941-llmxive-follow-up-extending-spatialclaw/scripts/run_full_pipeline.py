#!/usr/bin/env python3
"""
Full Pipeline Runner for llmXive SpatialClaw Restriction Project.

This script orchestrates the entire experiment flow:
1. Data Generation (T006b)
2. 3D Baseline Execution (T023b)
3. 2D Agent Execution (T017b)
4. Statistical Analysis (T029)
5. Paired Dataset Assembly (T047a)
6. Final Report Generation (T048)

Usage:
    python scripts/run_full_pipeline.py [--config data/power_config.yaml]
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from code.data.generator import main as generate_data_main
from code.agents.run_baseline_3d import main as baseline_main
from code.main import main as agent_2d_main
from code.stats.tests import main as stats_main
from code.analysis.assemble_paired_dataset import main as assemble_main
from code.stats.report_generator import main as report_main
from code.utils.logging import setup_logging
from code.utils.budget_check import check_budget
from code.utils.runtime_monitor import check_runtime_limit, RuntimeLimitExceededError
from code.data.loader import load_dataset, DataLoadError

# Configure logging
logger = logging.getLogger(__name__)

def run_step(step_name: str, func, *args, **kwargs) -> bool:
    """Execute a pipeline step with error handling and logging."""
    logger.info(f"--- Starting Step: {step_name} ---")
    start_time = time.time()
    try:
        func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"--- Step {step_name} completed successfully in {elapsed:.2f}s ---")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"--- Step {step_name} FAILED after {elapsed:.2f}s: {str(e)} ---")
        logger.exception(e)
        return False

def execute_data_generation():
    """Execute T006b: Full Data Generation."""
    logger.info("Executing Data Generation (T006b)...")
    # Call the generator main function
    generate_data_main()

def execute_baseline():
    """Execute T023b: 3D Baseline Execution."""
    logger.info("Executing 3D Baseline (T023b)...")
    # Run baseline on the generated dataset
    baseline_main()

def execute_agent_2d():
    """Execute T017b: 2D Agent Execution."""
    logger.info("Executing 2D Agent (T017b)...")
    # Run 2D agent on the generated dataset
    agent_2d_main()

def execute_stats():
    """Execute T029: Statistical Analysis."""
    logger.info("Executing Statistical Analysis (T029)...")
    # Run statistical tests
    stats_main()

def execute_assemble_paired():
    """Execute T047a: Final Paired Dataset Assembly."""
    logger.info("Executing Paired Dataset Assembly (T047a)...")
    # Assemble the final paired dataset
    assemble_main()

def execute_report_generation():
    """Execute T048: Final Report Generation."""
    logger.info("Executing Final Report Generation (T048)...")
    # Generate the final statistical report
    report_main()

def main():
    parser = argparse.ArgumentParser(description="Run the full SpatialClaw restriction pipeline")
    parser.add_argument("--config", type=str, default="data/power_config.yaml",
                      help="Path to power config file")
    parser.add_argument("--timeout", type=int, default=300,
                      help="Timeout in seconds (default: 300)")
    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger.info("Starting Full Pipeline Execution")
    logger.info(f"Config file: {args.config}")
    logger.info(f"Timeout: {args.timeout}s")

    # Check budget before starting
    try:
        check_budget(args.config)
        logger.info("Budget check passed")
    except Exception as e:
        logger.error(f"Budget check failed: {e}")
        sys.exit(1)

    start_time = time.time()
    pipeline_start = datetime.now().isoformat()

    # Define pipeline steps
    steps = [
        ("Data Generation", execute_data_generation),
        ("3D Baseline Execution", execute_baseline),
        ("2D Agent Execution", execute_agent_2d),
        ("Paired Dataset Assembly", execute_assemble_paired),
        ("Statistical Analysis", execute_stats),
        ("Final Report Generation", execute_report_generation),
    ]

    results = {}
    success_count = 0
    fail_count = 0

    for step_name, step_func in steps:
        # Check runtime limit
        try:
            check_runtime_limit(start_time, args.timeout)
        except RuntimeLimitExceededError:
            logger.error(f"Pipeline exceeded runtime limit of {args.timeout}s")
            # Move partial results to partial directory
            partial_dir = "results/logs/partial"
            os.makedirs(partial_dir, exist_ok=True)
            # Copy current results to partial
            for src_dir in ["results/runs", "results/logs", "results/analysis"]:
                if os.path.exists(src_dir):
                    import shutil
                    dest_dir = os.path.join(partial_dir, os.path.basename(src_dir))
                    shutil.move(src_dir, dest_dir, copy_function=shutil.copy2)
            sys.exit(1)

        success = run_step(step_name, step_func)
        results[step_name] = success
        if success:
            success_count += 1
        else:
            fail_count += 1
            logger.warning(f"Step {step_name} failed, continuing to next step...")

    total_time = time.time() - start_time
    pipeline_end = datetime.now().isoformat()

    # Log summary
    logger.info("=" * 60)
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Start: {pipeline_start}")
    logger.info(f"End: {pipeline_end}")
    logger.info(f"Total Time: {total_time:.2f}s")
    logger.info(f"Steps Passed: {success_count}/{len(steps)}")
    logger.info(f"Steps Failed: {fail_count}/{len(steps)}")

    for step_name, success in results.items():
        status = "PASSED" if success else "FAILED"
        logger.info(f"  {step_name}: {status}")

    # Write execution summary
    summary_path = "results/analysis/pipeline_execution_summary.json"
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    import json
    summary = {
        "pipeline_start": pipeline_start,
        "pipeline_end": pipeline_end,
        "total_time_seconds": total_time,
        "timeout_seconds": args.timeout,
        "steps_total": len(steps),
        "steps_passed": success_count,
        "steps_failed": fail_count,
        "step_results": results,
        "status": "SUCCESS" if fail_count == 0 else "PARTIAL"
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Execution summary written to {summary_path}")

    # Exit with error if any step failed
    if fail_count > 0:
        logger.error("Pipeline completed with failures")
        sys.exit(1)

    logger.info("Pipeline completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)