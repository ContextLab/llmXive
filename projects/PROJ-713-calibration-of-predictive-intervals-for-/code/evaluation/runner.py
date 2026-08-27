import os
import sys
import argparse
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Project imports matching API surface
from config import PROJECT_ROOT, RESULTS_DIR
from data_loader import fetch_data, load_m4_hourly, load_uci_electricity, split_series, standardize
from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel
from metrics.coverage import compute_coverage, aggregate_coverage_results, coverage_to_dataframe
from metrics.pit import calculate_pit, generate_pit_histogram, ljung_box_test, compute_pit_metrics
from metrics.crps import compute_crps, aggregate_crps_results, crps_to_dataframe
from utils.logger import get_logger, log_event
from utils.exceptions import CalibrationError, DataValidationError, ModelConvergenceError

# Ensure logger is configured
logger = get_logger(__name__)

# Model registry mapping model names to classes
MODEL_REGISTRY = {
    "arima": ARIMAModel,
    "prophet": ProphetModel,
    "lstm": LSTMModel
}

def process_single_series(
    series_id: str,
    series_data: Dict[str, Any],
    model_name: str,
    confidence_levels: List[float] = [0.80, 0.95],
    is_test: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Process a single time series for a specific model.
    
    Implements robust error handling to catch specific series failures
    (e.g., constant variance, convergence issues) without crashing the pipeline.
    
    Args:
        series_id: Unique identifier for the series
        series_data: Dictionary containing 'train' and 'test' arrays
        model_name: Name of the model to use (arima, prophet, lstm)
        confidence_levels: List of confidence levels for intervals
        is_test: Whether this is a test series (for logging differentiation)
        
    Returns:
        Dictionary of results if successful, None if an error occurred
    """
    result = {
        "series_id": series_id,
        "model": model_name,
        "status": "pending",
        "error_message": None,
        "coverage_results": {},
        "pit_results": {},
        "crps_results": {}
    }

    try:
        # Validate input data
        if "train" not in series_data or "test" not in series_data:
            raise DataValidationError(f"Series {series_id} missing train or test split")
        
        if len(series_data["train"]) == 0 or len(series_data["test"]) == 0:
            raise DataValidationError(f"Series {series_id} has empty train or test split")

        # Initialize model
        if model_name not in MODEL_REGISTRY:
            raise CalibrationError(f"Unknown model: {model_name}")
        
        ModelClass = MODEL_REGISTRY[model_name]
        model = ModelClass()

        # Fit model on training data
        logger.info(f"Fitting {model_name} model on series {series_id}")
        model.fit(series_data["train"])

        # Generate forecasts and intervals
        forecasts = model.forecast(len(series_data["test"]))
        intervals = model.get_intervals(len(series_data["test"]), confidence_levels)

        # Validate forecasts and intervals
        if forecasts is None or intervals is None:
            raise ModelConvergenceError(f"Model {model_name} failed to generate valid forecasts for {series_id}")

        # Check for NaN/Inf in forecasts (common failure mode for LSTM)
        if not (isinstance(forecasts, (list, tuple)) or hasattr(forecasts, '__len__')):
            forecasts = [forecasts] if np.isscalar(forecasts) else []
        
        if hasattr(forecasts, '__iter__'):
            forecasts_arr = np.array(forecasts)
            if np.any(np.isnan(forecasts_arr)) or np.any(np.isinf(forecasts_arr)):
                raise ModelConvergenceError(f"Forecasts contain NaN/Inf for series {series_id}")

        # Compute coverage metrics
        logger.info(f"Computing coverage for series {series_id}")
        coverage_results = {}
        for level in confidence_levels:
            coverage = compute_coverage(
                actuals=series_data["test"],
                forecasts=forecasts,
                intervals=intervals,
                confidence_level=level
            )
            coverage_results[f"coverage_{level}"] = coverage["empirical_coverage"]
            coverage_results[f"deviation_{level}"] = coverage["deviation"]

        # Compute PIT metrics
        logger.info(f"Computing PIT for series {series_id}")
        pit_metrics = compute_pit_metrics(
            actuals=series_data["test"],
            forecasts=forecasts,
            intervals=intervals,
            confidence_levels=confidence_levels
        )
        result["pit_results"] = pit_metrics

        # Compute CRPS
        logger.info(f"Computing CRPS for series {series_id}")
        crps_value = compute_crps(
            actuals=series_data["test"],
            forecasts=forecasts,
            intervals=intervals
        )
        result["crps_results"] = {"crps": crps_value}

        result["status"] = "success"
        result["coverage_results"] = coverage_results

        log_event(
            "series_processed",
            {
                "series_id": series_id,
                "model": model_name,
                "status": "success",
                "coverage": coverage_results
            }
        )

    except (CalibrationError, DataValidationError, ModelConvergenceError) as e:
        # Specific, expected errors - log and continue
        error_msg = str(e)
        logger.error(f"Expected error for series {series_id} ({model_name}): {error_msg}")
        result["status"] = "failed_expected"
        result["error_message"] = error_msg
        
        log_event(
            "series_processing_failed",
            {
                "series_id": series_id,
                "model": model_name,
                "error_type": type(e).__name__,
                "error_message": error_msg
            },
            level=logging.WARNING
        )

    except Exception as e:
        # Unexpected errors - log full traceback but continue pipeline
        error_msg = f"{type(e).__name__}: {str(e)}"
        full_traceback = traceback.format_exc()
        
        logger.critical(f"Unexpected error for series {series_id} ({model_name}): {error_msg}")
        logger.debug(f"Traceback:\n{full_traceback}")
        
        result["status"] = "failed_unexpected"
        result["error_message"] = error_msg
        
        log_event(
            "series_processing_crashed",
            {
                "series_id": series_id,
                "model": model_name,
                "error_type": type(e).__name__,
                "error_message": error_msg
            },
            level=logging.ERROR
        )

    return result

def run_evaluation(
    dataset_name: str,
    model_names: List[str],
    confidence_levels: List[float] = [0.80, 0.95],
    series_limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run evaluation on a dataset for multiple models.
    
    Args:
        dataset_name: Name of dataset ('m4_hourly' or 'uci_electricity')
        model_names: List of models to evaluate
        confidence_levels: Confidence levels for interval estimation
        series_limit: Maximum number of series to process (for testing)
        
    Returns:
        List of result dictionaries for all processed series
    """
    all_results = []
    
    # Load data
    logger.info(f"Loading dataset: {dataset_name}")
    if dataset_name == "m4_hourly":
        series_list = load_m4_hourly()
    elif dataset_name == "uci_electricity":
        series_list = load_uci_electricity()
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    if series_limit:
        series_list = series_list[:series_limit]
        logger.info(f"Processing only first {series_limit} series due to limit")
    
    total_series = len(series_list)
    logger.info(f"Starting evaluation on {total_series} series")
    
    for idx, series_item in enumerate(series_list):
        series_id = series_item.get("id", f"series_{idx}")
        series_data = series_item["data"]
        
        logger.info(f"Processing series {idx+1}/{total_series}: {series_id}")
        
        for model_name in model_names:
            result = process_single_series(
                series_id=series_id,
                series_data=series_data,
                model_name=model_name,
                confidence_levels=confidence_levels
            )
            
            if result:
                all_results.append(result)
                
                # Log progress summary
                if (idx + 1) % 10 == 0:
                    success_count = sum(1 for r in all_results if r["status"] == "success")
                    logger.info(f"Progress: {success_count}/{len(all_results)} series processed successfully")
    
    return all_results

def aggregate_and_save_results(
    results: List[Dict[str, Any]],
    output_path: str
) -> pd.DataFrame:
    """
    Aggregate results from multiple series and save to CSV.
    
    Args:
        results: List of result dictionaries from run_evaluation
        output_path: Path to save the aggregated CSV
        
    Returns:
        DataFrame containing aggregated results
    """
    if not results:
        logger.warning("No results to aggregate")
        return pd.DataFrame()
    
    # Flatten results for CSV output
    flat_results = []
    for res in results:
        row = {
            "series_id": res["series_id"],
            "model": res["model"],
            "status": res["status"],
            "error_message": res.get("error_message", "")
        }
        
        # Add coverage metrics
        for key, value in res.get("coverage_results", {}).items():
            row[f"coverage_{key}"] = value
        
        # Add PIT metrics
        for key, value in res.get("pit_results", {}).items():
            row[f"pit_{key}"] = value
        
        # Add CRPS metrics
        for key, value in res.get("crps_results", {}).items():
            row[f"crps_{key}"] = value
        
        flat_results.append(row)
    
    df = pd.DataFrame(flat_results)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Aggregated results saved to {output_path}")
    
    return df

def main():
    """Main entry point for the evaluation pipeline."""
    parser = argparse.ArgumentParser(description="Run predictive interval calibration evaluation")
    parser.add_argument(
        "--dataset", 
        type=str, 
        default="m4_hourly",
        choices=["m4_hourly", "uci_electricity"],
        help="Dataset to evaluate"
    )
    parser.add_argument(
        "--models", 
        type=str, 
        nargs="+", 
        default=["arima", "prophet", "lstm"],
        choices=["arima", "prophet", "lstm"],
        help="Models to evaluate"
    )
    parser.add_argument(
        "--confidence-levels",
        type=float,
        nargs="+",
        default=[0.80, 0.95],
        help="Confidence levels for interval estimation"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of series to process"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for results CSV (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_event("evaluation_started", {
        "dataset": args.dataset,
        "models": args.models,
        "confidence_levels": args.confidence_levels,
        "limit": args.limit
    })
    
    try:
        # Run evaluation
        results = run_evaluation(
            dataset_name=args.dataset,
            model_names=args.models,
            confidence_levels=args.confidence_levels,
            series_limit=args.limit
        )
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            output_filename = f"coverage_{args.dataset}_{'_'.join(args.models)}.csv"
            output_path = os.path.join(RESULTS_DIR, output_filename)
        
        # Aggregate and save results
        df = aggregate_and_save_results(results, output_path)
        
        # Log summary
        success_count = sum(1 for r in results if r["status"] == "success")
        total_count = len(results)
        
        log_event("evaluation_completed", {
            "total_series": total_count,
            "successful": success_count,
            "failed": total_count - success_count,
            "output_file": output_path
        })
        
        logger.info(f"Evaluation complete: {success_count}/{total_count} series processed successfully")
        logger.info(f"Results saved to: {output_path}")
        
    except Exception as e:
        log_event("evaluation_failed", {
            "error_type": type(e).__name__,
            "error_message": str(e)
        }, level=logging.ERROR)
        logger.critical(f"Evaluation pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()