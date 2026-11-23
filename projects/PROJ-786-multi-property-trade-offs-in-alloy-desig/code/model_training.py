import os
import sys
import logging
import argparse
import json
from pathlib import Path
import time
import traceback

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
import joblib

# Import from project API surface
from config import load_environment, get_config
from models.alloy_entry import AlloyEntry
from utils.logging_config import get_logger, log_info_with_context, log_warning_with_context, log_error_with_context, log_critical_with_context
from utils.convex_hull import ConvexHullWrapper

# Configure logger
logger = get_logger(__name__)

def load_encoded_data(file_path: str) -> pd.DataFrame:
    """Load the encoded alloy data from CSV."""
    if not os.path.exists(file_path):
        log_error_with_context(f"Encoded data file not found: {file_path}", logger)
        raise FileNotFoundError(f"Encoded data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    # Handle potential list-columns stored as strings if necessary, though pandas usually handles them
    # For now, assume standard numeric columns for features
    return df

def prepare_features_targets(df: pd.DataFrame) -> tuple:
    """Split dataframe into feature matrix X and target arrays (Bulk, Shear)."""
    # Identify feature columns (exclude composition, bulk_modulus, shear_modulus)
    exclude_cols = ['composition', 'bulk_modulus', 'shear_modulus']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    X = df[feature_cols].values
    y_bulk = df['bulk_modulus'].values
    y_shear = df['shear_modulus'].values
    
    # System groups for LOSO: Assume 'system' or derive from composition if not present.
    # Based on T012/T013, composition is a string. We need a 'system' column.
    # If not present, we might need to infer it or use a placeholder.
    # For this implementation, we assume a 'system' column exists or we group by composition hash if needed.
    # However, T012/T013 output schema might not include 'system'. 
    # Let's assume the data ingestion step T012 added a 'system' column or we derive it.
    # If 'system' is missing, we create a dummy group for demonstration, but ideally it's in data.
    if 'system' not in df.columns:
        log_warning_with_context("No 'system' column found. Deriving system from composition prefix for LOSO.", logger)
        # Simple heuristic: take first element symbol as system proxy if available, else hash
        # This is a fallback. Real data should have system labels (e.g., 'Fe-Cr', 'Ni-Al').
        # For now, we create a dummy group 'Unknown' if no system info, which defeats LOSO.
        # Let's try to parse the composition string if it looks like 'Element1-Element2'.
        try:
            systems = df['composition'].apply(lambda x: x.split('-')[0] if '-' in str(x) else 'Unknown')
        except Exception as e:
            log_error_with_context(f"Failed to derive system from composition: {e}", logger)
            systems = ['Unknown'] * len(df)
        groups = systems.values
    else:
        groups = df['system'].values
        
    return X, y_bulk, y_shear, groups, feature_cols

def train_model(X: np.ndarray, y: np.ndarray, name: str = "model") -> GradientBoostingRegressor:
    """Train a Gradient Boosting model."""
    # Memory constraints: max_depth and subsample
    model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=4,
        subsample=0.8,
        learning_rate=0.1,
        random_state=42,
        n_jobs=2
    )
    model.fit(X, y)
    log_info_with_context(f"Trained {name} model.", logger)
    return model

def run_loso_cv(X: np.ndarray, y_bulk: np.ndarray, y_shear: np.ndarray, groups: np.ndarray, feature_cols: list) -> dict:
    """
    Perform Leave-One-System-Out Cross-Validation.
    Returns metrics, test points, and variance stats.
    """
    logo = LeaveOneGroupOut()
    
    bulk_scores = []
    shear_scores = []
    test_points_list = []
    all_predictions_bulk = np.zeros(len(y_bulk))
    all_predictions_shear = np.zeros(len(y_bulk))
    
    # Store variance per sample
    bulk_variances = np.zeros(len(y_bulk))
    shear_variances = np.zeros(len(y_bulk))
    count_per_sample = np.zeros(len(y_bulk))
    
    log_info_with_context(f"Starting LOSO-CV with {len(np.unique(groups))} systems.", logger)
    
    for train_idx, test_idx in logo.split(X, y_bulk, groups):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train_bulk, y_test_bulk = y_bulk[train_idx], y_bulk[test_idx]
        y_train_shear, y_test_shear = y_shear[train_idx], y_shear[test_idx]
        groups_test = groups[test_idx]
        
        # Train models on this split
        model_bulk = train_model(X_train, y_train_bulk, "Bulk_LOSO")
        model_shear = train_model(X_train, y_train_shear, "Shear_LOSO")
        
        # Predict
        pred_bulk = model_bulk.predict(X_test)
        pred_shear = model_shear.predict(X_test)
        
        # Score
        r2_b = r2_score(y_test_bulk, pred_bulk)
        r2_s = r2_score(y_test_shear, pred_shear)
        bulk_scores.append(r2_b)
        shear_scores.append(r2_s)
        
        # Store predictions for variance calculation
        for i, idx in enumerate(test_idx):
            all_predictions_bulk[idx] += pred_bulk[i]
            all_predictions_shear[idx] += pred_shear[i]
            count_per_sample[idx] += 1
            
            # Accumulate test points data
            test_point = {
                'composition': X[test_idx[i]].tolist() if hasattr(X[test_idx[i]], 'tolist') else list(X[test_idx[i]]),
                'observed_bulk': y_test_bulk[i],
                'observed_shear': y_test_shear[i],
                'predicted_bulk': pred_bulk[i],
                'predicted_shear': pred_shear[i],
                'system': groups_test[i],
                'r2_bulk': r2_b,
                'r2_shear': r2_s
            }
            # Store features as well if needed, but composition string is better for CSV
            # We need to map back to original composition string if possible.
            # Since we don't have the original dataframe here, we assume X features are enough or we pass indices.
            # Better: pass the original dataframe indices or composition strings.
            # Let's assume we can reconstruct or we just store the features.
            # For the CSV output T021 requires, we need composition.
            # We will fix this by passing the original dataframe or indices.
            # For now, we store the index to look up later if needed, or just features.
            # Actually, we need to map back to the original composition string.
            # Let's assume the caller handles mapping or we pass the original dataframe.
            # To keep it simple, we'll store the features and let the user map back, 
            # OR we assume the 'composition' is in the original dataframe and we can access it via index.
            # We need the original dataframe to get the composition string.
            # Let's modify the signature to accept the original dataframe or indices.
            # For this implementation, we will assume we can't easily get the string here without passing it.
            # We will store the index in the test point and resolve it later.
            test_point['original_index'] = test_idx[i]
            test_points_list.append(test_point)
    
    # Calculate mean predictions and variances
    # Variance across splits where the sample was in the test set
    # Since each sample is in test set exactly once in LOSO (if unique groups), variance is 0?
    # Wait, LOSO: each group is held out once. If a sample belongs to a group, it is held out once.
    # So we only have ONE prediction per sample in standard LOSO.
    # To get variance, we need multiple predictions per sample.
    # The task says "variance across LOSO-CV splits". If a sample is in the test set only once, variance is undefined.
    # Perhaps the task implies K-Fold or that we treat the residuals as the uncertainty?
    # Or maybe we use the residuals from the global model as a proxy?
    # Re-reading T021: "calculate the actual uncertainty_variance for each point (variance across LOSO-CV splits)".
    # This implies samples might appear in test sets of multiple splits? That's not standard LOSO.
    # Maybe it means the variance of the PREDICTIONS for the held-out points across the different models trained?
    # But in LOSO, a specific sample is only held out in ONE split.
    # Unless the "system" definition is such that a sample can be in multiple systems? Unlikely.
    # Alternative interpretation: The variance of the R2 scores? No, "for each point".
    # Maybe we use the residuals from the GLOBAL model (trained on all data) as the uncertainty estimate?
    # Or maybe we use the variance of the predictions from the models trained on the training folds?
    # Let's assume the task wants the residual magnitude as a proxy for uncertainty, 
    # OR we use the variance of the predictions if we did K-Fold.
    # Given the constraint "variance across LOSO-CV splits", and the fact that in LOSO a point is tested once,
    # this metric is technically 0 or undefined per point.
    # However, T022 says "calculate the actual uncertainty_variance... (variance across LOSO-CV splits)".
    # This suggests a misunderstanding in the task description or a specific setup (e.g. overlapping systems?).
    # Let's assume we use the absolute residual from the GLOBAL model as the "uncertainty" for now, 
    # or we calculate the variance of the R2 scores as a global metric.
    # But the task asks for "per point".
    # Let's try a different approach: Use the residuals from the GLOBAL model (trained on all data) as the uncertainty.
    # Train global models
    global_model_bulk = train_model(X, y_bulk, "Global_Bulk")
    global_model_shear = train_model(X, y_shear, "Global_Shear")
    pred_global_bulk = global_model_bulk.predict(X)
    pred_global_shear = global_model_shear.predict(X)
    
    residuals_bulk = y_bulk - pred_global_bulk
    residuals_shear = y_shear - pred_global_shear
    
    # Use absolute residual as uncertainty proxy if variance is not calculable per point in LOSO
    # Or, if we assume the "variance" refers to the variance of the R2 scores across splits (global metric),
    # we calculate that.
    # Let's calculate the variance of the R2 scores as a global metric and assign a placeholder per point if needed.
    # But T021 says "placeholder for uncertainty_variance". T022 calculates the actual one.
    # If we can't calculate it per point, we put 0 or the global residual variance.
    # Let's use the global residual standard deviation as a placeholder for each point.
    global_uncertainty_bulk = np.std(residuals_bulk)
    global_uncertainty_shear = np.std(residuals_shear)
    
    # Construct the result
    # We need to map test_points_list back to the original dataframe to get composition strings.
    # We'll do this in the caller or assume we have the dataframe.
    # For now, we return the raw data and let the caller format it.
    
    avg_r2_bulk = np.mean(bulk_scores)
    avg_r2_shear = np.mean(shear_scores)
    
    result = {
        'loso_r2_bulk': float(avg_r2_bulk),
        'loso_r2_shear': float(avg_r2_shear),
        'r2_std_bulk': float(np.std(bulk_scores)),
        'r2_std_shear': float(np.std(shear_scores)),
        'num_systems': len(np.unique(groups)),
        'test_points': test_points_list,
        'global_uncertainty_bulk': float(global_uncertainty_bulk),
        'global_uncertainty_shear': float(global_uncertainty_shear),
        'coverage_stats': {
            'total_samples': len(y_bulk),
            'systems_covered': int(len(np.unique(groups)))
        }
    }
    
    return result

def save_loso_test_points_csv(test_points: list, output_path: str, original_df: pd.DataFrame):
    """Save LOSO test points to CSV, resolving indices to composition strings."""
    # Map index to composition
    idx_to_comp = dict(zip(original_df.index, original_df['composition']))
    
    rows = []
    for tp in test_points:
        idx = tp['original_index']
        comp = idx_to_comp.get(idx, "Unknown")
        row = {
            'composition': comp,
            'observed_bulk': tp['observed_bulk'],
            'observed_shear': tp['observed_shear'],
            'predicted_bulk': tp['predicted_bulk'],
            'predicted_shear': tp['predicted_shear'],
            'system': tp['system'],
            'r2_bulk': tp['r2_bulk'],
            'r2_shear': tp['r2_shear'],
            'uncertainty_variance': 0.0 # Placeholder as per T021, will be updated in T022
        }
        rows.append(row)
    
    df_out = pd.DataFrame(rows)
    df_out.to_csv(output_path, index=False)
    log_info_with_context(f"Saved LOSO test points to {output_path}", logger)

def generate_validation_report(metrics: dict, output_path: str):
    """Generate and save the model validation report JSON."""
    report = {
        'loso_metrics': {
            'bulk_r2_mean': metrics['loso_r2_bulk'],
            'bulk_r2_std': metrics['r2_std_bulk'],
            'shear_r2_mean': metrics['loso_r2_shear'],
            'shear_r2_std': metrics['r2_std_shear']
        },
        'system_level_variance': {
            'bulk_variance': metrics['r2_std_bulk'] ** 2,
            'shear_variance': metrics['r2_std_shear'] ** 2
        },
        'coverage_stats': metrics['coverage_stats'],
        'uncertainty_variance': {
            'bulk_placeholder': metrics['global_uncertainty_bulk'],
            'shear_placeholder': metrics['global_uncertainty_shear'],
            'note': "Placeholder values. Actual per-point variance to be calculated in T022."
        },
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    log_info_with_context(f"Saved validation report to {output_path}", logger)

def run_training_pipeline(input_path: str, output_csv: str, output_json: str):
    """Main pipeline for T021: LOSO-CV and report generation."""
    log_info_with_context(f"Starting Training Pipeline: {input_path}", logger)
    
    # Load data
    df = load_encoded_data(input_path)
    X, y_bulk, y_shear, groups, feature_cols = prepare_features_targets(df)
    
    # Run LOSO
    metrics = run_loso_cv(X, y_bulk, y_shear, groups, feature_cols)
    
    # Save outputs
    save_loso_test_points_csv(metrics['test_points'], output_csv, df)
    generate_validation_report(metrics, output_json)
    
    # Check R2 constraint
    r2_bulk = metrics['loso_r2_bulk']
    r2_shear = metrics['loso_r2_shear']
    
    if r2_bulk <= 0.6 or r2_shear <= 0.6:
        log_critical_with_context(f"LOSO-CV R2 score <= 0.6 (Bulk: {r2_bulk:.4f}, Shear: {r2_shear:.4f}). Triggering fallback to Poisson Anomaly mode.", logger)
        # Note: The task says "log a critical failure AND trigger fallback".
        # We log it. The actual fallback logic might be in the main orchestration or a flag.
        # We set a flag or exit code? The task says "not just exit with error".
        # We log and continue to allow T022 to run on the data, but mark the report as failed?
        # Or we write a flag to the JSON.
        # Let's add a 'fallback_triggered' flag to the report.
        # But T021 is the one writing the report.
        # We can update the report JSON to include this flag.
        # However, generate_validation_report is called before this check.
        # Let's modify the report after generation or pass the flag.
        # For simplicity, we log it and the user (main.py) handles the flow control.
        # But the task says "trigger fallback".
        # We can create a flag file or update the JSON.
        # Let's update the JSON to include 'fallback_triggered': True.
        # We need to reload the JSON, add the key, and save.
        with open(output_json, 'r') as f:
            report = json.load(f)
        report['fallback_triggered'] = True
        report['fallback_reason'] = f"R2 <= 0.6 (Bulk: {r2_bulk:.4f}, Shear: {r2_shear:.4f})"
        with open(output_json, 'w') as f:
            json.dump(report, f, indent=2)
        log_info_with_context(f"Updated validation report with fallback trigger.", logger)
    else:
        log_info_with_context(f"LOSO-CV R2 scores acceptable (Bulk: {r2_bulk:.4f}, Shear: {r2_shear:.4f}).", logger)
        
    return metrics

def save_models(models: dict, output_dir: str):
    """Save trained models."""
    os.makedirs(output_dir, exist_ok=True)
    for name, model in models.items():
        path = os.path.join(output_dir, f"{name}.pkl")
        joblib.dump(model, path)
        log_info_with_context(f"Saved model {name} to {path}", logger)

def main():
    parser = argparse.ArgumentParser(description="Model Training and LOSO-CV Validation")
    parser.add_argument('--input', type=str, default='data/processed/encoded_alloys.csv', help='Input encoded data CSV')
    parser.add_argument('--output-csv', type=str, default='data/processed/loso_test_points.csv', help='Output LOSO test points CSV')
    parser.add_argument('--output-json', type=str, default='data/processed/model_validation_report.json', help='Output validation report JSON')
    parser.add_argument('--models-dir', type=str, default='data/models', help='Directory to save models')
    args = parser.parse_args()
    
    load_environment()
    config = get_config()
    setup_logging = logging.getLogger()
    setup_logging.setLevel(logging.INFO)
    
    try:
        run_training_pipeline(args.input, args.output_csv, args.output_json)
        log_info_with_context("Training pipeline completed successfully.", logger)
    except Exception as e:
        log_error_with_context(f"Training pipeline failed: {e}", logger)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
