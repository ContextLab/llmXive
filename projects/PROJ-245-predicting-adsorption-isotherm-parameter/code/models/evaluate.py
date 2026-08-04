"""
Model evaluation module for Adsorption Isotherm Parameter Prediction.
Implements metrics calculation, bootstrapping for confidence intervals,
and model comparison logic.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import cross_val_predict
from sklearn.linear_model import LinearRegression
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure required output directories exist."""
    dirs = [
        Path("data/results"),
        Path("data/validation"),
        Path("trained_models")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def load_test_data(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load preprocessed test data.
    Returns:
        Tuple of (features_df, target_series)
    """
    try:
        # Look for the processed dataset
        processed_path = data_dir / "processed_dataset.csv"
        if not processed_path.exists():
            # Fallback to common locations
            processed_path = Path("data/processed/processed_dataset.csv")
        
        if not processed_path.exists():
            raise FileNotFoundError(f"Processed dataset not found at {processed_path}")

        df = pd.read_csv(processed_path)
        
        # Identify feature columns (exclude metadata and targets)
        exclude_cols = ['material_id', 'adsorbent_structure_id', 'adsorbate_smiles', 
                      'langmuir_capacity', 'henry_constant', 'pore_volume']
        
        # Determine target column based on context or default
        target_col = 'langmuir_capacity' if 'langmuir_capacity' in df.columns else None
        if target_col is None:
            # Try to find any target column
            target_cols = [c for c in df.columns if c in ['langmuir_capacity', 'henry_constant']]
            if target_cols:
                target_col = target_cols[0]
            else:
                raise ValueError("No target column found in dataset")

        features = df.drop(columns=[c for c in exclude_cols if c in df.columns])
        # Ensure only numeric columns are kept for features
        features = features.select_dtypes(include=[np.number])
        
        target = df[target_col]
        
        return features, target
    except Exception as e:
        logger.error(f"Failed to load test data: {e}")
        raise

def load_models(models_dir: Path = Path("trained_models")) -> Dict[str, Any]:
    """Load trained models from disk."""
    models = {}
    model_files = {
        'linear': 'linear_model.pkl',
        'rf': 'rf_model.pkl',
        'gb': 'gb_model.pkl'
    }
    
    for name, filename in model_files.items():
        path = models_dir / filename
        if path.exists():
            try:
                models[name] = joblib.load(path)
                logger.info(f"Loaded model: {name}")
            except Exception as e:
                logger.warning(f"Failed to load {name} model: {e}")
        else:
            logger.warning(f"Model file not found: {path}")
    
    return models

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate standard regression metrics.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        Dictionary with R2, RMSE, MAE
    """
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    
    return {
        'r2': float(r2),
        'rmse': float(rmse),
        'mae': float(mae)
    }

def bootstrap_confidence_intervals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None,
    metrics: Optional[List[str]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Calculate 95% confidence intervals for R2, RMSE, and MAE using bootstrapping.
    
    This function resamples the (y_true, y_pred) pairs with replacement to create
    bootstrap samples, calculates metrics for each sample, and then determines
    the 2.5th and 97.5th percentiles to form the 95% confidence interval.
    
    Args:
        y_true: Array of true values (n_samples,)
        y_pred: Array of predicted values (n_samples,)
        n_bootstrap: Number of bootstrap resamples (default: 1000)
        random_state: Random seed for reproducibility
        metrics: List of metrics to calculate. If None, calculates all supported.
                
    Returns:
        Dictionary mapping metric name to {'ci_lower': float, 'ci_upper': float, 'point_estimate': float}
        
    Raises:
        ValueError: If input arrays have different lengths or are empty
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    if len(y_true) != len(y_pred):
        raise ValueError(f"y_true and y_pred must have same length. Got {len(y_true)} and {len(y_pred)}")
    
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")
        
    if metrics is None:
        metrics = ['r2', 'rmse', 'mae']
        
    # Store metric values for each bootstrap sample
    bootstrap_results = {metric: [] for metric in metrics}
    
    n_samples = len(y_true)
    
    logger.info(f"Performing bootstrapping with {n_bootstrap} resamples...")
    
    for i in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]
        
        # Calculate metrics for this bootstrap sample
        if 'r2' in metrics:
            try:
                r2 = r2_score(y_true_boot, y_pred_boot)
                bootstrap_results['r2'].append(r2)
            except Exception as e:
                logger.warning(f"R2 calculation failed for bootstrap sample {i}: {e}")
                bootstrap_results['r2'].append(np.nan)
                
        if 'rmse' in metrics:
            rmse = np.sqrt(mean_squared_error(y_true_boot, y_pred_boot))
            bootstrap_results['rmse'].append(rmse)
            
        if 'mae' in metrics:
            mae = mean_absolute_error(y_true_boot, y_pred_boot)
            bootstrap_results['mae'].append(mae)
            
    # Calculate confidence intervals and point estimates
    final_results = {}
    for metric in metrics:
        values = np.array(bootstrap_results[metric])
        # Remove NaN values
        valid_values = values[~np.isnan(values)]
        
        if len(valid_values) == 0:
            logger.warning(f"No valid {metric} values for confidence interval calculation")
            final_results[metric] = {
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'point_estimate': np.nan
            }
            continue
            
        # Point estimate from original data
        if metric == 'r2':
            point_est = r2_score(y_true, y_pred)
        elif metric == 'rmse':
            point_est = np.sqrt(mean_squared_error(y_true, y_pred))
        elif metric == 'mae':
            point_est = mean_absolute_error(y_true, y_pred)
        else:
            point_est = np.nan
            
        # 95% CI (2.5th and 97.5th percentiles)
        ci_lower = np.percentile(valid_values, 2.5)
        ci_upper = np.percentile(valid_values, 97.5)
        
        final_results[metric] = {
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'point_estimate': float(point_est)
        }
        
    logger.info("Bootstrapping completed successfully")
    return final_results

def evaluate_single_model(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Evaluate a single model and calculate confidence intervals.
    
    Args:
        model: Trained sklearn model
        X: Feature matrix
        y: Target vector
        n_bootstrap: Number of bootstrap samples
        random_state: Random seed
        
    Returns:
        Dictionary with metrics and confidence intervals
    """
    # Get predictions
    y_pred = model.predict(X)
    
    # Calculate point estimates
    metrics = calculate_metrics(y, y_pred)
    
    # Calculate confidence intervals
    ci_results = bootstrap_confidence_intervals(
        y, y_pred, 
        n_bootstrap=n_bootstrap, 
        random_state=random_state
    )
    
    # Combine results
    result = {
        'metrics': metrics,
        'confidence_intervals': ci_results
    }
    
    return result

def evaluate_models(
    models: Dict[str, Any],
    X: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluate multiple models with bootstrapping.
    
    Args:
        models: Dictionary of model name -> model object
        X: Feature matrix
        y: Target vector
        n_bootstrap: Number of bootstrap samples
        random_state: Random seed
        
    Returns:
        Dictionary mapping model name to evaluation results
    """
    results = {}
    for name, model in models.items():
        logger.info(f"Evaluating model: {name}")
        results[name] = evaluate_single_model(
            model, X, y, 
            n_bootstrap=n_bootstrap, 
            random_state=random_state
        )
    return results

def save_evaluation_results(results: Dict[str, Any], output_path: Path):
    """Save evaluation results to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Evaluation results saved to {output_path}")

def prepare_features_and_target(df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare feature matrix and target vector from dataframe."""
    # Exclude non-numeric columns and metadata
    exclude_cols = ['material_id', 'adsorbent_structure_id', 'adsorbate_smiles']
    feature_cols = [c for c in df.columns if c not in exclude_cols and c != target_col]
    
    # Filter to numeric only
    feature_cols = [c for c in feature_cols if df[c].dtype in [np.float64, np.int64, np.float32, np.int32]]
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    return X, y

def run_evaluation_pipeline(
    data_dir: Path = Path("data"),
    models_dir: Path = Path("trained_models"),
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline.
    
    Args:
        data_dir: Directory containing processed data
        models_dir: Directory containing trained models
        n_bootstrap: Number of bootstrap samples
        random_state: Random seed
        
    Returns:
        Evaluation results dictionary
    """
    ensure_dirs()
    
    # Load data
    logger.info("Loading test data...")
    try:
        features, target = load_test_data(data_dir)
        X, y = prepare_features_and_target(features, target.name if hasattr(target, 'name') else 'langmuir_capacity')
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        # If data loading fails, return empty results but don't crash
        return {'error': str(e), 'status': 'data_load_failed'}
    
    # Load models
    logger.info("Loading models...")
    models = load_models(models_dir)
    
    if not models:
        logger.warning("No models found to evaluate")
        return {'error': 'No models loaded', 'status': 'no_models'}
    
    # Evaluate
    logger.info("Evaluating models with bootstrapping...")
    results = evaluate_models(models, X, y, n_bootstrap=n_bootstrap, random_state=random_state)
    
    # Save results
    output_path = Path("data/results/evaluation_metrics.json")
    save_evaluation_results(results, output_path)
    
    return results

def main():
    """Main entry point for evaluation script."""
    logger.info("Starting model evaluation with bootstrapping...")
    
    # Parse arguments if needed, otherwise use defaults
    import argparse
    parser = argparse.ArgumentParser(description='Evaluate models with confidence intervals')
    parser.add_argument('--data-dir', type=str, default='data', help='Directory containing processed data')
    parser.add_argument('--models-dir', type=str, default='trained_models', help='Directory containing models')
    parser.add_argument('--n-bootstrap', type=int, default=1000, help='Number of bootstrap samples')
    parser.add_argument('--random-state', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    results = run_evaluation_pipeline(
        data_dir=Path(args.data_dir),
        models_dir=Path(args.models_dir),
        n_bootstrap=args.n_bootstrap,
        random_state=args.random_state
    )
    
    logger.info(f"Evaluation completed. Results: {json.dumps(results, indent=2)}")
    return results

if __name__ == "__main__":
    main()