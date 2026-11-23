"""
Module to calculate and report uncertainty metrics for the GPR model.
Specifically implements Task T039: Calculate percentage of test samples in "high uncertainty" regions.
"""
import os
import sys
import json
import logging
import numpy as np
import pickle
from typing import Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config import get_results_dir, get_models_dir, get_processed_data_dir, get_logger, ensure_directories
from utils.logger import log_execution_time

def load_processed_test_data() -> tuple:
    """
    Load the preprocessed test data features (X_test) and targets (y_test).
    Assumes the processed data was saved by preprocess.py.
    """
    data_path = os.path.join(get_processed_data_dir(), "processed_test_data.npz")
    
    if not os.path.exists(data_path):
        # Fallback to checking for a CSV if npz wasn't used, though spec implies npz or similar
        # Based on T018/T027 implementation patterns, we expect a saved state.
        # If the file is missing, we raise a clear error rather than faking data.
        raise FileNotFoundError(f"Processed test data not found at {data_path}. "
                                "Ensure T018 (preprocess) has run and saved the split data.")
    
    data = np.load(data_path)
    X_test = data['X_test']
    y_test = data['y_test']
    feature_names = data['feature_names']
    
    return X_test, y_test, feature_names

def load_trained_gpr_model() -> Any:
    """
    Load the trained GPR model artifact.
    """
    model_path = os.path.join(get_models_dir(), "gpr_model.pkl")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"GPR model not found at {model_path}. "
                                "Ensure T026 (gpr_trainer) has run and saved the model.")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def calculate_high_uncertainty_percentage(X_test: np.ndarray, model: Any) -> Dict[str, Any]:
    """
    Calculates the percentage of test samples falling into "high uncertainty" regions.
    
    Logic (FR-007 / SC-003):
    1. Predict mean and standard deviation (sigma) for all test samples.
    2. Calculate the median of the predicted standard deviations.
    3. Define "high uncertainty" as sigma > 2 * median_sigma.
    4. Calculate the percentage of samples meeting this criteria.
    
    Returns:
        dict: Contains 'high_uncertainty_percentage', 'median_sigma', 'threshold', 'count_high_uncertainty', 'total_samples'
    """
    # Predict with uncertainty
    # GPR predict returns (mean, std) if return_std=True
    mean_pred, std_pred = model.predict(X_test, return_std=True)
    
    # Ensure std_pred is 1D array
    std_pred = np.array(std_pred).flatten()
    
    # Calculate median sigma
    median_sigma = np.median(std_pred)
    
    # Define threshold (2x median)
    threshold = 2.0 * median_sigma
    
    # Identify high uncertainty samples
    high_uncertainty_mask = std_pred > threshold
    count_high_uncertainty = int(np.sum(high_uncertainty_mask))
    total_samples = len(std_pred)
    
    # Calculate percentage
    if total_samples == 0:
        percentage = 0.0
    else:
        percentage = (count_high_uncertainty / total_samples) * 100.0
    
    result = {
        "high_uncertainty_percentage": round(percentage, 2),
        "median_sigma": round(float(median_sigma), 6),
        "threshold_sigma": round(float(threshold), 6),
        "count_high_uncertainty": count_high_uncertainty,
        "total_samples": total_samples,
        "logic": "sigma > 2 * median_sigma"
    }
    
    return result

def save_metrics_to_json(metrics: Dict[str, Any], existing_metrics_path: Optional[str] = None):
    """
    Saves the uncertainty metrics to the results/metrics.json file.
    If existing metrics exist (e.g., from T029/T031), they are loaded, updated, and saved back.
    """
    results_dir = get_results_dir()
    ensure_directories()
    
    metrics_file = os.path.join(results_dir, "metrics.json")
    
    # Load existing metrics if they exist
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r') as f:
            existing_metrics = json.load(f)
        # Update with new metrics
        existing_metrics.update(metrics)
        final_metrics = existing_metrics
    else:
        final_metrics = metrics
    
    # Save updated metrics
    with open(metrics_file, 'w') as f:
        json.dump(final_metrics, f, indent=4)
    
    logging.info(f"Uncertainty metrics saved to {metrics_file}")
    return metrics_file

@log_execution_time
def main():
    """
    Main entry point for T039.
    Orchestrates loading data, model, calculating metrics, and saving results.
    """
    logger = get_logger("uncertainty_metrics")
    logger.info("Starting Uncertainty Metrics Calculation (T039)")
    
    try:
        # 1. Load Data and Model
        logger.info("Loading processed test data...")
        X_test, y_test, feature_names = load_processed_test_data()
        logger.info(f"Loaded {X_test.shape[0]} test samples.")
        
        logger.info("Loading trained GPR model...")
        model = load_trained_gpr_model()
        
        # 2. Calculate Metrics
        logger.info("Calculating high uncertainty percentage...")
        metrics = calculate_high_uncertainty_percentage(X_test, model)
        
        logger.info(f"Median Sigma: {metrics['median_sigma']}")
        logger.info(f"Threshold (2x Median): {metrics['threshold_sigma']}")
        logger.info(f"High Uncertainty Count: {metrics['count_high_uncertainty']} / {metrics['total_samples']}")
        logger.info(f"High Uncertainty Percentage: {metrics['high_uncertainty_percentage']}%")
        
        # 3. Save to results/metrics.json
        logger.info("Saving metrics to results/metrics.json...")
        save_metrics_to_json(metrics)
        
        logger.info("T039 Uncertainty Metrics Calculation completed successfully.")
        return metrics
        
    except FileNotFoundError as e:
        logger.error(f"Data or Model file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during uncertainty calculation: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
