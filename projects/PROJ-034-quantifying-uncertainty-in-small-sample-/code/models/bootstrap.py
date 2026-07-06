"""
Non-parametric bootstrap implementation with BCa (Bias-Corrected and Accelerated) interval correction.
"""
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
from numpy.typing import ArrayLike
from scipy import stats
from scipy.special import norminv, normpdf

class BootstrapModel:
    """
    Non-parametric bootstrap regression model.
    """
    def __init__(self, n_bootstraps: int = 2000, confidence_level: float = 0.95, random_state: Optional[int] = None):
        self.n_bootstraps = n_bootstraps
        self.confidence_level = confidence_level
        self.random_state = random_state
        self.rng = np.random.default_rng(random_state)
        self.coefficients_: Optional[np.ndarray] = None
        self.intervals_: Optional[Dict[str, Tuple[float, float]]] = None

    def fit(self, X: ArrayLike, y: ArrayLike) -> 'BootstrapModel':
        """
        Fit the bootstrap model by resampling and estimating coefficients.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
        
        Returns:
            self
        """
        X = np.asarray(X)
        y = np.asarray(y)
        n_samples, n_features = X.shape

        # Store OLS estimates for bias correction calculation
        # Using simple OLS: beta = (X'X)^-1 X'y
        try:
            # Add regularization for stability if X'X is singular
            XtX = X.T @ X
            if np.linalg.cond(XtX) > 1e10:
                # Add small regularization term
                beta_hat = np.linalg.solve(XtX + 1e-8 * np.eye(n_features), X.T @ y)
            else:
                beta_hat = np.linalg.solve(XtX, X.T @ y)
        except np.linalg.LinAlgError:
            # Fallback to pseudo-inverse if singular
            beta_hat = np.linalg.lstsq(X, y, rcond=None)[0]

        self.coefficients_ = beta_hat
        bootstrap_coeffs = np.zeros((self.n_bootstraps, n_features))

        for i in range(self.n_bootstraps):
            # Resample with replacement
            indices = self.rng.integers(0, n_samples, size=n_samples)
            X_boot = X[indices]
            y_boot = y[indices]

            # Fit OLS on bootstrap sample
            try:
                XtX_boot = X_boot.T @ X_boot
                if np.linalg.cond(XtX_boot) > 1e10:
                  beta_boot = np.linalg.solve(XtX_boot + 1e-8 * np.eye(n_features), X_boot.T @ y_boot)
                else:
                  beta_boot = np.linalg.solve(XtX_boot, X_boot.T @ y_boot)
            except np.linalg.LinAlgError:
                beta_boot = np.linalg.lstsq(X_boot, y_boot, rcond=None)[0]
            
            bootstrap_coeffs[i] = beta_boot

        # Calculate BCa intervals for each coefficient
        self.intervals_ = {}
        alpha = 1 - self.confidence_level

        for j in range(n_features):
            theta_j = beta_hat[j]
            theta_boot_j = bootstrap_coeffs[:, j]

            # 1. Bias correction (z0)
            count_below = np.sum(theta_boot_j < theta_j)
            z0 = norminv(count_below / self.n_bootstraps)

            # 2. Acceleration factor (a) using jackknife
            jackknife_estimates = np.zeros(n_samples)
            for i in range(n_samples):
                X_jack = np.delete(X, i, axis=0)
                y_jack = np.delete(y, i)
                try:
                    XtX_jack = X_jack.T @ X_jack
                    if np.linalg.cond(XtX_jack) > 1e10:
                        beta_jack = np.linalg.solve(XtX_jack + 1e-8 * np.eye(n_features), X_jack.T @ y_jack)
                    else:
                        beta_jack = np.linalg.solve(XtX_jack, X_jack.T @ y_jack)
                except np.linalg.LinAlgError:
                    beta_jack = np.linalg.lstsq(X_jack, y_jack, rcond=None)[0]
                jackknife_estimates[i] = beta_jack[j]

            theta_mean = np.mean(jackknife_estimates)
            numerator = np.sum((theta_mean - jackknife_estimates) ** 3)
            denominator = 6 * (np.sum((theta_mean - jackknife_estimates) ** 2)) ** 1.5
            a = numerator / denominator if denominator != 0 else 0.0

            # 3. Calculate adjusted percentiles
        z_alpha = norminv(alpha / 2)
        z_1_minus_alpha = norminv(1 - alpha / 2)

        def bca_percentile(z_alpha_val: float) -> float:
            numerator = z0 + z_alpha_val + z0 * z_alpha_val * a
            denominator = 1 - a * (z0 + z_alpha_val)
            if abs(denominator) < 1e-10:
                denominator = 1e-10 if denominator >= 0 else -1e-10
            alpha_prime = norminv(z0 + numerator / denominator)
            return alpha_prime

        alpha_low = bca_percentile(z_alpha)
        alpha_high = bca_percentile(z_1_minus_alpha)

        # Ensure bounds are within [0, 1]
        alpha_low = max(0.0, min(1.0, alpha_low))
        alpha_high = max(0.0, min(1.0, alpha_high))

        # Calculate percentiles from bootstrap distribution
        low_idx = int(alpha_low * self.n_bootstraps)
        high_idx = int(alpha_high * self.n_bootstraps)
        
        sorted_coeffs = np.sort(theta_boot_j)
        lower_bound = sorted_coeffs[low_idx]
        upper_bound = sorted_coeffs[high_idx]

        self.intervals_[f"beta_{j}"] = (lower_bound, upper_bound)

        return self

    def get_intervals(self) -> Dict[str, Tuple[float, float]]:
        """
        Get the BCa confidence intervals for coefficients.
        
        Returns:
            Dictionary mapping coefficient names to (lower, upper) bounds
        """
        if self.intervals_ is None:
            raise RuntimeError("Model must be fitted before getting intervals")
        return self.intervals_

    def get_coefficients(self) -> np.ndarray:
        """
        Get the point estimates for coefficients.
        
        Returns:
            Array of coefficient estimates
        """
        if self.coefficients_ is None:
            raise RuntimeError("Model must be fitted before getting coefficients")
        return self.coefficients_


def fit_bootstrap_and_get_intervals(
    X: ArrayLike,
    y: ArrayLike,
    n_bootstraps: int = 2000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Tuple[np.ndarray, Dict[str, Tuple[float, float]]]:
    """
    Convenience function to fit a bootstrap model and return intervals.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        n_bootstraps: Number of bootstrap samples
        confidence_level: Confidence level for intervals (e.g., 0.95)
        random_state: Random seed for reproducibility
    
    Returns:
        Tuple of (coefficients, intervals_dict)
    """
    model = BootstrapModel(
        n_bootstraps=n_bootstraps,
        confidence_level=confidence_level,
        random_state=random_state
    )
    model.fit(X, y)
    return model.get_coefficients(), model.get_intervals()
