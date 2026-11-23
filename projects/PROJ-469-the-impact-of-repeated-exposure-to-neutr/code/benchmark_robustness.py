"""
Benchmark script to verify T035: Runtime < 6h on 2-core CPU.
This script runs the bootstrap pipeline with multiprocessing and measures time.
"""
import time
import logging
import pandas as pd
from pathlib import Path
from config_manager import get_data_processed_path, get_config
from logging_config import setup_logging, get_logger
from robustness import run_bootstrap_pipeline

def main():
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting Robustness Benchmark (T035).")
    
    # Load data
    data_path = get_data_processed_path()
    if not Path(data_path).exists():
        logger.error(f"Data not found at {data_path}. Please run preprocessing first.")
        return
    
    data = pd.read_csv(data_path)
    logger.info(f"Loaded {len(data)} rows from {data_path}")
    
    # Configuration
    config = get_config()
    n_resamples = config.get('bootstrap_count', 1000)
    logger.info(f"Running {n_resamples} bootstrap resamples.")
    
    start_time = time.time()
    
    # Run bootstrap
    try:
        results, metrics = run_bootstrap_pipeline(data)
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
        return
    
    elapsed = time.time() - start_time
    hours = elapsed / 3600
    
    logger.info(f"Benchmark completed in {elapsed:.2f} seconds ({hours:.2f} hours).")
    
    # Check constraint
    if hours < 6.0:
        logger.info("SUCCESS: Runtime is under 6 hours.")
    else:
        logger.warning("FAILURE: Runtime exceeded 6 hours.")
        
    # Save benchmark results
    benchmark_results = {
        'n_resamples': n_resamples,
        'elapsed_seconds': elapsed,
        'elapsed_hours': hours,
        'status': 'PASS' if hours < 6.0 else 'FAIL'
    }
    
    results_dir = Path(__file__).parent.parent / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    benchmark_path = results_dir / 'benchmark_robustness.csv'
    
    pd.DataFrame([benchmark_results]).to_csv(benchmark_path, index=False)
    logger.info(f"Benchmark results saved to {benchmark_path}")

if __name__ == '__main__':
    main()
