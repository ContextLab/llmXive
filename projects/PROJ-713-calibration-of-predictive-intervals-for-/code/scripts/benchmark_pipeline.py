"""
Benchmark script to run the full pipeline on M4/UCI subset and record runtime.

This script executes the evaluation runner on a subset of the data to measure
total execution time, model fitting times, and metric calculation times.
Results are saved to results/benchmark_timing.csv.
"""
import os
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import RESULTS_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR
from utils.logger import get_logger
from evaluation.runner import run_evaluation, aggregate_and_save_results
from data_loader import load_m4_hourly, load_uci_electricity, split_series
from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel
from metrics.coverage import compute_coverage
from metrics.pit import calculate_pit, ljung_box_test
from metrics.crps import compute_crps
from calibration.conformal import SelfCalibratingConformalWrapper

logger = get_logger(__name__)

def time_function(func, *args, **kwargs) -> tuple:
    """Time a function execution and return result and duration."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    return result, end - start

def run_benchmark_on_subset(
    dataset: str = "m4_hourly",
    num_series: int = 10,
    models: List[str] = None,
    use_conformal: bool = False
) -> Dict[str, Any]:
    """
    Run the full pipeline on a subset of data and record timing metrics.
    
    Args:
        dataset: Dataset to use ('m4_hourly' or 'uci_electricity')
        num_series: Number of series to process (subset size)
        models: List of models to evaluate ('arima', 'prophet', 'lstm')
        use_conformal: Whether to apply conformal prediction wrapper
    
    Returns:
        Dictionary containing timing metrics and results
    """
    if models is None:
        models = ['arima', 'prophet', 'lstm']
    
    logger.info(f"Starting benchmark on {dataset} with {num_series} series")
    logger.info(f"Models: {models}, Conformal: {use_conformal}")
    
    total_start = time.perf_counter()
    
    # Load data
    logger.info("Loading data...")
    load_start = time.perf_counter()
    
    if dataset == "m4_hourly":
        data = load_m4_hourly()
        series_list = list(data.keys())[:num_series]
    elif dataset == "uci_electricity":
        data = load_uci_electricity()
        series_list = list(data.columns[:num_series])
    else:
        raise ValueError(f"Unknown dataset: {dataset}")
    
    load_duration = time.perf_counter() - load_start
    logger.info(f"Data loaded in {load_duration:.2f}s")
    
    # Initialize timing records
    timing_records = []
    results_summary = {
        'total_duration': 0,
        'data_loading': load_duration,
        'models': {},
        'metrics': {},
        'conformal': {},
        'series_processed': num_series,
        'dataset': dataset
    }
    
    # Process each series
    for idx, series_id in enumerate(series_list):
        logger.info(f"Processing series {idx+1}/{num_series}: {series_id}")
        
        if dataset == "m4_hourly":
            series_data = data[series_id]
        else:
            series_data = data[series_id]
        
        train_data, test_data = split_series(series_data, train_ratio=0.8)
        
        series_start = time.perf_counter()
        
        # Fit models
        model_times = {}
        model_results = {}
        
        for model_name in models:
            model_start = time.perf_counter()
            
            try:
                if model_name == 'arima':
                    model = ARIMAModel()
                    forecasts, intervals = model.fit_predict(train_data, test_data)
                elif model_name == 'prophet':
                    model = ProphetModel()
                    forecasts, intervals = model.fit_predict(train_data, test_data)
                elif model_name == 'lstm':
                    model = LSTMModel()
                    forecasts, intervals = model.fit_predict(train_data, test_data)
                else:
                    raise ValueError(f"Unknown model: {model_name}")
                
                model_time = time.perf_counter() - model_start
                model_times[model_name] = model_time
                model_results[model_name] = {
                    'forecasts': forecasts,
                    'intervals': intervals
                }
                
                logger.info(f"  {model_name} completed in {model_time:.2f}s")
                
            except Exception as e:
                logger.error(f"  {model_name} failed: {str(e)}")
                model_times[model_name] = -1
                model_results[model_name] = None
        
        # Calculate metrics
        metric_times = {}
        metric_results = {}
        
        for model_name in models:
            if model_results[model_name] is None:
                continue
            
            metric_start = time.perf_counter()
            
            try:
                forecasts = model_results[model_name]['forecasts']
                intervals = model_results[model_name]['intervals']
                
                # Coverage
                coverage = compute_coverage(test_data, forecasts, intervals)
                
                # PIT
                pit_values, pit_hist = calculate_pit(test_data, forecasts, intervals)
                lb_pvalue = ljung_box_test(pit_values)
                
                # CRPS
                crps_score = compute_crps(test_data, forecasts, intervals)
                
                metric_time = time.perf_counter() - metric_start
                metric_times[model_name] = metric_time
                metric_results[model_name] = {
                    'coverage': coverage,
                    'pit_pvalue': lb_pvalue,
                    'crps': crps_score
                }
                
            except Exception as e:
                logger.error(f"  Metrics for {model_name} failed: {str(e)}")
                metric_times[model_name] = -1
                metric_results[model_name] = None
        
        # Conformal prediction (if requested)
        conformal_time = 0
        conformal_results = None
        if use_conformal:
            conformal_start = time.perf_counter()
            try:
                wrapper = SelfCalibratingConformalWrapper()
                conformal_forecasts, conformal_intervals = wrapper.fit_predict(
                    train_data, test_data, model_results['arima']['forecasts']
                )
                conformal_coverage = compute_coverage(test_data, conformal_forecasts, conformal_intervals)
                conformal_time = time.perf_counter() - conformal_start
                conformal_results = {'coverage': conformal_coverage}
            except Exception as e:
                logger.error(f"  Conformal prediction failed: {str(e)}")
                conformal_time = -1
                conformal_results = None
        
        series_duration = time.perf_counter() - series_start
        
        # Record timing for this series
        timing_records.append({
            'series_id': series_id,
            'series_index': idx + 1,
            'total_series_time': series_duration,
            **{f'{m}_fit_time': model_times.get(m, -1) for m in models},
            **{f'{m}_metric_time': metric_times.get(m, -1) for m in models},
            'conformal_time': conformal_time
        })
        
        # Aggregate results
        results_summary['total_duration'] += series_duration
        for m in models:
            if m not in results_summary['models']:
                results_summary['models'][m] = {'fit_times': [], 'metric_times': []}
            results_summary['models'][m]['fit_times'].append(model_times.get(m, -1))
            results_summary['models'][m]['metric_times'].append(metric_times.get(m, -1))
        
        if use_conformal and conformal_results:
            results_summary['conformal'] = conformal_results
    
    total_duration = time.perf_counter() - total_start
    results_summary['total_duration'] = total_duration
    
    logger.info(f"Benchmark completed in {total_duration:.2f}s")
    
    return {
        'timing_records': pd.DataFrame(timing_records),
        'summary': results_summary
    }

def save_benchmark_results(benchmark_results: Dict[str, Any], output_path: str):
    """Save benchmark results to CSV."""
    timing_df = benchmark_results['timing_records']
    summary = benchmark_results['summary']
    
    # Create summary row
    summary_data = {
        'metric': 'total_duration',
        'value': summary['total_duration'],
        'dataset': summary['dataset'],
        'series_count': summary['series_processed']
    }
    
    for model_name, model_data in summary['models'].items():
        avg_fit = np.mean([t for t in model_data['fit_times'] if t > 0]) if model_data['fit_times'] else -1
        avg_metric = np.mean([t for t in model_data['metric_times'] if t > 0]) if model_data['metric_times'] else -1
        
        summary_data[f'{model_name}_avg_fit_time'] = avg_fit
        summary_data[f'{model_name}_avg_metric_time'] = avg_metric
    
    summary_df = pd.DataFrame([summary_data])
    
    # Combine timing records and summary
    full_df = pd.concat([timing_df, summary_df], ignore_index=True)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    full_df.to_csv(output_path, index=False)
    logger.info(f"Benchmark results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Benchmark the predictive interval calibration pipeline')
    parser.add_argument('--dataset', type=str, default='m4_hourly', 
                      choices=['m4_hourly', 'uci_electricity'],
                      help='Dataset to benchmark on')
    parser.add_argument('--num-series', type=int, default=10,
                      help='Number of series to process')
    parser.add_argument('--models', type=str, nargs='+', default=['arima', 'prophet', 'lstm'],
                      help='Models to evaluate')
    parser.add_argument('--conformal', action='store_true',
                      help='Include conformal prediction in benchmark')
    parser.add_argument('--output', type=str, default=None,
                      help='Output file path (default: results/benchmark_timing.csv)')
    
    args = parser.parse_args()
    
    if args.output is None:
        args.output = str(RESULTS_DIR / 'benchmark_timing.csv')
    
    logger.info(f"Starting benchmark: dataset={args.dataset}, series={args.num_series}")
    
    try:
        results = run_benchmark_on_subset(
            dataset=args.dataset,
            num_series=args.num_series,
            models=args.models,
            use_conformal=args.conformal
        )
        
        save_benchmark_results(results, args.output)
        
        logger.info("Benchmark completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())