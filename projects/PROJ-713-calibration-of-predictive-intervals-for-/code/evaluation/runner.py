import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_PROCESSED_DIR, RESULTS_DIR, LOG_DIR
from utils.logger import get_logger, JsonFormatter
from utils.exceptions import ModelConvergenceError, DataValidationError, CalibrationError
from data_loader import load_m4_hourly, load_uci_electricity, split_series, standardize
from metrics.coverage import compute_coverage, aggregate_coverage_results, coverage_to_dataframe
from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel

logger = get_logger(__name__)

MODELS = {
    "arima": ARIMAModel,
    "prophet": ProphetModel,
    "lstm": LSTMModel
}

CONFIDENCE_LEVELS = [0.80, 0.95]

def process_single_series(
    series_id: str,
    train_data: Any,
    test_data: Any,
    model_type: str,
    horizon: int = 24
) -> Optional[Dict[str, Any]]:
    """
    Process a single time series with a specific model.
    
    Implements robust error handling: catches specific failures (e.g., constant variance,
    non-convergence) and logs them without crashing the pipeline. Returns None on failure
    instead of raising, allowing the main loop to continue.
    """
    result_entry = {
        "series_id": series_id,
        "model_type": model_type,
        "status": "unknown",
        "error_message": None
    }

    try:
        if model_type not in MODELS:
            raise ValueError(f"Unknown model type: {model_type}")

        ModelClass = MODELS[model_type]
        model = ModelClass()

        # Fit model
        logger.info(f"Fitting {model_type} on series {series_id}...")
        model.fit(train_data)

        # Generate forecasts and intervals
        logger.info(f"Generating forecasts and intervals for series {series_id}...")
        forecasts = model.forecast(horizon=horizon)
        
        # Ensure forecasts structure is valid
        if forecasts is None or not isinstance(forecasts, dict):
            raise ValueError("Model returned invalid forecast structure")

        if "mean" not in forecasts or "lower" not in forecasts or "upper" not in forecasts:
            raise ValueError("Forecast missing required keys: mean, lower, upper")

        # Compute coverage
        logger.info(f"Computing coverage for series {series_id}...")
        coverage_results = []
        for level in CONFIDENCE_LEVELS:
            coverage = compute_coverage(
                test_data,
                forecasts["mean"],
                forecasts["lower"],
                forecasts["upper"],
                level
            )
            coverage_results.append(coverage)

        result_entry["status"] = "success"
        result_entry["coverage_results"] = coverage_results
        
    except ModelConvergenceError as e:
        result_entry["status"] = "failed_convergence"
        result_entry["error_message"] = str(e)
        logger.warning(f"Series {series_id} ({model_type}) failed convergence: {e}")
        
    except DataValidationError as e:
        result_entry["status"] = "failed_data_validation"
        result_entry["error_message"] = str(e)
        logger.warning(f"Series {series_id} ({model_type}) failed data validation: {e}")
        
    except CalibrationError as e:
        result_entry["status"] = "failed_calibration"
        result_entry["error_message"] = str(e)
        logger.warning(f"Series {series_id} ({model_type}) failed calibration: {e}")
        
    except ValueError as e:
        # Catch specific issues like constant variance or malformed data
        error_str = str(e).lower()
        if "constant" in error_str or "variance" in error_str or "nan" in error_str:
            result_entry["status"] = "failed_constant_variance"
            result_entry["error_message"] = str(e)
            logger.warning(f"Series {series_id} ({model_type}) failed due to constant variance or NaN: {e}")
        else:
            result_entry["status"] = "failed_value_error"
            result_entry["error_message"] = str(e)
            logger.error(f"Series {series_id} ({model_type}) failed with ValueError: {e}")
            
    except Exception as e:
        # Catch-all for unexpected errors to prevent pipeline crash
        result_entry["status"] = "failed_unexpected"
        result_entry["error_message"] = str(e)
        logger.exception(f"Series {series_id} ({model_type}) encountered unexpected error: {e}")

    return result_entry

def run_evaluation(
    dataset_name: str,
    model_types: List[str],
    horizon: int = 24
) -> List[Dict[str, Any]]:
    """
    Run evaluation on a dataset for specified models.
    
    Handles dataset loading, splitting, and iteration over series.
    """
    all_results = []
    
    # Load data
    logger.info(f"Loading dataset: {dataset_name}")
    if dataset_name == "m4_hourly":
        data = load_m4_hourly()
    elif dataset_name == "uci_electricity":
        data = load_uci_electricity()
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    if not data:
        raise DataValidationError(f"No data loaded for {dataset_name}")
    
    logger.info(f"Loaded {len(data)} series from {dataset_name}")
    
    for series_id, series_data in data.items():
        try:
            train, test = split_series(series_data, train_ratio=0.8)
            train_std, test_std = standardize(train, test)
            
            for model_type in model_types:
                result = process_single_series(
                    series_id=series_id,
                    train_data=train_std,
                    test_data=test_std,
                    model_type=model_type,
                    horizon=horizon
                )
                if result:
                    all_results.append(result)
                    
        except Exception as e:
            logger.exception(f"Critical error processing series {series_id}: {e}")
            # Continue to next series even if one fails catastrophically
            continue
            
    return all_results

def aggregate_and_save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Aggregate results and save to CSV.
    
    Filters out failed entries for the main coverage report but logs them separately.
    """
    df = coverage_to_dataframe(results)
    
    # Separate successful and failed entries for logging
    failed_entries = [r for r in results if r["status"] != "success"]
    if failed_entries:
        logger.warning(f"Found {len(failed_entries)} failed series. Details logged above.")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run predictive interval calibration evaluation")
    parser.add_argument("--dataset", type=str, default="m4_hourly", help="Dataset to evaluate")
    parser.add_argument("--models", type=str, nargs="+", default=["arima", "prophet", "lstm"], 
                        help="Models to evaluate")
    parser.add_argument("--horizon", type=int, default=24, help="Forecast horizon")
    parser.add_argument("--output", type=str, default="results/coverage.csv", help="Output CSV path")
    
    args = parser.parse_args()
    
    logger.info(f"Starting evaluation: dataset={args.dataset}, models={args.models}")
    
    try:
        results = run_evaluation(args.dataset, args.models, args.horizon)
        aggregate_and_save_results(results, args.output)
        logger.info("Evaluation completed successfully.")
    except Exception as e:
        logger.exception(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()