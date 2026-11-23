"""
Script to evaluate trained GPR and Baseline models on test data
and save the metrics to results/metrics.json as required by T027.
"""
import os
import sys
import json
import pickle
import logging
import numpy as np
from typing import Dict, Any, Tuple

# Add project root to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import get_results_dir, get_models_dir, get_processed_data_dir, ensure_directories
from utils.logger import setup_logging
from models.metrics import evaluate_model, save_metrics
from data.preprocess import load_raw_csv # Assuming we need to load processed data or reconstruct

def load_processed_test_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load the processed test data.
    Assumes the preprocessing step saved a processed CSV or we can reconstruct the split.
    For this implementation, we assume the test data is available in a specific format
    or we load the full processed data and split it using the same seed if not saved separately.
    
    However, typically in this pipeline, the 'preprocess.py' splits data and saves it,
    or the trainer loads the split. 
    
    To make this script standalone and robust, we will assume the existence of 
    a processed file 'data/processed/processed_data.csv' and that we need to 
    re-split it using the random seed from config to get the test set.
    """
    from config import get_random_seed
    random_seed = get_random_seed()
    np.random.seed(random_seed)
    
    processed_path = os.path.join(get_processed_data_dir(), "processed_data.csv")
    
    if not os.path.exists(processed_path):
        raise FileNotFoundError(f"Processed data not found at {processed_path}. "
                                "Please run the preprocessing pipeline first.")
    
    # Load CSV manually to avoid dependency on pandas if not installed, 
    # but standard practice in this project seems to use numpy/csv.
    # Let's use the load_raw_csv from preprocess if it handles processed data, 
    # or just use csv module.
    data = []
    with open(processed_path, 'r') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if not data:
        raise ValueError("Processed data file is empty.")
    
    # Identify feature and target columns
    # Based on schema: predictors are process params, targets are mechanical props.
    # We need to know which columns are targets. 
    # Assuming the processed data has encoded alloy types and scaled numeric features.
    # We need to know the target column name. 
    # Let's assume the target is 'yield_strength' or 'ductility' or both.
    # For T027, we likely need to evaluate on the specific target the model was trained on.
    # The GPR trainer usually trains on one target at a time.
    # Let's assume we are evaluating on 'yield_strength' for this script, 
    # or we need to detect which target is present and not encoded.
    
    # Heuristic: Find columns that look like targets (yield_strength, ductility, fatigue_life)
    target_candidates = ['yield_strength', 'ductility', 'fatigue_life']
    target_col = None
    for t in target_candidates:
        if t in data[0]:
            target_col = t
            break
    
    if target_col is None:
        raise ValueError("Could not identify target column in processed data.")
    
    # Extract features and targets
    # We need to know which columns are features. 
    # Assuming all columns except target and any metadata are features.
    # But wait, the model was trained on scaled features. 
    # The processed data should contain the scaled features.
    
    features = []
    targets = []
    
    for row in data:
        # We need to know the feature columns. 
        # Let's assume the processed data has columns: [encoded_alloy, laser_power, scan_speed, ...]
        # We need to exclude the target column.
        feature_keys = [k for k in row.keys() if k != target_col and k != 'alloy_type']
        # Also exclude any non-numeric columns if present
        try:
            feat_vec = [float(row[k]) for k in feature_keys]
            target_val = float(row[target_col])
            features.append(feat_vec)
            targets.append(target_val)
        except ValueError:
            continue # Skip rows with non-numeric data if any
    
    X = np.array(features)
    y = np.array(targets)
    
    # Re-split to get test set (matching the training split logic)
    # The preprocess.py likely did a train-test split. 
    # If it saved the split indices, we'd use them. 
    # If not, we re-split with the same seed.
    # Assuming 80/20 split as per "majority-minority" in T016
    n_samples = len(y)
    indices = np.arange(n_samples)
    np.random.shuffle(indices)
    split_idx = int(0.8 * n_samples)
    
    test_indices = indices[split_idx:]
    
    X_test = X[test_indices]
    y_test = y[test_indices]
    
    return X_test, y_test, target_col

def main():
    logger = setup_logging()
    logger.info("Starting evaluation and metrics saving for T027...")
    
    ensure_directories()
    models_dir = get_models_dir()
    results_dir = get_results_dir()
    
    # Load models
    gpr_model_path = os.path.join(models_dir, "gpr_model.pkl")
    baseline_model_path = os.path.join(models_dir, "linear_regression.pkl")
    
    if not os.path.exists(gpr_model_path):
        raise FileNotFoundError(f"GPR model not found at {gpr_model_path}")
    if not os.path.exists(baseline_model_path):
        raise FileNotFoundError(f"Baseline model not found at {baseline_model_path}")
    
    with open(gpr_model_path, 'rb') as f:
        gpr_model = pickle.load(f)
    with open(baseline_model_path, 'rb') as f:
        baseline_model = pickle.load(f)
    
    # Load test data
    try:
        X_test, y_test, target_name = load_processed_test_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        # If processed data is not available, we cannot evaluate.
        # We raise to fail loudly.
        raise e
    
    logger.info(f"Loaded {len(y_test)} test samples for target: {target_name}")
    
    # Predict
    y_pred_gpr = gpr_model.predict(X_test)
    y_pred_baseline = baseline_model.predict(X_test)
    
    # Evaluate
    metrics_gpr = evaluate_model(y_test, y_pred_gpr, f"GPR_{target_name}")
    metrics_baseline = evaluate_model(y_test, y_pred_baseline, f"Linear_Baseline_{target_name}")
    
    # Compile final report
    final_report = {
        "target": target_name,
        "gpr_metrics": metrics_gpr,
        "baseline_metrics": metrics_baseline,
        "comparison": {
            "rmse_improvement": metrics_baseline['rmse'] - metrics_gpr['rmse'],
            "r2_improvement": metrics_gpr['r2'] - metrics_baseline['r2']
        }
    }
    
    # Save metrics
    output_path = save_metrics(final_report, "metrics.json")
    logger.info(f"Metrics saved to {output_path}")
    print(f"Metrics saved to {output_path}")
    print(json.dumps(final_report, indent=2))

if __name__ == "__main__":
    main()