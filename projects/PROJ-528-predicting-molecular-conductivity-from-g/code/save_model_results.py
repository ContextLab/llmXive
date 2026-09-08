import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from code.logging_config import setup_logging
from code.analysis import run_vif_iterative_loop, run_sensitivity_analysis
from code.model_training import train_models, run_cross_validation, apply_log_transformation
from code.data_loader import load_processed_data
from code.scaffold_split import scaffold_split
from code.config import SEED, OUTLIER_SIGMA

logger = setup_logging()

def load_sensitivity_analysis(path: str) -> Dict[str, Any]:
    """Load sensitivity analysis results from JSON file."""
    if not os.path.exists(path):
        logger.warning(f"Sensitivity analysis file not found at {path}. Returning empty dict.")
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load sensitivity analysis from {path}: {e}")
        return {}

def prepare_data_and_split(data_path: str, target_col: str = 'conductivity'):
    """Load data, validate target, apply log transform, and perform scaffold split."""
    logger.info(f"Loading processed data from {data_path}")
    df = load_processed_data(data_path)
    
    # Ensure target column exists
    if target_col not in df.columns:
        # Check for HOMO-LUMO gap as fallback per T026
        if 'HOMO_LUMO_gap' in df.columns:
            logger.warning(f"Target '{target_col}' not found. Using 'HOMO_LUMO_gap' as proxy.")
            target_col = 'HOMO_LUMO_gap'
        else:
            raise ValueError(f"Neither '{target_col}' nor 'HOMO_LUMO_gap' found in data.")
    
    # Apply log transformation
    df = apply_log_transformation(df, target_col)
    log_target_col = f"log_{target_col}"
    
    # Perform scaffold split
    train_idx, test_idx = scaffold_split(df, seed=SEED)
    train_df = df.iloc[train_idx]
    test_df = df.iloc[test_idx]
    
    return train_df, test_df, log_target_col

def train_models_and_get_r2(train_df: pd.DataFrame, test_df: pd.DataFrame, 
                            feature_cols: List[str], target_col: str,
                            model_type: str = 'rf') -> Dict[str, Any]:
    """Train a model and return R2 and MAE scores."""
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values
    
    model, metrics = train_models(X_train, y_train, X_test, y_test, model_type=model_type)
    return {
        'r2': metrics['r2'],
        'mae': metrics['mae'],
        'model': model
    }

def save_results_to_json(results: Dict[str, Any], output_path: str):
    """Save the final results dictionary to a JSON file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Remove non-serializable objects (like model instances) before saving
    serializable_results = {}
    for key, value in results.items():
        if isinstance(value, dict):
            serializable_results[key] = {}
            for k, v in value.items():
                if hasattr(v, '__dict__') or callable(v):
                    # Skip model objects in the saved JSON
                    continue
                if isinstance(v, (np.integer, np.floating)):
                    serializable_results[key][k] = float(v)
                else:
                    serializable_results[key][k] = v
        elif hasattr(value, '__dict__') or callable(value):
            continue # Skip model objects
        else:
            if isinstance(value, (np.integer, np.floating)):
                serializable_results[key] = float(value)
            else:
                serializable_results[key] = value
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Finalize model results by updating with VIF and Sensitivity analysis.")
    parser.add_argument("--data", type=str, default="data/processed/descriptors.csv",
                        help="Path to the processed descriptors CSV file.")
    parser.add_argument("--output", type=str, default="data/processed/model_results.json",
                        help="Path to save the final model results JSON.")
    parser.add_argument("--target", type=str, default="conductivity",
                        help="Name of the target variable column.")
    args = parser.parse_args()

    logger.info("Starting model results finalization.")

    # 1. Load Sensitivity Analysis (from T032)
    sensitivity_path = "data/processed/sensitivity_analysis.json"
    sensitivity_results = load_sensitivity_analysis(sensitivity_path)

    # 2. Prepare Data and Split
    try:
        train_df, test_df, log_target_col = prepare_data_and_split(args.data, args.target)
    except Exception as e:
        logger.error(f"Failed to prepare data: {e}")
        return 1

    # 3. Run VIF Iterative Loop (from T039c)
    # This updates the model with VIF-filtered features and returns the final metrics
    logger.info("Running VIF iterative loop...")
    try:
        final_metrics, vif_log, final_features = run_vif_iterative_loop(
            train_df, test_df, log_target_col,
            outlier_sigma=OUTLIER_SIGMA,
            vif_threshold=10.0,
            seed=SEED
        )
    except Exception as e:
        logger.error(f"VIF loop failed: {e}")
        # Fallback to full features if VIF loop fails completely, but log error
        logger.warning("Falling back to full feature set due to VIF loop failure.")
        final_features = [col for col in train_df.columns if col not in ['smiles', 'valid', 'error_msg', log_target_col]]
        final_metrics = train_models_and_get_r2(train_df, test_df, final_features, log_target_col)
        vif_log = {"iterations": [], "error": str(e)}

    # 4. Compile Final Results
    # Structure matches contracts/model_results_schema.yaml
    results = {
        "rf_r2": final_metrics['r2'],
        "gb_r2": None, # T029 trains both, but VIF loop might focus on one. Let's retrain GB for final.
        "cv_scores": {}, # Placeholder, can be populated if CV is run on final model
        "sensitivity_analysis": sensitivity_results,
        "vif_scores": vif_log
    }

    # Retrain GB on final features for final R2
    logger.info("Retraining Gradient Boosting on final VIF-filtered features...")
    try:
        gb_metrics = train_models_and_get_r2(train_df, test_df, final_features, log_target_col, model_type='gb')
        results["gb_r2"] = gb_metrics['r2']
        # Also store GB MAE if needed, though schema only asks for R2 in top level
        # We can store detailed metrics in vif_scores or a separate key if needed
    except Exception as e:
        logger.error(f"Failed to train GB model: {e}")
        results["gb_r2"] = None

    # 5. Save Results
    save_results_to_json(results, args.output)
    logger.info("Model results finalized and saved.")
    return 0

if __name__ == "__main__":
    exit(main())