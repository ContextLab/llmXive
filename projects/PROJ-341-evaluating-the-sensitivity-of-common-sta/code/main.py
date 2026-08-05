"""
Main entry point for the statistical sensitivity simulation pipeline.
Orchestrates the parameter loops for sample size, effect size, and hypothesis.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Import simulation components
from code.simulation.test_runner import main as simulation_main
from code.simulation.output_writer import write_p_values_raw, ensure_output_directory
from code.simulation.logging_config import get_logger, log_operation

# Import analysis components
from code.analysis.aggregator import main as aggregator_main, save_aggregated_results
from code.analysis.threshold_finder import main as threshold_main, save_thresholds
from code.analysis.validator import main as validator_main
from code.analysis.bootstrapper import main as bootstrapper_main
from code.analysis.validation_metrics import main as validation_metrics_main
from code.analysis.report_generator import main as report_generator_main

# Import visualization components
from code.visualization.plotter import main as plotter_main
from code.visualization.saver import main as saver_main

# Import utilities
from code.utils.checksum_utils import ensure_metadata_file_exists, save_simulation_metadata

logger = get_logger(__name__)


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB (Linux/Unix only)."""
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1]) / 1024.0
    except Exception:
        pass
    return 0.0


def check_memory_limit(limit_mb: float = 7000.0) -> bool:
    """Check if current memory usage is within limit."""
    usage = get_memory_usage_mb()
    if usage > limit_mb:
        logger.log("memory_exceeded", usage_mb=usage, limit_mb=limit_mb)
        return False
    return True


def force_gc() -> None:
    """Force garbage collection to free memory."""
    gc.collect()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run statistical sensitivity simulation pipeline"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["simulation", "aggregation", "thresholds", "plots", "validation", "bootstrap", "metrics", "report", "full", "test"],
        default="full",
        help="Execution mode"
    )
    parser.add_argument(
        "--test",
        type=str,
        choices=["t-test", "anova", "chi-squared"],
        default="t-test",
        help="Statistical test to run"
    )
    parser.add_argument(
        "--min-n",
        type=int,
        default=5,
        help="Minimum sample size"
    )
    parser.add_argument(
        "--max-n",
        type=int,
        default=500,
        help="Maximum sample size"
    )
    parser.add_argument(
        "--step-n",
        type=int,
        default=5,
        help="Step size for sample size"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10000,
        help="Number of iterations per condition (FR-001 constraint)"
    )
    parser.add_argument(
        "--effect-sizes",
        type=str,
        default="0.0,0.2,0.5,0.8",
        help="Comma-separated list of effect sizes (Cohen's d)"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--memory-limit",
        type=float,
        default=7000.0,
        help="Memory limit in MB"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    return parser.parse_args()


def run_simulation(args: argparse.Namespace) -> None:
    """
    Run the full simulation loop over parameters.
    Implements T014b: parameter loop logic for n=5..500, effect sizes, and hypotheses.
    """
    log_operation("simulation_start", mode=args.mode, args=vars(args))

    # Parse effect sizes
    effect_sizes = [float(e.strip()) for e in args.effect_sizes.split(",")]

    # Define sample size range
    sample_sizes = list(range(args.min_n, args.max_n + 1, args.step_n))

    # Ensure output directory exists
    ensure_output_directory()

    # Prepare results storage
    all_p_values = []
    total_conditions = len(sample_sizes) * len(effect_sizes)
    processed_conditions = 0

    logger.log("simulation_parameters",
               sample_sizes_count=len(sample_sizes),
               effect_sizes=effect_sizes,
               iterations=args.iterations,
               total_conditions=total_conditions)

    start_time = time.time()

    for n in sample_sizes:
        for effect_size in effect_sizes:
            # Check memory
            if not check_memory_limit(args.memory_limit):
                logger.log("memory_limit_reached", n=n, effect_size=effect_size)
                force_gc()
                if not check_memory_limit(args.memory_limit):
                    raise MemoryError(f"Memory limit exceeded at n={n}, effect_size={effect_size}")

            # Determine hypothesis state based on effect size
            # effect_size = 0.0 -> Null hypothesis is true
            # effect_size > 0.0 -> Alternative hypothesis is true
            is_null_true = (effect_size == 0.0)
            hypothesis_state = "H0" if is_null_true else "H1"

            # Run simulation for this condition
            # We call the simulation runner directly to get p-values
            # The simulation runner expects specific parameters
            try:
                # Generate p-values for this condition
                # Using the test_runner module's logic
                from code.simulation.test_runner import run_simulation_condition

                p_values = run_simulation_condition(
                    test_type=args.test,
                    n=n,
                    effect_size=effect_size,
                    iterations=args.iterations,
                    alpha=args.alpha,
                    seed=args.seed + int(n * 1000) + int(effect_size * 100)  # Unique seed per condition
                )

                # Store results
                for p_val in p_values:
                    all_p_values.append({
                        "sample_size": n,
                        "effect_size": effect_size,
                        "test_type": args.test,
                        "p_value": p_val,
                        "hypothesis_state": hypothesis_state,
                        "alpha": args.alpha,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                processed_conditions += 1
                elapsed = time.time() - start_time
                eta = (elapsed / processed_conditions) * (total_conditions - processed_conditions)
                logger.log("condition_completed",
                           n=n,
                           effect_size=effect_size,
                           processed=processed_conditions,
                           total=total_conditions,
                           eta_seconds=eta)

            except Exception as e:
                logger.log("condition_failed",
                           n=n,
                           effect_size=effect_size,
                           error=str(e))
                raise

    # Write raw p-values to CSV
    if all_p_values:
        df = pd.DataFrame(all_p_values)
        output_path = "data/simulation/p_values_raw.csv"
        df.to_csv(output_path, index=False)
        logger.log("output_written", path=output_path, rows=len(all_p_values))

        # Update metadata
        ensure_metadata_file_exists()
        metadata = load_simulation_metadata()
        if "simulation_runs" not in metadata:
            metadata["simulation_runs"] = []
        metadata["simulation_runs"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "test_type": args.test,
            "min_n": args.min_n,
            "max_n": args.max_n,
            "step_n": args.step_n,
            "iterations": args.iterations,
            "effect_sizes": effect_sizes,
            "alpha": args.alpha,
            "seed": args.seed,
            "output_file": output_path,
            "row_count": len(all_p_values)
        })
        save_simulation_metadata(metadata)

    elapsed_total = time.time() - start_time
    logger.log("simulation_complete", total_time_seconds=elapsed_total, total_rows=len(all_p_values))


def run_aggregation(args: argparse.Namespace) -> None:
    """Run aggregation to calculate error rates."""
    log_operation("aggregation_start")
    aggregator_main()
    log_operation("aggregation_complete")


def run_thresholds(args: argparse.Namespace) -> None:
    """Run threshold identification."""
    log_operation("thresholds_start")
    threshold_main()
    log_operation("thresholds_complete")


def run_plots(args: argparse.Namespace) -> None:
    """Generate visualization plots."""
    log_operation("plots_start")
    plotter_main()
    saver_main()
    log_operation("plots_complete")


def run_validation(args: argparse.Namespace) -> None:
    """Run validation on real datasets."""
    log_operation("validation_start")
    validator_main()
    log_operation("validation_complete")


def run_bootstrap(args: argparse.Namespace) -> None:
    """Run bootstrapped power estimation."""
    log_operation("bootstrap_start")
    bootstrapper_main()
    log_operation("bootstrap_complete")


def run_metrics(args: argparse.Namespace) -> None:
    """Calculate validation metrics."""
    log_operation("metrics_start")
    validation_metrics_main()
    log_operation("metrics_complete")


def run_report(args: argparse.Namespace) -> None:
    """Generate final report."""
    log_operation("report_start")
    report_generator_main()
    log_operation("report_complete")


def run_full_pipeline(args: argparse.Namespace) -> None:
    """Run the complete pipeline in sequence."""
    log_operation("full_pipeline_start")

    # 1. Simulation
    run_simulation(args)

    # 2. Aggregation
    run_aggregation(args)

    # 3. Thresholds
    run_thresholds(args)

    # 4. Validation (real data)
    run_validation(args)

    # 5. Bootstrap
    run_bootstrap(args)

    # 6. Metrics
    run_metrics(args)

    # 7. Plots
    run_plots(args)

    # 8. Report
    run_report(args)

    log_operation("full_pipeline_complete")


def main() -> None:
    """Main entry point."""
    args = parse_args()

    if args.mode == "test":
        # Quick test run with small parameters
        args.min_n = 5
        args.max_n = 50
        args.step_n = 10
        args.iterations = 100
        args.mode = "simulation"

    if args.mode == "full":
        run_full_pipeline(args)
    elif args.mode == "simulation":
        run_simulation(args)
    elif args.mode == "aggregation":
        run_aggregation(args)
    elif args.mode == "thresholds":
        run_thresholds(args)
    elif args.mode == "plots":
        run_plots(args)
    elif args.mode == "validation":
        run_validation(args)
    elif args.mode == "bootstrap":
        run_bootstrap(args)
    elif args.mode == "metrics":
        run_metrics(args)
    elif args.mode == "report":
        run_report(args)
    else:
        logger.log("unknown_mode", mode=args.mode)
        raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()