"""
Missingness Injection Module for MNAR Simulation.

This module provides classes and functions to inject Missing Not At Random (MNAR)
patterns into synthetic datasets. The core mechanism relies on the outcome variable Y,
making the missingness dependent on the unobserved values themselves.

IMPORTANT: Ground Truth and Identifiability
------------------------------------------
In this simulation framework, "ground truth" refers to the *generative parameters*
(specifically the true Average Treatment Effect, tau_true, and the MNAR parameter beta)
used to create the dataset.

CRITICAL WARNING: The causal effect (ATE) is NOT identifiable from the observed data
alone when MNAR mechanisms are active. The missingness mechanism M is a function of Y,
which introduces selection bias that standard imputation methods cannot fully correct
without strong, untestable assumptions. The "ground truth" ATE is known only because
we generated the data with a known structural equation model (SEM). In a real-world
observational study with potential MNAR, this ground truth would be unknown and the
estimates derived from incomplete data would be biased.

This simulation allows us to quantify that bias by comparing estimates from incomplete
data against the known generative parameter.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Union, Tuple, Dict, Any
import numpy as np
import pandas as pd
from scipy.special import expit
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

@dataclass
class MissingnessPattern:
    """
    Dataclass representing a specific missingness pattern.
    
    Attributes:
        mask: Boolean array where True indicates missing values.
        alpha: Intercept parameter for the logistic missingness model.
        beta: Slope parameter for the logistic missingness model (sensitivity parameter).
        target_rate: The desired proportion of missing values.
    """
    mask: np.ndarray
    alpha: float
    beta: float
    target_rate: float

class MissingnessInjector(ABC):
    """Abstract base class for missingness injection strategies."""

    @abstractmethod
    def inject(self, data: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, MissingnessPattern]:
        """
        Inject missingness into the provided data.
        
        Args:
            data: The input dataframe.
            **kwargs: Additional parameters specific to the injection strategy.
        
        Returns:
            A tuple containing the modified dataframe with NaNs and the MissingnessPattern object.
        """
        pass

def tune_alpha(beta: float, target_rate: float, n_iterations: int = 100) -> float:
    """
    Find the alpha parameter that yields the desired missingness rate for a given beta.
    
    This function performs a binary search to find the intercept (alpha) such that
    the probability of missingness, P(M=1 | Y), averages to the target_rate.
    
    Args:
        beta: The slope parameter (sensitivity to Y).
        target_rate: The desired proportion of missing values (0.0 to 1.0).
        n_iterations: Number of iterations for the binary search.
        
    Returns:
        The alpha value that achieves the target missingness rate.
    """
    if not 0.0 < target_rate < 1.0:
        raise ValueError("target_rate must be between 0 and 1 (exclusive).")
    
    # We need a reference distribution for Y to tune alpha.
    # Since Y ~ N(tau_true * T, sigma^2) and T is binary, Y is roughly normal centered around 0 or tau.
    # We assume a standard normal approximation for tuning purposes.
    # P(M=1) = E[expit(alpha + beta * Y)] = target_rate
    # If Y ~ N(0, 1), then we solve for alpha.
    
    # Binary search bounds for alpha
    low, high = -10.0, 10.0
    best_alpha = 0.0
    
    # Use a large sample for estimation during tuning
    n_samples = 10000
    y_sample = np.random.normal(0, 1, n_samples)
    
    for _ in range(n_iterations):
        mid = (low + high) / 2
        # Calculate probability of missingness for the sample
        probs = expit(mid + beta * y_sample)
        current_rate = np.mean(probs)
        
        if abs(current_rate - target_rate) < 1e-4:
            return mid
        
        if current_rate < target_rate:
            low = mid
        else:
            high = mid
    
    return (low + high) / 2

def inject_mnar(
    data: pd.DataFrame,
    beta: float,
    target_rate: float,
    outcome_col: str = 'Y',
    seed: Optional[int] = None
) -> Tuple[pd.DataFrame, MissingnessPattern]:
    """
    Inject MNAR missingness into the outcome variable Y based on a logistic model.
    
    The probability of missingness is modeled as:
    P(M=1 | Y) = expit(alpha + beta * Y)
    
    Where:
    - M is the missingness indicator (1 = missing)
    - Y is the outcome variable
    - alpha is the intercept (tuned to achieve target_rate)
    - beta is the sensitivity parameter (strength of MNAR mechanism)
    
    Args:
        data: The input dataframe containing the outcome variable.
        beta: The MNAR sensitivity parameter.
        target_rate: The desired overall missingness rate.
        outcome_col: Name of the column to apply missingness to (default 'Y').
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (modified dataframe with NaNs, MissingnessPattern object).
        
    Raises:
        ValueError: If the outcome column is not found or beta is invalid.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if outcome_col not in data.columns:
        raise ValueError(f"Outcome column '{outcome_col}' not found in data.")
    
    y_values = data[outcome_col].values
    
    # Tune alpha to achieve target_rate
    alpha = tune_alpha(beta, target_rate)
    
    # Calculate probability of missingness
    log_odds = alpha + beta * y_values
    p_missing = expit(log_odds)
    
    # Generate mask
    mask = np.random.random(len(y_values)) < p_missing
    
    # Create missingness pattern object
    pattern = MissingnessPattern(
        mask=mask,
        alpha=alpha,
        beta=beta,
        target_rate=target_rate
    )
    
    # Apply mask to create NaNs
    result_data = data.copy()
    result_data.loc[mask, outcome_col] = np.nan
    
    logger.info(
        f"Injected MNAR missingness: beta={beta:.3f}, alpha={alpha:.3f}, "
        f"target_rate={target_rate:.3f}, achieved_rate={np.mean(mask):.3f}"
    )
    
    return result_data, pattern