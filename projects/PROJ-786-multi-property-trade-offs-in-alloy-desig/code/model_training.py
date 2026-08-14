import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import r2_score, mean_squared_error
from scipy.stats import sem
import pickle

from config import load_environment, parse_cli_args, get_config, verify_config
from utils.logging_config import get_logger, log_info_with_context, log_error_with_context, log_warning_with_context
from utils.convex_hull import ConvexHullWrapper

# Ensure imports from sibling modules match API surface exactly
# Note: We assume load_encoded_data, prepare_features_targets, etc. are defined elsewhere in this file 
# or imported from a shared module. Since the API surface lists them as public names of this module,
# we define them here to make the file self-contained and runnable as per the "Implement the task for real" constraint.

logger = get_logger(__name__)

def load_encoded_data(data_path: str) -> pd.DataFrame:
    """Load encoded alloy data from CSV."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Encoded data file not found: {data_path}")
    df = pd.read_csv(data_path)
    return df

def prepare_features_targets(df: pd.DataFrame, target_cols: List[str]) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """
    Prepare feature matrix X and target dictionary Y.
    Assumes 'composition_vector' or similar flattened columns exist, or specific feature columns.
    For this implementation, we assume columns starting with 'feat_' are features, 
    and target_cols are the targets.
    """
    feature_cols = [col for col in df.columns if col.startswith('feat_')]
    if not feature_cols:
        # Fallback: assume all non-target numeric columns are features
        feature_cols = [col for col in df.columns if col not in target_cols and df[col].dtype in ['float64', 'int64']]
    
    X = df[feature_cols].values
    Y = {col: df[col].values for col in target_cols}
    return X, Y

def train_model(X: np.ndarray, y: np.ndarray, config: Dict[str, Any]) -> GradientBoostingRegressor:
    """Train a Gradient Boosting Regressor."""
    model = GradientBoostingRegressor(
        n_estimators=config.get('n_estimators', 100),
        max_depth=config.get('max_depth', 3),
        learning_rate=config.get('learning_rate', 0.1),
        n_jobs=config.get('n_jobs', 2)
    )
    model.fit(X, y)
    return model

def run_loso_cv(X: np.ndarray, Y: Dict[str, np.ndarray], groups: np.ndarray, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Leave-One-System-Out Cross-Validation.
    'groups' should be an array of system identifiers (e.g., alloy system names).
    Returns a dictionary of metrics per target and per fold.
    """
    logo = LeaveOneGroupOut()
    results = {target: {'r2': [], 'mse': [], 'predictions': [], 'actuals': []} for target in Y.keys()}
    
    log_info_with_context(logger, "Starting LOSO-CV", context={"n_splits": logo.get_n_splits(X, y=None, groups=groups)})

    for train_idx, test_idx in logo.split(X, y=None, groups=groups):
        X_train, X_test = X[train_idx], X[test_idx]
        
        fold_results = {}
        for target_name, y_full in Y.items():
            y_train, y_test = y_full[train_idx], y_full[test_idx]
            
            # Train on fold
            model = train_model(X_train, y_train, config)
            y_pred = model.predict(X_test)
            
            # Metrics
            r2 = r2_score(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            
            results[target_name]['r2'].append(r2)
            results[target_name]['mse'].append(mse)
            results[target_name]['predictions'].extend(y_pred)
            results[target_name]['actuals'].extend(y_test)
    
    # Aggregate results
    aggregated = {}
    for target_name, data in results.items():
        aggregated[target_name] = {
            'mean_r2': np.mean(data['r2']),
            'std_r2': np.std(data['r2']),
            'sem_r2': sem(data['r2']) if len(data['r2']) > 1 else 0.0,
            'mean_mse': np.mean(data['mse']),
            'std_mse': np.std(data['mse']),
            'sem_mse': sem(data['mse']) if len(data['mse']) > 1 else 0.0,
            'all_r2_scores': data['r2']
        }
    
    return aggregated

def calculate_uncertainty(X: np.ndarray, Y: Dict[str, np.ndarray], groups: np.ndarray, config: Dict[str, Any]) -> Dict[str, np.ndarray]:
    """
    Calculate uncertainty metrics for each sample based on LOSO-CV results.
    Uncertainty is defined as the standard deviation of predictions when the sample's system is left out.
    Returns a dictionary of uncertainty arrays (same length as X) for each target.
    """
    logo = LeaveOneGroupOut()
    uncertainties = {target: [] for target in Y.keys()}
    
    log_info_with_context(logger, "Calculating sample-wise uncertainty via LOSO-CV", context={"n_samples": len(X)})

    # We need to map each sample to its group to know which fold it was in
    # In LOSO, a sample is in the test set only when its group is the held-out group.
    # We iterate through splits and collect predictions for the test set.
    
    # Initialize lists to store predictions for each sample
    all_predictions = {target: [None] * len(X) for target in Y.keys()}
    
    for train_idx, test_idx in logo.split(X, y=None, groups=groups):
        X_train, X_test = X[train_idx], X[test_idx]
        
        for target_name, y_full in Y.items():
            y_train, y_test = y_full[train_idx], y_full[test_idx]
            
            model = train_model(X_train, y_train, config)
            y_pred = model.predict(X_test)
            
            # Store predictions for the test samples
            for i, idx in enumerate(test_idx):
                all_predictions[target_name][idx] = y_pred[i]
    
    # Calculate uncertainty (std dev) for each sample
    # Since each sample is tested exactly once in LOSO (when its group is left out),
    # we actually only have one prediction per sample. 
    # Wait, the standard definition of uncertainty in this context (LOSO) usually implies:
    # 1. Variance across folds if we were doing K-fold (but LOSO is specific).
    # 2. Or, we calculate the variance of the model's predictions on the *training* set of the left-out fold? No.
    #
    # Re-reading T022b: "link LOSO-CV results (T021) to the uncertainty metrics".
    # T021 calculates global metrics (mean R2, etc.). T022 calculates uncertainty.
    # A common approach for uncertainty in regression with LOSO is:
    # - The variance of the prediction error across the folds? But each sample is in only one test fold.
    # - Alternative: The variance of the model's predictions on the test set across different models? 
    #   But in LOSO, we only have one model for the test set of a specific group.
    #
    # Correction: In LOSO, we can calculate the uncertainty of a sample by looking at the variance of predictions 
    # made by models trained on *other* systems? No, that's not how LOSO works.
    #
    # Let's interpret "uncertainty" as the variance of the prediction errors for the samples in the test set of each fold.
    # But the task asks for uncertainty *per sample*.
    #
    # Standard practice for "uncertainty" in this context (often called "prediction interval" or "model variance"):
    # If we had multiple models, we could take the std dev of their predictions.
    # In LOSO, we have one model per group-left-out.
    # Perhaps the intent is to use the *global* variance of residuals from the LOSO-CV as a proxy for uncertainty?
    # Or, we calculate the variance of the predictions for a sample if we had multiple models?
    #
    # Let's pivot to a robust interpretation:
    # "Uncertainty" = The standard deviation of the prediction errors (residuals) for the samples in the test set of each fold.
    # But we need per-sample uncertainty.
    #
    # Alternative interpretation (Bagging-like approach within LOSO):
    # For a given sample, its uncertainty is the variance of predictions made by all models that *did not* include its group in training?
    # No, that's impossible because the model trained without its group is the one that predicts it.
    #
    # Let's go with the most common interpretation in materials science ML with LOSO:
    # Uncertainty for a sample is the standard deviation of the prediction errors of the models trained on the other systems, 
    # but applied to the sample? No.
    #
    # Actually, a simpler and common approach:
    # Calculate the global RMSE from LOSO-CV. Use that as a uniform uncertainty.
    # But the task implies a link to LOSO results specifically for *flagging regions*.
    #
    # Let's try this:
    # For each sample, we can't get a variance from LOSO directly because it's tested once.
    # HOWEVER, we can calculate the variance of the model's predictions on the *training* data of the fold? No.
    #
    # Let's re-read the requirement: "link LOSO-CV results to the uncertainty metrics".
    # Maybe it means: Use the LOSO-CV R2 scores to define a threshold for uncertainty?
    # Or: The uncertainty of a prediction is high if the model trained on the other systems performs poorly (low R2) on the test set?
    #
    # Let's implement a practical approach:
    # 1. Run LOSO-CV.
    # 2. For each fold (system left out), calculate the R2 and MSE on the test set.
    # 3. Assign the MSE (or RMSE) of that fold to all samples in that test set as their "uncertainty".
    # This links the uncertainty of a sample to the generalizability of the model for its specific system.
    # If a system is hard to predict (high MSE in LOSO), its samples have high uncertainty.
    
    fold_uncertainties = {target: [] for target in Y.keys()}
    sample_uncertainties = {target: np.zeros(len(X)) for target in Y.keys()}
    
    for fold_idx, (train_idx, test_idx) in enumerate(logo.split(X, y=None, groups=groups)):
        X_train, X_test = X[train_idx], X[test_idx]
        test_group = groups[test_idx[0]] # All in test_idx belong to the same group
        
        for target_name, y_full in Y.items():
            y_train, y_test = y_full[train_idx], y_full[test_idx]
            
            model = train_model(X_train, y_train, config)
            y_pred = model.predict(X_test)
            
            # Calculate fold-specific MSE
            fold_mse = mean_squared_error(y_test, y_pred)
            fold_rmse = np.sqrt(fold_mse)
            
            # Assign this RMSE as uncertainty to all samples in this test fold
            for idx in test_idx:
                sample_uncertainties[target_name][idx] = fold_rmse
            
            fold_uncertainties[target_name].append(fold_rmse)
    
    return sample_uncertainties

def save_metrics(metrics: Dict[str, Any], output_path: str):
    """Save metrics to JSON."""
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    log_info_with_context(logger, "Metrics saved", context={"path": output_path})

def save_models(models: Dict[str, GradientBoostingRegressor], output_dir: str):
    """Save trained models to pickle files."""
    os.makedirs(output_dir, exist_ok=True)
    for name, model in models.items():
        path = os.path.join(output_dir, f"{name}_model.pkl")
        with open(path, 'wb') as f:
            pickle.dump(model, f)
    log_info_with_context(logger, "Models saved", context={"path": output_dir})

def run_training_pipeline(data_path: str, output_dir: str, config: Dict[str, Any]):
    """Run the full training pipeline including LOSO-CV and uncertainty calculation."""
    # Load data
    df = load_encoded_data(data_path)
    
    # Identify system column (assuming 'system_name' or similar)
    system_col = 'system_name'
    if system_col not in df.columns:
        # Fallback: try to find a column that looks like a system identifier
        system_col = next((c for c in df.columns if 'system' in c.lower()), None)
        if not system_col:
            raise ValueError("Could not find system identifier column in data")
    
    target_cols = ['bulk_modulus', 'shear_modulus']
    if not all(col in df.columns for col in target_cols):
        raise ValueError(f"Missing target columns. Expected: {target_cols}")
    
    X, Y = prepare_features_targets(df, target_cols)
    groups = df[system_col].values
    
    # Run LOSO-CV
    loso_metrics = run_loso_cv(X, Y, groups, config)
    
    # Calculate uncertainty (linked to LOSO results)
    uncertainties = calculate_uncertainty(X, Y, groups, config)
    
    # Integrate uncertainty into LOSO metrics for FR-006 coverage
    # We add the mean uncertainty per target to the metrics
    for target in target_cols:
        loso_metrics[target]['mean_uncertainty'] = float(np.mean(uncertainties[target]))
        loso_metrics[target]['max_uncertainty'] = float(np.max(uncertainties[target]))
        loso_metrics[target]['uncertainty_samples'] = uncertainties[target].tolist()
    
    # Train final models on full data
    final_models = {}
    for target in target_cols:
        model = train_model(X, Y[target], config)
        final_models[target] = model
    
    # Save results
    metrics_path = os.path.join(output_dir, "training_metrics.json")
    save_metrics(loso_metrics, metrics_path)
    
    models_path = os.path.join(output_dir, "models")
    save_models(final_models, models_path)
    
    # Save uncertainty data for downstream tasks (T034, T022b verification)
    uncertainty_path = os.path.join(output_dir, "uncertainties.csv")
    uncertainty_df = pd.DataFrame(uncertainties)
    uncertainty_df['system_name'] = groups
    uncertainty_df.to_csv(uncertainty_path, index=False)
    
    log_info_with_context(logger, "Training pipeline completed", context={"output_dir": output_dir})
    
    return loso_metrics, final_models, uncertainties

def main():
    """Main entry point for model training."""
    args = parse_cli_args()
    load_environment()
    config = get_config()
    
    # Override config with CLI args if provided
    if args.config:
        config.update(args.config)
    
    data_path = config.get('data_path', 'data/processed/encoded_alloys.csv')
    output_dir = config.get('output_dir', 'data/processed/models')
    
    try:
        metrics, models, uncertainties = run_training_pipeline(data_path, output_dir, config)
        print("Training completed successfully.")
        print(f"LOSO R2 (Bulk): {metrics['bulk_modulus']['mean_r2']:.4f} +/- {metrics['bulk_modulus']['std_r2']:.4f}")
        print(f"LOSO R2 (Shear): {metrics['shear_modulus']['mean_r2']:.4f} +/- {metrics['shear_modulus']['std_r2']:.4f}")
    except Exception as e:
        log_error_with_context(logger, str(e), context={"task": "model_training"})
        sys.exit(1)

if __name__ == "__main__":
    main()
