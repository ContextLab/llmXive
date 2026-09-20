import sys
import os
import time
import json
import subprocess
import resource
import logging
from pathlib import Path
from config import get_config, ensure_directories
from utils import setup_logging, exit_with_error

def get_peak_memory_mb() -> float:
    """
    Returns the peak memory usage of the current process in MB.
    """
    try:
        # ru_maxrss is in KB on Linux, but sometimes bytes or different units on others.
        # On Linux/macOS it's usually KB.
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0  # Convert KB to MB
    except Exception as e:
        logging.warning(f"Could not determine memory usage: {e}")
        return 0.0

def run_generation_pipeline() -> Dict[str, Any]:
    """
    Runs the generation script and captures timing and memory metrics.
    Returns a dictionary with execution time and peak memory.
    """
    # Reset resource usage stats before running the logic
    resource.setrlimit(resource.RUSAGE_SELF, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    
    start_time = time.time()
    
    # We import and run the main logic directly to measure the process itself,
    # rather than spawning a subprocess, to get accurate resource usage of the generator.
    # However, to isolate the 'generation' part, we assume this script is the wrapper.
    # Since T014 is about the generation script itself, we measure the call to generate_primes.main()
    
    # Import the generation logic
    try:
        from generate_primes import main as gen_main
    except ImportError:
        exit_with_error("generate_primes module not found.")

    # Run the generation
    try:
        gen_main()
    except SystemExit as e:
        if e.code != 0:
            exit_with_error(f"Generation pipeline failed with exit code {e.code}")
    
    end_time = time.time()
    execution_time = end_time - start_time
    peak_memory = get_peak_memory_mb()

    return {
        "execution_time_seconds": round(execution_time, 3),
        "peak_memory_mb": round(peak_memory, 2)
    }

def main():
    """
    Main entry point for measuring generation performance.
    Saves metrics to data/results/performance_gen.json.
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger = setup_logging(level=log_level)

    config = get_config()
    ensure_directories(config)
    
    output_path = Path(config['data']['results']) / 'performance_gen.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting performance measurement for generation pipeline...")
    
    metrics = run_generation_pipeline()
    
    # Save metrics
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Performance metrics saved to {output_path}")
    logger.info(f"Execution Time: {metrics['execution_time_seconds']}s")
    logger.info(f"Peak Memory: {metrics['peak_memory_mb']} MB")

if __name__ == "__main__":
    main()