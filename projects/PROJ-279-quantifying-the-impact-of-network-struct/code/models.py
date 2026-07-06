import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import cross_val_score, LeaveOneOut, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
import logging

logger = logging.getLogger(__name__)

def get_cross_validation_split(X: np.ndarray, y: np.ndarray) -> Any:
    """
    Implement cross-validation logic: 5-fold if N >= 30, else LOOCV.
    
    Args:
        X: Feature matrix (N, M)
        y: Target vector (N,)
        
    Returns:
        A cross-validator object (KFold or LeaveOneOut) configured for the dataset size.
    """
    n_samples = X.shape[0]
    
    if n_samples >= 30:
        logger.info(f"Dataset size N={n_samples} >= 30. Using 5-fold Cross-Validation.")
        return KFold(n_splits=5, shuffle=True, random_state=42)
    else:
        logger.info(f"Dataset size N={n_samples} < 30. Using Leave-One-Out Cross-Validation.")
        return LeaveOneOut()

def run_ridge_regression(X: np.ndarray, y: np.ndarray, cv_splitter: Any = None, alpha: float = 1.0) -> Dict[str, Any]:
    """
    Run Ridge Regression with the specified cross-validation strategy.
    
    Args:
        X: Feature matrix
        y: Target vector
        cv_splitter: Cross-validator object from get_cross_validation_split
        alpha: Ridge regularization strength
        
    Returns:
        Dictionary containing mean R2, std R2, and fitted model coefficients.
    """
    if cv_splitter is None:
        cv_splitter = get_cross_validation_split(X, y)
        
    # Standardize features within the pipeline to avoid data leakage
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('ridge', Ridge(alpha=alpha))
    ])
    
    scores = cross_val_score(pipeline, X, y, cv=cv_splitter, scoring='r2')
    
    mean_r2 = np.mean(scores)
    std_r2 = np.std(scores)
    
    logger.info(f"Ridge Regression CV Results: Mean R² = {mean_r2:.4f} (+/- {std_r2:.4f})")
    
    # Fit on full data to get coefficients for interpretation
    pipeline.fit(X, y)
    final_model = pipeline.named_steps['ridge']
    scaler = pipeline.named_steps['scaler']
    
    # Scale coefficients back to original feature space if needed, 
    # but usually we report importance based on scaled coefficients or raw.
    # Here we return the scaled coefficients for feature importance analysis.
    coefficients = final_model.coef_
    
    return {
        'mean_r2': mean_r2,
        'std_r2': std_r2,
        'scores': scores,
        'coefficients': coefficients,
        'intercept': final_model.intercept_,
        'model': pipeline
    }

def calculate_feature_pvalues(X: np.ndarray, y: np.ndarray, cv_splitter: Any = None) -> List[float]:
    """
    Calculate approximate p-values for features using OLS on the full dataset
    (as a proxy for significance, noting Ridge shrinks coefficients).
    For rigorous p-values with Ridge, permutation tests are preferred, 
    but here we use OLS as a standard reference for feature significance 
    in the context of correlation analysis.
    
    Args:
        X: Feature matrix
        y: Target vector
        cv_splitter: (Unused for OLS p-value calculation, but kept for signature consistency)
        
    Returns:
        List of p-values for each feature.
    """
    # Using OLS for p-value estimation as Ridge does not provide standard errors directly
    model = LinearRegression()
    model.fit(X, y)
    
    n = X.shape[0]
    p = X.shape[1]
    
    # Residuals
    y_pred = model.predict(X)
    residuals = y - y_pred
    
    # Residual Sum of Squares
    rss = np.sum(residuals ** 2)
    
    # Variance of residuals
    sigma_sq = rss / (n - p - 1)
    
    # Covariance matrix of coefficients: sigma_sq * (X'X)^-1
    # Add small epsilon for numerical stability if X'X is singular
    try:
        XtX_inv = np.linalg.inv(X.T @ X + 1e-8 * np.eye(p))
    except np.linalg.LinAlgError:
        logger.warning("X'X is singular, using pseudo-inverse for p-value calculation.")
        XtX_inv = np.linalg.pinv(X.T @ X)
        
    coef_var = sigma_sq * np.diag(XtX_inv)
    coef_se = np.sqrt(coef_var)
    
    # T-statistics
    t_stats = model.coef_ / coef_se
    
    # P-values (two-tailed)
    from scipy import stats
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n-p-1))
    
    return p_values.tolist()

def extract_feature_importance(X: np.ndarray, y: np.ndarray, cv_splitter: Any = None) -> Dict[str, Any]:
    """
    Extract feature importance (absolute coefficient magnitude) from Ridge model.
    
    Args:
        X: Feature matrix
        y: Target vector
        cv_splitter: Cross-validator object
        
    Returns:
        Dictionary with feature importances and mean/std from CV.
    """
    # This is a simplified version. A robust implementation would aggregate
    # coefficients across folds. Here we fit on full data as a baseline
    # or use the model returned from run_ridge_regression.
    # To get std across folds, we would need to re-run the model manually per fold.
    # For this task, we return the global fit importance.
    
    result = run_ridge_regression(X, y, cv_splitter)
    coeffs = result['coefficients']
    
    # Normalize by absolute sum to get relative importance
    abs_coeffs = np.abs(coeffs)
    total_importance = np.sum(abs_coeffs)
    if total_importance > 0:
        relative_importance = abs_coeffs / total_importance
    else:
        relative_importance = np.zeros_like(abs_coeffs)
        
    return {
        'importance': relative_importance,
        'coefficients': coeffs,
        'mean_r2': result['mean_r2'],
        'std_r2': result['std_r2']
    }

def get_top_features(feature_names: List[str], importance: np.ndarray, top_k: int = 3) -> List[Tuple[str, float]]:
    """
    Get the top K features by importance.
    
    Args:
        feature_names: List of feature names
        importance: Array of importance scores
        top_k: Number of top features to return
        
    Returns:
        List of (feature_name, importance_score) tuples sorted descending.
    """
    if len(feature_names) != len(importance):
        raise ValueError("feature_names and importance must have the same length")
        
    indices = np.argsort(importance)[::-1]
    top_indices = indices[:top_k]
    
    return [(feature_names[i], float(importance[i])) for i in top_indices]