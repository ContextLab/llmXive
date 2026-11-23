import time
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import cross_val_predict, cross_val_score, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_metric(y_true: np.ndarray, y_pred: np.ndarray, mode: str = 'individual') -> float:
    """
    Calculate evaluation metric based on mode.
    - 'individual': Returns R² score.
    - 'population': Returns Pearson correlation coefficient.
    """
    if mode == 'individual':
        return float(r2_score(y_true, y_pred))
    elif mode == 'population':
        # Pearson correlation
        if len(y_true) == 0 or len(y_pred) == 0:
            return 0.0
        corr_matrix = np.corrcoef(y_true, y_pred)
        if corr_matrix.shape != (2, 2):
            return 0.0
        return float(corr_matrix[0, 1])
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'individual' or 'population'.")

def train_random_forest(X: pd.DataFrame, y: pd.Series, cv: int = 5, mode: str = 'individual') -> Tuple[Any, Dict[str, Any]]:
    """
    Train a Random Forest Regressor with cross-validation.

    Args:
        X: Feature matrix (DataFrame).
        y: Target vector (Series).
        cv: Number of cross-validation folds.
        mode: Metric calculation mode ('individual' or 'population').

    Returns:
        Tuple of (fitted_model, metrics_dict) compliant with model_result.schema.yaml.
    """
    logger.info(f"Starting Random Forest training with {cv} CV folds.")
    start_time = time.time()

    # Initialize model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=-1
    )

    # Get cross-validated predictions for metric calculation
    y_pred_cv = cross_val_predict(model, X, y, cv=cv)

    # Fit the model on full data for feature importance and future use
    model.fit(X, y)

    # Calculate metrics
    r2 = calculate_metric(y.values, y_pred_cv, mode=mode)
    rmse = float(np.sqrt(mean_squared_error(y.values, y_pred_cv)))
    mae = float(mean_absolute_error(y.values, y_pred_cv))

    training_time = time.time() - start_time

    # Construct metrics dictionary compliant with model_result.schema.yaml
    # Includes 'mode' to fully describe the context of the r2 value
    metrics = {
        "r2": r2,
        "rmse": rmse,
        "mean_absolute_error": mae,
        "model_type": "RandomForestRegressor",
        "cv_folds": cv,
        "training_time_seconds": training_time,
        "mode": mode
    }

    logger.info(f"Random Forest training complete. R²: {r2:.4f}, RMSE: {rmse:.4f}, Time: {training_time:.2f}s")

    return model, metrics

def train_svm(X: pd.DataFrame, y: pd.Series, cv: int = 5, mode: str = 'individual') -> Tuple[Any, Dict[str, Any]]:
    """
    Train an SVM Regressor with cross-validation.

    Args:
        X: Feature matrix (DataFrame).
        y: Target vector (Series).
        cv: Number of cross-validation folds.
        mode: Metric calculation mode ('individual' or 'population').

    Returns:
        Tuple of (fitted_model, metrics_dict).
    """
    logger.info(f"Starting SVM training with {cv} CV folds.")
    start_time = time.time()

    # Initialize model
    model = SVR(kernel='rbf', C=1.0, epsilon=0.1)

    # Get cross-validated predictions
    y_pred_cv = cross_val_predict(model, X, y, cv=cv)

    # Fit on full data
    model.fit(X, y)

    # Calculate metrics
    r2 = calculate_metric(y.values, y_pred_cv, mode=mode)
    rmse = float(np.sqrt(mean_squared_error(y.values, y_pred_cv)))
    mae = float(mean_absolute_error(y.values, y_pred_cv))

    training_time = time.time() - start_time

    metrics = {
        "r2": r2,
        "rmse": rmse,
        "mean_absolute_error": mae,
        "model_type": "SVR",
        "cv_folds": cv,
        "training_time_seconds": training_time,
        "mode": mode
    }

    logger.info(f"SVM training complete. R²: {r2:.4f}, RMSE: {rmse:.4f}, Time: {training_time:.2f}s")

    return model, metrics

def get_top_features(model: Any, feature_names: List[str], n: int = 20) -> List[Tuple[str, float]]:
    """
    Extract top N features based on importance.

    Args:
        model: Fitted model with feature_importances_ or coef_ attribute.
        feature_names: List of feature names corresponding to model columns.
        n: Number of top features to return.

    Returns:
        List of (feature_name, importance) tuples.
    """
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importances = np.abs(model.coef_)
    else:
        logger.warning("Model has no feature importance attribute.")
        return []

    if len(feature_names) != len(importances):
        raise ValueError("Length of feature_names must match length of importances.")

    indices = np.argsort(importances)[::-1][:n]
    return [(feature_names[i], float(importances[i])) for i in indices]

def load_trained_model(path: str) -> Any:
    """
    Load a trained model from disk.
    Note: Requires joblib or pickle, ensuring dependencies are available.
    """
    import joblib
    logger.info(f"Loading model from {path}")
    return joblib.load(path)

def hyperparameter_search(model_type: str, X: pd.DataFrame, y: pd.Series, cv: int = 5, mode: str = 'individual') -> Tuple[Any, Dict[str, Any]]:
    """
    Perform a limited grid search to optimize hyperparameters for Random Forest or SVM.
    
    This function implements a 3x3 grid search to find better hyperparameters than
    the defaults used in train_random_forest and train_svm, addressing the requirement
    for robust predictive signal detection (T050).
    
    CONSTRAINT: Small grid size ensures completion within SC-005 (6h limit).
    
    Args:
        model_type: Either 'random_forest' or 'svm'.
        X: Feature matrix (DataFrame).
        y: Target vector (Series).
        cv: Number of cross-validation folds (default 5).
        mode: Metric calculation mode ('individual' or 'population').
    
    Returns:
        Tuple of (best_model, metrics_dict) where metrics include the best parameters
        and improved performance metrics.
    """
    logger.info(f"Starting hyperparameter search for {model_type} with {cv} CV folds.")
    start_time = time.time()
    
    if model_type == 'random_forest':
        # 3x3 grid for Random Forest
        # n_estimators: 50, 100, 200
        # max_depth: None, 10, 20
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20]
        }
        base_model = RandomForestRegressor(random_state=42, n_jobs=-1)
        grid_search = GridSearchCV(
            estimator=base_model,
            param_grid=param_grid,
            cv=cv,
            scoring='r2',
            n_jobs=-1,
            verbose=1
        )
    elif model_type == 'svm':
        # 3x3 grid for SVM
        # C: 0.1, 1.0, 10.0
        # gamma: scale, auto, 0.01
        param_grid = {
            'C': [0.1, 1.0, 10.0],
            'gamma': ['scale', 'auto', 0.01]
        }
        base_model = SVR(kernel='rbf')
        grid_search = GridSearchCV(
            estimator=base_model,
            param_grid=param_grid,
            cv=cv,
            scoring='r2',
            n_jobs=-1,
            verbose=1
        )
    else:
        raise ValueError(f"Unsupported model_type: {model_type}. Use 'random_forest' or 'svm'.")
    
    # Fit the grid search
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    best_cv_score = grid_search.best_score_
    
    # Get cross-validated predictions with the best model for final metrics
    y_pred_cv = cross_val_predict(best_model, X, y, cv=cv)
    
    # Calculate final metrics
    r2 = calculate_metric(y.values, y_pred_cv, mode=mode)
    rmse = float(np.sqrt(mean_squared_error(y.values, y_pred_cv)))
    mae = float(mean_absolute_error(y.values, y_pred_cv))
    
    training_time = time.time() - start_time
    
    metrics = {
        "model_type": f"{model_type}_optimized",
        "cv_folds": cv,
        "best_params": best_params,
        "best_cv_score": float(best_cv_score),
        "r2": r2,
        "rmse": rmse,
        "mean_absolute_error": mae,
        "training_time_seconds": training_time,
        "mode": mode
    }
    
    logger.info(
        f"Hyperparameter search complete for {model_type}. "
        f"Best params: {best_params}, Best CV R²: {best_cv_score:.4f}, "
        f"Final R²: {r2:.4f}, Time: {training_time:.2f}s"
    )
    
    return best_model, metrics