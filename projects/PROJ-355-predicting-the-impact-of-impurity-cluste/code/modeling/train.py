"""
Linear Regression model training with k-fold cross-validation.

Implements manual k-fold CV using statsmodels OLS to extract p-values,
R², and RMSE. Handles collinearity warnings and saves metrics to disk.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.model_selection import GroupKFold, KFold
from sklearn.metrics import r2_score, mean_squared_error
from config import get_project_root, get_data_paths, save_config_snapshot
from validators import validate_schema

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load JSON schema from file."""
    import yaml
    with open(schema_path, 'r') as f:
        # Handle YAML schema files if needed, otherwise JSON
        if schema_path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        return json.load(f)

def validate_input_data(data_path: Path, schema_path: Path) -> bool:
    """Validate input data against schema before training."""
    if not data_path.exists():
        raise FileNotFoundError(f"Input data file not found: {data_path}")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Load data and schema
    df = pd.read_csv(data_path)
    schema = load_schema(schema_path)
    
    # Validate using the validate_schema function from validators module
    # We pass the dataframe as a dict of dicts for validation
    data_dict = df.to_dict(orient='records')
    if not validate_schema(data_dict, schema):
        logger.error("Input data failed schema validation")
        return False
    
    logger.info(f"Input data validated successfully: {len(df)} samples")
    return True

def check_collinearity_warning(collinearity_report_path: Path) -> bool:
    """Check if collinearity report exists and contains VIF >= 10 warning."""
    if not collinearity_report_path.exists():
        logger.warning("Collinearity report not found. Proceeding without check.")
        return False
    
    with open(collinearity_report_path, 'r') as f:
        content = f.read()
    
    if "VIF >= 10" in content or "collinearity detected" in content.lower():
        logger.warning("High collinearity detected (VIF >= 10). P-values may be unstable.")
        return True
    return False

def train_model(X_train: np.ndarray, y_train: np.ndarray, 
                feature_names: List[str]) -> Tuple[sm.RegressionResults, Dict[str, float]]:
    """
    Train a Linear Regression model using statsmodels OLS.
    
    Returns:
        results: Fitted OLS results object
        metrics: Dictionary with R², RMSE, and p-values
    """
    # Add constant for intercept
    X_train_const = sm.add_constant(X_train)
    
    # Fit model
    model = sm.OLS(y_train, X_train_const)
    results = model.fit()
    
    # Extract metrics
    y_pred = results.predict(X_train_const)
    r2 = r2_score(y_train, y_pred)
    rmse = np.sqrt(mean_squared_error(y_train, y_pred))
    
    # Extract p-values for features (excluding intercept)
    p_values = {}
    for i, name in enumerate(feature_names):
        p_values[name] = results.pvalues[i + 1]  # +1 to skip intercept
    
    return results, {
        'r2': r2,
        'rmse': rmse,
        'p_values': p_values
    }

def run_kfold_cv(X: np.ndarray, y: np.ndarray, 
                 groups: Optional[np.ndarray] = None,
                 feature_names: Optional[List[str]] = None,
                 n_splits: int = 5) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run k-fold cross-validation with manual loop.
    
    Logic:
    - IF N >= 5 THEN use 5-fold CV
    - ELSE use LOOCV (n_splits = len(y))
    
    Args:
        X: Feature matrix
        y: Target vector
        groups: Optional group labels for GroupKFold
        feature_names: List of feature names for p-value labeling
        n_splits: Number of folds (default 5)
        
    Returns:
        fold_metrics: List of metrics per fold
        aggregated: Aggregated metrics across folds
    """
    n_samples = len(y)
    
    # Determine CV strategy
    if n_samples < 5:
        logger.info(f"Dataset too small ({n_samples} samples). Using LOOCV.")
        n_splits = n_samples
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    elif groups is not None:
        logger.info("Using GroupKFold for cross-validation.")
        cv = GroupKFold(n_splits=min(n_splits, len(np.unique(groups))))
    else:
        logger.info(f"Using {n_splits}-fold cross-validation.")
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    
    fold_metrics = []
    all_predictions = []
    all_targets = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y, groups)):
        logger.info(f"Processing fold {fold_idx + 1}/{n_splits}")
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Train model
        results, fold_metrics_dict = train_model(X_train, y_train, feature_names)
        fold_metrics_dict['fold'] = fold_idx + 1
        
        # Calculate test metrics
        y_pred = results.predict(sm.add_constant(X_test))
        test_r2 = r2_score(y_test, y_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        fold_metrics_dict['test_r2'] = test_r2
        fold_metrics_dict['test_rmse'] = test_rmse
        
        fold_metrics.append(fold_metrics_dict)
        all_predictions.extend(y_pred)
        all_targets.extend(y_test)
    
    # Aggregate metrics
    avg_r2 = np.mean([m['test_r2'] for m in fold_metrics])
    avg_rmse = np.mean([m['test_rmse'] for m in fold_metrics])
    std_r2 = np.std([m['test_r2'] for m in fold_metrics])
    std_rmse = np.std([m['test_rmse'] for m in fold_metrics])
    
    # Aggregate p-values (average across folds)
    avg_p_values = {}
    for name in feature_names:
        p_vals = [m['p_values'][name] for m in fold_metrics]
        avg_p_values[name] = np.mean(p_vals)
    
    aggregated = {
        'avg_r2': avg_r2,
        'avg_rmse': avg_rmse,
        'std_r2': std_r2,
        'std_rmse': std_rmse,
        'avg_p_values': avg_p_values,
        'n_folds': n_splits,
        'cv_strategy': 'LOOCV' if n_samples < 5 else f'{n_splits}-fold CV'
    }
    
    return fold_metrics, aggregated

def calculate_confidence_intervals(X_test: np.ndarray, y_test: np.ndarray, 
                                   results: sm.RegressionResults) -> List[Dict[str, float]]:
    """
    Calculate confidence intervals for predictions using statsmodels.
    
    Returns:
        List of dicts with sample_id, predicted_energy, ci_lower, ci_upper
    """
    X_test_const = sm.add_constant(X_test)
    predictions = results.get_prediction(X_test_const)
    conf_int = predictions.conf_int()
    
    ci_results = []
    for i, (pred, (lower, upper)) in enumerate(zip(predictions.predicted_mean, conf_int)):
        ci_results.append({
            'sample_id': i,
            'predicted_energy': float(pred),
            'ci_lower': float(lower),
            'ci_upper': float(upper)
        })
    
    return ci_results

def save_results(fold_metrics: List[Dict[str, Any]], aggregated: Dict[str, Any],
                 confidence_intervals: List[Dict[str, float]],
                 output_dir: Path) -> Dict[str, str]:
    """
    Save all results to disk.
    
    Returns:
        Dict mapping output filenames to their paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save per-fold metrics
    fold_metrics_path = output_dir / 'metrics_per_fold.json'
    with open(fold_metrics_path, 'w') as f:
        json.dump(fold_metrics, f, indent=2)
    
    # Save aggregated metrics
    metrics_path = output_dir / 'metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(aggregated, f, indent=2)
    
    # Save confidence intervals
    ci_path = output_dir / 'confidence_intervals.json'
    with open(ci_path, 'w') as f:
        json.dump(confidence_intervals, f, indent=2)
    
    # Save config snapshot for provenance
    config_snapshot = save_config_snapshot(output_dir / 'config_snapshot.json')
    
    # Calculate and save code version hash
    code_files = ['code/modeling/train.py', 'code/data/descriptors.py', 'code/data/simulate_energy.py']
    code_content = ""
    for file_path in code_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                code_content += f.read()
    
    code_hash = hashlib.sha256(code_content.encode()).hexdigest()
    state_dir = output_dir.parent
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / 'project.yaml'
    
    # Read existing state or create new
    state_data = {}
    if state_file.exists():
        import yaml
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    state_data['code_version_hash'] = code_hash
    state_data['last_updated'] = str(pd.Timestamp.now())
    
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f)
    
    logger.info(f"Results saved to {output_dir}")
    return {
        'metrics_per_fold': str(fold_metrics_path),
        'metrics': str(metrics_path),
        'confidence_intervals': str(ci_path),
        'state': str(state_file)
    }

def main():
    """Main entry point for model training."""
    logger.info("Starting model training (T023)")
    
    # Get paths
    project_root = get_project_root()
    data_paths = get_data_paths()
    
    # Input data paths
    descriptors_path = data_paths['processed'] / 'descriptors.csv'
    energies_path = data_paths['processed'] / 'segregation_energies.csv'
    alloy_systems_path = data_paths['processed'] / 'alloy_systems.json'
    collinearity_report_path = data_paths['processed'] / 'collinearity_report.md'
    
    # Schema paths
    dataset_schema_path = project_root / 'contracts' / 'dataset.schema.yaml'
    
    # Output paths
    results_dir = project_root / 'results'
    
    # Validate input data
    if not validate_input_data(descriptors_path, dataset_schema_path):
        logger.error("Validation failed. Exiting.")
        return
    
    # Check for collinearity warning
    check_collinearity_warning(collinearity_report_path)
    
    # Load data
    logger.info("Loading descriptors and energies...")
    descriptors_df = pd.read_csv(descriptors_path)
    energies_df = pd.read_csv(energies_path)
    
    # Merge data
    # Assuming both have a common identifier or are aligned
    # For MVP, we assume they are aligned by index
    if 'alloy_system_id' in energies_df.columns:
        merged_df = pd.merge(descriptors_df, energies_df[['segregation_energy', 'alloy_system_id']], 
                             left_index=True, right_index=True)
    else:
        merged_df = pd.merge(descriptors_df, energies_df[['segregation_energy']], 
                             left_index=True, right_index=True)
    
    # Prepare features and target
    feature_cols = [col for col in merged_df.columns if col not in ['segregation_energy', 'alloy_system_id', 'bulk_config_id', 'impurity_species', 'alloy_system']]
    if not feature_cols:
        logger.error("No feature columns found in descriptors.")
        return
    
    X = merged_df[feature_cols].values
    y = merged_df['segregation_energy'].values
    groups = merged_df['alloy_system_id'].values if 'alloy_system_id' in merged_df.columns else None
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Target vector shape: {y.shape}")
    
    # Run k-fold CV
    fold_metrics, aggregated = run_kfold_cv(X, y, groups=groups, feature_names=feature_cols)
    
    # Calculate confidence intervals on full data for demonstration
    # In practice, this would be on a held-out test set
    X_const = sm.add_constant(X)
    full_model = sm.OLS(y, X_const).fit()
    confidence_intervals = calculate_confidence_intervals(X, y, full_model)
    
    # Save results
    output_paths = save_results(fold_metrics, aggregated, confidence_intervals, results_dir)
    
    logger.info(f"Training complete. R²: {aggregated['avg_r2']:.4f}, RMSE: {aggregated['avg_rmse']:.4f}")
    logger.info(f"Results saved to: {output_paths}")

if __name__ == "__main__":
    main()