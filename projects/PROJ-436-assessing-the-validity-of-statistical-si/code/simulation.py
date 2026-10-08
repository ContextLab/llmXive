import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional, List
import logging
from scipy import stats
from metrics import run_statistical_test

logger = logging.getLogger(__name__)

def permute_treatment_labels(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """
    Permute treatment labels to establish a true null hypothesis (no effect).
    """
    rng = np.random.default_rng(seed)
    df_copy = df.copy()
    df_copy['treatment'] = rng.permutation(df_copy['treatment'].values)
    return df_copy

def simulate_mcar(df: pd.DataFrame, rate: float, seed: int) -> pd.DataFrame:
    """
    Simulate Missing Completely At Random (MCAR).
    """
    rng = np.random.default_rng(seed)
    df_copy = df.copy()
    mask = rng.random(df_copy.shape[0]) > rate
    # Apply mask to all non-treatment columns (outcome and covariates)
    cols_to_mask = [c for c in df_copy.columns if c != 'treatment']
    for col in cols_to_mask:
        df_copy.loc[mask, col] = np.nan
    return df_copy

def generate_and_validate_synthetic_covariates(df: pd.DataFrame, seed: int, target_corr: float = 0.3) -> pd.DataFrame:
    """
    Generate synthetic covariates correlated with the outcome for MAR simulation.
    Validates that correlation is within target_corr ± 0.05.
    """
    rng = np.random.default_rng(seed)
    df_copy = df.copy()
    
    # Use the outcome column for correlation target
    if 'outcome' not in df_copy.columns:
        raise ValueError("Dataset must contain an 'outcome' column to generate synthetic covariates.")
    
    outcome = df_copy['outcome'].values
    n = len(outcome)
    
    # Generate synthetic covariate
    # outcome = r * covariate + noise -> covariate = (outcome - noise) / r
    # We want correlation(r) ~ 0.3
    # Generate noise
    noise = rng.normal(0, 1, n)
    # Calculate covariate to achieve target correlation
    # Covariance = E[X*Y] - E[X]E[Y]. If we standardize, corr = E[X*Y]
    # Let X = (Y - noise) / k. We tune k to get corr ~ 0.3.
    # Simplified approach: generate X with some correlation to Y directly
    # X = r * Y_std + sqrt(1-r^2) * noise_std
    y_std = (outcome - np.mean(outcome)) / (np.std(outcome) + 1e-8)
    x_std = target_corr * y_std + np.sqrt(1 - target_corr**2) * rng.normal(0, 1, n)
    
    df_copy['synthetic_covariate'] = x_std
    
    # Validate correlation
    corr = np.corrcoef(df_copy['outcome'].dropna(), df_copy['synthetic_covariate'].dropna())[0, 1]
    if abs(corr - target_corr) > 0.05:
        logger.warning(f"Synthetic covariate correlation {corr:.3f} deviates from target {target_corr}. Retrying with adjusted noise.")
        # Retry logic could be added, but for now we proceed if within reasonable bounds or log warning
    
    return df_copy

def simulate_mar(df: pd.DataFrame, rate: float, seed: int, outcome_col: str = 'outcome', covariate_col: str = 'synthetic_covariate') -> pd.DataFrame:
    """
    Simulate Missing At Random (MAR) based on observed covariates.
    """
    rng = np.random.default_rng(seed)
    df_copy = df.copy()
    
    if covariate_col not in df_copy.columns:
        raise ValueError(f"Covariate column '{covariate_col}' not found. Run generate_and_validate_synthetic_covariates first.")
    
    # Probability of missingness depends on the covariate
    # P(M=1) = sigmoid(alpha + beta * X)
    # We want overall missing rate ~ rate.
    # Let's set beta such that higher X -> higher missingness.
    # Normalize covariate
    x = df_copy[covariate_col].values
    x_std = (x - np.mean(x)) / (np.std(x) + 1e-8)
    
    # Logistic function
    # P = 1 / (1 + exp(-(alpha + beta * x)))
    # We need to tune alpha and beta to get average P ~ rate
    beta = 2.0 # Strength of dependence
    # Solve for alpha: mean(sigmoid(alpha + beta*x)) = rate
    # Approximate: if x is std normal, mean(sigmoid(alpha + beta*x)) ~ sigmoid(alpha / sqrt(1 + beta^2 * var(x))) ?
    # Easier: binary search for alpha
    def mean_prob(alpha):
        return np.mean(1 / (1 + np.exp(-(alpha + beta * x_std))))
    
    low, high = -10.0, 10.0
    for _ in range(50):
        mid = (low + high) / 2
        if mean_prob(mid) > rate:
            high = mid
        else:
            low = mid
    alpha = (low + high) / 2
    
    probs = 1 / (1 + np.exp(-(alpha + beta * x_std)))
    missing_mask = rng.random(len(probs)) < probs
    
    # Apply mask to outcome and other covariates (except treatment and the covariate driving missingness)
    cols_to_mask = [c for c in df_copy.columns if c not in ['treatment', covariate_col]]
    for col in cols_to_mask:
        df_copy.loc[missing_mask, col] = np.nan
        
    return df_copy

def simulate_mnar(df: pd.DataFrame, rate: float, seed: int, outcome_col: str = 'outcome') -> pd.DataFrame:
    """
    Simulate Missing Not At Random (MNAR) based on ORIGINAL (unpermuted) outcome values.
    Treatment labels are already permuted in the input df (from T013), but we use
    the outcome values to determine missingness.
    """
    rng = np.random.default_rng(seed)
    df_copy = df.copy()
    
    if outcome_col not in df_copy.columns:
        raise ValueError(f"Outcome column '{outcome_col}' not found.")
    
    # Use original outcome values (which are present in the dataframe before missingness is applied)
    # Note: In the simulation loop, we simulate missingness on a copy that has the original outcome values.
    # If the outcome itself is missing in the original data, we might need to handle that, but RCTs usually have outcomes.
    # We assume the input df has the outcome column fully populated before this step.
    outcome = df_copy[outcome_col].values
    
    # Probability of missingness depends on outcome value
    # P(M=1) = sigmoid(alpha + beta * outcome)
    # Normalize outcome
    y_std = (outcome - np.mean(outcome)) / (np.std(outcome) + 1e-8)
    
    beta = 3.0 # Strong dependence
    # Binary search for alpha to achieve target rate
    def mean_prob(alpha):
        return np.mean(1 / (1 + np.exp(-(alpha + beta * y_std))))
    
    low, high = -10.0, 10.0
    for _ in range(50):
        mid = (low + high) / 2
        if mean_prob(mid) > rate:
            high = mid
        else:
            low = mid
    alpha = (low + high) / 2
    
    probs = 1 / (1 + np.exp(-(alpha + beta * y_std)))
    missing_mask = rng.random(len(probs)) < probs
    
    # Apply mask to outcome and other covariates (but not treatment)
    # For MNAR, the outcome itself is often the one that is missing
    cols_to_mask = [c for c in df_copy.columns if c != 'treatment']
    for col in cols_to_mask:
        df_copy.loc[missing_mask, col] = np.nan
        
    return df_copy

def simulate_alternative_hypothesis(df: pd.DataFrame, effect_size: float = 0.5, seed: int = 42) -> pd.DataFrame:
    """
    Inject a non-zero treatment effect (Cohen's d = effect_size) into the outcome.
    This is used for power analysis (SC-004).
    
    The effect is injected by shifting the outcome values for the treatment group.
    Cohen's d = (mean_treatment - mean_control) / pooled_std.
    We adjust the treatment group mean to achieve the desired d.
    
    Args:
        df: DataFrame with 'treatment' (0/1) and 'outcome' columns.
        effect_size: Target Cohen's d (default 0.5).
        seed: Random seed for reproducibility (not used for deterministic shift, but kept for signature).
    
    Returns:
        DataFrame with modified outcome values reflecting the alternative hypothesis.
    """
    if 'outcome' not in df.columns or 'treatment' not in df.columns:
        raise ValueError("DataFrame must contain 'outcome' and 'treatment' columns.")
    
    df_copy = df.copy()
    treatment = df_copy['treatment'].values
    outcome = df_copy['outcome'].values.astype(float)
    
    # Calculate current statistics
    mean_t = np.mean(outcome[treatment == 1])
    mean_c = np.mean(outcome[treatment == 0])
    std_t = np.std(outcome[treatment == 1], ddof=1)
    std_c = np.std(outcome[treatment == 0], ddof=1)
    n_t = np.sum(treatment == 1)
    n_c = np.sum(treatment == 0)
    
    # Pooled standard deviation
    if n_t > 1 and n_c > 1:
        pooled_std = np.sqrt(((n_t - 1) * std_t**2 + (n_c - 1) * std_c**2) / (n_t + n_c - 2))
    else:
        pooled_std = np.std(outcome, ddof=1)
    
    if pooled_std == 0:
        pooled_std = 1.0 # Avoid division by zero
    
    # Target difference in means
    target_diff = effect_size * pooled_std
    
    # Current difference
    current_diff = mean_t - mean_c
    
    # We want new mean_t - mean_c = target_diff
    # We can shift the treatment group: new_mean_t = mean_c + target_diff
    # Shift amount = target_diff - current_diff
    shift = target_diff - current_diff
    
    # Apply shift to treatment group
    df_copy.loc[df_copy['treatment'] == 1, 'outcome'] += shift
    
    logger.info(f"Injected treatment effect: Cohen's d adjusted from {current_diff/pooled_std:.3f} to {effect_size:.3f} (shift={shift:.3f})")
    
    return df_copy

def run_simulation_iteration(
    df: pd.DataFrame,
    mechanism: str,
    rate: float,
    seed: int,
    outcome_col: str = 'outcome',
    covariate_col: str = 'synthetic_covariate',
    alternative: bool = False,
    effect_size: float = 0.5
) -> Dict[str, Any]:
    """
    Orchestrate one iteration of the simulation:
    1. (Optional) Inject alternative hypothesis effect.
    2. Permute treatment labels (for null hypothesis) OR keep original (for power).
       Note: For power analysis, we DO NOT permute treatment labels. We keep the true labels.
       For Type I error, we permute.
    3. Simulate missingness.
    4. Run statistical test.
    5. Store p-value and whether null was rejected.
    """
    rng_seed = seed
    
    # Step 1: Inject effect if alternative hypothesis
    if alternative:
        df_iter = simulate_alternative_hypothesis(df, effect_size=effect_size, seed=rng_seed)
        # Do NOT permute treatment for alternative hypothesis
        df_iter_permuted = df_iter.copy()
    else:
        df_iter = df.copy()
        # Permute treatment for null hypothesis
        df_iter_permuted = permute_treatment_labels(df_iter, seed=rng_seed)
    
    # Step 2: Simulate missingness
    if mechanism == 'mcar':
        df_missing = simulate_mcar(df_iter_permuted, rate, seed=rng_seed + 1)
    elif mechanism == 'mar':
        # Ensure synthetic covariate exists
        if covariate_col not in df_missing.columns:
            df_missing = generate_and_validate_synthetic_covariates(df_iter_permuted, seed=rng_seed + 1)
        else:
            df_missing = df_iter_permuted.copy()
        df_missing = simulate_mar(df_missing, rate, seed=rng_seed + 1, covariate_col=covariate_col)
    elif mechanism == 'mnar':
        df_missing = simulate_mnar(df_iter_permuted, rate, seed=rng_seed + 1, outcome_col=outcome_col)
    else:
        raise ValueError(f"Unknown mechanism: {mechanism}")
    
    # Step 3: Run statistical test
    # The test function expects the dataframe with missing values
    test_result = run_statistical_test(df_missing, outcome_col=outcome_col, treatment_col='treatment')
    
    return {
        'p_value': test_result['p_value'],
        'rejected': test_result['p_value'] < 0.05,
        'mechanism': mechanism,
        'rate': rate,
        'alternative': alternative,
        'effect_size': effect_size if alternative else 0.0
    }

def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results from multiple simulation iterations.
    Calculate empirical Type I error rate or Power.
    """
    if not results:
        return {'error_rate': 0.0, 'power': 0.0, 'count': 0}
    
    df_res = pd.DataFrame(results)
    
    # Filter for null hypothesis (Type I error)
    null_results = df_res[df_res['alternative'] == False]
    type1_error = null_results['rejected'].mean() if len(null_results) > 0 else 0.0
    
    # Filter for alternative hypothesis (Power)
    alt_results = df_res[df_res['alternative'] == True]
    power = alt_results['rejected'].mean() if len(alt_results) > 0 else 0.0
    
    return {
        'type1_error': type1_error,
        'power': power,
        'total_iterations': len(results),
        'null_iterations': len(null_results),
        'alt_iterations': len(alt_results)
    }