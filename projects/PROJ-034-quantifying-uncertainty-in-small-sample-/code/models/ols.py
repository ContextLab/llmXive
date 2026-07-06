"""
Ordinary Least Squares (OLS) regression model implementation.

Provides fitting, parameter estimation, and 95% confidence interval calculation.
"""
from typing import Tuple, Dict, Any, Optional
import numpy as np
from numpy.typing import ArrayLike
from scipy import stats

class OLSModel:
    """
    Ordinary Least Squares Regression Model.
    
    Fits a linear model y = Xβ + ε and calculates standard 95% confidence intervals
    for the coefficients using the t-distribution.
    """

    def __init__(self):
        self.coefficients: Optional[np.ndarray] = None
        self.se: Optional[np.ndarray] = None
        self.confidence_intervals: Optional[np.ndarray] = None
        self.residuals: Optional[np.ndarray] = None
        self.n: int = 0
        self.p: int = 0
        self.r_squared: float = 0.0
        self._fitted = False

    def fit(self, X: ArrayLike, y: ArrayLike, confidence_level: float = 0.95) -> 'OLSModel':
        """
        Fit the OLS model to the provided data.
        
        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target vector of shape (n_samples,).
            confidence_level: Confidence level for intervals (default 0.95 for 95%).
        
        Returns:
            self
        
        Raises:
            ValueError: If X and y shapes are incompatible or if X is rank-deficient.
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)

        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if y.ndim == 1:
            y = y.reshape(-1)

        if X.shape[0] != y.shape[0]:
            raise ValueError(f"X and y must have the same number of samples. Got {X.shape[0]} and {y.shape[0]}.")

        n, p = X.shape
        self.n = n
        self.p = p

        # Add intercept column
        X_design = np.column_stack([np.ones(n), X])
        p_design = p + 1

        # Check for rank deficiency
        rank = np.linalg.matrix_rank(X_design)
        if rank < p_design:
            raise ValueError(f"Design matrix is rank-deficient. Rank {rank} < {p_design}.")

        # Solve normal equations: (X'X)β = X'y
        # Using np.linalg.lstsq for numerical stability
        coefficients, residuals, rank, s = np.linalg.lstsq(X_design, y, rcond=None)

        self.coefficients = coefficients
        self.residuals = y - X_design @ coefficients

        # Calculate residual sum of squares
        rss = np.sum(self.residuals ** 2)
        
        # Estimate variance of residuals (sigma^2)
        # Degrees of freedom = n - p_design
        if n > p_design:
            sigma_sq = rss / (n - p_design)
        else:
            # If n <= p, variance is undefined or zero; handle gracefully
            sigma_sq = 0.0

        # Calculate standard errors of coefficients
        # Var(β) = sigma^2 * (X'X)^-1
        XtX_inv = np.linalg.inv(X_design.T @ X_design)
        self.se = np.sqrt(sigma_sq * np.diag(XtX_inv))

        # Calculate confidence intervals
        # CI = β ± t_{alpha/2, df} * SE(β)
        alpha = 1 - confidence_level
        df = n - p_design
        
        if df > 0:
            t_critical = stats.t.ppf(1 - alpha / 2, df)
        else:
            t_critical = np.inf # Cannot calculate CI if df <= 0

        margin = t_critical * self.se
        self.confidence_intervals = np.column_stack([self.coefficients - margin, self.coefficients + margin])

        # Calculate R-squared
        y_mean = np.mean(y)
        ss_tot = np.sum((y - y_mean) ** 2)
        if ss_tot > 0:
            self.r_squared = 1 - (rss / ss_tot)
        else:
            self.r_squared = 0.0

        self._fitted = True
        return self

    def get_results(self) -> Dict[str, Any]:
        """
        Get the results of the fitted model.
        
        Returns:
            Dictionary containing coefficients, standard errors, confidence intervals,
            R-squared, and other metrics.
        """
        if not self._fitted:
            raise RuntimeError("Model has not been fitted yet. Call fit() first.")

        return {
            "coefficients": self.coefficients.tolist(),
            "standard_errors": self.se.tolist(),
            "confidence_intervals": self.confidence_intervals.tolist(),
            "r_squared": float(self.r_squared),
            "n_samples": self.n,
            "n_features": self.p,
            "residual_sum_of_squares": float(np.sum(self.residuals ** 2)),
            "degrees_of_freedom": self.n - (self.p + 1)
        }

    def predict(self, X: ArrayLike) -> np.ndarray:
        """
        Predict using the fitted model.
        
        Args:
            X: Feature matrix of shape (n_samples, n_features).
        
        Returns:
            Predicted values.
        """
        if not self._fitted:
            raise RuntimeError("Model has not been fitted yet. Call fit() first.")
        
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        # Add intercept
        X_design = np.column_stack([np.ones(X.shape[0]), X])
        return X_design @ self.coefficients

def fit_ols_and_get_intervals(X: ArrayLike, y: ArrayLike, confidence_level: float = 0.95) -> Dict[str, Any]:
    """
    Convenience function to fit an OLS model and return results.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        confidence_level: Confidence level for intervals (default 0.95).
    
    Returns:
        Dictionary with coefficients, standard errors, and 95% confidence intervals.
    """
    model = OLSModel()
    model.fit(X, y, confidence_level=confidence_level)
    return model.get_results()
