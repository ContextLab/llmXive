"""
Single-series evaluation runner for debugging and traceability.

This script loads a specific time series, fits a specified model,
generates predictive intervals, and computes calibration metrics.
It outputs a JSON dictionary suitable for debugging and verification.

Usage:
    python -m code.evaluation.runner_single --series-id "M4_hourly_1" --model-type "ARIMA" --config-path "code/config.yaml"
"""

import os
import sys
import argparse
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config, ensure_dirs
from utils.logger import get_logger
from utils.exceptions import DataValidationError, ModelConvergenceError, CalibrationError
from data_loader import fetch_data, split_series, standardize
from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel
from metrics.coverage import compute_coverage, compute_coverage_deviation
from metrics.pit import calculate_pit, ljung_box_test
from metrics.crps import compute_crps_for_series

logger = get_logger(__name__)

def load_model(model_type: str):
    """
    Factory function to instantiate the requested model.
    """
    model_type = model_type.upper()
    if model_type == "ARIMA":
        return ARIMAModel()
    elif model_type == "PROPHET":
        return ProphetModel()
    elif model_type == "LSTM":
        return LSTMModel()
    else:
        raise ValueError(f"Unsupported model type: {model_type}. Choose from ARIMA, PROPHET, LSTM.")

def process_single_series(series_id: str, model_type: str, config: Config) -> Dict[str, Any]:
    """
    Core logic to process a single series: load, fit, predict, evaluate.

    Returns a dictionary with keys matching the required JSON schema:
    - series_id
    - model
    - coverage_0.80
    - coverage_0.95
    - pit_p_value
    - crps
    - nominal_level (internal use for alignment with CSV schema)
    - empirical_coverage (internal use)
    - deviation (internal use)
    """
    logger.info(f"Processing series: {series_id} with model: {model_type}")

    # 1. Load Data
    # We assume the data has been fetched to data/raw/ by T000.
    # We need to locate the specific series. For this implementation,
    # we assume the data_loader can fetch a specific series or we iterate.
    # Given the API surface, we use fetch_data and filter.
    
    try:
        # Fetch all data (or the specific dataset containing the series)
        # The exact implementation of fetch_data depends on T000 output structure.
        # Assuming fetch_data returns a dict or dataframe with 'series_id' column if applicable.
        # If series_id is a key in a dict of series:
        data_df = fetch_data(config.paths.data_raw, series_id=series_id)
        
        if data_df is None or data_df.empty:
            raise DataValidationError(f"Series {series_id} not found in raw data.")

        # Split into train/test
        # Assuming standard split ratio from config
        train_df, test_df = split_series(data_df, test_size=config.test_size)
        
        # Standardize
        train_std, test_std, scaler = standardize(train_df, test_df)

    except Exception as e:
        logger.error(f"Data loading failed for {series_id}: {str(e)}")
        raise DataValidationError(f"Failed to load data for {series_id}: {str(e)}")

    # 2. Fit Model
    try:
        model = load_model(model_type)
        model.fit(train_std)
    except ModelConvergenceError as e:
        logger.error(f"Model {model_type} failed to converge on {series_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fitting model {model_type}: {str(e)}")
        raise ModelConvergenceError(f"Model fitting failed for {series_id}: {str(e)}")

    # 3. Generate Forecasts and Intervals
    # We need predictions and interval bounds for the test set
    try:
        forecast = model.predict(n_periods=len(test_std))
        # forecast should contain: 'mean', 'lower_0.80', 'upper_0.80', 'lower_0.95', 'upper_0.95'
        # or similar structure. Adjust based on actual model output.
        if 'mean' not in forecast or 'lower_0.80' not in forecast:
            raise CalibrationError("Model prediction missing required interval bounds.")
    except Exception as e:
        logger.error(f"Prediction failed for {series_id}: {str(e)}")
        raise

    # 4. Compute Metrics
    results = {
        "series_id": series_id,
        "model": model_type,
    }

    # Coverage 0.80
    try:
        cov_80 = compute_coverage(test_std['value'], forecast['lower_0.80'], forecast['upper_0.80'])
        dev_80 = compute_coverage_deviation(cov_80, 0.80)
        results["coverage_0.80"] = cov_80
        results["deviation_0.80"] = dev_80
        results["nominal_level_0.80"] = 0.80
        results["empirical_coverage_0.80"] = cov_80
    except Exception as e:
        logger.warning(f"Coverage 0.80 calculation failed: {str(e)}")
        results["coverage_0.80"] = None
        results["deviation_0.80"] = None

    # Coverage 0.95
    try:
        cov_95 = compute_coverage(test_std['value'], forecast['lower_0.95'], forecast['upper_0.95'])
        dev_95 = compute_coverage_deviation(cov_95, 0.95)
        results["coverage_0.95"] = cov_95
        results["deviation_0.95"] = dev_95
        results["nominal_level_0.95"] = 0.95
        results["empirical_coverage_0.95"] = cov_95
    except Exception as e:
        logger.warning(f"Coverage 0.95 calculation failed: {str(e)}")
        results["coverage_0.95"] = None
        results["deviation_0.95"] = None

    # PIT and Ljung-Box
    try:
        # Calculate PIT for the test set
        # Assuming compute_crps_for_series or similar returns PIT values
        pit_values = calculate_pit(test_std['value'], forecast)
        _, pit_p_value = ljung_box_test(pit_values)
        results["pit_p_value"] = pit_p_value
    except Exception as e:
        logger.warning(f"PIT calculation failed: {str(e)}")
        results["pit_p_value"] = None

    # CRPS
    try:
        crps_val = compute_crps_for_series(test_std['value'], forecast)
        results["crps"] = crps_val
    except Exception as e:
        logger.warning(f"CRPS calculation failed: {str(e)}")
        results["crps"] = None

    logger.info(f"Completed processing for {series_id}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Single-series evaluation runner for debugging.")
    parser.add_argument("--series-id", type=str, required=True, help="ID of the series to process")
    parser.add_argument("--model-type", type=str, required=True, choices=["ARIMA", "PROPHET", "LSTM"], help="Model type")
    parser.add_argument("--config-path", type=str, default="code/config.yaml", help="Path to config file")
    
    args = parser.parse_args()

    try:
        # Load config
        config = Config(args.config_path)
        ensure_dirs(config)

        # Process
        results = process_single_series(args.series_id, args.model_type, config)

        # Output JSON to stdout
        print(json.dumps(results, indent=2, default=str))

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        traceback.print_exc()
        # Return error code
        sys.exit(1)

if __name__ == "__main__":
    main()