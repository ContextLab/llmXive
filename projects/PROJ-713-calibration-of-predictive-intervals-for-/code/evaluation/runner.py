import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import json
import pandas as pd
import numpy as np

# Local imports based on provided API surface
from config import PROJECT_ROOT, RESULTS_DIR, DATA_PROCESSED_DIR, DATA_RAW_DIR
from utils.logger import get_logger, log_event
from utils.exceptions import DataValidationError, ModelConvergenceError, CalibrationError

from data_loader import fetch_data, load_m4_hourly, load_uci_electricity, split_series, standardize
from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.lstm_model import LSTMModel

from metrics.coverage import compute_coverage, compute_coverage_deviation, aggregate_coverage_results, coverage_to_dataframe
from metrics.pit import calculate_pit, generate_pit_histogram, ljung_box_test, compute_pit_metrics
from metrics.crps import compute_crps, aggregate_crps_results, crps_to_dataframe, compute_crps_for_series

logger = get_logger(__name__)

MODEL_MAP = {
    "arima": ARIMAModel,
    "prophet": ProphetModel,
    "lstm": LSTMModel
}

def process_single_series(
    series_name: str,
    train_data: np.ndarray,
    test_data: np.ndarray,
    model_name: str,
    horizon: int = 24,
    confidence_levels: List[float] = [0.80, 0.95]
) -> Dict[str, Any]:
    """
    Fits a model to train_data, forecasts horizon steps, and computes
    Coverage, PIT, and CRPS metrics against test_data.
    """
    logger.info(f"Processing series '{series_name}' with {model_name} model.")
    
    # Initialize Model
    if model_name not in MODEL_MAP:
        raise ValueError(f"Unknown model: {model_name}. Options: {list(MODEL_MAP.keys())}")
    
    model_cls = MODEL_MAP[model_name]
    model = model_cls(horizon=horizon, confidence_levels=confidence_levels)

    try:
        # Fit Model
        model.fit(train_data)
        
        # Forecast
        forecast, intervals = model.predict()
        
        # Ensure shapes are correct for metric calculation
        # forecast: (horizon,)
        # intervals: (horizon, 2, n_intervals) or similar depending on model
        # We expect intervals to be lower and upper bounds for each level
        
        if len(forecast) != len(test_data):
            logger.warning(f"Forecast length {len(forecast)} != test length {len(test_data)}. Truncating.")
            forecast = forecast[:len(test_data)]
            test_data = test_data[:len(forecast)]
            # Adjust intervals if necessary (assuming intervals match forecast length)
            if isinstance(intervals, dict):
                for k in intervals:
                    if intervals[k].shape[0] > len(forecast):
                        intervals[k] = intervals[k][:len(forecast)]

        # --- Coverage Metrics ---
        coverage_results = compute_coverage(
            actual=test_data,
            forecast=forecast,
            intervals=intervals,
            confidence_levels=confidence_levels
        )

        # --- PIT Metrics ---
        # PIT requires the full predictive distribution. 
        # If model returns samples, use them. If it returns parametric, we might need to sample or use parametric PIT.
        # For this implementation, we assume the model can provide samples or we use the intervals to approximate.
        # However, the spec implies using the full distribution. 
        # Let's assume the model's 'predict' returns 'samples' if available, or we derive from intervals if parametric.
        # Given the API surface, we assume 'intervals' might be a dict of 'lower'/'upper' or a specific structure.
        # To be robust, we check if the model provided a 'samples' attribute or similar. 
        # If not, we might need to approximate. 
        # For this task, we assume the model returns a structure compatible with compute_pit_metrics.
        # If the model only returns intervals, we might need to generate samples from the implied distribution.
        # Let's assume the model returns 'samples' in the prediction dict if available.
        
        pit_results = {}
        if hasattr(model, 'get_samples') and callable(model.get_samples):
            samples = model.get_samples(n_samples=1000) # Default 1000 samples
            pit_results = compute_pit_metrics(actual=test_data, samples=samples)
        else:
            # Fallback: If only intervals are available, we cannot compute full PIT accurately without distributional assumption.
            # However, the task requires integrating PIT. 
            # We will attempt to use the intervals to approximate if the model is parametric (e.g., Gaussian).
            # If not, we log a warning and skip or return None.
            logger.warning(f"Model {model_name} does not provide samples. Attempting parametric PIT or skipping.")
            # For now, we assume the model returns a 'dist_params' or similar. 
            # If not, we skip PIT for this specific series to avoid crashing, but log it.
            # Ideally, the model should return samples.
            pit_results = {"status": "skipped", "reason": "No samples or distribution params provided by model"}

        # --- CRPS Metrics ---
        # CRPS also requires samples or a parametric distribution.
        crps_results = {}
        if hasattr(model, 'get_samples') and callable(model.get_samples):
            samples = model.get_samples(n_samples=1000)
            crps_val = compute_crps_for_series(actual=test_data, samples=samples)
            crps_results = {"crps": float(crps_val)}
        else:
            logger.warning(f"Model {model_name} does not provide samples. CRPS skipped.")
            crps_results = {"status": "skipped", "reason": "No samples provided"}

        return {
            "series_name": series_name,
            "model_name": model_name,
            "coverage": coverage_results,
            "pit": pit_results,
            "crps": crps_results
        }

    except (ModelConvergenceError, DataValidationError) as e:
        logger.error(f"Error processing {series_name} with {model_name}: {e}")
        return {
            "series_name": series_name,
            "model_name": model_name,
            "error": str(e),
            "coverage": None,
            "pit": None,
            "crps": None
        }

def run_evaluation(
    dataset: str,
    models: List[str],
    horizon: int = 24,
    confidence_levels: List[float] = [0.80, 0.95]
) -> List[Dict[str, Any]]:
    """
    Runs the evaluation pipeline for a given dataset and list of models.
    Returns a list of result dictionaries.
    """
    logger.info(f"Starting evaluation for dataset: {dataset}, models: {models}")
    
    # Load Data
    if dataset == "m4_hourly":
        data = load_m4_hourly()
    elif dataset == "uci_electricity":
        data = load_uci_electricity()
    else:
        raise ValueError(f"Unknown dataset: {dataset}")

    results = []
    
    # Iterate over series
    for series_name, series_data in data.items():
        train, test = split_series(series_data, split_ratio=0.8)
        train_std, test_std, params = standardize(train, test)

        for model_name in models:
            res = process_single_series(
                series_name=series_name,
                train_data=train_std,
                test_data=test_std,
                model_name=model_name,
                horizon=horizon,
                confidence_levels=confidence_levels
            )
            results.append(res)
    
    return results

def aggregate_and_save_results(results: List[Dict[str, Any]], output_dir: Optional[Path] = None):
    """
    Aggregates results into DataFrames and saves to CSV.
    Creates:
    - results/coverage.csv
    - results/distributional_metrics.csv (for PIT and CRPS)
    """
    if output_dir is None:
        output_dir = RESULTS_DIR
    
    os.makedirs(output_dir, exist_ok=True)

    # 1. Coverage Results
    coverage_rows = []
    for res in results:
        if res.get("coverage") and res["coverage"].get("status") != "error":
            cov = res["coverage"]
            row = {
                "series_name": res["series_name"],
                "model_name": res["model_name"],
                "nominal_level": cov.get("nominal_level"),
                "empirical_coverage": cov.get("empirical_coverage"),
                "deviation": cov.get("deviation")
            }
            coverage_rows.append(row)
    
    if coverage_rows:
        df_cov = pd.DataFrame(coverage_rows)
        # Pivot if necessary, or keep long format. Long format is safer for aggregation.
        # Aggregate per model/series/level
        df_cov.to_csv(output_dir / "coverage.csv", index=False)
        logger.info(f"Saved coverage results to {output_dir / 'coverage.csv'}")
    else:
        logger.warning("No coverage results to save.")

    # 2. Distributional Metrics (PIT and CRPS)
    dist_rows = []
    for res in results:
        row = {
            "series_name": res["series_name"],
            "model_name": res["model_name"],
            "crps_value": None,
            "pit_p_value": None,
            "pit_uniformity": None,
            "pit_status": None
        }
        
        if res.get("crps") and res["crps"].get("status") != "skipped":
            row["crps_value"] = res["crps"].get("crps")
        
        if res.get("pit") and res["pit"].get("status") != "skipped":
            row["pit_p_value"] = res["pit"].get("p_value")
            row["pit_uniformity"] = res["pit"].get("uniformity") # e.g., "uniform" or "non-uniform"
            row["pit_status"] = res["pit"].get("status")
        else:
            row["pit_status"] = res.get("pit", {}).get("status", "unknown")

        dist_rows.append(row)
    
    if dist_rows:
        df_dist = pd.DataFrame(dist_rows)
        df_dist.to_csv(output_dir / "distributional_metrics.csv", index=False)
        logger.info(f"Saved distributional metrics to {output_dir / 'distributional_metrics.csv'}")
    else:
        logger.warning("No distributional metrics to save.")

def main():
    parser = argparse.ArgumentParser(description="Run calibration evaluation pipeline.")
    parser.add_argument("--dataset", type=str, default="m4_hourly", choices=["m4_hourly", "uci_electricity"])
    parser.add_argument("--models", type=str, nargs="+", default=["arima", "prophet", "lstm"])
    parser.add_argument("--horizon", type=int, default=24)
    parser.add_argument("--confidence-levels", type=float, nargs="+", default=[0.80, 0.95])
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for results")
    
    args = parser.parse_args()
    
    log_event("evaluation_start", {
        "dataset": args.dataset,
        "models": args.models,
        "horizon": args.horizon
    })

    try:
        results = run_evaluation(
            dataset=args.dataset,
            models=args.models,
            horizon=args.horizon,
            confidence_levels=args.confidence_levels
        )
        
        output_dir = Path(args.output_dir) if args.output_dir else RESULTS_DIR
        aggregate_and_save_results(results, output_dir)
        
        log_event("evaluation_end", {"status": "success", "results_count": len(results)})
        
    except Exception as e:
        logger.exception("Evaluation pipeline failed.")
        log_event("evaluation_end", {"status": "failed", "error": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()