import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel as C
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_squared_error
from utils.logger import get_logger, log_model_training_failure
from config import get_config_from_args

# Import the existing downsampling function to ensure consistency
from data.processor import downsample_dataset

logger = get_logger(__name__)


def _calculate_nested_cv_scores(
    model,
    X: np.ndarray,
    y: np.ndarray,
    outer_n_splits: int = 5,
    inner_n_splits: int = 2,
    scoring: str = 'neg_mean_squared_error'
) -> Tuple[float, float]:
    """
    Perform 5x2 Nested Cross-Validation.
    Returns mean and std of the inner CV scores.
    """
    outer_cv = KFold(n_splits=outer_n_splits, shuffle=True, random_state=42)
    outer_scores = []

    for train_idx, test_idx in outer_cv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        inner_cv = KFold(n_splits=inner_n_splits, shuffle=True, random_state=42)
        inner_scores = cross_val_score(model, X_train, y_train, cv=inner_cv, scoring=scoring)

        outer_scores.append(-np.mean(inner_scores)) # Convert back to positive RMSE

    mean_score = np.mean(outer_scores)
    std_score = np.std(outer_scores)
    return mean_score, std_score


def train_models(
    data_path: str,
    output_dir: str,
    mode: str = 'local'
) -> Dict[str, Any]:
    """
    Train Random Forest, Gradient Boosting, and Gaussian Process models.
    Implements 5x2 Nested Cross-Validation for model evaluation.
    
    Args:
        data_path: Path to the processed CSV file.
        output_dir: Directory to save model artifacts.
        mode: 'ci' or 'local' to determine downsampling limits.
        
    Returns:
        Dictionary containing model instances, scores, and metadata.
    """
    logger.info(f"Starting model training from {data_path} in {mode} mode")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
        
    df = pd.read_csv(data_path)
    
    # Apply downsampling if necessary (T017 logic)
    if mode == 'ci' and len(df) > 500:
        logger.info("CI mode: Downsampling dataset to 500 rows")
        df = downsample_dataset(df, max_rows=500)
    elif mode == 'local' and len(df) > 1000:
        logger.info("Local mode: Downsampling dataset to 1000 rows")
        df = downsample_dataset(df, max_rows=1000)
    
    # Identify feature columns and target
    # Assuming the processed data has specific columns. 
    # We filter out non-numeric columns and the target 'observed_weight_gain'
    target_col = 'observed_weight_gain'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data. Columns: {df.columns.tolist()}")
        
    feature_cols = [col for col in df.columns if col != target_col and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not feature_cols:
        raise ValueError("No valid feature columns found for training.")
        
    logger.info(f"Training on {len(feature_cols)} features: {feature_cols}")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Handle NaNs if any (though processor should have cleaned)
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X = X[mask]
    y = y[mask]
    
    if len(X) < 10:
        raise ValueError(f"Insufficient data points ({len(X)}) after cleaning for model training.")
    
    results = {
        'models': {},
        'scores': {},
        'feature_names': feature_cols
    }
    
    # Define Models
    # 1. Random Forest
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=-1
    )
    
    # 2. Gradient Boosting
    gb_model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=5,
        random_state=42,
        learning_rate=0.1
    )
    
    # 3. Gaussian Process (T036 Implementation)
    # Kernel: Constant * (RBF + White)
    # Optimized for regression with uncertainty estimation
    kernel_gp = C(1.0, (1e-3, 1e3)) * RBF(10.0, (1e-2, 1e2)) + WhiteKernel(1e-1, (1e-5, 1e2))
    gp_model = GaussianProcessRegressor(
        kernel=kernel_gp,
        n_restarts_optimizer=10,
        normalize_y=True,
        random_state=42,
        alpha=1e-10 # Numerical stability
    )
    
    models_to_train = [
        ('RandomForest', rf_model),
        ('GradientBoosting', gb_model),
        ('GaussianProcess', gp_model)
    ]
    
    for name, model in models_to_train:
        try:
            logger.info(f"Training {name} model with Nested CV...")
            
            # Perform 5x2 Nested CV
            mean_rmse, std_rmse = _calculate_nested_cv_scores(model, X, y)
            
            # Fit final model on full data for later prediction
            model.fit(X, y)
            
            results['models'][name] = model
            results['scores'][name] = {
                'rmse': mean_rmse,
                'rmse_std': std_rmse
            }
            
            logger.info(f"{name} model trained. Nested CV RMSE: {mean_rmse:.4f} (+/- {std_rmse:.4f})")
            
            # Save model artifacts if it's the GP model specifically (or all)
            # For now, we save the full results dict at the end
            
        except Exception as e:
            log_model_training_failure(name, str(e))
            logger.error(f"Failed to train {name} model: {e}")
            # Continue training other models
            continue
    
    # Save results summary
    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, 'training_results.json')
    
    # Convert numpy types to native python types for JSON serialization
    serializable_scores = {}
    for name, score_data in results['scores'].items():
        serializable_scores[name] = {
            'rmse': float(score_data['rmse']),
            'rmse_std': float(score_data['rmse_std'])
        }
        
    import json
    summary_data = {
        'feature_names': results['feature_names'],
        'scores': serializable_scores,
        'model_count': len(results['models'])
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
        
    logger.info(f"Training summary saved to {summary_path}")
    
    return results


def main():
    """CLI entry point for model training."""
    args = parse_args()
    config = get_config_from_args(args)
    
    # Ensure output directory exists
    os.makedirs(config['output_dir'], exist_ok=True)
    
    # Determine data path based on mode (assuming processed data is in data/processed)
    # This assumes T013 has already run and produced the file
    # If the file doesn't exist, the function will raise an error as per "fail loudly"
    data_file = os.path.join(config['data_dir'], 'processed', 'alloy_data_processed.csv')
    
    if not os.path.exists(data_file):
        # Check for alternative names or raise specific error
        logger.error(f"Processed data file not found: {data_file}")
        # In a real pipeline, this might trigger a re-run of T013, 
        # but here we fail loudly as per constraints
        raise FileNotFoundError(f"Expected processed data at {data_file}")
        
    results = train_models(
        data_path=data_file,
        output_dir=config['output_dir'],
        mode=config['mode']
    )
    
    logger.info("Model training complete.")
    return 0


if __name__ == "__main__":
    # Ensure config is available for main
    from config import parse_args, get_config_from_args
    sys.exit(main())