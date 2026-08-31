import time
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import r2_score
from sklearn.model_selection import cross_val_score
from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_metric(y_true: np.ndarray, y_pred: np.ndarray, mode: str = "individual") -> float:
    """
    Calculate performance metric based on mode.
    - 'individual': Returns R² score.
    - 'population': Returns Pearson correlation coefficient (r).
    """
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()

    if mode == "individual":
        if np.var(y_true) == 0:
            return 0.0
        return float(r2_score(y_true, y_pred))
    elif mode == "population":
        # Pearson r
        if np.std(y_true) == 0 or np.std(y_pred) == 0:
            return 0.0
        correlation = np.corrcoef(y_true, y_pred)[0, 1]
        return float(correlation) if not np.isnan(correlation) else 0.0
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'individual' or 'population'.")

def train_random_forest(X: pd.DataFrame, y: pd.Series, cv: int = 5) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """
    Train a Random Forest regressor and return the model plus metrics.
    Performs K-Fold cross-validation to compute a real metric_value.
    """
    start_time = time.time()
    
    # Ensure feature names are available for the model
    if hasattr(X, 'columns'):
        X = X.copy()
        X.columns = [str(c) for c in X.columns]
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=-1
    )
    
    # Fit the model on the full data for the return object
    model.fit(X, y)
    
    # Perform Cross-Validation to get a real metric value
    # We use negative MSE from sklearn and convert, or directly use scoring='r2'
    try:
        cv_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        mean_r2 = float(np.mean(cv_scores))
    except Exception as e:
        logger.warning(f"Cross-validation failed: {e}. Using 0.0 as metric value.")
        mean_r2 = 0.0

    duration = time.time() - start_time

    # Extract top features for logging
    top_features = get_top_features(model, n=5)
    feature_str = ", ".join([f"{name} ({val:.4f})" for name, val in top_features])

    # Log the metrics as required by T027
    logger.info(
        f"RandomForest Training Complete | "
        f"Time: {duration:.2f}s | "
        f"CV Folds: {cv} | "
        f"Mean R²: {mean_r2:.4f} | "
        f"Top 5 Features: {feature_str}"
    )

    metrics = {
        "model_type": "RandomForest",
        "training_time_sec": duration,
        "n_estimators": 100,
        "cv_folds": cv,
        "metric_value": mean_r2,
        "metric_name": "R2",
        "top_features": top_features
    }

    return model, metrics

def train_svm(X: pd.DataFrame, y: pd.Series, cv: int = 5) -> Tuple[SVR, Dict[str, Any]]:
    """
    Train an SVM regressor and return the model plus metrics.
    Performs K-Fold cross-validation to compute a real metric value.
    """
    start_time = time.time()
    
    if hasattr(X, 'columns'):
        X = X.copy()
        X.columns = [str(c) for c in X.columns]

    model = SVR(kernel='rbf', C=1.0, epsilon=0.2)
    model.fit(X, y)

    # Perform Cross-Validation
    try:
        cv_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        mean_r2 = float(np.mean(cv_scores))
    except Exception as e:
        logger.warning(f"Cross-validation failed: {e}. Using 0.0 as metric value.")
        mean_r2 = 0.0

    duration = time.time() - start_time

    # Extract top features for logging (may be empty for RBF SVR)
    top_features = get_top_features(model, n=5)
    if top_features:
        feature_str = ", ".join([f"{name} ({val:.4f})" for name, val in top_features])
    else:
        feature_str = "N/A (RBF SVR lacks intrinsic importance)"

    # Log the metrics as required by T027
    logger.info(
        f"SVM Training Complete | "
        f"Time: {duration:.2f}s | "
        f"CV Folds: {cv} | "
        f"Mean R²: {mean_r2:.4f} | "
        f"Top 5 Features: {feature_str}"
    )

    metrics = {
        "model_type": "SVM",
        "training_time_sec": duration,
        "kernel": "rbf",
        "cv_folds": cv,
        "metric_value": mean_r2,
        "metric_name": "R2",
        "top_features": top_features
    }

    return model, metrics

def get_top_features(model: Any, n: int = 20) -> List[Tuple[str, float]]:
    """
    Extract the top N most important features from a trained model.
    
    Supported models:
    - RandomForestRegressor (uses feature_importances_)
    - SVR (uses coefficients magnitude for linear kernels, otherwise warns)
    """
    feature_names = []
    importances = []

    if hasattr(model, 'feature_importances_'):
        # Standard for tree-based models (RandomForest)
        feature_names = list(model.feature_names_in_) if hasattr(model, 'feature_names_in_') else [f"f{i}" for i in range(len(model.feature_importances_))]
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        # Linear models (LinearSVR, SVR with linear kernel)
        # Coefficients magnitude can be used as importance proxy
        feature_names = list(model.feature_names_in_) if hasattr(model, 'feature_names_in_') else [f"f{i}" for i in range(len(model.coef_))]
        importances = np.abs(model.coef_)
    else:
        logger.warning(f"Model type {type(model).__name__} does not have intrinsic feature importance. "
                     "Returning empty list. Consider using permutation importance externally.")
        return []

    if len(feature_names) != len(importances):
        logger.error("Mismatch between feature names and importances length.")
        return []

    # Create list of tuples
    feature_importance_pairs = list(zip(feature_names, importances))
    
    # Sort by importance descending
    feature_importance_pairs.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N
    return feature_importance_pairs[:n]

def load_trained_model(path: str) -> Any:
    """
    Load a trained model from a file path.
    """
    import joblib
    logger.info(f"Loading model from {path}")
    return joblib.load(path)