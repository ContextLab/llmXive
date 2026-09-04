import os
import sys
import logging
import json
import pickle
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut, cross_validate
from sklearn.metrics import r2_score, mean_absolute_error
from scipy.stats import pearsonr, spearmanr

from config.config import get_config
from resource_monitor import enforce_resource_limits, ResourceLimitExceeded
from descriptors import process_dataframe, calculate_weighted_mean_radius
from analyze import load_descriptors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_prepared_data() -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Load the processed descriptors and target variable.
    
    Returns:
        Tuple containing:
            - DataFrame with features and target
            - List of feature columns
            - List of family columns (for grouping)
    """
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "descriptors.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Desired data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Identify target and grouping columns
    target_col = 'Tg'
    family_col = 'family'
    
    # Features are all numeric columns except target and family
    feature_cols = [col for col in df.columns if col not in [target_col, family_col]]
    
    return df, feature_cols, [family_col]

def get_family_groups(df: pd.DataFrame, family_col: str) -> List[Any]:
    """
    Extract family groups for LOFO cross-validation.
    
    Args:
        df: DataFrame containing the family column
        family_col: Name of the column containing family labels
        
    Returns:
        List of family group identifiers corresponding to each row
    """
    return df[family_col].tolist()

def lofo_cv_score(
    df: pd.DataFrame,
    feature_cols: List[str],
    family_col: str,
    groups: List[Any],
    max_depth: int = 5,
    n_estimators: int = 100
) -> Dict[str, Any]:
    """
    Perform Leave-One-Family-Out cross-validation.
    
    Handles the edge case where a specific family results in an empty test set
    by logging a warning and skipping that fold.
    
    Args:
        df: DataFrame with features and target
        feature_cols: List of feature column names
        family_col: Name of the family column
        groups: List of family group identifiers
        max_depth: Max depth for GradientBoostingRegressor
        n_estimators: Number of estimators
        
    Returns:
        Dictionary containing R2 scores, MAE scores, and fold details
    """
    logo = LeaveOneGroupOut()
    r2_scores = []
    mae_scores = []
    fold_details = []
    
    X = df[feature_cols].values
    y = df['Tg'].values
    
    logger.info(f"Starting LOFO CV with {len(np.unique(groups))} unique families")
    
    for train_index, test_index in logo.split(X, y, groups):
        # Check for empty test set (Edge Case: LOFO_EMPTY_SPLIT)
        if len(test_index) == 0:
            logger.warning("LOFO_EMPTY_SPLIT: Test set is empty for this family fold. Skipping.")
            continue
        
        # Check for empty train set (safety)
        if len(train_index) == 0:
            logger.warning("LOFO_EMPTY_SPLIT: Train set is empty for this family fold. Skipping.")
            continue
        
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
        # Identify the family being left out
        test_family = groups[test_index[0]]
        
        # Train model
        model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=get_config().get('seed', 42)
        )
        
        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            r2_scores.append(r2)
            mae_scores.append(mae)
            
            fold_details.append({
                'fold_family': test_family,
                'train_size': len(train_index),
                'test_size': len(test_index),
                'r2': r2,
                'mae': mae
            })
            
            logger.info(f"Fold (Family: {test_family}): R²={r2:.4f}, MAE={mae:.4f}")
            
        except Exception as e:
            logger.error(f"Error in fold for family {test_family}: {str(e)}")
            continue
    
    if not r2_scores:
        logger.error("No valid folds completed. Check data distribution.")
        raise RuntimeError("LOFO CV failed: No valid splits produced results.")
    
    return {
        'r2_scores': r2_scores,
        'mae_scores': mae_scores,
        'mean_r2': float(np.mean(r2_scores)),
        'std_r2': float(np.std(r2_scores)),
        'mean_mae': float(np.mean(mae_scores)),
        'fold_details': fold_details,
        'total_folds': len(fold_details)
    }

def train_and_evaluate(
    df: pd.DataFrame,
    feature_cols: List[str],
    groups: List[Any],
    max_depth: int = 5,
    n_estimators: int = 100
) -> Tuple[GradientBoostingRegressor, Dict[str, Any]]:
    """
    Train the final model on the full dataset and evaluate via LOFO.
    
    Args:
        df: DataFrame with features and target
        feature_cols: List of feature column names
        groups: List of family group identifiers
        max_depth: Max depth for GradientBoostingRegressor
        n_estimators: Number of estimators
        
    Returns:
        Tuple of (trained model, evaluation metrics dict)
    """
    X = df[feature_cols].values
    y = df['Tg'].values
    
    # Perform LOFO CV
    cv_results = lofo_cv_score(df, feature_cols, 'family', groups, max_depth, n_estimators)
    
    # Train final model on full data
    logger.info("Training final model on full dataset...")
    final_model = GradientBoostingRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=get_config().get('seed', 42)
    )
    final_model.fit(X, y)
    
    # Calculate full data metrics (for reference, not CV)
    y_pred_full = final_model.predict(X)
    full_r2 = r2_score(y, y_pred_full)
    full_mae = mean_absolute_error(y, y_pred_full)
    
    metrics = {
        'cv_results': cv_results,
        'final_model_r2': float(full_r2),
        'final_model_mae': float(full_mae),
        'feature_importances': final_model.feature_importances_.tolist(),
        'feature_names': feature_cols
    }
    
    return final_model, metrics

def save_artifacts(
    model: GradientBoostingRegressor,
    metrics: Dict[str, Any],
    project_root: Path
) -> None:
    """
    Save model and metrics to artifacts directory.
    
    Args:
        model: Trained GradientBoostingRegressor
        metrics: Dictionary containing performance metrics
        project_root: Path to project root
    """
    model_dir = project_root / "artifacts" / "models"
    metrics_dir = project_root / "artifacts" / "metrics"
    
    model_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = model_dir / "best_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")
    
    # Save metrics
    metrics_path = metrics_dir / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

@enforce_resource_limits(runtime_limit_h=6, memory_limit_gb=7)
def main() -> None:
    """Main entry point for the training pipeline."""
    logger.info("Starting training pipeline...")
    
    try:
        # Load data
        df, feature_cols, family_cols = load_prepared_data()
        logger.info(f"Loaded {len(df)} samples with {len(feature_cols)} features")
        
        # Get family groups
        groups = get_family_groups(df, 'family')
        
        # Get config
        config = get_config()
        max_depth = config.get('max_depth', 5)
        n_estimators = config.get('n_estimators', 100)
        
        # Train and evaluate
        model, metrics = train_and_evaluate(df, feature_cols, groups, max_depth, n_estimators)
        
        # Save artifacts
        project_root = get_project_root()
        save_artifacts(model, metrics, project_root)
        
        logger.info("Training pipeline completed successfully.")
        
    except ResourceLimitExceeded as e:
        logger.error(f"Resource limit exceeded: {str(e)}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {str(e)}")
        raise

if __name__ == "__main__":
    main()