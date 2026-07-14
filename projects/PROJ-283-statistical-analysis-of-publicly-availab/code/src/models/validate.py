"""
Cross-validation and model validation logic.
Implements k-fold cross-validation for Gaussian GLM and Ridge models.
Enforces SC-003 model stability threshold.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
import json

from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families

from src.config import ensure_directories
from src.models.fit import prepare_features_for_modeling, fit_ridge_regression

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SC-003 Threshold: If std_dev_r2 >= 0.05, model is unstable
SC003_THRESHOLD = 0.05

def perform_kfold_cross_validation(
    df: pd.DataFrame,
    model_type: str = 'ridge',
    n_folds: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation on the provided dataset.
    
    Args:
        df: DataFrame with features and target 'outcome_deviation'
        model_type: 'ridge' or 'glm'
        n_folds: Number of folds
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing R2 scores, MSE scores, and stability metrics
    """
    ensure_directories()
    
    # Prepare features using existing pipeline
    logger.info(f"Preparing features for {model_type} model...")
    try:
        X, y, feature_names = prepare_features_for_modeling(df)
    except Exception as e:
        logger.error(f"Feature preparation failed: {e}")
        raise
    
    if X.empty or y.empty:
        raise ValueError("Feature matrix or target vector is empty after preparation")
    
    # Initialize KFold
    kfold = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    r2_scores = []
    mse_scores = []
    fold_metrics = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kfold.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        fold_results = {
            'fold': fold_idx + 1,
            'train_size': len(X_train),
            'test_size': len(X_test)
        }
        
        if model_type == 'ridge':
            # Fit Ridge Regression
            model = Ridge(alpha=1.0)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            fold_results['coefficients'] = dict(zip(feature_names, model.coef_.tolist()))
            fold_results['intercept'] = float(model.intercept_)
            
        elif model_type == 'glm':
            # Fit Gaussian GLM
            # Add constant for GLM (statsmodels requires it)
            X_train_const = sm.add_constant(X_train)
            X_test_const = sm.add_constant(X_test)
            
            try:
                glm_model = GLM(y_train, X_train_const, family=families.Gaussian())
                glm_results = glm_model.fit()
                y_pred = glm_results.predict(X_test_const)
                
                fold_results['coefficients'] = dict(
                    zip(['const'] + feature_names, glm_results.params.tolist())
                )
                fold_results['aic'] = float(glm_results.aic)
                fold_results['bic'] = float(glm_results.bic)
            except Exception as e:
                logger.warning(f"GLM failed on fold {fold_idx + 1}: {e}")
                # If GLM fails, skip this fold or use fallback
                continue
        else:
            raise ValueError(f"Unknown model_type: {model_type}")
        
        # Calculate metrics
        r2 = r2_score(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        
        fold_results['r2'] = float(r2)
        fold_results['mse'] = float(mse)
        
        r2_scores.append(r2)
        mse_scores.append(mse)
        fold_metrics.append(fold_results)
        logger.info(f"Fold {fold_idx + 1}: R2={r2:.4f}, MSE={mse:.4f}")
    
    if not r2_scores:
        raise RuntimeError("No valid folds completed for cross-validation")
    
    # Calculate aggregate metrics
    mean_r2 = float(np.mean(r2_scores))
    std_r2 = float(np.std(r2_scores))
    mean_mse = float(np.mean(mse_scores))
    std_mse = float(np.std(mse_scores))
    
    # SC-003 Check: Model Stability
    if std_r2 >= SC003_THRESHOLD:
        raise RuntimeError(
            f"SC-003 Threshold Exceeded: Model instability detected. "
            f"Std Dev R2 ({std_r2:.4f}) >= Threshold ({SC003_THRESHOLD})"
        )
    
    return {
        'model_type': model_type,
        'n_folds': n_folds,
        'mean_r2': mean_r2,
        'std_r2': std_r2,
        'mean_mse': mean_mse,
        'std_mse': std_mse,
        'r2_scores': r2_scores,
        'mse_scores': mse_scores,
        'fold_details': fold_metrics,
        'sc003_passed': True
    }

def run_validation_pipeline(
    data_path: str,
    output_path: str,
    n_folds: int = 5
) -> Dict[str, Any]:
    """
    Run full validation pipeline: load data, run CV for both models, save results.
    
    Args:
        data_path: Path to processed games parquet file
        output_path: Path to save validation results JSON
        n_folds: Number of CV folds
        
    Returns:
        Combined validation results
    """
    ensure_directories()
    
    # Load data
    logger.info(f"Loading data from {data_path}...")
    df = pd.read_parquet(data_path)
    
    if 'outcome_deviation' not in df.columns:
        raise ValueError("Dataset must contain 'outcome_deviation' column")
    
    results = {}
    
    # Run Ridge CV
    logger.info("Running Ridge Regression Cross-Validation...")
    try:
        ridge_results = perform_kfold_cross_validation(
            df, model_type='ridge', n_folds=n_folds
        )
        results['ridge'] = ridge_results
        logger.info(f"Ridge CV complete: Mean R2={ridge_results['mean_r2']:.4f}")
    except RuntimeError as e:
        if "SC-003" in str(e):
            results['ridge'] = {'error': str(e), 'sc003_passed': False}
            logger.error(str(e))
        else:
            raise
    
    # Run GLM CV
    logger.info("Running Gaussian GLM Cross-Validation...")
    try:
        glm_results = perform_kfold_cross_validation(
            df, model_type='glm', n_folds=n_folds
        )
        results['glm'] = glm_results
        logger.info(f"GLM CV complete: Mean R2={glm_results['mean_r2']:.4f}")
    except RuntimeError as e:
        if "SC-003" in str(e):
            results['glm'] = {'error': str(e), 'sc003_passed': False}
            logger.error(str(e))
        else:
            raise
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Validation results saved to {output_path}")
    return results

def main():
    """Main entry point for validation script."""
    # Default paths from config conventions
    data_file = Path("data/processed/games.parquet")
    output_file = Path("data/results/validation_metrics.json")
    
    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        logger.info("Please run data ingestion pipeline first (T018).")
        return 1
    
    try:
        results = run_validation_pipeline(
            data_path=str(data_file),
            output_path=str(output_file),
            n_folds=5
        )
        logger.info("Validation pipeline completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
