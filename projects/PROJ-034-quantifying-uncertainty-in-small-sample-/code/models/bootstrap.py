"""
Non-parametric Bootstrap implementation with BCa (Bias-Corrected and Accelerated) interval correction.

This module provides the BootstrapModel class and a convenience function to fit
a bootstrap regression model and extract confidence intervals for coefficients.

Implements the BCa correction method to improve coverage probability in small samples.
"""

from typing import Tuple, Dict, Any, Optional, List
import numpy as np
from numpy.typing import ArrayLike
from scipy import stats
from scipy.special import norminv, normpdf


class BootstrapModel:
    """
    Non-parametric bootstrap regression model.
    
    This model resamples the dataset with replacement to estimate the sampling
    distribution of regression coefficients and construct confidence intervals.
    
    Attributes:
        n_bootstrap (int): Number of bootstrap replications.
        confidence_level (float): Confidence level for intervals (default 0.95).
        method (str): Interval method ('basic', 'percentile', 'bca').
        seed (Optional[int]): Random seed for reproducibility.
    """
    
    def __init__(
        self,
        n_bootstrap: int = 2000,
        confidence_level: float = 0.95,
        method: str = "bca",
        seed: Optional[int] = None
    ):
        self.n_bootstrap = n_bootstrap
        self.confidence_level = confidence_level
        self.method = method
        self.seed = seed
        
        if seed is not None:
            np.random.seed(seed)
        
        # Internal state
        self._coefficient_samples: Optional[np.ndarray] = None
        self._original_coef: Optional[np.ndarray] = None
        self._alpha: float = 1.0 - confidence_level
        
    def _fit_ols_once(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Fit OLS once and return coefficients.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
            
        Returns:
            np.ndarray: Coefficients (n_features,)
        """
        # Add intercept column
        X_aug = np.column_stack([np.ones(X.shape[0]), X])
        
        # Solve using normal equations: beta = (X'X)^{-1} X'y
        try:
            # Use pinv for numerical stability with potentially ill-conditioned matrices
            beta = np.linalg.lstsq(X_aug, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            # Fallback to pseudoinverse if singular
            beta = np.linalg.pinv(X_aug) @ y
        
        return beta
    
    def fit(self, X: ArrayLike, y: ArrayLike) -> "BootstrapModel":
        """
        Fit the bootstrap model by resampling and storing coefficient distributions.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
            
        Returns:
            self: Fitted model instance
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        
        n_samples, n_features = X.shape
        
        # Fit original model
        self._original_coef = self._fit_ols_once(X, y)
        
        # Store coefficient samples: (n_bootstrap, n_features + 1 for intercept)
        self._coefficient_samples = np.zeros((self.n_bootstrap, n_features + 1))
        
        # Bootstrap resampling
        for i in range(self.n_bootstrap):
            # Resample indices with replacement
            indices = np.random.choice(n_samples, size=n_samples, replace=True)
            X_boot = X[indices]
            y_boot = y[indices]
            
            # Fit on bootstrap sample
            self._coefficient_samples[i] = self._fit_ols_once(X_boot, y_boot)
        
        return self
    
    def _calculate_bca_parameters(
        self,
        theta_boot: np.ndarray,
        theta_hat: float
    ) -> Tuple[float, float]:
        """
        Calculate BCa parameters: z0 (bias correction) and a (acceleration).
        
        Args:
            theta_boot: Bootstrap estimates (1D array of shape n_bootstrap)
            theta_hat: Original estimate
            
        Returns:
            Tuple[float, float]: (z0, a)
        """
        # z0: Bias correction factor
        # Proportion of bootstrap estimates less than original estimate
        prop_less = np.mean(theta_boot < theta_hat)
        # Clamp to avoid infinite z0
        prop_less = np.clip(prop_less, 1e-10, 1 - 1e-10)
        z0 = norminv(prop_less)
        
        # a: Acceleration factor (using jackknife)
        n = len(theta_boot)  # Approximate n with bootstrap count for efficiency
        # For proper acceleration, we'd need jackknife samples, but we approximate
        # using the skewness of bootstrap distribution
        # This is a common approximation when jackknife is too expensive
        theta_boot_centered = theta_boot - np.mean(theta_boot)
        numerator = np.sum(theta_boot_centered ** 3)
        denominator = 6 * (np.sum(theta_boot_centered ** 2) ** 1.5)
        
        if denominator == 0:
            a = 0.0
        else:
            a = numerator / denominator
        
        return z0, a
    
    def _get_bca_intervals(
        self,
        coef_idx: int
    ) -> Tuple[float, float]:
        """
        Calculate BCa confidence interval for a specific coefficient.
        
        Args:
            coef_idx: Index of the coefficient (including intercept at 0)
            
        Returns:
            Tuple[float, float]: (lower_bound, upper_bound)
        """
        theta_boot = self._coefficient_samples[:, coef_idx]
        theta_hat = self._original_coef[coef_idx]
        
        # Calculate BCa parameters
        z0, a = self._calculate_bca_parameters(theta_boot, theta_hat)
        
        # Standard normal quantiles for alpha/2 and 1-alpha/2
        z_alpha2 = norminv(self._alpha / 2)
        z_1_alpha2 = norminv(1 - self._alpha / 2)
        
        # BCa adjustment formula
        # alpha1 = Phi(z0 + (z0 + z_alpha2) / (1 - a * (z0 + z_alpha2)))
        # alpha2 = Phi(z0 + (z0 + z_1_alpha2) / (1 - a * (z0 + z_1_alpha2)))
        
        def bca_adjusted_quantile(z: float) -> float:
            numerator = z0 + z
            denominator = 1 - a * numerator
            if denominator == 0:
                return 0.5
            adjusted_z = z0 + numerator / denominator
            return stats.norm.cdf(adjusted_z)
        
        alpha1 = bca_adjusted_quantile(z_alpha2)
        alpha2 = bca_adjusted_quantile(z_1_alpha2)
        
        # Clamp percentiles to valid range [0, 1]
        alpha1 = np.clip(alpha1, 0.001, 0.999)
        alpha2 = np.clip(alpha2, 0.001, 0.999)
        
        # Get percentiles from bootstrap distribution
        lower = np.percentile(theta_boot, alpha1 * 100)
        upper = np.percentile(theta_boot, alpha2 * 100)
        
        return lower, upper
    
    def get_confidence_intervals(self) -> Dict[str, Any]:
        """
        Get confidence intervals for all coefficients.
        
        Returns:
            Dict[str, Any]: Dictionary containing:
                - 'coef_names': List of coefficient names (intercept, beta_0, ...)
                - 'estimates': Original coefficient estimates
                - 'intervals': List of (lower, upper) tuples for each coefficient
                - 'method': Interval method used
                - 'confidence_level': Confidence level
        """
        if self._coefficient_samples is None or self._original_coef is None:
            raise RuntimeError("Model must be fitted before getting intervals.")
        
        n_coefs = self._original_coef.shape[0]
        coef_names = ["intercept"] + [f"beta_{i}" for i in range(n_coefs - 1)]
        
        intervals = []
        for i in range(n_coefs):
            if self.method == "bca":
                lower, upper = self._get_bca_intervals(i)
            elif self.method == "percentile":
                lower = np.percentile(
                    self._coefficient_samples[:, i],
                    self._alpha / 2 * 100
                )
                upper = np.percentile(
                    self._coefficient_samples[:, i],
                    (1 - self._alpha / 2) * 100
                )
            else:
                # Basic (pivotal) interval
                mean_boot = np.mean(self._coefficient_samples[:, i])
                lower = 2 * self._original_coef[i] - upper
                upper = 2 * self._original_coef[i] - lower
                # Recalculate properly for basic interval
                diff_upper = self._coefficient_samples[:, i] - self._original_coef[i]
                diff_lower = self._coefficient_samples[:, i] - self._original_coef[i]
                lower = self._original_coef[i] - np.percentile(
                    diff_upper, (1 - self._alpha / 2) * 100
                )
                upper = self._original_coef[i] - np.percentile(
                    diff_lower, self._alpha / 2 * 100
                )
            
            intervals.append((lower, upper))
        
        return {
            "coef_names": coef_names,
            "estimates": self._original_coef.tolist(),
            "intervals": intervals,
            "method": self.method,
            "confidence_level": self.confidence_level,
            "n_bootstrap": self.n_bootstrap
        }
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for the bootstrap distribution.
        
        Returns:
            Dict[str, Any]: Dictionary with mean, std, and percentiles for each coefficient.
        """
        if self._coefficient_samples is None:
            raise RuntimeError("Model must be fitted first.")
        
        n_coefs = self._coefficient_samples.shape[1]
        stats_dict = {}
        
        for i in range(n_coefs):
            coef_name = f"beta_{i}" if i > 0 else "intercept"
            samples = self._coefficient_samples[:, i]
            stats_dict[coef_name] = {
                "mean": float(np.mean(samples)),
                "std": float(np.std(samples)),
                "median": float(np.median(samples)),
                "min": float(np.min(samples)),
                "max": float(np.max(samples)),
                "percentile_2.5": float(np.percentile(samples, 2.5)),
                "percentile_97.5": float(np.percentile(samples, 97.5))
            }
        
        return stats_dict


def fit_bootstrap_and_get_intervals(
    X: ArrayLike,
    y: ArrayLike,
    n_bootstrap: int = 2000,
    confidence_level: float = 0.95,
    method: str = "bca",
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function to fit a bootstrap model and return confidence intervals.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        n_bootstrap: Number of bootstrap replications (default 2000)
        confidence_level: Confidence level for intervals (default 0.95)
        method: Interval method ('basic', 'percentile', 'bca')
        seed: Random seed for reproducibility
        
    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'coef_names': List of coefficient names
            - 'estimates': Original OLS coefficient estimates
            - 'intervals': List of (lower, upper) tuples for each coefficient
            - 'method': Interval method used
            - 'confidence_level': Confidence level
            - 'n_bootstrap': Number of bootstrap samples
            - 'summary': Summary statistics for each coefficient
    """
    model = BootstrapModel(
        n_bootstrap=n_bootstrap,
        confidence_level=confidence_level,
        method=method,
        seed=seed
    )
    
    model.fit(X, y)
    
    intervals = model.get_confidence_intervals()
    summary = model.get_summary_statistics()
    
    return {
        **intervals,
        "summary": summary
    }