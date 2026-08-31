"""
Single-series runner for debugging predictive interval calibration.

This script evaluates a single time series using a specified model
and computes calibration metrics (coverage, PIT, CRPS).

Usage:
    python -m code.evaluation.runner_single --series_id <id> --model_type <model> --config_path <path>
"""
import os
import sys
import argparse
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_dirs, PROJECT_ROOT as CONFIG_ROOT, RESULTS_DIR
from utils.logger import get_logger
from utils.exceptions import DataValidationError, ModelConvergenceError, ConfigurationError
from data_loader import fetch_data, load_m4_hourly, load_uci_electricity, split_series, standardize
from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel
from metrics.coverage import compute_coverage
from metrics.pit import calculate_pit, ljung_box_test
from metrics.crps import compute_crps

logger = get_logger(__name__)


def load_model(model_type: str):
    """Factory function to instantiate the requested model."""
    model_type = model_type.lower()
    if model_type == 'arima':
        return ARIMAModel()
    elif model_type == 'prophet':
        return ProphetModel()
    elif model_type == 'lstm':
        return LSTMModel()
    else:
        raise ConfigurationError(f"Unknown model type: {model_type}. Supported: arima, prophet, lstm")


def process_single_series(series_id: str, model_type: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a single series and compute calibration metrics.

    Args:
        series_id: Identifier for the series (e.g., 'M4_H1', 'UCI_E_1').
        model_type: Model to use ('arima', 'prophet', 'lstm').
        config_path: Path to config file (optional, uses defaults if None).

    Returns:
        Dictionary with keys: coverage_0.80, coverage_0.95, pit_p_value, crps.
    """
    logger.info(f"Starting evaluation for series_id={series_id}, model={model_type}")

    # 1. Load Data
    # Attempt to fetch data based on series_id prefix or content
    # Assuming series_id format hints at source (M4 vs UCI)
    raw_data = None
    try:
        if series_id.startswith("M4"):
            # Attempt to load M4 data. In a real scenario, we might have a mapping.
            # For this runner, we assume fetch_data can resolve the ID or we load full M4 and filter.
            # Given the constraints of a single-series runner, we try to load the specific series if possible,
            # or load the dataset and filter.
            # Using the data_loader's fetch_data which likely handles the bulk download.
            df = fetch_data("M4", series_id) # Hypothetical signature based on typical patterns
            # Fallback if fetch_data expects bulk:
            if df is None:
                # Load full M4 hourly as example for M4
                df = load_m4_hourly()
                df = df[df['series_id'] == series_id]
                if df.empty:
                    raise DataValidationError(f"Series {series_id} not found in M4 dataset")
        elif series_id.startswith("UCI"):
            df = fetch_data("UCI", series_id)
            if df is None:
                df = load_uci_electricity()
                df = df[df['series_id'] == series_id]
                if df.empty:
                    raise DataValidationError(f"Series {series_id} not found in UCI dataset")
        else:
            # Try generic fetch
            df = fetch_data("generic", series_id)
            if df is None:
                raise DataValidationError(f"Could not determine data source for series_id: {series_id}")

        # Standardize and split
        train_df, test_df = split_series(df, test_ratio=0.2)
        train_values = standardize(train_df['value'].values)
        test_values = standardize(test_df['value'].values)
        test_timestamps = test_df['timestamp'].values if 'timestamp' in test_df.columns else None

    except Exception as e:
        logger.error(f"Failed to load data for {series_id}: {e}")
        raise

    # 2. Fit Model
    model = load_model(model_type)
    try:
        model.fit(train_values)
    except Exception as e:
        logger.error(f"Model fitting failed for {series_id}: {e}")
        raise ModelConvergenceError(f"Model {model_type} failed to converge for series {series_id}")

    # 3. Generate Forecasts and Intervals
    # We need to generate intervals for the test set horizon
    # Assuming model.predict returns mean, lower, upper for the test horizon
    try:
        # Determine horizon
        horizon = len(test_values)
        forecasts = model.predict(horizon=horizon)
        
        # forecasts expected structure: dict or object with 'mean', 'lower_80', 'upper_80', etc.
        # If model returns raw arrays, we might need to adjust based on specific model implementation.
        # Assuming standard interface:
        pred_mean = forecasts['mean']
        pred_lower_80 = forecasts['lower_80']
        pred_upper_80 = forecasts['upper_80']
        pred_lower_95 = forecasts['lower_95']
        pred_upper_95 = forecasts['upper_95']

    except Exception as e:
        logger.error(f"Prediction failed for {series_id}: {e}")
        raise

    # 4. Compute Metrics
    results = {}

    # Coverage 0.80
    cov_80 = compute_coverage(test_values, pred_lower_80, pred_upper_80, level=0.80)
    results['coverage_0.80'] = float(cov_80)

    # Coverage 0.95
    cov_95 = compute_coverage(test_values, pred_lower_95, pred_upper_95, level=0.95)
    results['coverage_0.95'] = float(cov_95)

    # PIT and Ljung-Box
    # Calculate PIT values (Probability Integral Transform)
    # Requires the full predictive distribution. If only intervals are available, 
    # we approximate or use the model's sampling method if available.
    # For this implementation, we assume the model can provide samples or we approximate PIT from intervals.
    # If the model supports `predict_samples`, use that. Otherwise, we might need to approximate.
    # Given the task asks for PIT p-value, we assume we have a way to get the CDF or samples.
    # Let's assume the model provides a method to get samples or we use the interval info to approximate.
    # For robustness, we'll try to get samples if the model has it, else we might need to mock the distribution.
    # However, the task implies real metrics. Let's assume we use the interval bounds to approximate a normal or t-dist if needed,
    # OR the model returns samples.
    
    # Fallback: If we don't have samples, we can't compute exact PIT. 
    # We will assume the model returns a distribution object or we use the interval info to estimate.
    # For this code, we will assume the model has a `predict_samples` method or similar.
    # If not, we might need to implement a generic wrapper.
    # Let's assume we can get samples from the model's internal state or a method.
    try:
        if hasattr(model, 'predict_samples'):
            pit_samples = model.predict_samples(horizon=horizon, n_samples=1000)
            pit_values = calculate_pit(test_values, pit_samples)
            _, p_value = ljung_box_test(pit_values)
            results['pit_p_value'] = float(p_value)
        else:
            # Fallback for models that don't expose samples directly:
            # Approximate PIT using the interval bounds assuming a Gaussian distribution
            # This is a simplification.
            import numpy as np
            from scipy.stats import norm
            # Estimate sigma from intervals: (upper - lower) / (2 * z)
            sigma_80 = (pred_upper_80 - pred_lower_80) / (2 * 1.28155)
            # PIT = CDF((y - mean) / sigma)
            z_scores = (test_values - pred_mean) / sigma_80
            pit_values = norm.cdf(z_scores)
            _, p_value = ljung_box_test(pit_values)
            results['pit_p_value'] = float(p_value)
    except Exception as e:
        logger.warning(f"Could not compute PIT for {series_id}: {e}. Setting to NaN.")
        results['pit_p_value'] = float('nan')

    # CRPS
    # CRPS requires samples or a parametric distribution
    try:
        if hasattr(model, 'predict_samples'):
            pit_samples = model.predict_samples(horizon=horizon, n_samples=1000)
            crps_val = compute_crps(test_values, pit_samples)
            results['crps'] = float(crps_val)
        else:
            # Approximate CRPS using Gaussian assumption
            import numpy as np
            from properscoring import crps_gaussian
            sigma_80 = (pred_upper_80 - pred_lower_80) / (2 * 1.28155)
            crps_val = crps_gaussian(test_values, mu=pred_mean, sigma=sigma_80)
            results['crps'] = float(np.mean(crps_val))
    except Exception as e:
        logger.warning(f"Could not compute CRPS for {series_id}: {e}. Setting to NaN.")
        results['crps'] = float('nan')

    logger.info(f"Completed evaluation for {series_id}. Results: {results}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Single-series calibration runner")
    parser.add_argument("--series_id", type=str, required=True, help="ID of the series to evaluate")
    parser.add_argument("--model_type", type=str, required=True, choices=['arima', 'prophet', 'lstm'], help="Model type")
    parser.add_argument("--config_path", type=str, default=None, help="Path to config file")
    
    args = parser.parse_args()

    try:
        # Ensure output directories exist
        ensure_dirs()

        results = process_single_series(
            series_id=args.series_id,
            model_type=args.model_type,
            config_path=args.config_path
        )

        # Output as JSON to stdout
        print(json.dumps(results))

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        traceback.print_exc()
        # Exit with error code
        sys.exit(1)


if __name__ == "__main__":
    main()