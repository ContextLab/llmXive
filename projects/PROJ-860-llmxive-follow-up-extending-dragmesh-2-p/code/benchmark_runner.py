"""
Benchmark Runner for llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

This script runs the full end-to-end benchmark pipeline, measuring:
1. Wall-clock time for the entire pipeline (must be <= 6 hours)
2. Peak memory usage (must be <= 7GB)

It orchestrates:
- Object generation (T007a)
- Training (T012)
- Evaluation (T013)
- Aggregation (T014a)
- Analysis (T014)

Results are logged to data/results/benchmark_metrics.json
"""
import os
import sys
import time
import json
import tracemalloc
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
GENERATED_DIR = DATA_DIR / "generated"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Import project modules
sys.path.insert(0, str(CODE_DIR))

from generator import NovelObjectSet, main as generate_main
from train import main as train_main
from evaluate import main as evaluate_main
from aggregate import main as aggregate_main
from analysis import main as analysis_main
from seed_config import init_reproducibility, get_seed
from logging_config import setup_all_loggers

def setup_logging():
    """Setup benchmark-specific logging"""
    logger = logging.getLogger("benchmark")
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(RESULTS_DIR / "benchmark.log")
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def run_pipeline_component(
    name: str, 
    func, 
    logger: logging.Logger, 
    args: tuple = (), 
    kwargs: dict = None
) -> Dict[str, Any]:
    """
    Run a pipeline component with timing and memory profiling.
    
    Args:
        name: Name of the component
        func: Function to execute
        logger: Logger instance
        args: Positional arguments for func
        kwargs: Keyword arguments for func
        
    Returns:
        Dictionary with timing and memory metrics
    """
    if kwargs is None:
        kwargs = {}
        
    logger.info(f"Starting {name}...")
    
    # Start memory profiling
    tracemalloc.start()
    start_time = time.time()
    
    try:
        func(*args, **kwargs)
        success = True
        error_msg = None
    except Exception as e:
        success = False
        error_msg = str(e)
        logger.error(f"{name} failed: {error_msg}")
        raise
    finally:
        # Stop memory profiling and get peak
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        elapsed_time = time.time() - start_time
        
        metrics = {
            "component": name,
            "success": success,
            "elapsed_seconds": elapsed_time,
            "peak_memory_bytes": peak,
            "peak_memory_mb": peak / (1024 * 1024),
            "error": error_msg
        }
        
        logger.info(
            f"{name} completed: "
            f"time={elapsed_time:.2f}s, "
            f"peak_memory={metrics['peak_memory_mb']:.2f}MB"
        )
        
        return metrics

def main():
    """Main benchmark runner"""
    parser = argparse.ArgumentParser(description="Run full end-to-end benchmark")
    parser.add_argument(
        "--seed", 
        type=int, 
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--num-objects",
        type=int,
        default=5,
        help="Number of novel objects to generate for testing"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=2,
        help="Number of episodes per object"
    )
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info("Starting full end-to-end benchmark")
    logger.info(f"Seed: {args.seed}, Objects: {args.num_objects}, Episodes: {args.episodes}")
    
    # Initialize reproducibility
    if args.seed is not None:
        init_reproducibility(args.seed)
        logger.info(f"Reproducibility initialized with seed {args.seed}")
    else:
        logger.warning("No seed provided - results may not be reproducible")
    
    # Start overall benchmark timing
    benchmark_start = time.time()
    tracemalloc.start()
    
    all_metrics = {
        "benchmark_start": datetime.now().isoformat(),
        "config": {
            "seed": args.seed,
            "num_objects": args.num_objects,
            "episodes_per_object": args.episodes
        },
        "components": []
    }
    
    try:
        # Step 1: Generate novel objects
        # We need to pass arguments to the generator
        # Since the generator main() doesn't accept args directly, we'll call the class
        logger.info("Step 1: Generating novel objects")
        
        # Create and run generator
        generator = NovelObjectSet(
            output_dir=str(GENERATED_DIR),
            num_objects=args.num_objects,
            seed=args.seed
        )
        generator.generate_all()
        
        component_metrics = {
            "component": "generation",
            "success": True,
            "elapsed_seconds": 0,  # Will be updated
            "peak_memory_bytes": 0,
            "peak_memory_mb": 0,
            "error": None
        }
        all_metrics["components"].append(component_metrics)
        
        # Step 2: Training
        logger.info("Step 2: Running training pipeline")
        training_metrics = run_pipeline_component(
            "training",
            train_main,
            logger,
            args=(),
            kwargs={
                "num_episodes": args.episodes,
                "seed": args.seed
            }
        )
        all_metrics["components"].append(training_metrics)
        
        # Step 3: Evaluation
        logger.info("Step 3: Running evaluation pipeline")
        evaluation_metrics = run_pipeline_component(
            "evaluation",
            evaluate_main,
            logger,
            args=(),
            kwargs={
                "num_episodes": args.episodes,
                "seed": args.seed
            }
        )
        all_metrics["components"].append(evaluation_metrics)
        
        # Step 4: Aggregation
        logger.info("Step 4: Running aggregation pipeline")
        aggregation_metrics = run_pipeline_component(
            "aggregation",
            aggregate_main,
            logger,
            args=(),
            kwargs={}
        )
        all_metrics["components"].append(aggregation_metrics)
        
        # Step 5: Analysis
        logger.info("Step 5: Running analysis pipeline")
        analysis_metrics = run_pipeline_component(
            "analysis",
            analysis_main,
            logger,
            args=(),
            kwargs={}
        )
        all_metrics["components"].append(analysis_metrics)
        
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        all_metrics["error"] = str(e)
        all_metrics["success"] = False
    finally:
        # Final metrics
        benchmark_end = time.time()
        current, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        all_metrics["benchmark_end"] = datetime.now().isoformat()
        all_metrics["total_elapsed_seconds"] = benchmark_end - benchmark_start
        all_metrics["total_elapsed_hours"] = (benchmark_end - benchmark_start) / 3600
        all_metrics["peak_memory_bytes"] = peak_memory
        all_metrics["peak_memory_mb"] = peak_memory / (1024 * 1024)
        all_metrics["peak_memory_gb"] = peak_memory / (1024 * 1024 * 1024)
        
        # Assertions for constraints
        time_limit_hours = 6
        memory_limit_gb = 7.0
        
        all_metrics["time_constraint_passed"] = all_metrics["total_elapsed_hours"] <= time_limit_hours
        all_metrics["memory_constraint_passed"] = all_metrics["peak_memory_gb"] <= memory_limit_gb
        all_metrics["success"] = all_metrics.get("success", True) and \
                                all_metrics["time_constraint_passed"] and \
                                all_metrics["memory_constraint_passed"]
        
        # Log final results
        logger.info("=" * 60)
        logger.info("BENCHMARK RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total time: {all_metrics['total_elapsed_hours']:.2f} hours "
                   f"(limit: {time_limit_hours}h) - {'PASS' if all_metrics['time_constraint_passed'] else 'FAIL'}")
        logger.info(f"Peak memory: {all_metrics['peak_memory_gb']:.2f} GB "
                   f"(limit: {memory_limit_gb}GB) - {'PASS' if all_metrics['memory_constraint_passed'] else 'FAIL'}")
        logger.info(f"Overall status: {'PASS' if all_metrics['success'] else 'FAIL'}")
        
        # Write results to JSON
        results_file = RESULTS_DIR / "benchmark_metrics.json"
        with open(results_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        
        logger.info(f"Results written to {results_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"Total Time: {all_metrics['total_elapsed_hours']:.2f}h <= {time_limit_hours}h? {all_metrics['time_constraint_passed']}")
        print(f"Peak Memory: {all_metrics['peak_memory_gb']:.2f}GB <= {memory_limit_gb}GB? {all_metrics['memory_constraint_passed']}")
        print(f"Overall: {'SUCCESS' if all_metrics['success'] else 'FAILURE'}")
        
        return 0 if all_metrics['success'] else 1

if __name__ == "__main__":
    sys.exit(main())
