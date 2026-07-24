"""
Model Training Module for Steel Yield Strength Prediction.

Implements training pipelines for GAM, Regularized Linear Regression,
Random Forest, and XGBoost models with adaptive cross-validation strategies.
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, KFold, RepeatedKFold
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, make_scorer
import xgboost as xgb

# Import project utilities
from src.utils.config import PROJECT_ROOT
from src.data.loader import optimize_dataframe_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_N_FOLDS = 3
MIN_DATASET_SIZE_FOR_DEFAULT_FOLDS = 100
DEFAULT_RANDOM_STATE = 42


def train_gam(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: Optional[int] = None,
    random_state: int = DEFAULT_RANDOM_STATE
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Train a Generalized Additive Model (GAM) with splines.

    Since sklearn does not have a native GAM implementation that exposes
    splines directly in the same way, we approximate the behavior using
    a linear model with pre-computed spline features or use a library like
    pygam if available. However, to maintain strict dependency on the
    provided API surface (sklearn), we use a Ridge Regression with
    polynomial/spline-like feature expansion if needed, or simply
    Ridge as the linear baseline for the GAM comparison.

    Note: For a true GAM with splines, one would typically use `pygam`.
    Given the constraints and imports, we implement a robust Ridge Regression
    which acts as the linear baseline, and if `pygam` is installed, we attempt
    to use it. If not, we fall back to Ridge with a clear log message.

    Args:
        X: Feature matrix (n_samples, n_features).
        y: Target vector (n_samples,).
        n_folds: Number of folds for CV. Defaults to adaptive logic.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (model_results_dict, cv_results_df).
    """
    logger.info(f"Training GAM model (Ridge Regression baseline)...")

    # Adaptive CV strategy
    if n_folds is None:
        if X.shape[0] < MIN_DATASET_SIZE_FOR_DEFAULT_FOLDS:
            n_folds = 10
            logger.info(f"Dataset size ({X.shape[0]}) < 100. Using 10-Fold Repeated CV.")
            cv = RepeatedKFold(n_splits=n_folds, n_repeats=3, random_state=random_state)
        else:
            n_folds = DEFAULT_N_FOLDS
            logger.info(f"Dataset size ({X.shape[0]}) >= 100. Using {n_folds}-Fold CV.")
            cv = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    else:
        if X.shape[0] < MIN_DATASET_SIZE_FOR_DEFAULT_FOLDS and n_folds < 10:
            logger.warning(f"Requested {n_folds}-fold CV on small dataset. Switching to 10-Fold Repeated CV.")
            cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=random_state)
        else:
            cv = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)

    # Attempt to use pygam if available for true spline GAM, else use Ridge
    try:
        from pygam import LinearGAM, s
        # Create a simple GAM with spline terms for all features
        # This is a simplified approach; a full implementation would select knots per feature
        gam = LinearGAM(s(0) + s(1) + s(2)).fit(X, y)
        # For cross-validation scores, we need to manually loop or use a wrapper
        # Since pygam doesn't have a direct cross_val_score interface like sklearn,
        # we implement a manual loop for R2
        scores = []
        for train_idx, val_idx in cv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            temp_gam = LinearGAM(s(0) + s(1) + s(2)).fit(X_train, y_train)
            pred = temp_gam.predict(X_val)
            scores.append(r2_score(y_val, pred))
        
        mean_r2 = np.mean(scores)
        std_r2 = np.std(scores)
        
        results = {
            "model_type": "GAM (pygam)",
            "mean_r2": mean_r2,
            "std_r2": std_r2,
            "cv_folds": n_folds,
            "model": gam,
            "params": {"method": "LinearGAM with splines"}
        }
        
        # Create results dataframe
        results_df = pd.DataFrame({
            "fold": range(1, len(scores) + 1),
            "r2_score": scores
        })
        
        logger.info(f"GAM (pygam) training complete. Mean R²: {mean_r2:.4f} (+/- {std_r2:.4f})")
        return results, results_df

    except ImportError:
        logger.warning("pygam not found. Falling back to Ridge Regression as GAM baseline.")
        model = Ridge(alpha=1.0)
        scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        
        mean_r2 = np.mean(scores)
        std_r2 = np.std(scores)
        
        model.fit(X, y)
        
        results = {
            "model_type": "GAM (Ridge Baseline)",
            "mean_r2": mean_r2,
            "std_r2": std_r2,
            "cv_folds": n_folds,
            "model": model,
            "params": {"alpha": 1.0}
        }
        
        results_df = pd.DataFrame({
            "fold": range(1, len(scores) + 1),
            "r2_score": scores
        })
        
        logger.info(f"GAM (Ridge) training complete. Mean R²: {mean_r2:.4f} (+/- {std_r2:.4f})")
        return results, results_df


def train_regularized_linear(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: Optional[int] = None,
    random_state: int = DEFAULT_RANDOM_STATE,
    alpha: float = 1.0,
    l1_ratio: float = 0.5
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Train a Regularized Linear Regression (Elastic Net) model.

    Args:
        X: Feature matrix.
        y: Target vector.
        n_folds: Number of folds for CV.
        random_state: Random seed.
        alpha: Regularization strength.
        l1_ratio: Mixing parameter for Elastic Net (0=L2, 1=L1).

    Returns:
        Tuple of (model_results_dict, cv_results_df).
    """
    logger.info(f"Training Regularized Linear Regression (Elastic Net)...")

    # Adaptive CV strategy
    if n_folds is None:
        if X.shape[0] < MIN_DATASET_SIZE_FOR_DEFAULT_FOLDS:
            n_folds = 10
            logger.info(f"Dataset size ({X.shape[0]}) < 100. Using 10-Fold Repeated CV.")
            cv = RepeatedKFold(n_splits=n_folds, n_repeats=3, random_state=random_state)
        else:
            n_folds = DEFAULT_N_FOLDS
            logger.info(f"Dataset size ({X.shape[0]}) >= 100. Using {n_folds}-Fold CV.")
            cv = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    else:
        if X.shape[0] < MIN_DATASET_SIZE_FOR_DEFAULT_FOLDS and n_folds < 10:
            logger.warning(f"Requested {n_folds}-fold CV on small dataset. Switching to 10-Fold Repeated CV.")
            cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=random_state)
        else:
            cv = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)

    model = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=random_state, max_iter=5000)
    
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
    
    mean_r2 = np.mean(scores)
    std_r2 = np.std(scores)
    
    model.fit(X, y)
    
    results = {
        "model_type": "Regularized Linear (Elastic Net)",
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "cv_folds": n_folds,
        "model": model,
        "params": {"alpha": alpha, "l1_ratio": l1_ratio}
    }
    
    results_df = pd.DataFrame({
        "fold": range(1, len(scores) + 1),
        "r2_score": scores
    })
    
    logger.info(f"Regularized Linear training complete. Mean R²: {mean_r2:.4f} (+/- {std_r2:.4f})")
    return results, results_df


def train_random_forest(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: Optional[int] = None,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_estimators: int = 100,
    max_depth: Optional[int] = None
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Train a Random Forest Regressor.

    Args:
        X: Feature matrix.
        y: Target vector.
        n_folds: Number of folds for CV.
        random_state: Random seed.
        n_estimators: Number of trees.
        max_depth: Maximum depth of trees.

    Returns:
        Tuple of (model_results_dict, cv_results_df).
    """
    logger.info(f"Training Random Forest...")

    # Adaptive CV strategy
    if n_folds is None:
        if X.shape[0] < MIN_DATASET_SIZE_FOR_DEFAULT_FOLDS:
            n_folds = 10
            logger.info(f"Dataset size ({X.shape[0]}) < 100. Using 10-Fold Repeated CV.")
            cv = RepeatedKFold(n_splits=n_folds, n_repeats=3, random_state=random_state)
        else:
            n_folds = DEFAULT_N_FOLDS
            logger.info(f"Dataset size ({X.shape[0]}) >= 100. Using {n_folds}-Fold CV.")
            cv = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    else:
        if X.shape[0] < MIN_DATASET_SIZE_FOR_DEFAULT_FOLDS and n_folds < 10:
            logger.warning(f"Requested {n_folds}-fold CV on small dataset. Switching to 10-Fold Repeated CV.")
            cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=random_state)
        else:
            cv = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )
    
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
    
    mean_r2 = np.mean(scores)
    std_r2 = np.std(scores)
    
    model.fit(X, y)
    
    results = {
        "model_type": "Random Forest",
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "cv_folds": n_folds,
        "model": model,
        "params": {"n_estimators": n_estimators, "max_depth": max_depth}
    }
    
    results_df = pd.DataFrame({
        "fold": range(1, len(scores) + 1),
        "r2_score": scores
    })
    
    logger.info(f"Random Forest training complete. Mean R²: {mean_r2:.4f} (+/- {std_r2:.4f})")
    return results, results_df


def train_xgboost(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: Optional[int] = None,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_estimators: int = 100,
    max_depth: int = 6,
    learning_rate: float = 0.1
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Train an XGBoost Regressor (CPU-only).

    Args:
        X: Feature matrix.
        y: Target vector.
        n_folds: Number of folds for CV.
        random_state: Random seed.
        n_estimators: Number of boosting rounds.
        max_depth: Maximum tree depth.
        learning_rate: Learning rate.

    Returns:
        Tuple of (model_results_dict, cv_results_df).
    """
    logger.info(f"Training XGBoost (CPU-only)...")

    # Adaptive CV strategy
    if n_folds is None:
        if X.shape[0] < MIN_DATASET_SIZE_FOR_DEFAULT_FOLDS:
            n_folds = 10
            logger.info(f"Dataset size ({X.shape[0]}) < 100. Using 10-Fold Repeated CV.")
            cv = RepeatedKFold(n_splits=n_folds, n_repeats=3, random_state=random_state)
        else:
            n_folds = DEFAULT_N_FOLDS
            logger.info(f"Dataset size ({X.shape[0]}) >= 100. Using {n_folds}-Fold CV.")
            cv = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    else:
        if X.shape[0] < MIN_DATASET_SIZE_FOR_DEFAULT_FOLDS and n_folds < 10:
            logger.warning(f"Requested {n_folds}-fold CV on small dataset. Switching to 10-Fold Repeated CV.")
            cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=random_state)
        else:
            cv = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)

    model = xgb.XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        random_state=random_state,
        n_jobs=-1,
        tree_method='hist', # Efficient for CPU
        enable_categorical=False
    )
    
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
    
    mean_r2 = np.mean(scores)
    std_r2 = np.std(scores)
    
    model.fit(X, y)
    
    results = {
        "model_type": "XGBoost",
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "cv_folds": n_folds,
        "model": model,
        "params": {"n_estimators": n_estimators, "max_depth": max_depth, "learning_rate": learning_rate}
    }
    
    results_df = pd.DataFrame({
        "fold": range(1, len(scores) + 1),
        "r2_score": scores
    })
    
    logger.info(f"XGBoost training complete. Mean R²: {mean_r2:.4f} (+/- {std_r2:.4f})")
    return results, results_df


def run_training_pipeline(
    data_path: str,
    target_column: str = 'yield_strength',
    output_dir: Optional[str] = None,
    n_folds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full training pipeline for all models.

    Args:
        data_path: Path to the processed data CSV.
        target_column: Name of the target column.
        output_dir: Directory to save results. Defaults to data/results.
        n_folds: Override for number of folds (uses adaptive logic if None).

    Returns:
        Dictionary containing results from all models.
    """
    logger.info(f"Starting training pipeline with data: {data_path}")
    
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "data", "results")
        os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    df = optimize_dataframe_memory(df)
    
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in data. Available: {df.columns.tolist()}")
    
    # Prepare features and target
    X = df.drop(columns=[target_column]).values
    y = df[target_column].values
    
    logger.info(f"Data shape: {X.shape}")
    logger.info(f"Target stats: mean={np.mean(y):.2f}, std={np.std(y):.2f}")
    
    # Train models
    results = {}
    
    # 1. GAM
    gam_results, gam_cv_df = train_gam(X, y, n_folds=n_folds)
    results['GAM'] = gam_results
    gam_cv_df.to_csv(os.path.join(output_dir, 'gam_cv_results.csv'), index=False)
    
    # 2. Regularized Linear
    reg_linear_results, reg_linear_cv_df = train_regularized_linear(X, y, n_folds=n_folds)
    results['RegularizedLinear'] = reg_linear_results
    reg_linear_cv_df.to_csv(os.path.join(output_dir, 'regularized_linear_cv_results.csv'), index=False)
    
    # 3. Random Forest
    rf_results, rf_cv_df = train_random_forest(X, y, n_folds=n_folds)
    results['RandomForest'] = rf_results
    rf_cv_df.to_csv(os.path.join(output_dir, 'random_forest_cv_results.csv'), index=False)
    
    # 4. XGBoost
    xgb_results, xgb_cv_df = train_xgboost(X, y, n_folds=n_folds)
    results['XGBoost'] = xgb_results
    xgb_cv_df.to_csv(os.path.join(output_dir, 'xgboost_cv_results.csv'), index=False)
    
    # Save summary
    summary_data = {
        "Model": [r['model_type'] for r in results.values()],
        "Mean_R2": [r['mean_r2'] for r in results.values()],
        "Std_R2": [r['std_r2'] for r in results.values()],
        "CV_Folds": [r['cv_folds'] for r in results.values()]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_path = os.path.join(output_dir, 'training_summary.csv')
    summary_df.to_csv(summary_path, index=False)
    logger.info(f"Training summary saved to {summary_path}")
    
    # Save best model (highest mean R2)
    best_model_name = max(results.keys(), key=lambda k: results[k]['mean_r2'])
    best_model = results[best_model_name]['model']
    best_model_path = os.path.join(output_dir, f'best_model_{best_model_name}.pkl')
    import joblib
    joblib.dump(best_model, best_model_path)
    logger.info(f"Best model ({best_model_name}) saved to {best_model_path}")
    
    logger.info("Training pipeline completed successfully.")
    return results