import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import pickle
from pathlib import Path

# Project root and path utilities (imported from existing infrastructure if available, 
# but we define minimal helpers here to ensure standalone execution if needed)
def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def ensure_output_directories():
    """Ensure all necessary output directories exist."""
    dirs = [
        "data/processed",
        "data/validation",
        "data/state",
        "figures"
    ]
    project_root = get_project_root()
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)

def load_json_file(path: str) -> Dict:
    """Load a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path: str, data: Dict):
    """Save a dictionary to a JSON file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_csv_file(path: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    return pd.read_csv(path)

def save_csv_file(path: str, df: pd.DataFrame):
    """Save a DataFrame to a CSV file."""
    df.to_csv(path, index=False)

def load_processed_data():
    """Load processed features and targets."""
    project_root = get_project_root()
    features_path = project_root / "data" / "processed" / "features.csv"
    targets_path = project_root / "data" / "processed" / "targets.csv"
    
    if not features_path.exists() or not targets_path.exists():
        raise FileNotFoundError("Processed data files not found. Run T018/T020 first.")
    
    return load_csv_file(str(features_path)), load_csv_file(str(targets_path))

def load_models():
    """Load trained models from T021."""
    project_root = get_project_root()
    model_path = project_root / "data" / "processed" / "models.pkl"
    
    if not model_path.exists():
        raise FileNotFoundError("Trained models not found. Run T021 first.")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_confounding_config():
    """Load confounding configuration."""
    project_root = get_project_root()
    config_path = project_root / "data" / "processed" / "confounding_config.json"
    
    if not config_path.exists():
        return {}
    
    return load_json_file(str(config_path))

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, threshold: float) -> Tuple[float, float]:
    """
    Calculate FPR and FNR for a given threshold.
    
    For regression-to-classification conversion, we binarize based on deviation from mean.
    We consider a prediction as 'positive' (defect significantly impacts property) 
    if the absolute relative change exceeds the threshold.
    
    Args:
        y_true: True values (relative changes)
        y_pred: Predicted values (relative changes)
        threshold: Threshold for binarization
        
    Returns:
        Tuple of (FPR, FNR)
    """
    # Binarize: 1 if absolute relative change > threshold, else 0
    y_true_bin = (np.abs(y_true) > threshold).astype(int)
    y_pred_bin = (np.abs(y_pred) > threshold).astype(int)
    
    # Calculate confusion matrix components
    tp = np.sum((y_true_bin == 1) & (y_pred_bin == 1))
    tn = np.sum((y_true_bin == 0) & (y_pred_bin == 0))
    fp = np.sum((y_true_bin == 0) & (y_pred_bin == 1))
    fn = np.sum((y_true_bin == 1) & (y_pred_bin == 0))
    
    # Calculate rates
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    return fpr, fnr

def run_sensitivity_analysis():
    """
    Run sensitivity analysis over different thresholds.
    
    This implements T033: Generate table of FPR/FNR vs. swept thresholds.
    Sweeps over:
    - Deciles of the absolute relative change distribution
    - Fixed thresholds: {low, medium, high} -> {0.05, 0.10, 0.15}
    
    Outputs:
        data/validation/sensitivity_table.csv
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting sensitivity analysis (T033)...")
    
    # Ensure output directories
    ensure_output_directories()
    
    # Load processed data
    try:
        features, targets = load_processed_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Load models
    try:
        models = load_models()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # Determine which target properties we have
    target_cols = [col for col in targets.columns if col in ['conductivity', 'youngs_modulus', 'fracture_strength']]
    
    if not target_cols:
        logger.warning("No target properties found in processed data.")
        # Create empty result
        result_df = pd.DataFrame(columns=['property', 'threshold_type', 'threshold_value', 'fpr', 'fnr'])
        output_path = get_project_root() / "data" / "validation" / "sensitivity_table.csv"
        save_csv_file(str(output_path), result_df)
        logger.info(f"Saved empty sensitivity table to {output_path}")
        return
    
    results = []
    
    # Define threshold sets
    # 1. Fixed thresholds: low (0.05), medium (0.10), high (0.15)
    fixed_thresholds = {
        'low': 0.05,
        'medium': 0.10,
        'high': 0.15
    }
    
    # 2. Decile-based thresholds (using the first target property as reference)
    first_target = target_cols[0]
    y_true_first = targets[first_target].values
    abs_changes = np.abs(y_true_first)
    
    # Calculate deciles (10%, 20%, ..., 90%)
    decile_thresholds = np.percentile(abs_changes, [10, 20, 30, 40, 50, 60, 70, 80, 90])
    decile_labels = [f'decile_{int(p)}' for p in [10, 20, 30, 40, 50, 60, 70, 80, 90]]
    
    all_thresholds = []
    for label, value in fixed_thresholds.items():
        all_thresholds.append((label, value))
    for label, value in zip(decile_labels, decile_thresholds):
        all_thresholds.append((label, value))
    
    logger.info(f"Analyzing {len(target_cols)} target properties with {len(all_thresholds)} thresholds...")
    
    # For each target property
    for target_col in target_cols:
        y_true = targets[target_col].values
        
        # Get predictions from the model
        # Assuming models is a dict with target names as keys
        if target_col not in models:
            logger.warning(f"Model for {target_col} not found, skipping.")
            continue
        
        model = models[target_col]
        
        # Predict (assuming features are already prepared)
        # We need to handle the case where features might have different columns than expected
        # For simplicity, we use all numeric columns in features
        feature_cols = [col for col in features.columns if col not in ['id', 'defect_type']]
        X = features[feature_cols].values
        
        try:
            y_pred = model.predict(X)
        except Exception as e:
            logger.error(f"Error predicting for {target_col}: {e}")
            continue
        
        # Ensure y_pred has same length as y_true
        if len(y_pred) != len(y_true):
            logger.error(f"Prediction length mismatch for {target_col}")
            continue
        
        # Calculate metrics for each threshold
        for threshold_label, threshold_value in all_thresholds:
            fpr, fnr = calculate_metrics(y_true, y_pred, threshold_value)
            
            results.append({
                'property': target_col,
                'threshold_type': 'fixed' if threshold_label in fixed_thresholds else 'decile',
                'threshold_value': threshold_value,
                'threshold_label': threshold_label,
                'fpr': fpr,
                'fnr': fnr
            })
    
    # Create results DataFrame
    result_df = pd.DataFrame(results)
    
    # Sort by property and threshold value
    result_df = result_df.sort_values(['property', 'threshold_value'])
    
    # Save to CSV
    output_path = get_project_root() / "data" / "validation" / "sensitivity_table.csv"
    save_csv_file(str(output_path), result_df)
    
    logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
    logger.info(f"Total rows: {len(result_df)}")
    
    return result_df

def run_inference_analysis():
    """
    Main function to run inference analysis including sensitivity analysis.
    This is the entry point for T033.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Running inference analysis...")
    
    # Run sensitivity analysis (T033)
    try:
        sensitivity_results = run_sensitivity_analysis()
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise
    
    logger.info("Inference analysis complete.")
    return sensitivity_results

def main():
    """Main entry point for the script."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting code/04_inference.py (T033 - Sensitivity Analysis Report)")
    
    try:
        results = run_inference_analysis()
        logger.info("Script completed successfully.")
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        raise

if __name__ == "__main__":
    main()