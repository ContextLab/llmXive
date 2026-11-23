"""
Bootstrap model implementation for non-parametric uncertainty quantification.
Implements BCa (Bias-Corrected and Accelerated) interval correction.
"""
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
from numpy.typing import ArrayLike
from scipy import stats
from scipy.special import norminv, normpdf

class BootstrapModel:
    """
    Non-parametric bootstrap regression model with BCa confidence intervals.
    
    Attributes:
        n_bootstrap: Number of bootstrap replications
        confidence_level: Confidence level for intervals (default 0.95)
        random_state: Seed for reproducibility
    """
    
    def __init__(
        self,
        n_bootstrap: int = 2000,
        confidence_level: float = 0.95,
        random_state: Optional[int] = None
    ):
        self.n_bootstrap = n_bootstrap
        self.confidence_level = confidence_level
        self.random_state = random_state
        self.rng = np.random.default_rng(random_state)
        
    def _fit_ols(self, X: ArrayLike, y: ArrayLike) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit OLS regression and return coefficients and residuals.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
            
        Returns:
            Tuple of (coefficients, residuals)
        """
        X = np.asarray(X)
        y = np.asarray(y)
        
        # Add intercept column
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
        
        # Solve using least squares
        try:
            coeffs, residuals, rank, s = np.linalg.lstsq(
                X_with_intercept, y, rcond=None
            )
        except np.linalg.LinAlgError:
            # Handle rank-deficient case
            coeffs = np.zeros(X_with_intercept.shape[1])
            residuals = np.array([0.0])
        
        # Calculate residuals for BCa acceleration
        fitted = X_with_intercept @ coeffs
        residuals = y - fitted
        
        return coeffs, residuals
    
    def _calculate_bca_params(
        self,
        theta_hat: np.ndarray,
        theta_boot: np.ndarray,
        residuals: np.ndarray,
        X: ArrayLike
    ) -> Tuple[float, float, float]:
        """
        Calculate BCa parameters: bias correction (z0), acceleration (a), and alpha.
        
        Args:
            theta_hat: Original estimate
            theta_boot: Bootstrap estimates
            residuals: Residuals from original fit
            X: Feature matrix
            
        Returns:
            Tuple of (z0, a, alpha)
        """
        # Bias correction (z0)
        prop_less = np.mean(theta_boot < theta_hat)
        z0 = norminv(prop_less)
        
        # Acceleration (a) using jackknife
        n = len(residuals)
        p = X.shape[1] if len(X.shape) > 1 else 1
        
        # Use a simplified acceleration calculation based on skewness of residuals
        # This is a common approximation when full jackknife is computationally expensive
        skewness = stats.skew(residuals)
        a = skewness / (6 * np.sqrt(n))
        
        # Alpha level
        alpha = 1 - self.confidence_level
        
        return z0, a, alpha
    
    def _calculate_bca_intervals(
        self,
        theta_hat: np.ndarray,
        theta_boot: np.ndarray,
        residuals: np.ndarray,
        X: ArrayLike
    ) -> np.ndarray:
        """
        Calculate BCa confidence intervals for each coefficient.
        
        Args:
            theta_hat: Original coefficient estimates
            theta_boot: Bootstrap coefficient estimates (n_bootstrap, n_coeffs)
            residuals: Residuals from original fit
            X: Feature matrix
            
        Returns:
            Array of shape (n_coeffs, 2) with [lower, upper] bounds
        """
        n_coeffs = len(theta_hat)
        intervals = np.zeros((n_coeffs, 2))
        
        z0, a, alpha = self._calculate_bca_params(
            theta_hat, theta_boot[:, 0], residuals, X
        )  # Use first coefficient for z0 calculation as approximation
        
        # Calculate BCa adjusted percentiles for each coefficient
        for i in range(n_coeffs):
            theta_boot_i = theta_boot[:, i]
            
            # Bias correction for this coefficient
            prop_less = np.mean(theta_boot_i < theta_hat[i])
            z0_i = norminv(prop_less)
            
            # Adjusted percentiles
            z_alpha_1 = norminv(alpha / 2)
            z_alpha_2 = norminv(1 - alpha / 2)
            
            # BCa adjustment formula
            if abs(a) < 1e-10:
                # If acceleration is near zero, use standard percentile
                lower_idx = int(np.floor((alpha / 2) * self.n_bootstrap))
                upper_idx = int(np.ceil((1 - alpha / 2) * self.n_bootstrap))
            else:
                # Full BCa calculation
                num1 = z0_i + z_alpha_1
                den1 = 1 - a * num1
                z1 = z0_i + num1 / den1
                
                num2 = z0_i + z_alpha_2
                den2 = 1 - a * num2
                z2 = z0_i + num2 / den2
                
                lower_idx = int(np.floor(stats.norm.cdf(z1) * self.n_bootstrap))
                upper_idx = int(np.ceil(stats.norm.cdf(z2) * self.n_bootstrap))
            
            # Ensure indices are within bounds
            lower_idx = max(0, min(lower_idx, self.n_bootstrap - 1))
            upper_idx = max(0, min(upper_idx, self.n_bootstrap - 1))
            
            # Sort bootstrap estimates and get percentiles
            sorted_boot = np.sort(theta_boot_i)
            intervals[i, 0] = sorted_boot[lower_idx]
            intervals[i, 1] = sorted_boot[upper_idx]
        
        return intervals
    
    def fit(
        self,
        X: ArrayLike,
        y: ArrayLike,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fit the bootstrap model and return coefficients with BCa intervals.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
            seed: Optional seed for reproducibility
            
        Returns:
            Dictionary containing:
                - coefficients: Original OLS estimates
                - intervals: BCa confidence intervals
                - bootstrap_means: Mean of bootstrap estimates
                - bootstrap_std: Standard deviation of bootstrap estimates
                - n_bootstrap: Number of bootstrap samples used
        """
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        
        X = np.asarray(X)
        y = np.asarray(y)
        
        n_samples, n_features = X.shape
        
        # Fit original model
        theta_hat, residuals = self._fit_ols(X, y)
        
        # Store intercept in coefficients (first element)
        coefficients = theta_hat[1:] if len(theta_hat) > 1 else np.array([])
        intercept = theta_hat[0] if len(theta_hat) > 1 else 0.0
        
        # Generate bootstrap samples
        theta_boot_list = []
        
        for _ in range(self.n_bootstrap):
            # Resample indices with replacement
            indices = self.rng.integers(0, n_samples, size=n_samples)
            X_boot = X[indices]
            y_boot = y[indices]
            
            # Fit bootstrap model
            theta_boot, _ = self._fit_ols(X_boot, y_boot)
            theta_boot_list.append(theta_boot)
        
        theta_boot = np.array(theta_boot_list)
        
        # Calculate BCa intervals
        bca_intervals = self._calculate_bca_intervals(
            theta_hat, theta_boot, residuals, np.column_stack([np.ones(n_samples), X])
        )
        
        # Extract intervals for coefficients (excluding intercept)
        if len(coefficients) > 0:
            coef_intervals = bca_intervals[1:, :]
        else:
            coef_intervals = np.array([]).reshape(0, 2)
        
        # Calculate bootstrap statistics
        bootstrap_means = np.mean(theta_boot, axis=0)
        bootstrap_std = np.std(theta_boot, axis=0)
        
        return {
            'coefficients': coefficients,
            'intercept': intercept,
            'intervals': coef_intervals,
            'bootstrap_means': bootstrap_means[1:] if len(bootstrap_means) > 1 else np.array([]),
            'bootstrap_std': bootstrap_std[1:] if len(bootstrap_std) > 1 else np.array([]),
            'n_bootstrap': self.n_bootstrap,
            'confidence_level': self.confidence_level
        }


def fit_bootstrap_and_get_intervals(
    X: ArrayLike,
    y: ArrayLike,
    n_bootstrap: int = 2000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function to fit bootstrap model and return intervals.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        n_bootstrap: Number of bootstrap replications
        confidence_level: Confidence level for intervals
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with coefficients and BCa confidence intervals
    """
    model = BootstrapModel(
        n_bootstrap=n_bootstrap,
        confidence_level=confidence_level,
        random_state=seed
    )
    return model.fit(X, y, seed=seed)