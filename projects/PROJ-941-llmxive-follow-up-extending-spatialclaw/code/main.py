"""
code/main.py

Orchestration entry point for the SpatialClaw pipeline.
Handles argument parsing, seed pinning, budget validation, and execution flow.
"""
import argparse
import json
import logging
import os
import random
import sys
import time

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data.generator import generate_dataset
from code.utils.reproducibility import set_seed, enforce_temperature_zero
from code.kernel.restricted_kernel import enforce_2d_policy, release_2d_policy
from code.utils.logging_config import setup_logging, get_logger
from code.metrics.collector import MetricsCollector
from code.utils.budget_check import check_budget, ConfigurationError

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="SpatialClaw Pipeline Orchestration")
    parser.add_argument("--seed", type=int, default=42, help="Master random seed")
    parser.add_argument("--n-tasks", type=int, default=100, help="Number of tasks to generate")
    parser.add_argument("--output", type=str, default="data/raw/synthetic_spatialclaw_v1.json", help="Output dataset path")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    parser.add_argument("--budget-seconds", type=float, default=6 * 60 * 60,
                        help="Maximum allowed runtime in seconds (default: 6 hours)")
    return parser.parse_args()

def run_orchestration(args):
    """Main orchestration logic."""
    logger.info("Starting SpatialClaw Pipeline Orchestration")

    # 0. Budget Check (T044) - Must happen before data generation
    try:
        check_budget(budget_seconds=args.budget_seconds)
    except ConfigurationError as e:
        logger.critical(f"Budget check failed: {e}")
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Setup Logging
    setup_logging(level=args.log_level)

    # 2. Enforce Reproducibility
    set_seed(args.seed)
    enforce_temperature_zero()
    logger.info(f"Reproducibility enforced: seed={args.seed}, temperature=0")

    # 3. Enforce 2D Policy
    enforce_2d_policy()
    logger.info("2D Restriction Policy enforced")

    # 4. Generate Dataset
    logger.info(f"Generating {args.n_tasks} synthetic tasks...")
    start_time = time.time()
    tasks = generate_dataset(n_tasks=args.n_tasks, seed=args.seed, output_path=args.output)
    gen_time = time.time() - start_time
    logger.info(f"Dataset generation completed in {gen_time:.2f}s. Output: {args.output}")

    # 5. Record Metrics
    collector = MetricsCollector()
    collector.record_step(
        task_id="generation",
        latency_ms=gen_time * 1000,
        status="success",
        blocked_time_ms=0.0
    )

    # 6. Cleanup
    release_2d_policy()
    logger.info("2D Restriction Policy released")

    logger.info("Orchestration completed successfully")
    return tasks

def main():
    args = parse_args()
    run_orchestration(args)

if __name__ == "__main__":
    main()