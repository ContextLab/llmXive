import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error
from scipy import stats

# Import from local project modules
from config import CONFIG
from utils.logging import get_logger, log_provenance_event
from modeling.features import prepare_modeling_features

logger = get_logger(__name__)

def train_random_forest_cv(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    n_splits: int = 5,
    random_state: int = 42,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    min_samples_split: int = 2,
    min_samples_leaf: int = 1
) -> Dict[str, Any]:
    """
    Train a Random Forest regressor using k-fold cross-validation.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        feature_names: List of feature names corresponding to columns in X
        n_splits: Number of CV folds
        random_state: Random seed for reproducibility
        n_estimators: Number of trees in the forest
        max_depth: Maximum tree depth (None for unlimited)
        min_samples_split: Minimum samples required to split a node
        min_samples_leaf: Minimum samples required at a leaf node
        
    Returns:
        Dictionary containing:
            - 'predictions': CV predictions for each sample
            - 'r2': R² score
            - 'mae': Mean Absolute Error
            - 'fold_r2': R² score for each fold
            - 'fold_mae': MAE for each fold
            - 'feature_importance': Mean importance across trees
            - 'model': Trained RandomForestRegressor (fitted on full data)
    """
    logger.info(f"Training Random Forest with {n_estimators} estimators, {n_splits}-fold CV")
    logger.info(f"Feature matrix shape: {X.shape}")
    
    # Initialize KFold
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    # Initialize model
    rf_model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1,
        verbose=0
    )
    
    # Perform cross-validation to get predictions for each sample
    cv_predictions = cross_val_predict(rf_model, X, y, cv=kfold)
    
    # Calculate metrics
    r2 = r2_score(y, cv_predictions)
    mae = mean_absolute_error(y, cv_predictions)
    
    # Calculate per-fold metrics
    fold_r2 = []
    fold_mae = []
    for fold_idx, (train_idx, test_idx) in enumerate(kfold.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        fold_model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state + fold_idx,
            n_jobs=-1
        )
        fold_model.fit(X_train, y_train)
        y_pred = fold_model.predict(X_test)
        
        fold_r2.append(r2_score(y_test, y_pred))
        fold_mae.append(mean_absolute_error(y_test, y_pred))
        logger.debug(f"Fold {fold_idx + 1}: R²={fold_r2[-1]:.4f}, MAE={fold_mae[-1]:.4f}")
    
    # Train final model on full dataset for feature importance and saving
    rf_model.fit(X, y)
    
    # Get feature importance
    feature_importance = dict(zip(feature_names, rf_model.feature_importances_.tolist()))
    
    # Sort by importance
    sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
    
    result = {
        'predictions': cv_predictions.tolist(),
        'r2': r2,
        'mae': mae,
        'fold_r2': fold_r2,
        'fold_mae': fold_mae,
        'feature_importance': sorted_importance,
        'model': rf_model,
        'n_estimators': n_estimators,
        'n_splits': n_splits,
        'n_samples': len(y),
        'n_features': X.shape[1]
    }
    
    logger.info(f"CV Results: R²={r2:.4f}, MAE={mae:.4f}")
    logger.info(f"Top 5 features: {list(sorted_importance.keys())[:5]}")
    
    return result

def run_training_pipeline(
    input_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    model_type: str = "dft_enhanced",
    n_estimators: int = 100,
    n_splits: int = 5
) -> Dict[str, Any]:
    """
    Run the full training pipeline for the specified model type.
    
    Args:
        input_path: Path to the merged dataset (default: CONFIG.MERGED_DATA_PATH)
        output_dir: Directory to save results (default: CONFIG.RESULTS_DIR)
        model_type: Either "composition_only" or "dft_enhanced"
        n_estimators: Number of trees for Random Forest
        n_splits: Number of CV folds
        
    Returns:
        Dictionary containing training results and model artifact
    """
    if input_path is None:
        input_path = CONFIG.MERGED_DATA_PATH
    if output_dir is None:
        output_dir = CONFIG.RESULTS_DIR
        
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")
    
    # Prepare features based on model type
    logger.info(f"Preparing features for model type: {model_type}")
    X, y, feature_names = prepare_modeling_features(df, model_type=model_type)
    
    if len(X) == 0:
        raise ValueError("No valid samples after feature preparation")
    
    # Train model
    results = train_random_forest_cv(
        X=X,
        y=y,
        feature_names=feature_names,
        n_splits=n_splits,
        random_state=CONFIG.SEED,
        n_estimators=n_estimators
    )
    
    # Extract model and metrics
    model = results.pop('model')
    predictions = np.array(results.pop('predictions'))
    
    # Save model artifact
    model_path = output_dir / f"rf_model_{model_type}.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")
    
    # Save predictions
    predictions_path = output_dir / f"predictions_{model_type}.csv"
    pred_df = pd.DataFrame({
        'actual': y,
        'predicted': predictions
    })
    pred_df.to_csv(predictions_path, index=False)
    logger.info(f"Predictions saved to {predictions_path}")
    
    # Save feature importance details
    importance_path = output_dir / f"feature_importance_{model_type}.json"
    with open(importance_path, 'w') as f:
        json.dump(results['feature_importance'], f, indent=2)
    logger.info(f"Feature importance saved to {importance_path}")
    
    # Log provenance
    log_provenance_event(
        event_type="model_training",
        model_type=model_type,
        metrics={
            "r2": results['r2'],
            "mae": results['mae'],
            "n_samples": results['n_samples'],
            "n_features": results['n_features']
        },
        artifacts=[str(model_path), str(predictions_path)]
    )
    
    return {
        'metrics': {
            'r2': results['r2'],
            'mae': results['mae'],
            'fold_r2': results['fold_r2'],
            'fold_mae': results['fold_mae']
        },
        'feature_importance': results['feature_importance'],
        'model_path': str(model_path),
        'predictions_path': str(predictions_path),
        'model_type': model_type
    }

def main():
    """Main entry point for training script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Random Forest models for yield strength prediction")
    parser.add_argument(
        '--model-type', 
        choices=['composition_only', 'dft_enhanced'], 
        default='dft_enhanced',
        help='Model type to train (default: dft_enhanced)'
    )
    parser.add_argument(
        '--n-estimators', 
        type=int, 
        default=100,
        help='Number of trees in Random Forest (default: 100)'
    )
    parser.add_argument(
        '--n-splits', 
        type=int, 
        default=5,
        help='Number of CV folds (default: 5)'
    )
    parser.add_argument(
        '--input', 
        type=str, 
        default=None,
        help='Path to input merged dataset (default: from config)'
    )
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default=None,
        help='Output directory for results (default: from config)'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else None
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    try:
        results = run_training_pipeline(
            input_path=input_path,
            output_dir=output_dir,
            model_type=args.model_type,
            n_estimators=args.n_estimators,
            n_splits=args.n_splits
        )
        
        print(json.dumps(results['metrics'], indent=2))
        logger.info(f"Training completed successfully for {args.model_type}")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()