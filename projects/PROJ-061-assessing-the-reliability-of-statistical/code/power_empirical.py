import numpy as np
from typing import Dict, Any, List, Tuple
from scipy import stats
import logging
import os
from config import RANDOM_SEED, BOOTSTRAP_ITERATIONS
from utils import handle_missing_values

logger = logging.getLogger(__name__)

def run_bootstrap_power_simulation(
    data: Dict[str, Any], 
    n_iterations: int = BOOTSTRAP_ITERATIONS,
    alpha: float = 0.05,
    treatment_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run bootstrap simulation to estimate empirical power.
    
    This function performs listwise deletion on missing values before calculation,
    then uses bootstrap resampling to estimate the probability of rejecting the null hypothesis.
    
    Args:
        data: Dictionary containing 'X' (features), 'y' (outcome), and optionally 'treatment'.
        n_iterations: Number of bootstrap iterations.
        alpha: Significance level.
        treatment_col: Key name for treatment if data is list of dicts.
    
    Returns:
        Dictionary with 'empirical_power', 'n_samples', 'n_iterations', etc.
    """
    # 1. Handle missing values via listwise deletion
    logger.info("Handling missing values via listwise deletion...")
    clean_data = handle_missing_values(data, outcome_col='y', treatment_col=treatment_col)
    
    X = clean_data['X']
    y = clean_data['y']
    treatment = clean_data.get('treatment')
    
    n_samples = len(y)
    if n_samples < 30:
        logger.warning(f"Sample size {n_samples} is too small for reliable power estimation.")
        return {
            'empirical_power': None,
            'n_samples': n_samples,
            'n_iterations': n_iterations,
            'status': 'insufficient_sample_size'
        }
    
    # If treatment is not provided, assume it's the last column of X or handle as needed
    # For a two-sample t-test, we need a binary treatment vector.
    # If not provided, we might need to infer or raise an error.
    # Assuming the caller ensures 'treatment' is in clean_data if needed.
    if treatment is None:
        # Fallback: assume treatment is the last column of X if X is 2D
        if isinstance(X, list) and len(X) > 0 and isinstance(X[0], (list, np.ndarray)):
            treatment = [row[-1] for row in X]
            X = [row[:-1] for row in X] # Remove treatment from features if it was included
        else:
            raise ValueError("Treatment vector is required for power calculation and not found.")
    
    # Convert to numpy arrays
    y = np.array(y)
    treatment = np.array(treatment)
    
    # Ensure treatment is binary (0/1)
    unique_t = np.unique(treatment)
    if len(unique_t) != 2:
        logger.warning(f"Non-binary treatment detected: {unique_t}. Attempting to binarize.")
        # Simple binarization: map to 0 and 1 based on sorted unique values
        mapping = {val: i for i, val in enumerate(sorted(unique_t))}
        treatment = np.array([mapping[t] for t in treatment])
    
    # Separate groups
    group0 = y[treatment == 0]
    group1 = y[treatment == 1]
    
    if len(group0) < 2 or len(group1) < 2:
        logger.warning("One of the groups has insufficient samples for t-test.")
        return {
            'empirical_power': None,
            'n_samples': n_samples,
            'n_iterations': n_iterations,
            'status': 'insufficient_group_size'
        }
    
    # Calculate observed effect size (Cohen's d)
    mean0, mean1 = np.mean(group0), np.mean(group1)
    std0, std1 = np.std(group0, ddof=1), np.std(group1, ddof=1)
    pooled_std = np.sqrt(((len(group0)-1)*std0**2 + (len(group1)-1)*std1**2) / (len(group0)+len(group1)-2))
    cohens_d = (mean1 - mean0) / pooled_std
    
    logger.info(f"Observed Cohen's d: {cohens_d:.4f}")
    
    # Bootstrap simulation
    rejections = 0
    for i in range(n_iterations):
        # Resample with replacement
        idx0 = np.random.choice(len(group0), size=len(group0), replace=True)
        idx1 = np.random.choice(len(group1), size=len(group1), replace=True)
        
        boot_group0 = group0[idx0]
        boot_group1 = group1[idx1]
        
        # Perform t-test
        try:
            t_stat, p_val = stats.ttest_ind(boot_group1, boot_group0, equal_var=True)
            if p_val < alpha:
                rejections += 1
        except Exception as e:
            logger.debug(f"Bootstrap iteration {i} failed: {e}")
            continue
    
    empirical_power = rejections / n_iterations
    
    return {
        'empirical_power': empirical_power,
        'n_samples': n_samples,
        'n_iterations': n_iterations,
        'observed_cohens_d': cohens_d,
        'rejections': rejections,
        'status': 'success'
    }
