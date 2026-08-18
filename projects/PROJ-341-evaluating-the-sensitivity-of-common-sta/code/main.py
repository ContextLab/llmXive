"""
Main entry point for the simulation pipeline.
Orchestrates simulation, aggregation, threshold finding, visualization, and validation.
Implements streaming/batch processing to respect memory constraints (< 7GB RAM).
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
import tracemalloc
from typing import List, Dict, Any, Optional, Tuple

# Local imports from project structure
from code.simulation.test_runner import run_simulation_condition
from code.simulation.output_writer import write_p_values_raw, ensure_output_directory
from code.analysis.aggregator import main as aggregator_main, load_p_values_raw_safe, save_aggregated_results
from code.analysis.threshold_finder import main as threshold_main, save_thresholds
from code.visualization.plotter import main as plotter_main
from code.analysis.validator import main as validator_main
from code.analysis.bootstrapper import main as bootstrapper_main
from code.analysis.validation_metrics import main as metrics_main
from code.analysis.report_generator import main as report_main
from code.simulation.logging_config import get_logger, log_operation

# Constants
MAX_RAM_MB = 7168  # 7GB limit
MAX_RUNTIME_SECONDS = 21600  # 6 hours
BATCH_SIZE_DEFAULT = 50  # Number of sample sizes to process in one batch
DEFAULT_MIN_N = 5
DEFAULT_MAX_N = 500
DEFAULT_STEP = 5
DEFAULT_ITERATIONS = 10000

logger = get_logger(__name__)


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        # Try to use resource module if available (Unix)
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux
    except ImportError:
        # Fallback for Windows or if resource not available
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Last resort: return 0 if we can't measure
            return 0.0


def check_memory_limit(current_mb: float) -> bool:
    """Check if current memory usage exceeds the limit."""
    if current_mb > MAX_RAM_MB:
        logger.log("MEMORY_EXCEEDED", f"Current usage {current_mb:.2f}MB exceeds limit {MAX_RAM_MB}MB")
        return False
    return True


def force_gc() -> None:
    """Force garbage collection to free up memory."""
    gc.collect()
    gc.collect()
    gc.collect()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run statistical test sensitivity simulation pipeline."
    )
    parser.add_argument(
        "--mode",
        choices=["simulation", "aggregation", "thresholds", "plots", "validation", "bootstrap", "metrics", "report", "full"],
        default="full",
        help="Pipeline mode to run"
    )
    parser.add_argument(
        "--test",
        choices=["t-test", "anova", "chi-squared", "all"],
        default="all",
        help="Which statistical test to run"
    )
    parser.add_argument(
        "--min-n",
        type=int,
        default=DEFAULT_MIN_N,
        help=f"Minimum sample size (default: {DEFAULT_MIN_N})"
    )
    parser.add_argument(
        "--max-n",
        type=int,
        default=DEFAULT_MAX_N,
        help=f"Maximum sample size (default: {DEFAULT_MAX_N})"
    )
    parser.add_argument(
        "--step",
        type=int,
        default=DEFAULT_STEP,
        help=f"Step size for sample sizes (default: {DEFAULT_STEP})"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Number of iterations per condition (default: {DEFAULT_ITERATIONS})"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (default: 0.05)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE_DEFAULT,
        help=f"Number of sample sizes to process per batch (default: {BATCH_SIZE_DEFAULT})"
    )
    parser.add_argument(
        "--effect-size",
        type=float,
        default=0.5,
        help="Effect size for simulation (default: 0.5)"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode with fewer iterations"
    )
    return parser.parse_args()


def run_simulation_batch(
    min_n: int,
    max_n: int,
    step: int,
    iterations: int,
    test_type: str,
    alpha: float,
    effect_size: float,
    batch_size: int
) -> List[Dict[str, Any]]:
    """
    Run simulation in batches to manage memory usage.
    Processes sample sizes in chunks, writing results incrementally.
    """
    sample_sizes = list(range(min_n, max_n + 1, step))
    all_results = []
    
    # Ensure output directory exists
    ensure_output_directory()
    
    # Clear any existing raw p-values file for fresh run
    p_values_file = "data/simulation/p_values_raw.csv"
    if os.path.exists(p_values_file):
        os.remove(p_values_file)
    
    total_batches = (len(sample_sizes) + batch_size - 1) // batch_size
    
    for batch_idx in range(0, len(sample_sizes), batch_size):
        batch = sample_sizes[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        
        logger.log(
            "BATCH_START",
            batch_number=batch_num,
            total_batches=total_batches,
            sample_sizes=batch
        )
        
        # Check memory before processing batch
        mem_mb = get_memory_usage_mb()
        if not check_memory_limit(mem_mb):
            logger.log("MEMORY_ERROR", "Memory limit exceeded, forcing GC and continuing")
            force_gc()
            time.sleep(1)
        
        batch_results = []
        
        for n in batch:
            try:
                # Run simulation for this sample size
                results = run_simulation_condition(
                    sample_size=n,
                    iterations=iterations,
                    test_type=test_type,
                    alpha=alpha,
                    effect_size=effect_size
                )
                batch_results.extend(results)
                
                # Log progress
                if n % (step * 10) == 0:
                    logger.log(
                        "PROGRESS",
                        sample_size=n,
                        total_sample_sizes=len(sample_sizes),
                        current_results=len(batch_results)
                    )
                
            except Exception as e:
                logger.log(
                    "SIMULATION_ERROR",
                    sample_size=n,
                    error=str(e)
                )
                # Continue with next sample size
                continue
        
        # Write batch results to CSV immediately to free memory
        if batch_results:
            write_p_values_raw(batch_results, append=True)
            all_results.extend(batch_results)
            
            # Clear batch results from memory
            batch_results.clear()
            force_gc()
        
        # Check memory after batch
        mem_mb = get_memory_usage_mb()
        logger.log(
            "BATCH_COMPLETE",
            batch_number=batch_num,
            results_written=len(batch_results) if batch_results else 0,
            memory_mb=mem_mb
        )
        
        # Force GC between batches
        if batch_idx + batch_size < len(sample_sizes):
            force_gc()
            time.sleep(0.5)
    
    return all_results


def run_simulation(args: argparse.Namespace) -> Dict[str, Any]:
    """Run the full simulation with batch processing."""
    start_time = time.time()
    tracemalloc.start()
    
    logger.log(
        "SIMULATION_START",
        mode="full",
        min_n=args.min_n,
        max_n=args.max_n,
        step=args.step,
        iterations=args.iterations,
        test_type=args.test,
        alpha=args.alpha
    )
    
    # Determine test types to run
    test_types = ["t-test", "anova", "chi-squared"] if args.test == "all" else [args.test]
    
    all_results = []
    
    for test_type in test_types:
        logger.log("TEST_TYPE_START", test_type=test_type)
        
        results = run_simulation_batch(
            min_n=args.min_n,
            max_n=args.max_n,
            step=args.step,
            iterations=args.iterations if not args.test_mode else 100,
            test_type=test_type,
            alpha=args.alpha,
            effect_size=args.effect_size,
            batch_size=args.batch_size
        )
        
        all_results.extend(results)
        logger.log("TEST_TYPE_COMPLETE", test_type=test_type, count=len(results))
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    runtime = end_time - start_time
    peak_ram_mb = peak / (1024 * 1024)
    
    metrics = {
        "peak_ram_mb": peak_ram_mb,
        "total_runtime": runtime,
        "total_results": len(all_results),
        "test_types_run": test_types,
        "config": {
            "min_n": args.min_n,
            "max_n": args.max_n,
            "step": args.step,
            "iterations": args.iterations,
            "alpha": args.alpha,
            "effect_size": args.effect_size
        }
    }
    
    # Save metrics
    metrics_path = "data/simulation/metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.log(
        "SIMULATION_COMPLETE",
        peak_ram_mb=peak_ram_mb,
        runtime=runtime,
        results_count=len(all_results),
        metrics_file=metrics_path
    )
    
    return metrics


def run_aggregation() -> Dict[str, Any]:
    """Run aggregation to calculate error rates."""
    logger.log("AGGREGATION_START")
    
    # Call aggregator main which reads p_values_raw.csv and writes error_rates_summary.csv
    result = aggregator_main()
    
    logger.log("AGGREGATION_COMPLETE")
    return result


def run_thresholds() -> Dict[str, Any]:
    """Run threshold finding analysis."""
    logger.log("THRESHOLDS_START")
    
    result = threshold_main()
    
    logger.log("THRESHOLDS_COMPLETE")
    return result


def run_plots() -> Dict[str, Any]:
    """Generate visualization plots."""
    logger.log("PLOTS_START")
    
    result = plotter_main()
    
    logger.log("PLOTS_COMPLETE")
    return result


def run_validation() -> Dict[str, Any]:
    """Run validation on real datasets."""
    logger.log("VALIDATION_START")
    
    result = validator_main()
    
    logger.log("VALIDATION_COMPLETE")
    return result


def run_bootstrap() -> Dict[str, Any]:
    """Run bootstrapped power estimation."""
    logger.log("BOOTSTRAP_START")
    
    result = bootstrapper_main()
    
    logger.log("BOOTSTRAP_COMPLETE")
    return result


def run_metrics() -> Dict[str, Any]:
    """Calculate validation metrics."""
    logger.log("METRICS_START")
    
    result = metrics_main()
    
    logger.log("METRICS_COMPLETE")
    return result


def run_report() -> Dict[str, Any]:
    """Generate final validation report."""
    logger.log("REPORT_START")
    
    result = report_main()
    
    logger.log("REPORT_COMPLETE")
    return result


def run_full_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    """Run the complete pipeline in order."""
    start_time = time.time()
    
    logger.log("FULL_PIPELINE_START")
    
    # 1. Run simulation
    sim_metrics = run_simulation(args)
    
    # Check if simulation produced results
    if sim_metrics.get("total_results", 0) == 0:
        logger.log("SIMULATION_ERROR", "No results generated, skipping aggregation")
        return {"error": "Simulation produced no results"}
    
    # 2. Run aggregation
    agg_result = run_aggregation()
    
    # 3. Run threshold finding
    thresh_result = run_thresholds()
    
    # 4. Generate plots
    plot_result = run_plots()
    
    # 5. Run validation (optional, may take longer)
    if not args.test_mode:
        val_result = run_validation()
        boot_result = run_bootstrap()
        metrics_result = run_metrics()
        report_result = run_report()
    else:
        val_result = {"skipped": "test_mode"}
        boot_result = {"skipped": "test_mode"}
        metrics_result = {"skipped": "test_mode"}
        report_result = {"skipped": "test_mode"}
    
    end_time = time.time()
    
    pipeline_metrics = {
        "total_runtime": end_time - start_time,
        "simulation": sim_metrics,
        "aggregation": agg_result,
        "thresholds": thresh_result,
        "plots": plot_result,
        "validation": val_result,
        "bootstrap": boot_result,
        "metrics": metrics_result,
        "report": report_result
    }
    
    logger.log(
        "FULL_PIPELINE_COMPLETE",
        total_runtime=end_time - start_time,
        metrics_saved="data/simulation/pipeline_metrics.json"
    )
    
    return pipeline_metrics


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set test mode parameters if requested
    if args.test_mode:
        args.iterations = 100
        args.min_n = 5
        args.max_n = 50
        args.step = 5
        args.batch_size = 10
        logger.log("TEST_MODE_ENABLED", iterations=args.iterations)
    
    try:
        if args.mode == "simulation":
            result = run_simulation(args)
        elif args.mode == "aggregation":
            result = run_aggregation()
        elif args.mode == "thresholds":
            result = run_thresholds()
        elif args.mode == "plots":
            result = run_plots()
        elif args.mode == "validation":
            result = run_validation()
        elif args.mode == "bootstrap":
            result = run_bootstrap()
        elif args.mode == "metrics":
            result = run_metrics()
        elif args.mode == "report":
            result = run_report()
        elif args.mode == "full":
            result = run_full_pipeline(args)
        else:
            logger.log("ERROR", f"Unknown mode: {args.mode}")
            sys.exit(1)
        
        # Print summary
        print(f"Pipeline completed successfully.")
        if isinstance(result, dict) and "total_runtime" in result:
            print(f"Total runtime: {result['total_runtime']:.2f} seconds")
        if isinstance(result, dict) and "peak_ram_mb" in result:
            print(f"Peak RAM usage: {result['peak_ram_mb']:.2f} MB")
        
    except Exception as e:
        logger.log("PIPELINE_ERROR", error=str(e))
        raise
    finally:
        force_gc()


if __name__ == "__main__":
    main()