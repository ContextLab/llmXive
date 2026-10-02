import os
import json
import logging
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from sklearn.model_selection import GroupKFold
import json
import hashlib

from code.config import get_project_root, get_data_paths, get_config_summary, save_config_snapshot
from code.modeling.confidence_intervals import calculate_prediction_intervals

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_input_data(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate input dataframe against the dataset schema.
    Checks for required columns and types.
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required columns
    for field in required_fields:
        if field not in df.columns:
            logger.error(f"Missing required column: {field}")
            return False
    
    # Basic type validation (simplified)
    # In a real scenario, we'd check types more rigorously
    if 'segregation_energy' in df.columns and not pd.api.types.is_numeric_dtype(df['segregation_energy']):
        logger.error("segregation_energy must be numeric")
        return False
    
    return True

def check_collinearity_warning() -> bool:
    """
    Check if collinearity report exists and indicates high VIF.
    Returns True if warning should be logged.
    """
    project_root = get_project_root()
    report_path = project_root / 'data' / 'processed' / 'collinearity_report.md'
    
    if not report_path.exists():
        logger.warning("Collinearity report not found. Proceeding without check.")
        return False
    
    try:
        with open(report_path, 'r') as f:
            content = f.read()
            # Simple heuristic: check for VIF >= 10 mention
            if "VIF" in content and "10" in content:
                logger.warning("High collinearity detected in previous report. P-values may be unstable.")
                return True
    except Exception as e:
        logger.warning(f"Could not read collinearity report: {e}")
    
    return False

def train_model(X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a single OLS model and return results.
    Returns the fitted model object and a dict of metrics.
    """
    # Add constant for intercept
    X_const = add_constant(X)
    
    model = OLS(y, X_const)
    results = model.fit()
    
    metrics = {
        'r2': results.rsquared,
        'rmse': np.sqrt(np.mean(results.resid ** 2)),
        'p_values': results.pvalues.to_dict(),
        'coefficients': results.params.to_dict(),
        'std_errors': results.bse.to_dict()
    }
    
    return results, metrics

def run_kfold_cv(
    df: pd.DataFrame, 
    feature_cols: List[str], 
    target_col: str, 
    group_col: str,
    n_splits: int = 5
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Run k-fold cross-validation with GroupKFold.
    Logic: IF N >= 5 THEN use 5-fold CV. ELSE use LOOCV.
    Extracts p-values for each fold.
    """
    n_samples = len(df)
    
    # Determine split strategy
    if n_samples >= 5:
        n_splits = min(n_splits, n_samples)
        cv = GroupKFold(n_splits=n_splits)
        logger.info(f"Using {n_splits}-fold CV (N={n_samples})")
    else:
        # LOOCV for small datasets
        n_splits = n_samples
        cv = GroupKFold(n_splits=n_samples)
        logger.info(f"Using LOOCV (N={n_samples})")
    
    X = df[feature_cols].values
    y = df[target_col].values
    groups = df[group_col].values if group_col in df.columns else np.zeros(n_samples)
    
    fold_metrics = []
    all_p_values = []
    all_r2 = []
    all_rmse = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y, groups)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Train model on this fold
        _, metrics = train_model(X_train, y_train)
        
        # Evaluate on test set
        X_test_const = add_constant(X_test)
        y_pred = metrics['coefficients']  # This is wrong, need to predict
        
        # Re-fit to get prediction capability for test set metrics
        X_train_const = add_constant(X_train)
        model_fold = OLS(y_train, X_train_const)
        results_fold = model_fold.fit()
        
        y_pred = results_fold.predict(X_test_const)
        r2_fold = results_fold.rsquared
        rmse_fold = np.sqrt(np.mean((y_test - y_pred) ** 2))
        
        fold_data = {
            'fold': fold_idx + 1,
            'r2': r2_fold,
            'rmse': rmse_fold,
            'p_values': results_fold.pvalues.to_dict(),
            'coefficients': results_fold.params.to_dict(),
            'n_train': len(train_idx),
            'n_test': len(test_idx)
        }
        fold_metrics.append(fold_data)
        
        all_r2.append(r2_fold)
        all_rmse.append(rmse_fold)
        
        # Collect p-values for each feature
        for feat in feature_cols:
            if feat in results_fold.pvalues.index:
                all_p_values.append({
                    'feature': feat,
                    'fold': fold_idx + 1,
                    'p_value': float(results_fold.pvalues[feat])
                })
    
    # Aggregate metrics
    aggregated = {
        'r2_mean': float(np.mean(all_r2)),
        'r2_std': float(np.std(all_r2)),
        'rmse_mean': float(np.mean(all_rmse)),
        'rmse_std': float(np.std(all_rmse)),
        'n_folds': n_splits
    }
    
    return aggregated, fold_metrics

def calculate_confidence_intervals(
    df: pd.DataFrame, 
    feature_cols: List[str], 
    target_col: str
) -> pd.DataFrame:
    """
    Calculate confidence intervals for predictions using statsmodels get_prediction.
    """
    X = df[feature_cols].values
    y = df[target_col].values
    
    X_const = add_constant(X)
    model = OLS(y, X_const)
    results = model.fit()
    
    # Get prediction intervals
    pred = results.get_prediction(X_const)
    summary_frame = pred.summary_frame(alpha=0.05)
    
    df['predicted_energy'] = pred.predicted_mean
    df['ci_lower'] = summary_frame['obs_ci_lower']
    df['ci_upper'] = summary_frame['obs_ci_upper']
    
    return df

def save_results(
    aggregated_metrics: Dict[str, Any],
    fold_metrics: List[Dict[str, Any]],
    df_with_ci: pd.DataFrame,
    config_snapshot: Dict[str, Any]
) -> None:
    """
    Save all results to disk.
    - results/metrics.json: Aggregated metrics
    - results/metrics_per_fold.json: Per-fold metrics including p-values
    - results/confidence_intervals.json: Predictions with intervals
    - state/project.yaml: Provenance hash
    """
    project_root = get_project_root()
    results_dir = project_root / 'results'
    state_dir = project_root / 'state'
    
    results_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Save aggregated metrics
    metrics_path = results_dir / 'metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(aggregated_metrics, f, indent=2)
    logger.info(f"Saved aggregated metrics to {metrics_path}")
    
    # Save per-fold metrics (including p-values)
    fold_path = results_dir / 'metrics_per_fold.json'
    with open(fold_path, 'w') as f:
        json.dump(fold_metrics, f, indent=2)
    logger.info(f"Saved per-fold metrics to {fold_path}")
    
    # Save confidence intervals
    ci_path = results_dir / 'confidence_intervals.json'
    df_with_ci.to_json(ci_path, orient='records', indent=2)
    logger.info(f"Saved confidence intervals to {ci_path}")
    
    # Save config snapshot and compute hash
    config_snapshot['code_version_hash'] = hashlib.sha256(
        json.dumps(config_snapshot, sort_keys=True).encode()
    ).hexdigest()
    
    state_path = state_dir / 'project.yaml'
    with open(state_path, 'w') as f:
        yaml.dump(config_snapshot, f, default_flow_style=False)
    logger.info(f"Saved project state to {state_path}")

def main():
    """
    Main entry point for T023: Train Linear Regression model with k-fold CV.
    """
    project_root = get_project_root()
    data_paths = get_data_paths()
    
    # Load input data
    processed_data_path = project_root / 'data' / 'processed' / 'segregation_energies.csv'
    if not processed_data_path.exists():
        logger.error(f"Input data not found: {processed_data_path}")
        return
    
    df = pd.read_csv(processed_data_path)
    logger.info(f"Loaded {len(df)} samples from {processed_data_path}")
    
    # Load schema for validation
    schema_path = project_root / 'contracts' / 'dataset.schema.yaml'
    schema = load_schema(schema_path)
    
    # Validate input
    if not validate_input_data(df, schema):
        logger.error("Input validation failed. Exiting.")
        return
    
    # Check collinearity warning
    check_collinearity_warning()
    
    # Define features and target
    feature_cols = ['rdf_peak', 'pair_corr', 'voronoi_count']
    target_col = 'segregation_energy'
    group_col = 'sample_id' # Using sample_id as group to ensure unique samples per fold
    
    # Filter out rows with missing values in features or target
    valid_mask = df[feature_cols + [target_col]].notna().all(axis=1)
    df_clean = df[valid_mask].reset_index(drop=True)
    
    if len(df_clean) == 0:
        logger.error("No valid data after cleaning. Exiting.")
        return
    
    logger.info(f"Training on {len(df_clean)} clean samples")
    
    # Run k-fold CV
    aggregated, fold_metrics = run_kfold_cv(
        df_clean, 
        feature_cols, 
        target_col, 
        group_col
    )
    
    logger.info(f"Aggregated R2: {aggregated['r2_mean']:.4f} (+/- {aggregated['r2_std']:.4f})")
    logger.info(f"Aggregated RMSE: {aggregated['rmse_mean']:.4f} (+/- {aggregated['rmse_std']:.4f})")
    
    # Calculate confidence intervals
    df_with_ci = calculate_confidence_intervals(df_clean, feature_cols, target_col)
    
    # Prepare config snapshot
    config_snapshot = get_config_summary()
    config_snapshot['training_info'] = {
        'n_samples': len(df_clean),
        'n_features': len(feature_cols),
        'features': feature_cols,
        'cv_folds': aggregated['n_folds']
    }
    
    # Save results
    save_results(aggregated, fold_metrics, df_with_ci, config_snapshot)
    
    logger.info("Training complete. Results saved.")

if __name__ == '__main__':
    main()