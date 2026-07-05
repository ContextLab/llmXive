"""
Model training module for Perovskite Stability Prediction.

This module implements the training pipeline including:
- Data loading and splitting
- Hyperparameter tuning with GridSearchCV
- Model evaluation
- Metadata management (including DFT functional verification)
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_pipeline_event, log_exclusion_reason
from utils.model_metadata import save_model_metadata, embed_metadata_in_model

logger = get_logger(__name__)

# Constants
RESULTS_DIR = "results"
MODEL_FILENAME = "model.pkl"
METRICS_FILENAME = "metrics.json"
METADATA_FILENAME = "model_metadata.json"
DFT_FUNCTIONAL = "PBE"

def load_data(features_path: str) -> pd.DataFrame:
    """
    Load preprocessed features from CSV.

    Args:
        features_path: Path to the features CSV file.

    Returns:
        DataFrame containing features and target.
    """
    logger.info(f"Loading data from {features_path}")
    df = pd.read_csv(features_path)
    logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns")
    return df

def inner_loop_cv_selection(
    X: pd.DataFrame,
    y: pd.Series,
    param_grid: Dict[str, List],
    cv_folds: int = 5
) -> Dict[str, Any]:
    """
    Perform inner-loop cross-validation to select best hyperparameters.

    Args:
        X: Feature matrix.
        y: Target variable.
        param_grid: Grid of hyperparameters to search.
        cv_folds: Number of CV folds.

    Returns:
        Dictionary containing best parameters and CV results.
    """
    logger.info("Starting inner-loop CV for hyperparameter selection...")
    
    model = RandomForestRegressor(random_state=42)
    
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        cv=cv_folds,
        scoring='neg_mean_squared_error',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X, y)
    
    best_params = grid_search.best_params_
    best_cv_score = -grid_search.best_score_  # Convert back to positive MSE
    
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best CV MSE: {best_cv_score:.4f}")
    
    return {
        "best_params": best_params,
        "best_cv_score": best_cv_score,
        "cv_results": grid_search.cv_results_
    }

def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    best_params: Dict[str, Any]
) -> RandomForestRegressor:
    """
    Train the final model with selected hyperparameters.

    Args:
        X_train: Training features.
        y_train: Training target.
        best_params: Best hyperparameters from CV.

    Returns:
        Trained RandomForest model.
    """
    logger.info("Training final model with best parameters...")
    
    model = RandomForestRegressor(**best_params, random_state=42)
    model.fit(X_train, y_train)
    
    logger.info(f"Model trained with {model.n_estimators} trees")
    return model

def evaluate_model(
    model: RandomForestRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, float]:
    """
    Evaluate model performance on test set.

    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test target.

    Returns:
        Dictionary of evaluation metrics.
    """
    logger.info("Evaluating model on test set...")
    
    y_pred = model.predict(X_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mae = np.mean(np.abs(y_test - y_pred))
    
    metrics = {
        "test_rmse": float(rmse),
        "test_r2": float(r2),
        "test_mae": float(mae),
        "test_samples": int(len(y_test))
    }
    
    logger.info(f"Test RMSE: {rmse:.4f} eV/atom")
    logger.info(f"Test R2: {r2:.4f}")
    logger.info(f"Test MAE: {mae:.4f} eV/atom")
    
    # Check for low confidence flag
    if rmse > 0.15:
        logger.warning(f"Low confidence flag: Test RMSE ({rmse:.4f}) > 0.15 eV/atom threshold")
        metrics["low_confidence"] = True
    else:
        metrics["low_confidence"] = False
    
    return metrics

def run_permutation_sensitivity_analysis(
    model: RandomForestRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    n_repeats: int = 10
) -> Dict[str, float]:
    """
    Run permutation-based sensitivity analysis.

    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test target.
        n_repeats: Number of repeats for permutation.

    Returns:
        Dictionary of feature importance scores.
    """
    logger.info("Running permutation sensitivity analysis...")
    
    try:
        from sklearn.inspection import permutation_importance
        
        result = permutation_importance(
            model, X_test, y_test,
            n_repeats=n_repeats,
            random_state=42,
            n_jobs=-1
        )
        
        importance_scores = {}
        for i, feature in enumerate(X_test.columns):
            importance_scores[feature] = float(result.importances_mean[i])
        
        logger.info("Permutation importance calculated")
        return importance_scores
        
    except ImportError:
        logger.warning("sklearn.inspection not available, skipping permutation analysis")
        return {}

def save_artifacts(
    model: RandomForestRegressor,
    metrics: Dict[str, float],
    feature_columns: List[str],
    best_params: Dict[str, Any],
    training_stats: Dict[str, Any],
    output_dir: str
) -> None:
    """
    Save model, metrics, and metadata to disk.

    Args:
        model: Trained model.
        metrics: Evaluation metrics.
        feature_columns: List of feature names.
        best_params: Best hyperparameters.
        training_stats: Training statistics.
        output_dir: Directory to save artifacts.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = output_path / MODEL_FILENAME
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Saved model to {model_path}")
    
    # Save metrics
    metrics_path = output_path / METRICS_FILENAME
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")
    
    # Save metadata with explicit DFT functional
    metadata_path = save_model_metadata(
        output_dir=output_dir,
        dft_functional=DFT_FUNCTIONAL,
        model_type="RandomForestRegressor",
        feature_columns=feature_columns,
        hyperparameters=best_params,
        training_stats=training_stats
    )
    logger.info(f"Saved metadata to {metadata_path}")
    
    # Also embed metadata in the model for redundancy
    embed_metadata_in_model(
        str(model_path),
        {
            "dft_functional": DFT_FUNCTIONAL,
            "model_type": "RandomForestRegressor",
            "feature_columns": feature_columns
        }
    )
    logger.info("Embedded metadata in model file")

def main():
    """
    Main entry point for model training.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Train Perovskite Stability Model")
    parser.add_argument(
        "--features-path",
        type=str,
        default="data/processed/features.csv",
        help="Path to features CSV (default: data/processed/features.csv)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Output directory for model artifacts (default: results)"
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test set size (default: 0.2)"
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help="Number of CV folds (default: 5)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    log_pipeline_event("Starting model training pipeline", level="INFO")

    try:
        # Load data
        df = load_data(args.features_path)
        
        # Prepare features and target
        feature_columns = [col for col in df.columns if col != 'decomposition_energy']
        X = df[feature_columns]
        y = df['decomposition_energy']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=42
        )
        
        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # Define parameter grid
        param_grid = {
            'max_depth': [10, 15, 20],
            'min_samples_leaf': [1, 2, 4]
        }
        
        # Inner loop CV
        cv_results = inner_loop_cv_selection(X_train, y_train, param_grid, args.cv_folds)
        best_params = cv_results['best_params']
        
        # Train final model
        model = train_model(X_train, y_train, best_params)
        
        # Evaluate
        metrics = evaluate_model(model, X_test, y_test)
        
        # Permutation analysis
        perm_importance = run_permutation_sensitivity_analysis(model, X_test, y_test)
        
        # Prepare training stats
        training_stats = {
            "train_size": int(len(X_train)),
            "test_size": int(len(X_test)),
            "feature_count": len(feature_columns),
            "cv_folds": args.cv_folds,
            "best_cv_score": float(cv_results['best_cv_score']),
            "perm_importance": perm_importance
        }
        
        # Save artifacts
        save_artifacts(
            model=model,
            metrics=metrics,
            feature_columns=feature_columns,
            best_params=best_params,
            training_stats=training_stats,
            output_dir=args.output_dir
        )
        
        log_pipeline_event("Model training completed successfully", level="INFO")
        logger.info("Training pipeline completed")
        
        return 0

    except Exception as e:
        logger.exception(f"Training pipeline failed: {e}")
        log_pipeline_event(f"Training pipeline failed: {e}", level="ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())
