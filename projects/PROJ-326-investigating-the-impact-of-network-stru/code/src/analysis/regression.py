"""
Regression analysis module for network topology and energy transfer studies.

Implements linear and non-linear regression models to correlate network metrics
(e.g., clustering coefficient, average path length) with simulation outcomes
(e.g., diffusion rates, energy density changes).

Uses scikit-learn for model fitting and scipy for statistical inference.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

logger = logging.getLogger(__name__)


class RegressionResult:
    """Container for regression analysis results."""

    def __init__(
        self,
        model_type: str,
        coefficients: Optional[np.ndarray] = None,
        intercept: Optional[float] = None,
        r_squared: Optional[float] = None,
        p_values: Optional[np.ndarray] = None,
        std_errors: Optional[np.ndarray] = None,
        mse: Optional[float] = None,
        mae: Optional[float] = None,
        predictions: Optional[np.ndarray] = None,
        residuals: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.model_type = model_type
        self.coefficients = coefficients
        self.intercept = intercept
        self.r_squared = r_squared
        self.p_values = p_values
        self.std_errors = std_errors
        self.mse = mse
        self.mae = mae
        self.predictions = predictions
        self.residuals = residuals
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "model_type": self.model_type,
            "coefficients": self.coefficients.tolist() if self.coefficients is not None else None,
            "intercept": float(self.intercept) if self.intercept is not None else None,
            "r_squared": float(self.r_squared) if self.r_squared is not None else None,
            "p_values": self.p_values.tolist() if self.p_values is not None else None,
            "std_errors": self.std_errors.tolist() if self.std_errors is not None else None,
            "mse": float(self.mse) if self.mse is not None else None,
            "mae": float(self.mae) if self.mae is not None else None,
            "metadata": self.metadata
        }


def _calculate_p_values(
    self,
    X: np.ndarray,
    y: np.ndarray,
    coef: np.ndarray,
    intercept: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate p-values and standard errors for linear regression coefficients.

    Uses t-test based on residual sum of squares and degrees of freedom.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        coef: Coefficients from fitted model
        intercept: Intercept from fitted model

    Returns:
        Tuple of (p_values, std_errors)
    """
    n_samples, n_features = X.shape
    residuals = y - (X @ coef + intercept)
    ss_res = np.sum(residuals ** 2)
    df = n_samples - n_features - 1

    if df <= 0:
        logger.warning("Degrees of freedom <= 0. Cannot compute reliable p-values.")
        return np.ones(n_features), np.ones(n_features)

    # Estimate variance of residuals
    sigma_sq = ss_res / df

    # Calculate (X^T X)^-1
    try:
        XtX_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError:
        logger.warning("X^T X is singular. Using pseudo-inverse.")
        XtX_inv = np.linalg.pinv(X.T @ X)

    # Standard errors of coefficients
    std_errors = np.sqrt(np.diag(XtX_inv) * sigma_sq)

    # t-statistics
    t_stats = coef / std_errors

    # Two-tailed p-values
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df))

    return p_values, std_errors


def fit_linear_regression(
    self,
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    normalize: bool = False,
    fit_intercept: bool = True
) -> RegressionResult:
    """
    Fit a simple linear regression model.

    Args:
        X: Feature matrix (n_samples, n_features) or DataFrame
        y: Target vector (n_samples,) or Series
        normalize: Whether to normalize features before fitting
        fit_intercept: Whether to calculate the intercept

    Returns:
        RegressionResult object containing model parameters and statistics
    """
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, pd.Series):
        y = y.values

    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if len(X) != len(y):
        raise ValueError(f"X and y must have the same number of samples. "
                       f"Got {len(X)} and {len(y)}.")

    model = LinearRegression(fit_intercept=fit_intercept)
    model.fit(X, y)

    y_pred = model.predict(X)
    residuals = y - y_pred

    r_squared = model.score(X, y)
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)

    p_values, std_errors = self._calculate_p_values(
        X, y, model.coef_, model.intercept_
    )

    logger.info(f"Linear regression fit: R²={r_squared:.4f}, "
               f"MSE={mse:.4f}, MAE={mae:.4f}")

    return RegressionResult(
        model_type="linear",
        coefficients=model.coef_,
        intercept=model.intercept_,
        r_squared=r_squared,
        p_values=p_values,
        std_errors=std_errors,
        mse=mse,
        mae=mae,
        predictions=y_pred,
        residuals=residuals,
        metadata={"n_samples": len(X), "n_features": X.shape[1]}
    )


def fit_polynomial_regression(
    self,
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    degree: int = 2,
    normalize: bool = False,
    fit_intercept: bool = True
) -> RegressionResult:
    """
    Fit a polynomial (non-linear) regression model.

    Creates polynomial features up to the specified degree and fits
    a linear model to them.

    Args:
        X: Feature matrix (n_samples, n_features) or DataFrame
        y: Target vector (n_samples,) or Series
        degree: Degree of polynomial features
        normalize: Whether to normalize features
        fit_intercept: Whether to calculate the intercept

    Returns:
        RegressionResult object containing model parameters and statistics
    """
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, pd.Series):
        y = y.values

    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if len(X) != len(y):
        raise ValueError(f"X and y must have the same number of samples. "
                       f"Got {len(X)} and {len(y)}.")

    # Create polynomial features
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(X)

    model = LinearRegression(fit_intercept=fit_intercept)
    model.fit(X_poly, y)

    y_pred = model.predict(X_poly)
    residuals = y - y_pred

    r_squared = model.score(X_poly, y)
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)

    p_values, std_errors = self._calculate_p_values(
        X_poly, y, model.coef_, model.intercept_
    )

    logger.info(f"Polynomial regression (degree={degree}) fit: "
               f"R²={r_squared:.4f}, MSE={mse:.4f}, MAE={mae:.4f}")

    return RegressionResult(
        model_type=f"polynomial_degree_{degree}",
        coefficients=model.coef_,
        intercept=model.intercept_,
        r_squared=r_squared,
        p_values=p_values,
        std_errors=std_errors,
        mse=mse,
        mae=mae,
        predictions=y_pred,
        residuals=residuals,
        metadata={
            "n_samples": len(X),
            "n_features": X.shape[1],
            "degree": degree,
            "n_poly_features": X_poly.shape[1]
        }
    )


def fit_robust_regression(
    self,
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    method: str = "ridge",
    alpha: float = 1.0,
    normalize: bool = False
) -> RegressionResult:
    """
    Fit a regularized (robust) regression model.

    Supports Ridge (L2) and Lasso (L1) regularization to handle
    multicollinearity and prevent overfitting.

    Args:
        X: Feature matrix (n_samples, n_features) or DataFrame
        y: Target vector (n_samples,) or Series
        method: Regularization method ('ridge' or 'lasso')
        alpha: Regularization strength (higher = more regularization)
        normalize: Whether to normalize features

    Returns:
        RegressionResult object containing model parameters and statistics
    """
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, pd.Series):
        y = y.values

    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if len(X) != len(y):
        raise ValueError(f"X and y must have the same number of samples. "
                       f"Got {len(X)} and {len(y)}.")

    if method == "ridge":
        model = Ridge(alpha=alpha, fit_intercept=True, normalize=normalize)
    elif method == "lasso":
        model = Lasso(alpha=alpha, fit_intercept=True, normalize=normalize)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'ridge' or 'lasso'.")

    model.fit(X, y)

    y_pred = model.predict(X)
    residuals = y - y_pred

    r_squared = model.score(X, y)
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)

    # Note: Regularized models don't have straightforward p-values
    # We return None for p_values and std_errors
    logger.info(f"{method.capitalize()} regression fit (alpha={alpha}): "
               f"R²={r_squared:.4f}, MSE={mse:.4f}, MAE={mae:.4f}")

    return RegressionResult(
        model_type=f"{method}_regularized",
        coefficients=model.coef_,
        intercept=model.intercept_,
        r_squared=r_squared,
        p_values=None,
        std_errors=None,
        mse=mse,
        mae=mae,
        predictions=y_pred,
        residuals=residuals,
        metadata={
            "n_samples": len(X),
            "n_features": X.shape[1],
            "alpha": alpha,
            "method": method
        }
    )


def compare_models(
    self,
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    degrees: Optional[List[int]] = None
) -> Dict[str, RegressionResult]:
    """
    Compare multiple regression models (linear and polynomial).

    Fits linear regression and polynomial regressions of various degrees,
    returning results for comparison.

    Args:
        X: Feature matrix (n_samples, n_features) or DataFrame
        y: Target vector (n_samples,) or Series
        degrees: List of polynomial degrees to test (default: [1, 2, 3])

    Returns:
        Dictionary mapping model type to RegressionResult
    """
    if degrees is None:
        degrees = [1, 2, 3]

    results = {}

    # Linear regression (degree 1)
    if 1 in degrees:
        results["linear"] = self.fit_linear_regression(X, y)
        degrees.remove(1)

    # Polynomial regressions
    for deg in degrees:
        results[f"polynomial_{deg}"] = self.fit_polynomial_regression(
            X, y, degree=deg
        )

    return results


def analyze_correlation(
    self,
    x: Union[np.ndarray, pd.Series],
    y: Union[np.ndarray, pd.Series],
    method: str = "pearson"
) -> Dict[str, float]:
    """
    Calculate correlation statistics between two variables.

    Args:
        x: First variable (n_samples,)
        y: Second variable (n_samples,)
        method: Correlation method ('pearson', 'spearman', 'kendall')

    Returns:
        Dictionary with correlation coefficient and p-value
    """
    if isinstance(x, pd.Series):
        x = x.values
    if isinstance(y, pd.Series):
        y = y.values

    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if len(x) != len(y):
        raise ValueError(f"x and y must have the same length. "
                       f"Got {len(x)} and {len(y)}.")

    if method == "pearson":
        corr, p_value = stats.pearsonr(x, y)
    elif method == "spearman":
        corr, p_value = stats.spearmanr(x, y)
    elif method == "kendall":
        corr, p_value = stats.kendalltau(x, y)
    else:
        raise ValueError(f"Unknown method: {method}. "
                       f"Use 'pearson', 'spearman', or 'kendall'.")

    return {
        "correlation": float(corr),
        "p_value": float(p_value),
        "method": method
    }