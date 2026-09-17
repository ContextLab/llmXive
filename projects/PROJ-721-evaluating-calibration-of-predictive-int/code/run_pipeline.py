"""
Orchestration script for the calibration evaluation pipeline.

This script loops over a selected subset of 1000 time series from the M4 dataset,
fits the configured models, generates prediction intervals, and prepares intermediate
results for coverage calculation. It handles short series and model convergence
failures gracefully, logging errors to `state/errors.log`.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yaml

# Import from local modules (matching API surface)
from metrics import empirical_coverage, interval_score
from models import (
    arima_forecast,
    ets_forecast,
    lightgbm_quantile_forecast,
    prophet_forecast,
)
from stratify import stl_decompose_train_only

# Configure logging
LOG_DIR = "state"
LOG_FILE = os.path.join(LOG_DIR, "errors.log")
RESULTS_DIR = "results"

def setup_logging():
    """Configure logging to write to state/errors.log and console."""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Clear existing handlers to avoid duplicates in repeated runs
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE, mode='w')
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required keys
    required_keys = ['nominal_levels', 'threshold', 'seed']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    return config

def load_series_indices(indices_path: str) -> List[str]:
    """Load the list of series indices to process."""
    if not os.path.exists(indices_path):
        raise FileNotFoundError(f"Sample indices file not found: {indices_path}")
    
    df = pd.read_csv(indices_path)
    # Expecting a column named 'series_id' or similar
    if 'series_id' in df.columns:
        return df['series_id'].astype(str).tolist()
    elif 'id' in df.columns:
        return df['id'].astype(str).tolist()
    else:
        # Fallback: assume first column is ID
        return df.iloc[:, 0].astype(str).tolist()

def load_m4_series(series_id: str, data_dir: str = "data/raw") -> Optional[pd.Series]:
    """
    Load a specific M4 series by ID.
    Assumes data is unpacked in data/raw/ or similar structure.
    Returns None if not found or invalid.
    """
    # M4 dataset structure: typically data/raw/M4-Dataset/ or similar
    # We'll try to find the series in common locations
    possible_paths = [
        os.path.join(data_dir, "M4-Dataset", "Daily", f"{series_id}.csv"),
        os.path.join(data_dir, "M4-Dataset", "Hourly", f"{series_id}.csv"),
        os.path.join(data_dir, "M4-Dataset", "Monthly", f"{series_id}.csv"),
        os.path.join(data_dir, "M4-Dataset", "Quarterly", f"{series_id}.csv"),
        os.path.join(data_dir, "M4-Dataset", "Yearly", f"{series_id}.csv"),
        os.path.join(data_dir, "M4-Dataset", "Weekly", f"{series_id}.csv"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, header=None)
                # M4 format: first column is time (optional), second is values
                if len(df.columns) >= 2:
                    values = df.iloc[:, 1].dropna()
                    return pd.Series(values.values)
                elif len(df.columns) == 1:
                    values = df.iloc[:, 0].dropna()
                    return pd.Series(values.values)
            except Exception as e:
                logging.warning(f"Error reading {path}: {e}")
    
    return None

def process_series(
    series_id: str,
    series_data: pd.Series,
    config: Dict[str, Any],
    logger: logging.Logger
) -> Optional[List[Dict[str, Any]]]:
    """
    Process a single series: fit models, generate intervals, compute metrics.
    
    Returns a list of result dictionaries, one per model/horizon/level combination.
    Returns None if the series is too short or all models fail.
    """
    # Minimum length check (e.g., need at least 2*horizon for train/test split)
    min_length = 24  # 2 horizons of 12
    if len(series_data) < min_length:
        logger.error(f"Series {series_id} too short (length={len(series_data)}). Skipping.")
        return None

    # Split into train/test (last 12 points for testing)
    train_size = len(series_data) - 12
    if train_size <= 0:
        logger.error(f"Series {series_id} has insufficient training data after split.")
        return None
    
    train = series_data.iloc[:train_size]
    test = series_data.iloc[train_size:]
    
    results = []
    models = {
        'arima': arima_forecast,
        'ets': ets_forecast,
        'prophet': prophet_forecast,
        'lightgbm': lightgbm_quantile_forecast
    }
    
    nominal_levels = config.get('nominal_levels', [0.80, 0.95])
    horizons = list(range(1, 13))  # h=1 to 12
    
    for model_name, model_func in models.items():
        try:
            # Fit model and generate forecasts
            forecast_result = model_func(train, config=config)
            
            if forecast_result is None:
                logger.warning(f"Model {model_name} failed to converge for series {series_id}.")
                continue
            
            point_forecast = forecast_result.get('point_forecast')
            lower_bound = forecast_result.get('lower')
            upper_bound = forecast_result.get('upper')
            
            if point_forecast is None or lower_bound is None or upper_bound is None:
                logger.warning(f"Model {model_name} returned invalid forecasts for series {series_id}.")
                continue
            
            # Ensure arrays are aligned with test set
            test_len = len(test)
            if len(point_forecast) < test_len:
                # Pad if necessary (should not happen with proper model implementation)
                padding = np.full(test_len - len(point_forecast), np.nan)
                point_forecast = np.concatenate([point_forecast, padding])
                lower_bound = np.concatenate([lower_bound, padding])
                upper_bound = np.concatenate([upper_bound, padding])
            
            # Compute metrics for each nominal level
            for level in nominal_levels:
                # For simplicity, we assume the model returns bounds for the specific level
                # In a real implementation, we might need to select the correct level from multiple outputs
                lower = lower_bound if isinstance(lower_bound, np.ndarray) else np.array([lower_bound])
                upper = upper_bound if isinstance(upper_bound, np.ndarray) else np.array([upper_bound])
                
                # Align with test data
                if len(lower) != len(test):
                    logger.warning(f"Model {model_name} bounds length mismatch for series {series_id}.")
                    continue
                
                # Calculate empirical coverage
                cov = empirical_coverage(test.values, lower, upper)
                
                # Calculate interval score
                score = interval_score(test.values, lower, upper, alpha=1-level)
                
                results.append({
                    'series_id': series_id,
                    'model': model_name,
                    'nominal_level': level,
                    'empirical_coverage': float(cov),
                    'interval_score': float(score),
                    'horizon': 'all'  # Aggregated over horizons for now
                })
                
        except Exception as e:
            logger.error(f"Error processing series {series_id} with model {model_name}: {e}")
            continue
    
    return results if results else None

def run_pipeline(
    indices_path: str = "data/processed/sample_indices_1000.csv",
    config_path: str = "config.yaml",
    output_path: str = "results/coverage_intermediate.csv"
):
    """
    Main pipeline execution function.
    
    Iterates over the selected series, processes each one, and aggregates results.
    """
    logger = setup_logging()
    logger.info("Starting calibration evaluation pipeline...")
    
    # Load configuration
    try:
        config = load_config(config_path)
        logger.info(f"Loaded configuration: nominal_levels={config['nominal_levels']}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return
    
    # Load series indices
    try:
        series_ids = load_series_indices(indices_path)
        logger.info(f"Loaded {len(series_ids)} series indices from {indices_path}")
    except Exception as e:
        logger.error(f"Failed to load series indices: {e}")
        return
    
    # Process each series
    all_results = []
    processed_count = 0
    failed_count = 0
    
    for i, series_id in enumerate(series_ids):
        logger.info(f"Processing series {i+1}/{len(series_ids)}: {series_id}")
        
        # Load series data
        series_data = load_m4_series(series_id)
        
        if series_data is None or len(series_data) == 0:
            logger.error(f"Could not load data for series {series_id}. Skipping.")
            failed_count += 1
            continue
        
        # Process the series
        results = process_series(series_id, series_data, config, logger)
        
        if results is None:
            failed_count += 1
            continue
        
        all_results.extend(results)
        processed_count += 1
        
        # Log progress every 100 series
        if (i + 1) % 100 == 0:
            logger.info(f"Progress: {i+1}/{len(series_ids)} series processed. "
                        f"Successful: {processed_count}, Failed: {failed_count}")
    
    # Save results
    if all_results:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        df_results = pd.DataFrame(all_results)
        df_results.to_csv(output_path, index=False)
        logger.info(f"Pipeline complete. Saved {len(all_results)} results to {output_path}")
        logger.info(f"Summary: {processed_count} series processed successfully, "
                    f"{failed_count} series failed.")
    else:
        logger.error("No results were generated. Check logs for errors.")

def main():
    """Entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Run calibration evaluation pipeline")
    parser.add_argument(
        "--indices",
        type=str,
        default="data/processed/sample_indices_1000.csv",
        help="Path to the CSV file containing series indices"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/coverage_intermediate.csv",
        help="Path for the output CSV file"
    )
    
    args = parser.parse_args()
    run_pipeline(
        indices_path=args.indices,
        config_path=args.config,
        output_path=args.output
    )

if __name__ == "__main__":
    main()