import os
import sys
import time
import argparse
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config, ensure_dirs
from utils.logger import get_logger
from utils.exceptions import DataValidationError, ModelConvergenceError
from data.sampler import stratified_sampler, save_sample_metadata
from data_loader import fetch_data, load_m4_hourly, load_uci_electricity, split_series, standardize
from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel
from metrics.coverage import compute_coverage, aggregate_coverage_results
from metrics.pit import compute_pit_metrics
from metrics.crps import compute_crps
from evaluation.runner import load_sample_metadata, process_single_series, run_evaluation

logger = get_logger(__name__)

def time_function(func, *args, **kwargs) -> float:
    """
    Times the execution of a function.
    Returns the elapsed time in seconds.
    """
    start_time = time.perf_counter()
    func(*args, **kwargs)
    end_time = time.perf_counter()
    return end_time - start_time

def run_benchmark_on_subset(
    config: Config,
    models: List[str],
    num_series: int = 10,
    limit_per_model: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Runs the full evaluation pipeline on a stratified subset of data
    to measure runtime.
    
    Args:
        config: Configuration object
        models: List of model names to benchmark (e.g., ['arima', 'prophet'])
        num_series: Number of series to sample from the dataset
        limit_per_model: Optional limit on series per model for speed
        
    Returns:
        List of dictionaries containing benchmark results
    """
    logger.info(f"Starting benchmark on {num_series} series for models: {models}")
    
    # Ensure directories exist
    ensure_dirs(config)
    
    # Load or create sample metadata
    # We assume a sample has been created or we create one on the fly for the benchmark
    # If sample_metadata doesn't exist, we create a small one
    sample_path = config.SAMPLE_METADATA_PATH
    if not sample_path.exists():
        logger.info("No sample metadata found. Creating a stratified sample.")
        # Fetch a small amount of real data to sample from
        try:
            # Attempt to load a small subset of M4 hourly data
            m4_data = load_m4_hourly(limit=num_series * 2) # Fetch slightly more to sample
            if m4_data is None or len(m4_data) == 0:
                raise DataValidationError("Could not load M4 hourly data for sampling.")
            
            # Create sample metadata
            sample_indices = stratified_sampler(m4_data, n_samples=num_series, seed=config.SEED)
            save_sample_metadata(sample_indices, sample_path)
            logger.info(f"Saved sample metadata to {sample_path}")
        except Exception as e:
            logger.error(f"Failed to create sample metadata: {e}")
            raise
    
    sample_meta = load_sample_metadata(sample_path)
    results = []
    
    total_start = time.perf_counter()
    
    for idx, series_info in enumerate(sample_meta):
        series_id = series_info['series_id']
        logger.info(f"Processing series {idx+1}/{len(sample_meta)}: {series_id}")
        
        series_start = time.perf_counter()
        
        for model_name in models:
            if limit_per_model and len([r for r in results if r['model'] == model_name]) >= limit_per_model:
                continue
            
            model_start = time.perf_counter()
            try:
                # Run the evaluation for this series and model
                # We use the existing process_single_series logic but wrap it for timing
                # Note: process_single_series expects a loaded series, we need to fetch it
                # Re-fetching data for the specific series to ensure real data usage
                full_data = fetch_data(config.DATA_DIR, series_id)
                if full_data is None:
                    logger.warning(f"Could not fetch data for {series_id}, skipping.")
                    continue
                    
                train, test = split_series(full_data, test_size=config.TEST_SIZE)
                
                # Initialize model
                if model_name == 'arima':
                    model = ARIMAModel()
                elif model_name == 'prophet':
                    model = ProphetModel()
                elif model_name == 'lstm':
                    model = LSTMModel()
                else:
                    logger.error(f"Unknown model: {model_name}")
                    continue
                
                # Fit and Predict
                model.fit(train)
                predictions, intervals = model.predict(test)
                
                # Metrics
                coverage_res = compute_coverage(test['value'].values, predictions, intervals, config)
                pit_res = compute_pit_metrics(test['value'].values, predictions, intervals)
                crps_val = compute_crps(test['value'].values, predictions, intervals)
                
                model_end = time.perf_counter()
                model_time = model_end - model_start
                
                results.append({
                    'series_id': series_id,
                    'model': model_name,
                    'status': 'success',
                    'runtime_seconds': model_time,
                    'coverage_0.80': coverage_res.get('coverage_0.80', 0.0),
                    'coverage_0.95': coverage_res.get('coverage_0.95', 0.0),
                    'crps': crps_val
                })
                
            except (ModelConvergenceError, DataValidationError) as e:
                model_end = time.perf_counter()
                model_time = model_end - model_start
                logger.warning(f"Series {series_id} / Model {model_name} failed: {e}")
                results.append({
                    'series_id': series_id,
                    'model': model_name,
                    'status': 'failed',
                    'runtime_seconds': model_time,
                    'error': str(e)
                })
            except Exception as e:
                model_end = time.perf_counter()
                model_time = model_end - model_start
                logger.error(f"Unexpected error for {series_id} / {model_name}: {e}")
                results.append({
                    'series_id': series_id,
                    'model': model_name,
                    'status': 'error',
                    'runtime_seconds': model_time,
                    'error': str(e)
                })
        
        series_end = time.perf_counter()
        logger.info(f"Finished series {series_id} in {series_end - series_start:.2f}s")
    
    total_end = time.perf_counter()
    total_time = total_end - total_start
    logger.info(f"Benchmark completed in {total_time:.2f} seconds")
    
    return results

def save_benchmark_results(results: List[Dict[str, Any]], output_path: Path):
    """
    Saves benchmark results to a CSV file.
    """
    logger.info(f"Saving benchmark results to {output_path}")
    if not results:
        logger.warning("No results to save.")
        return
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(results[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} benchmark results.")

def main():
    parser = argparse.ArgumentParser(description="Benchmark the full pipeline on a subset.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--models", type=str, nargs="+", default=["arima", "prophet"], 
                        help="Models to benchmark")
    parser.add_argument("--num-series", type=int, default=5, help="Number of series to process")
    parser.add_argument("--output", type=str, default="results/benchmark_timing.csv", 
                        help="Output path for benchmark results")
    
    args = parser.parse_args()
    
    # Load config
    config = Config(args.config)
    ensure_dirs(config)
    
    # Run benchmark
    results = run_benchmark_on_subset(
        config, 
        models=args.models, 
        num_series=args.num_series
    )
    
    # Save results
    output_path = Path(args.output)
    save_benchmark_results(results, output_path)
    
    print(f"Benchmark completed. Results saved to {output_path}")

if __name__ == "__main__":
    main()