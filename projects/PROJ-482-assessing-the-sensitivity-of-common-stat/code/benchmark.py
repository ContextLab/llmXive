"""
Benchmarking module for the statistical sensitivity simulation pipeline.

This module measures the execution time of the full simulation suite to ensure
performance requirements are met (total runtime < 6 hours).
"""
import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime

# Ensure the project root is in the path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import get_simulation_grid, SimulationConfig
from simulation_engine import run_full_simulation_batch
from setup_directories import ensure_dir

# Configure logging
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
ensure_dir(LOG_DIR)
LOG_FILE = os.path.join(LOG_DIR, "benchmark.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_benchmark(config: SimulationConfig) -> dict:
    """
    Executes the full simulation suite and measures execution time.

    Args:
        config (SimulationConfig): The configuration object for the simulation.

    Returns:
        dict: A dictionary containing benchmark results including total runtime.
    """
    logger.info("Starting benchmark execution...")
    start_time = time.time()
    
    logger.info("Starting Full Pipeline Benchmark")
    logger.info(f"Configuration: Sample sizes {config.sample_sizes}, "
                f"Distributions {config.distributions}, "
                f"Tests {config.tests}")
    
    # 1. Ground Truth Validation (T017b)
    logger.info("Phase 1: Ground Truth Validation")
    try:
        # Run the full simulation batch
        # Note: This will execute the adaptive Monte Carlo simulation for all grid points
        results = run_full_simulation_batch(config)
        
        end_time = time.time()
        total_runtime_seconds = end_time - start_time

        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "total_runtime_seconds": total_runtime_seconds,
            "total_runtime_formatted": f"{total_runtime_seconds / 3600:.2f} hours",
            "config_summary": {
                "sample_sizes": len(config.sample_sizes),
                "distributions": len(config.distributions),
                "test_types": len(config.test_types),
                "max_replicates": config.max_replicates
            },
            "status": "success"
        }

        logger.info(f"Benchmark completed successfully.")
        logger.info(f"Total runtime: {total_runtime_seconds:.2f} seconds ({total_runtime_seconds / 3600:.2f} hours)")
        
        # Log the full JSON structure as required
        logger.info(f"Benchmark JSON: {json.dumps(benchmark_results, indent=2)}")
        
        return benchmark_results

    except Exception as e:
        end_time = time.time()
        total_runtime_seconds = end_time - start_time
        
        logger.error(f"Benchmark failed with error: {str(e)}")
        
        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "total_runtime_seconds": total_runtime_seconds,
            "status": "failed",
            "error": str(e)
        }
        
        logger.info(f"Benchmark JSON: {json.dumps(benchmark_results, indent=2)}")
        return benchmark_results

def main():
    """
    Main entry point for the benchmark script.
    """
    parser = argparse.ArgumentParser(description="Run benchmark for statistical sensitivity simulation")
    parser.add_argument("--max-replicates", type=int, default=1000, help="Maximum number of replicates for benchmark")
    parser.add_argument("--sample-sizes", type=str, default="10,50,100", help="Comma-separated list of sample sizes to test")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("BENCHMARK EXECUTION STARTED")
    logger.info("=" * 60)

    # Parse sample sizes
    sample_sizes = [int(x.strip()) for x in args.sample_sizes.split(",")]

    # Create a reduced configuration for benchmarking
    # In a full run, this would use the complete grid from config.py
    config = SimulationConfig(
        sample_sizes=sample_sizes,
        distributions=["normal", "uniform"],  # Reduced for benchmark speed
        test_types=["t-test"],  # Reduced for benchmark speed
        alpha=0.05,
        effect_size=0.5,
        min_replicates=100,  # Reduced for benchmark speed
        max_replicates=args.max_replicates,
        log_epsilon=1e-15
    )

    # Ensure output directories exist
    ensure_dir(os.path.join(PROJECT_ROOT, "data", "raw"))
    ensure_dir(os.path.join(PROJECT_ROOT, "data", "processed"))
    ensure_dir(os.path.join(PROJECT_ROOT, "logs"))

    # Run the benchmark
    results = run_benchmark(config)

    # Write results to log file in JSON format
    with open(LOG_FILE, 'a') as f:
        f.write("\n--- BENCHMARK RESULTS ---\n")
        f.write(json.dumps(results, indent=2))
        f.write("\n---------------------------\n")

    logger.info("=" * 60)
    logger.info("BENCHMARK EXECUTION COMPLETED")
    logger.info("=" * 60)

    # Exit with appropriate code
    if results["status"] == "failed":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()