"""
Main entry point for the statistical test sensitivity simulation pipeline.
Orchestrates simulation, aggregation, threshold finding, visualization, and validation.
Includes memory optimization strategies for large-scale simulations.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
import traceback
import resource
from typing import Dict, Any, Optional, List, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.simulation.test_runner import run_simulation_condition, aggregate_results
from code.simulation.data_generator import generate_normal_data, generate_contingency_table_data
from code.simulation.output_writer import write_p_values_raw, ensure_output_directory
from code.simulation.logging_config import get_logger, log_simulation_params, log_error_details
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
from code.analysis.threshold_finder import calculate_confidence_intervals, save_thresholds
from code.analysis.validator import run_validation_on_datasets, main as validator_main
from code.analysis.bootstrapper import run_bootstrapped_validation, save_power_results
from code.analysis.validation_metrics import calculate_validation_metrics, save_validation_metrics
from code.analysis.report_generator import generate_report
from code.visualization.plotter import generate_all_plots
from code.visualization.saver import save_individual_plots, save_comparative_plots
from code.simulation import get_rng
from code.utils.checksum_utils import register_run, update_run_status, ensure_metadata_file_exists, register_dataset_checksum

logger = get_logger(__name__)

# Memory constraint constants (in MB)
MEMORY_LIMIT_MB = 7000  # 7GB limit as per requirement
GC_THRESHOLD = 100000   # Run GC if object count exceeds this

def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the process in MB.
    Uses resource module on Unix systems.
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on some other systems
        # Normalize to MB
        if sys.platform == 'darwin':
            return usage.ru_maxrss / (1024 * 1024)
        else:
            return usage.ru_maxrss / 1024.0
    except Exception as e:
        logger.warning(f"Could not determine memory usage: {e}")
        return 0.0

def check_memory_limit(limit_mb: float = MEMORY_LIMIT_MB) -> bool:
    """
    Check if current memory usage is within the specified limit.
    Returns True if within limit, False otherwise.
    """
    current_mb = get_memory_usage_mb()
    if current_mb > limit_mb:
        logger.error(f"Memory limit exceeded: {current_mb:.2f}MB > {limit_mb}MB")
        return False
    return True

def force_gc() -> None:
    """Force garbage collection to reclaim memory."""
    gc.collect()
    gc.collect()
    gc.collect()  # Triple collection for deep graphs

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run statistical test sensitivity simulation pipeline."
    )

    # Simulation parameters
    parser.add_argument("--min-n", type=int, default=5, help="Minimum sample size")
    parser.add_argument("--max-n", type=int, default=500, help="Maximum sample size")
    parser.add_argument("--step-n", type=int, default=5, help="Step size for sample size")
    parser.add_argument("--iterations", type=int, default=100, help="Number of iterations per condition")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--effect-size", type=float, default=0.5, help="Effect size for alternative hypothesis")

    # Test type selection
    parser.add_argument("--test", type=str, choices=["t-test", "anova", "chi-squared", "all"],
                        default="all", help="Statistical test to run")

    # Modes
    parser.add_argument("--mode", type=str, choices=["simulation", "aggregation", "thresholds",
                                                    "plots", "validation", "full", "bootstrap"],
                        default="full", help="Pipeline mode to run")

    # Memory optimization flags
    parser.add_argument("--batch-size", type=int, default=1000,
                        help="Batch size for processing iterations (memory optimization)")
    parser.add_argument("--gc-threshold", type=int, default=GC_THRESHOLD,
                        help="Garbage collection threshold")

    return parser.parse_args()

def run_simulation(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Run the core simulation with memory optimization.
    Processes data in batches to stay within memory limits.
    """
    logger.info("Starting simulation with memory optimization...")
    logger.info(f"Parameters: n=[{args.min_n}, {args.max_n}], iterations={args.iterations}, "
               f"test={args.test}, alpha={args.alpha}")

    # Ensure output directories exist
    ensure_output_directory()
    ensure_metadata_file_exists()

    # Register this run in metadata
    run_id = register_run("simulation", {
        "min_n": args.min_n,
        "max_n": args.max_n,
        "step_n": args.step_n,
        "iterations": args.iterations,
        "alpha": args.alpha,
        "test_type": args.test,
        "batch_size": args.batch_size
    })

    all_p_values = []
    sample_sizes = range(args.min_n, args.max_n + 1, args.step_n)

    # Memory-efficient batch processing
    batch_results = []
    batch_count = 0
    total_conditions = len(sample_sizes) * (3 if args.test == "all" else 1)

    logger.info(f"Processing {total_conditions} conditions in batches...")

    for n in sample_sizes:
        # Check memory before each sample size batch
        if not check_memory_limit(MEMORY_LIMIT_MB * 0.9):  # Safety margin
            logger.warning("Memory usage high, forcing garbage collection...")
            force_gc()
            if not check_memory_limit(MEMORY_LIMIT_MB):
                logger.error("Memory limit still exceeded after GC. Aborting simulation.")
                raise MemoryError(f"Memory limit {MEMORY_LIMIT_MB}MB exceeded")

        # Generate data for this sample size
        if args.test in ["t-test", "all"]:
            # T-test: two groups
            data_null = generate_normal_data(n, mu1=0, mu2=0, sigma=1)
            data_alt = generate_normal_data(n, mu1=0, mu2=args.effect_size, sigma=1)

            # Process in smaller batches
            p_values_null = []
            p_values_alt = []

            for batch_start in range(0, args.iterations, args.batch_size):
                batch_end = min(batch_start + args.batch_size, args.iterations)
                batch_null = []
                batch_alt = []

                for _ in range(batch_start, batch_end):
                    rng = get_rng()
                    # Null hypothesis: no difference
                    p_null = run_simulation_condition(data_null, "t-test", rng)
                    batch_null.append(p_null)

                    # Alternative hypothesis: difference exists
                    p_alt = run_simulation_condition(data_alt, "t-test", rng)
                    batch_alt.append(p_alt)

                p_values_null.extend(batch_null)
                p_values_alt.extend(batch_alt)

                # Force GC after each batch
                if (batch_end - batch_start) >= args.gc_threshold:
                    force_gc()

            # Store results for this condition
            for p in p_values_null:
                all_p_values.append({
                    "sample_size": n,
                    "test_type": "t-test",
                    "hypothesis": "null",
                    "p_value": p,
                    "iteration": len([x for x in all_p_values if x["iteration"] == len(all_p_values)])
                })

            for p in p_values_alt:
                all_p_values.append({
                    "sample_size": n,
                    "test_type": "t-test",
                    "hypothesis": "alternative",
                    "p_value": p,
                    "iteration": len([x for x in all_p_values if x["iteration"] == len(all_p_values)])
                })

        if args.test in ["anova", "all"]:
            # ANOVA: multiple groups
            data_null = generate_normal_data(n, mu1=0, mu2=0, mu3=0, sigma=1)
            data_alt = generate_normal_data(n, mu1=0, mu2=args.effect_size, mu3=0, sigma=1)

            p_values_null = []
            p_values_alt = []

            for batch_start in range(0, args.iterations, args.batch_size):
                batch_end = min(batch_start + args.batch_size, args.iterations)
                batch_null = []
                batch_alt = []

                for _ in range(batch_start, batch_end):
                    rng = get_rng()
                    p_null = run_simulation_condition(data_null, "anova", rng)
                    batch_null.append(p_null)

                    p_alt = run_simulation_condition(data_alt, "anova", rng)
                    batch_alt.append(p_alt)

                p_values_null.extend(batch_null)
                p_values_alt.extend(batch_alt)

                if (batch_end - batch_start) >= args.gc_threshold:
                    force_gc()

            for p in p_values_null:
                all_p_values.append({
                    "sample_size": n,
                    "test_type": "anova",
                    "hypothesis": "null",
                    "p_value": p,
                    "iteration": len([x for x in all_p_values if x["iteration"] == len(all_p_values)])
                })

            for p in p_values_alt:
                all_p_values.append({
                    "sample_size": n,
                    "test_type": "anova",
                    "hypothesis": "alternative",
                    "p_value": p,
                    "iteration": len([x for x in all_p_values if x["iteration"] == len(all_p_values)])
                })

        if args.test in ["chi-squared", "all"]:
            # Chi-squared: contingency tables
            # Generate contingency table data
            data_null = generate_contingency_table_data(n, effect_size=0)
            data_alt = generate_contingency_table_data(n, effect_size=args.effect_size)

            p_values_null = []
            p_values_alt = []

            for batch_start in range(0, args.iterations, args.batch_size):
                batch_end = min(batch_start + args.batch_size, args.iterations)
                batch_null = []
                batch_alt = []

                for _ in range(batch_start, batch_end):
                    rng = get_rng()
                    p_null = run_simulation_condition(data_null, "chi-squared", rng)
                    batch_null.append(p_null)

                    p_alt = run_simulation_condition(data_alt, "chi-squared", rng)
                    batch_alt.append(p_alt)

                p_values_null.extend(batch_null)
                p_values_alt.extend(batch_alt)

                if (batch_end - batch_start) >= args.gc_threshold:
                    force_gc()

            for p in p_values_null:
                all_p_values.append({
                    "sample_size": n,
                    "test_type": "chi-squared",
                    "hypothesis": "null",
                    "p_value": p,
                    "iteration": len([x for x in all_p_values if x["iteration"] == len(all_p_values)])
                })

            for p in p_values_alt:
                all_p_values.append({
                    "sample_size": n,
                    "test_type": "chi-squared",
                    "hypothesis": "alternative",
                    "p_value": p,
                    "iteration": len([x for x in all_p_values if x["iteration"] == len(all_p_values)])
                })

        # Write batch to file periodically to avoid memory buildup
        if len(all_p_values) >= args.batch_size * 10:
            write_p_values_raw(all_p_values, "data/simulation/p_values_raw.csv")
            # Clear processed data
            all_p_values = []
            force_gc()
            logger.info(f"Written batch {batch_count} to CSV, cleared memory")
            batch_count += 1

    # Write remaining results
    if all_p_values:
        write_p_values_raw(all_p_values, "data/simulation/p_values_raw.csv")

    update_run_status(run_id, "completed", {"total_records": len(all_p_values)})
    logger.info("Simulation completed successfully")
    return {"status": "completed", "records_written": len(all_p_values)}

def run_aggregation(args: argparse.Namespace) -> Dict[str, Any]:
    """Run aggregation to calculate error rates."""
    logger.info("Starting aggregation...")
    ensure_metadata_file_exists()

    run_id = register_run("aggregation", {"alpha": args.alpha})

    try:
        # Calculate error rates
        error_rates = calculate_error_rates("data/simulation/p_values_raw.csv", args.alpha)

        # Save aggregated results
        save_aggregated_results(error_rates, "data/simulation/error_rates_summary.csv")

        update_run_status(run_id, "completed", {"error_rates_count": len(error_rates)})
        logger.info("Aggregation completed successfully")
        return {"status": "completed", "error_rates_count": len(error_rates)}
    except Exception as e:
        update_run_status(run_id, "failed", {"error": str(e)})
        log_error_details(e)
        raise

def run_thresholds(args: argparse.Namespace) -> Dict[str, Any]:
    """Calculate thresholds for reliability."""
    logger.info("Starting threshold calculation...")
    ensure_metadata_file_exists()

    run_id = register_run("thresholds", {"alpha": args.alpha})

    try:
        # Calculate confidence intervals
        error_rates = calculate_confidence_intervals("data/simulation/error_rates_summary.csv")

        # Save thresholds
        save_thresholds(error_rates, "data/simulation/thresholds.json")

        update_run_status(run_id, "completed", {"thresholds_count": len(error_rates)})
        logger.info("Threshold calculation completed successfully")
        return {"status": "completed", "thresholds_count": len(error_rates)}
    except Exception as e:
        update_run_status(run_id, "failed", {"error": str(e)})
        log_error_details(e)
        raise

def run_plots(args: argparse.Namespace) -> Dict[str, Any]:
    """Generate visualization plots."""
    logger.info("Starting plot generation...")
    ensure_metadata_file_exists()

    run_id = register_run("plots", {})

    try:
        # Generate all plots
        generate_all_plots(
            error_rates_path="data/simulation/error_rates_summary.csv",
            thresholds_path="data/simulation/thresholds.json",
            output_dir="data/visualization"
        )

        # Save individual and comparative plots
        save_individual_plots("data/visualization")
        save_comparative_plots("data/visualization")

        update_run_status(run_id, "completed", {"plots_generated": True})
        logger.info("Plot generation completed successfully")
        return {"status": "completed", "plots_generated": True}
    except Exception as e:
        update_run_status(run_id, "failed", {"error": str(e)})
        log_error_details(e)
        raise

def run_validation(args: argparse.Namespace) -> Dict[str, Any]:
    """Run validation against real-world datasets."""
    logger.info("Starting validation with real datasets...")
    ensure_metadata_file_exists()

    run_id = register_run("validation", {"alpha": args.alpha})

    try:
        # Run validation on real datasets
        validation_results = run_validation_on_datasets(
            alpha=args.alpha,
            output_csv="data/simulation/real_data_pvalues.csv"
        )

        # Register dataset checksums
        for dataset_name, checksum in validation_results.get("checksums", {}).items():
            register_dataset_checksum(dataset_name, checksum)

        update_run_status(run_id, "completed", validation_results)
        logger.info("Validation completed successfully")
        return {"status": "completed", "results": validation_results}
    except Exception as e:
        update_run_status(run_id, "failed", {"error": str(e)})
        log_error_details(e)
        raise

def run_bootstrap(args: argparse.Namespace) -> Dict[str, Any]:
    """Run bootstrapped power estimation."""
    logger.info("Starting bootstrapped power estimation...")
    ensure_metadata_file_exists()

    run_id = register_run("bootstrap", {"alpha": args.alpha})

    try:
        # Run bootstrapped validation
        power_results = run_bootstrapped_validation(
            simulated_power_path="data/simulation/error_rates_summary.csv",
            real_data_path="data/simulation/real_data_pvalues.csv",
            output_path="data/simulation/real_data_power.json"
        )

        update_run_status(run_id, "completed", power_results)
        logger.info("Bootstrapped power estimation completed successfully")
        return {"status": "completed", "results": power_results}
    except Exception as e:
        update_run_status(run_id, "failed", {"error": str(e)})
        log_error_details(e)
        raise

def run_metrics(args: argparse.Namespace) -> Dict[str, Any]:
    """Calculate validation metrics."""
    logger.info("Starting validation metrics calculation...")
    ensure_metadata_file_exists()

    run_id = register_run("metrics", {"alpha": args.alpha})

    try:
        # Calculate validation metrics
        metrics = calculate_validation_metrics(
            simulated_path="data/simulation/error_rates_summary.csv",
            real_data_path="data/simulation/real_data_pvalues.csv"
        )

        # Save metrics
        save_validation_metrics(metrics, "data/simulation/validation_metrics.json")

        update_run_status(run_id, "completed", {"metrics_count": len(metrics)})
        logger.info("Validation metrics calculation completed successfully")
        return {"status": "completed", "metrics_count": len(metrics)}
    except Exception as e:
        update_run_status(run_id, "failed", {"error": str(e)})
        log_error_details(e)
        raise

def run_report(args: argparse.Namespace) -> Dict[str, Any]:
    """Generate final validation report."""
    logger.info("Generating validation report...")
    ensure_metadata_file_exists()

    run_id = register_run("report", {})

    try:
        # Generate report
        report_content = generate_report(
            error_rates_path="data/simulation/error_rates_summary.csv",
            thresholds_path="data/simulation/thresholds.json",
            validation_metrics_path="data/simulation/validation_metrics.json",
            real_data_power_path="data/simulation/real_data_power.json",
            output_path="data/reports/validation_report.md"
        )

        update_run_status(run_id, "completed", {"report_generated": True})
        logger.info("Report generation completed successfully")
        return {"status": "completed", "report_generated": True}
    except Exception as e:
        update_run_status(run_id, "failed", {"error": str(e)})
        log_error_details(e)
        raise

def run_full_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    """Run the complete pipeline with memory optimization."""
    logger.info("Starting full pipeline with memory optimization...")
    start_time = time.time()

    results = {}

    try:
        # Step 1: Simulation
        if args.mode in ["full", "simulation"]:
            results["simulation"] = run_simulation(args)

        # Step 2: Aggregation
        if args.mode in ["full", "aggregation"]:
            results["aggregation"] = run_aggregation(args)

        # Step 3: Thresholds
        if args.mode in ["full", "thresholds"]:
            results["thresholds"] = run_thresholds(args)

        # Step 4: Plots
        if args.mode in ["full", "plots"]:
            results["plots"] = run_plots(args)

        # Step 5: Validation
        if args.mode in ["full", "validation"]:
            results["validation"] = run_validation(args)

        # Step 6: Bootstrap
        if args.mode in ["full", "bootstrap"]:
            results["bootstrap"] = run_bootstrap(args)

        # Step 7: Metrics
        if args.mode in ["full", "metrics"]:
            results["metrics"] = run_metrics(args)

        # Step 8: Report
        if args.mode in ["full", "report"]:
            results["report"] = run_report(args)

        elapsed_time = time.time() - start_time
        logger.info(f"Full pipeline completed in {elapsed_time:.2f} seconds")

        # Final memory check
        final_memory = get_memory_usage_mb()
        logger.info(f"Final memory usage: {final_memory:.2f}MB")

        return {
            "status": "completed",
            "results": results,
            "elapsed_time": elapsed_time,
            "final_memory_mb": final_memory
        }

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        log_error_details(e)
        return {"status": "failed", "error": str(e)}

def main():
    """Main entry point."""
    args = parse_args()

    # Set garbage collection threshold
    gc.set_threshold(args.gc_threshold)

    try:
        if args.mode == "full":
            result = run_full_pipeline(args)
        elif args.mode == "simulation":
            result = run_simulation(args)
        elif args.mode == "aggregation":
            result = run_aggregation(args)
        elif args.mode == "thresholds":
            result = run_thresholds(args)
        elif args.mode == "plots":
            result = run_plots(args)
        elif args.mode == "validation":
            result = run_validation(args)
        elif args.mode == "bootstrap":
            result = run_bootstrap(args)
        elif args.mode == "metrics":
            result = run_metrics(args)
        elif args.mode == "report":
            result = run_report(args)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)

        if result["status"] == "completed":
            logger.info("Pipeline completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Pipeline failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
