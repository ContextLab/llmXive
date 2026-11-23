import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional
import resource
import os

# Import existing pipeline stages
from download import main as run_download_main
from generate import main as run_generation_main
from analyze import main as run_analysis_main
from stats import main as run_statistics_main
from config import get_config, set_seed, ensure_directories, get_paths

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Resource limits (SC-004)
MAX_CPU_HOURS = 6.0
MAX_MEMORY_GB = 7.0

def log_resource_usage(stage_name: str, start_time: float, start_mem: int):
    """
    Logs CPU time and memory usage for a specific stage.
    Checks against SC-004 limits (<=6h CPU, <=7GB RAM).
    """
    end_time = time.time()
    end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # In KB on Linux/macOS

    elapsed_seconds = end_time - start_time
    elapsed_hours = elapsed_seconds / 3600.0
    memory_gb = end_mem / (1024 * 1024)  # Convert KB to GB

    logger.info(f"--- Resource Usage: {stage_name} ---")
    logger.info(f"  CPU Time Elapsed: {elapsed_hours:.2f} hours ({elapsed_seconds:.1f} seconds)")
    logger.info(f"  Peak Memory Usage: {memory_gb:.2f} GB ({end_mem / 1024:.1f} MB)")

    # Check limits
    if elapsed_hours > MAX_CPU_HOURS:
        logger.error(f"CRITICAL: CPU time limit exceeded for {stage_name}. Limit: {MAX_CPU_HOURS}h, Actual: {elapsed_hours:.2f}h")
        raise MemoryError(f"Pipeline exceeded CPU time limit ({MAX_CPU_HOURS}h).")

    if memory_gb > MAX_MEMORY_GB:
        logger.error(f"CRITICAL: Memory limit exceeded for {stage_name}. Limit: {MAX_MEMORY_GB}GB, Actual: {memory_gb:.2f}GB")
        raise MemoryError(f"Pipeline exceeded memory limit ({MAX_MEMORY_GB}GB).")

    logger.info(f"  Status: OK (Within limits)")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="llmXive Vulnerability Density Pipeline")
    parser.add_argument("--models", type=str, nargs="+", default=["starcoder", "codegen"],
                        help="List of models to evaluate (e.g., starcoder codegen)")
    parser.add_argument("--benchmarks", type=str, nargs="+", default=["humaneval", "mbpp"],
                        help="List of benchmarks to use (e.g., humaneval mbpp)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--skip-download", action="store_true", help="Skip dataset download if already present")
    parser.add_argument("--skip-generation", action="store_true", help="Skip code generation if samples exist")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip static analysis if reports exist")
    parser.add_argument("--skip-stats", action="store_true", help="Skip statistical analysis if results exist")
    return parser.parse_args()

def run_download(args: argparse.Namespace):
    logger.info("Starting Download Stage...")
    start_time = time.time()
    start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    
    try:
        # Prepare arguments for download module
        sys.argv = ['download', '--benchmarks'] + args.benchmarks
        run_download_main()
    except SystemExit as e:
        if e.code != 0:
            raise
    finally:
        log_resource_usage("Download", start_time, start_mem)

def run_generation(args: argparse.Namespace):
    logger.info("Starting Generation Stage...")
    start_time = time.time()
    start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    try:
        # Prepare arguments for generation module
        sys.argv = ['generate', '--models'] + args.models + ['--benchmarks'] + args.benchmarks + ['--seed', str(args.seed)]
        run_generation_main()
    except SystemExit as e:
        if e.code != 0:
            raise
    finally:
        log_resource_usage("Generation", start_time, start_mem)

def run_analysis(args: argparse.Namespace):
    logger.info("Starting Analysis Stage...")
    start_time = time.time()
    start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    try:
        # Prepare arguments for analysis module
        sys.argv = ['analyze']
        run_analysis_main()
    except SystemExit as e:
        if e.code != 0:
            raise
    finally:
        log_resource_usage("Analysis", start_time, start_mem)

def run_statistics(args: argparse.Namespace):
    logger.info("Starting Statistics Stage...")
    start_time = time.time()
    start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    try:
        # Prepare arguments for stats module
        sys.argv = ['stats']
        run_statistics_main()
    except SystemExit as e:
        if e.code != 0:
            raise
    finally:
        log_resource_usage("Statistics", start_time, start_mem)

def main():
    args = parse_args()
    
    # Initialize config and paths
    config = get_config()
    set_seed(args.seed)
    ensure_directories()
    paths = get_paths()

    logger.info(f"Pipeline started with seed: {args.seed}")
    logger.info(f"Models: {args.models}")
    logger.info(f"Benchmarks: {args.benchmarks}")
    logger.info(f"Max CPU Limit: {MAX_CPU_HOURS}h, Max Memory Limit: {MAX_MEMORY_GB}GB")

    try:
        if not args.skip_download:
            run_download(args)
        
        if not args.skip_generation:
            run_generation(args)
        
        if not args.skip_analysis:
            run_analysis(args)
        
        if not args.skip_stats:
            run_statistics(args)

        logger.info("Pipeline completed successfully within resource limits.")
    except MemoryError as e:
        logger.error(f"Pipeline halted due to resource constraints: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()