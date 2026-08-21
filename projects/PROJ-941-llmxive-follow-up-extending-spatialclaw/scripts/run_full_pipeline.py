#!/usr/bin/env python3
"""
Full Pipeline Runner for SpatialClaw Restriction Experiment.

This script orchestrates the entire experiment flow:
1. Data Generation (T006b)
2. 3D Baseline Execution (T023b)
3. 2D Agent Execution (T017b)
4. Statistical Analysis (T029)
5. Paired Dataset Assembly (T047)
6. Final Report Generation (T048)
7. Kernel Audit (T050)

Dependencies:
- T006b, T023b, T017b, T029, T047, T048, T050

Usage:
    python scripts/run_full_pipeline.py [--config data/power_config.yaml]
"""

import argparse
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.logging import setup_logging
from utils.runtime_monitor import runtime_monitor, RuntimeLimitExceededError
from utils.budget_check import check_budget, ConfigurationError
from data.generator import main as generate_data_main
from agents.baseline_3d import main as baseline_main
from agents.agent_2d import main as agent_2d_main
from stats.tests import main as stats_main
from analysis.assemble_paired_dataset import main as assemble_main
from stats.report_generator import main as report_main
from utils.kernel_audit import main as audit_main


def setup_pipeline_logger(log_path: str) -> logging.Logger:
    """Configure the pipeline logger to write to a specific file."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    logger = logging.getLogger("pipeline_runner")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_path, mode='w')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger


def run_step(step_name: str, func, logger: logging.Logger, *args, **kwargs) -> bool:
    """Execute a pipeline step with timing and error handling."""
    logger.info(f"{'='*60}")
    logger.info(f"STARTING STEP: {step_name}")
    logger.info(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"COMPLETED STEP: {step_name} in {elapsed:.2f}s")
        return True
    except RuntimeLimitExceededError as e:
        elapsed = time.time() - start_time
        logger.error(f"STEP FAILED (Runtime Limit): {step_name} after {elapsed:.2f}s")
        logger.error(f"Error: {str(e)}")
        raise
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"STEP FAILED: {step_name} after {elapsed:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def execute_data_generation(logger: logging.Logger) -> bool:
    """Execute T006b: Full Data Generation."""
    # Prepare arguments for generator
    args = argparse.Namespace(
        output_path="data/raw/synthetic_spatialclaw_v1.json",
        pilot_path=None,
        n_tasks=None,  # Will be read from power analysis
        seed=42
    )
    
    # Load n_tasks from power analysis summary
    power_summary_path = os.path.join(PROJECT_ROOT, "results/analysis/power_analysis_summary.json")
    if os.path.exists(power_summary_path):
        with open(power_summary_path, 'r') as f:
            power_config = json.load(f)
            args.n_tasks = power_config.get('n_required', 50)
        logger.info(f"Using n_tasks={args.n_tasks} from power analysis")
    else:
        logger.warning("power_analysis_summary.json not found, using default n_tasks=50")
        args.n_tasks = 50
    
    return run_step("Data Generation (T006b)", generate_data_main, logger, args)


def execute_baseline(logger: logging.Logger) -> bool:
    """Execute T023b: 3D Baseline Execution."""
    args = argparse.Namespace(
        input_path="data/raw/synthetic_spatialclaw_v1.json",
        output_path="results/logs/baseline_run.json",
        seed=42
    )
    return run_step("3D Baseline Execution (T023b)", baseline_main, logger, args)


def execute_agent_2d(logger: logging.Logger) -> bool:
    """Execute T017b: 2D Agent Execution."""
    args = argparse.Namespace(
        input_path="data/raw/synthetic_spatialclaw_v1.json",
        output_dir="results/runs",
        n_runs=5,
        seed_base=42
    )
    return run_step("2D Agent Execution (T017b)", agent_2d_main, logger, args)


def execute_stats(logger: logging.Logger) -> bool:
    """Execute T029: Statistical Tests."""
    args = argparse.Namespace(
        input_path="results/analysis/final_paired_dataset.csv",
        output_path="results/analysis/final_statistical_report.md"
    )
    return run_step("Statistical Analysis (T029)", stats_main, logger, args)


def execute_assemble_paired(logger: logging.Logger) -> bool:
    """Execute T047: Final Paired Dataset Assembly."""
    args = argparse.Namespace(
        baseline_path="results/logs/baseline_run.json",
        agent_2d_dir="results/runs",
        output_path="results/analysis/final_paired_dataset.csv",
        config_path="data/power_config.yaml"
    )
    return run_step("Paired Dataset Assembly (T047)", assemble_main, logger, args)


def execute_report_generation(logger: logging.Logger) -> bool:
    """Execute T048: Final Report Generation."""
    args = argparse.Namespace(
        paired_dataset_path="results/analysis/final_paired_dataset.csv",
        sensitivity_path="results/analysis/depth_threshold_sweep.csv",
        output_path="results/analysis/final_statistical_report.md"
    )
    return run_step("Report Generation (T048)", report_main, logger, args)


def execute_kernel_audit(logger: logging.Logger) -> bool:
    """Execute T050: Kernel Blockage Final Audit."""
    args = argparse.Namespace(
        log_dir="results/logs",
        output_path="results/analysis/kernel_audit.txt"
    )
    return run_step("Kernel Audit (T050)", audit_main, logger, args)


def execute_budget_report(logger: logging.Logger, start_time: float) -> bool:
    """Generate budget compliance report."""
    total_runtime = time.time() - start_time
    config_path = os.path.join(PROJECT_ROOT, "data/power_config.yaml")
    
    # Load budget limit
    max_hours = 6.0
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            import yaml
            config = yaml.safe_load(f)
            max_hours = config.get('max_runtime_hours', 6.0)
    
    max_seconds = max_hours * 3600
    status = "PASS" if total_runtime <= max_seconds else "FAIL"
    
    report = {
        "total_runtime_seconds": round(total_runtime, 2),
        "budget_limit_seconds": max_seconds,
        "status": status
    }
    
    os.makedirs(os.path.join(PROJECT_ROOT, "results/analysis"), exist_ok=True)
    report_path = os.path.join(PROJECT_ROOT, "results/analysis/budget_compliance_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"BUDGET REPORT: {status} ({total_runtime:.2f}s / {max_seconds:.2f}s)")
    return True


def main():
    """Main pipeline orchestration."""
    parser = argparse.ArgumentParser(description="Run full SpatialClaw restriction experiment pipeline")
    parser.add_argument("--config", type=str, default="data/power_config.yaml", help="Path to power config")
    parser.add_argument("--log-path", type=str, default="results/logs/pipeline_run.log", help="Path to pipeline log")
    parser.add_argument("--max-runtime-hours", type=float, default=6.0, help="Maximum runtime in hours")
    args = parser.parse_args()
    
    # Setup logger
    log_path = os.path.join(PROJECT_ROOT, args.log_path)
    logger = setup_pipeline_logger(log_path)
    
    logger.info("Starting Full Pipeline Execution")
    logger.info(f"Config: {args.config}")
    logger.info(f"Log Path: {log_path}")
    
    start_time = time.time()
    
    try:
        # Check budget before starting
        budget_ok = check_budget(args.config, logger)
        if not budget_ok:
            logger.error("Budget check failed. Aborting pipeline.")
            sys.exit(1)
        
        # Step 1: Data Generation
        if not execute_data_generation(logger):
            logger.error("Data generation failed. Aborting.")
            sys.exit(1)
        
        # Step 2: 3D Baseline
        if not execute_baseline(logger):
            logger.error("Baseline execution failed. Aborting.")
            sys.exit(1)
        
        # Step 3: 2D Agent
        if not execute_agent_2d(logger):
            logger.error("2D Agent execution failed. Aborting.")
            sys.exit(1)
        
        # Step 4: Assemble Paired Dataset
        if not execute_assemble_paired(logger):
            logger.error("Paired dataset assembly failed. Aborting.")
            sys.exit(1)
        
        # Step 5: Statistical Analysis
        if not execute_stats(logger):
            logger.error("Statistical analysis failed. Aborting.")
            sys.exit(1)
        
        # Step 6: Report Generation
        if not execute_report_generation(logger):
            logger.error("Report generation failed. Aborting.")
            sys.exit(1)
        
        # Step 7: Kernel Audit
        if not execute_kernel_audit(logger):
            logger.error("Kernel audit failed. Aborting.")
            sys.exit(1)
        
        # Generate budget report
        execute_budget_report(logger, start_time)
        
        total_time = time.time() - start_time
        logger.info(f"{'='*60}")
        logger.info(f"PIPELINE COMPLETED SUCCESSFULLY in {total_time:.2f}s")
        logger.info(f"{'='*60}")
        
    except RuntimeLimitExceededError as e:
        logger.error(f"Pipeline aborted due to runtime limit: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()