"""
Benchmark runner for performance optimization validation.
Measures total runtime across baseline and spiking training runs to ensure <6h total.
"""
import os
import sys
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import training runners
from run_baseline_seeds import run_all_seeds as run_baseline_seeds_main
from run_spiking_seeds import run_all_seeds as run_spiking_seeds_main
from utils.logging_config import setup_logging, get_logger

# Setup logging
logger = get_logger("benchmark_runner")

def run_single_benchmark(
    name: str,
    runner_func: callable,
    config: Dict[str, Any],
    output_path: str
) -> Dict[str, Any]:
    """
    Run a single benchmark (baseline or spiking) and record timing.

    Args:
        name: Name of the benchmark (e.g., "baseline", "spiking")
        runner_func: Function to run the benchmark
        config: Configuration dictionary for the run
        output_path: Path to save results

    Returns:
        Dictionary with timing results
    """
    logger.info(f"Starting benchmark: {name}")
    start_time = time.time()

    try:
        # Run the benchmark
        runner_func(config)
        end_time = time.time()
        duration = end_time - start_time

        result = {
            "name": name,
            "status": "success",
            "duration_seconds": duration,
            "duration_hours": duration / 3600,
            "timestamp": datetime.now().isoformat(),
            "config": config
        }

        logger.info(f"Benchmark {name} completed in {duration:.2f} seconds ({duration/3600:.2f} hours)")

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time

        result = {
            "name": name,
            "status": "failed",
            "duration_seconds": duration,
            "duration_hours": duration / 3600,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "config": config
        }

        logger.error(f"Benchmark {name} failed after {duration:.2f} seconds: {e}")

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    return result

def run_full_benchmark(
    baseline_config: Optional[Dict[str, Any]] = None,
    spiking_config: Optional[Dict[str, Any]] = None,
    output_dir: str = "data/results"
) -> Dict[str, Any]:
    """
    Run full benchmark suite (baseline + spiking) and aggregate results.

    Args:
        baseline_config: Configuration for baseline training
        spiking_config: Configuration for spiking training
        output_dir: Directory to save results

    Returns:
        Aggregated results dictionary
    """
    if baseline_config is None:
        baseline_config = {
            "num_seeds": 3,
            "epochs": 3,
            "batch_size": 32,
            "lr": 1e-3,
            "early_stopping_patience": 2
        }

    if spiking_config is None:
        spiking_config = {
            "num_seeds": 3,
            "epochs": 3,
            "batch_size": 32,
            "lr": 1e-3,
            "time_steps": 5,
            "beta": 0.9,
            "early_stopping_patience": 2
        }

    os.makedirs(output_dir, exist_ok=True)

    # Run baseline benchmark
    baseline_output = os.path.join(output_dir, "baseline_benchmark.json")
    baseline_result = run_single_benchmark(
        "baseline",
        run_baseline_seeds_main,
        baseline_config,
        baseline_output
    )

    # Run spiking benchmark
    spiking_output = os.path.join(output_dir, "spiking_benchmark.json")
    spiking_result = run_single_benchmark(
        "spiking",
        run_spiking_seeds_main,
        spiking_config,
        spiking_output
    )

    # Aggregate results
    total_duration = baseline_result["duration_seconds"] + spiking_result["duration_seconds"]
    total_hours = total_duration / 3600

    aggregated = {
        "baseline": baseline_result,
        "spiking": spiking_result,
        "total_duration_seconds": total_duration,
        "total_duration_hours": total_hours,
        "meets_6h_requirement": total_hours < 6.0,
        "timestamp": datetime.now().isoformat()
    }

    # Save aggregated results
    aggregated_output = os.path.join(output_dir, "benchmark_summary.json")
    with open(aggregated_output, 'w') as f:
        json.dump(aggregated, f, indent=2)

    logger.info(f"Full benchmark completed. Total time: {total_hours:.2f} hours")
    logger.info(f"Meets 6h requirement: {aggregated['meets_6h_requirement']}")

    return aggregated

def main():
    """Main entry point for benchmark runner."""
    parser = argparse.ArgumentParser(description="Run performance benchmarks")
    parser.add_argument(
        "--num-seeds",
        type=int,
        default=3,
        help="Number of random seeds to use (default: 3)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of epochs per run (default: 3)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/results",
        help="Output directory for results (default: data/results)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size (default: 32)"
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-3,
        help="Learning rate (default: 1e-3)"
    )

    args = parser.parse_args()

    # Setup configurations
    baseline_config = {
        "num_seeds": args.num_seeds,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "early_stopping_patience": 2
    }

    spiking_config = {
        "num_seeds": args.num_seeds,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "time_steps": 5,
        "beta": 0.9,
        "early_stopping_patience": 2
    }

    # Run benchmark
    results = run_full_benchmark(
        baseline_config=baseline_config,
        spiking_config=spiking_config,
        output_dir=args.output_dir
    )

    # Print summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    print(f"Baseline duration: {results['baseline']['duration_hours']:.2f} hours")
    print(f"Spiking duration:  {results['spiking']['duration_hours']:.2f} hours")
    print(f"Total duration:    {results['total_duration_hours']:.2f} hours")
    print(f"Meets 6h target:   {results['meets_6h_requirement']}")
    print("="*60)

    if not results['meets_6h_requirement']:
        print("\nWARNING: Total runtime exceeds 6 hours!")
        print("Consider reducing num_seeds or epochs for faster execution.")
        sys.exit(1)
    else:
        print("\nSUCCESS: Total runtime is within 6-hour budget.")
        sys.exit(0)

if __name__ == "__main__":
    setup_logging()
    main()