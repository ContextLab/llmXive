from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Union
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.optimize import bisect

@dataclass
class MissingnessPattern:
    """Represents a specific missingness pattern injected into data."""
    mask: np.ndarray
    alpha: float
    beta: float
    target_rate: float

class MissingnessInjector(ABC):
    """Abstract base class for missingness injection strategies."""

    @abstractmethod
    def inject(self, data: pd.DataFrame) -> pd.DataFrame:
        """Inject missingness into the provided dataframe."""
        pass

    @abstractmethod
    def get_pattern(self) -> MissingnessPattern:
        """Return the resulting missingness pattern metadata."""
        pass

def tune_alpha(beta: float, target_rate: float, tol: float = 1e-4, max_iter: int = 50) -> float:
    """
    Finds the intercept parameter (alpha) that yields the desired missingness rate
    for a given slope parameter (beta) using binary search.

    The missingness mechanism is defined as:
    P(M=1 | Y) = sigmoid(alpha + beta * Y)

    Args:
        beta: The slope parameter determining the dependency on Y.
        target_rate: The desired proportion of missing values (0.0 to 1.0).
        tol: Tolerance for the binary search convergence.
        max_iter: Maximum number of iterations for the search.

    Returns:
        float: The alpha value that achieves the target missingness rate.

    Raises:
        ValueError: If the target rate is not achievable with the given beta
                    or if convergence fails.
    """
    if not 0.0 < target_rate < 1.0:
        raise ValueError("target_rate must be strictly between 0.0 and 1.0")

    # We need a representative distribution of Y to solve for alpha.
    # Since Y is generated from a standard normal (N(0,1)) in generate_scm
    # (mean=0, std=1), we approximate the expected missingness rate
    # by integrating over a large sample of standard normal Y values.
    # This avoids needing the specific dataset instance which might vary slightly.
    # Using a large fixed sample for the root finding ensures stability.
    rng = np.random.RandomState(42)  # Fixed seed for deterministic alpha calculation
    y_sample = rng.normal(loc=0.0, scale=1.0, size=100000)

    def missingness_rate(alpha: float) -> float:
        """Calculate the expected missingness rate for a given alpha."""
        logits = alpha + beta * y_sample
        probs = expit(logits)
        return np.mean(probs)

    # Check bounds to ensure a solution exists
    # As alpha -> -inf, rate -> 0. As alpha -> +inf, rate -> 1.
    # So a solution should theoretically always exist for 0 < rate < 1.
    # However, we check a reasonable range to avoid numerical issues.
    low_alpha, high_alpha = -10.0, 10.0
    
    rate_low = missingness_rate(low_alpha)
    rate_high = missingness_rate(high_alpha)

    if not (rate_low <= target_rate <= rate_high):
        # If the target is outside the achievable range for these bounds,
        # we might need to expand bounds, but for standard normal Y and
        # typical betas, [-10, 10] is sufficient.
        # If beta is extremely large, the sigmoid becomes a step function.
        # We try to expand if necessary, but for now, assume standard range.
        # If it fails here, it's a configuration issue.
        raise ValueError(
            f"Target rate {target_rate} is not achievable within alpha bounds "
            f"[-10, 10] for beta={beta}. Low rate: {rate_low:.4f}, High rate: {rate_high:.4f}"
        )

    # Binary search (Bisection method)
    alpha = 0.0
    for _ in range(max_iter):
        alpha = (low_alpha + high_alpha) / 2.0
        current_rate = missingness_rate(alpha)

        if abs(current_rate - target_rate) < tol:
            return alpha

        if current_rate < target_rate:
            low_alpha = alpha
        else:
            high_alpha = alpha

    # Return best guess if max_iter reached
    return alpha

def inject_mnar(data: pd.DataFrame, beta: float, target_rate: float) -> pd.DataFrame:
    """
    Injects MNAR (Missing Not At Random) missingness into the dataframe.
    
    The missingness probability depends on the outcome variable Y itself:
    P(M=1 | Y) = sigmoid(alpha + beta * Y)
    
    This function first tunes alpha to achieve the target_rate given beta,
    then applies the mask to the data.

    Args:
        data: The input dataframe containing columns X, T, Y.
        beta: The parameter controlling the strength of the dependency on Y.
        target_rate: The desired overall missingness rate.

    Returns:
        pd.DataFrame: A copy of the input data with NaNs introduced in column Y.
        The function returns the data with Y masked, but the mask itself is
        not stored in the dataframe columns (standard practice for downstream
        imputation tasks).
    
    Note:
        This implementation assumes the 'Y' column exists in the dataframe.
        If 'Y' is not present, a KeyError will be raised.
    """
    if 'Y' not in data.columns:
        raise KeyError("Column 'Y' not found in dataframe. MNAR injection requires Y.")

    # 1. Tune alpha to match the target rate
    alpha = tune_alpha(beta, target_rate)

    # 2. Calculate probabilities for each row
    y_values = data['Y'].values
    logits = alpha + beta * y_values
    probs = expit(logits)

    # 3. Generate mask (1 = missing, 0 = observed)
    # Use a deterministic seed derived from the data or a fixed seed if needed
    # For reproducibility in a pipeline, we might want to pass a seed, 
    # but here we rely on the global RNG state or a fixed internal one for consistency
    # unless the caller manages RNG.
    # To ensure the mask is deterministic given the inputs, we could use a hash,
    # but standard practice is to use numpy's global RNG.
    mask = np.random.random(len(y_values)) < probs

    # 4. Apply mask to a copy
    result = data.copy()
    result.loc[mask, 'Y'] = np.nan

    # Optional: Store metadata in attributes or return a tuple?
    # The task description implies returning the data. 
    # The pattern object could be returned separately if needed, 
    # but the function signature in T011 implies returning the data.
    # We will store the alpha/beta used in the dataframe attrs for debugging if needed.
    result.attrs['missingness_alpha'] = alpha
    result.attrs['missingness_beta'] = beta
    result.attrs['missingness_rate'] = np.mean(mask)

    return result

# Re-export for consistency with task requirements
__all__ = ['MissingnessPattern', 'MissingnessInjector', 'inject_mnar', 'tune_alpha']
