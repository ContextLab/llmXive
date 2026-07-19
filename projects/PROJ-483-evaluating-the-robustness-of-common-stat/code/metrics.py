import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Optional
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import os
import json
import pandas as pd

def clopper_pearson_ci(successes: int, trials: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate the Clopper-Pearson exact confidence interval for a binomial proportion.

    Args:
        successes: Number of observed successes (significant tests).
        trials: Total number of trials (replications).
        alpha: Significance level for the confidence interval (default 0.05 for 95% CI).

    Returns:
        A tuple (lower_bound, upper_bound).
    """
    if trials == 0:
        return 0.0, 0.0
    if successes == 0:
        lower = 0.0
    else:
        lower = stats.beta.ppf(alpha / 2, successes, trials - successes + 1)
    
    if successes == trials:
        upper = 1.0
    else:
        upper = stats.beta.ppf(1 - alpha / 2, successes + 1, trials - successes)
    
    return lower, upper

def calculate_type1_error(p_values: List[float], alpha: float = 0.05) -> Tuple[float, float, float]:
    """
    Calculate Type I error rate and its Clopper-Pearson confidence interval.

    Args:
        p_values: List of p-values from hypothesis tests under the true null.
        alpha: Nominal significance level.

    Returns:
        Tuple of (observed_error_rate, lower_ci, upper_ci).
    """
    if not p_values:
        return 0.0, 0.0, 0.0
    
    successes = sum(1 for p in p_values if p < alpha)
    trials = len(p_values)
    
    observed_rate = successes / trials
    lower, upper = clopper_pearson_ci(successes, trials, alpha=0.05)
    
    return observed_rate, lower, upper

def calculate_power(p_values: List[float], alpha: float = 0.05) -> Tuple[float, float, float]:
    """
    Calculate statistical power (proportion of rejections under alternative) 
    and its Clopper-Pearson confidence interval.

    Args:
        p_values: List of p-values from hypothesis tests under the alternative hypothesis.
        alpha: Nominal significance level.

    Returns:
        Tuple of (observed_power, lower_ci, upper_ci).
    """
    if not p_values:
        return 0.0, 0.0, 0.0
    
    successes = sum(1 for p in p_values if p < alpha)
    trials = len(p_values)
    
    observed_power = successes / trials
    lower, upper = clopper_pearson_ci(successes, trials, alpha=0.05)
    
    return observed_power, lower, upper

def calculate_chi_squared_error_rate(p_values: List[float], alpha: float = 0.05) -> Tuple[float, float, float]:
    """
    Calculate error rate for Chi-squared tests (same logic as Type I error).
    Included for semantic clarity in aggregation pipelines.

    Args:
        p_values: List of p-values from Chi-squared tests.
        alpha: Nominal significance level.

    Returns:
        Tuple of (observed_error_rate, lower_ci, upper_ci).
    """
    return calculate_type1_error(p_values, alpha)

def aggregate_chi_squared_results(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Aggregate Chi-squared results from a raw results dataframe.

    Args:
        results_df: DataFrame containing columns 'p_value', 'dependency_strength', etc.
        alpha: Nominal significance level.

    Returns:
        DataFrame with aggregated error rates and CIs per dependency strength.
    """
    if results_df.empty:
        return pd.DataFrame()
    
    # Group by dependency strength
    grouped = results_df.groupby('dependency_strength')['p_value'].apply(list).reset_index()
    
    aggregated = []
    for _, row in grouped.iterrows():
        strength = row['dependency_strength']
        p_vals = row['p_value']
        rate, lower, upper = calculate_chi_squared_error_rate(p_vals, alpha)
        aggregated.append({
            'dependency_strength': strength,
            'error_rate': rate,
            'ci_lower': lower,
            'ci_upper': upper,
            'n_replications': len(p_vals)
        })
    
    return pd.DataFrame(aggregated)

def train_logistic_model(data: pd.DataFrame, target_col: str = 'significant', feature_cols: List[str] = ['dependency_strength']) -> LogisticRegression:
    """
    Train a logistic regression model to predict significance based on dependency strength.

    Args:
        data: DataFrame containing features and the target binary column.
        target_col: Name of the binary target column (0 or 1).
        feature_cols: List of feature column names.

    Returns:
        Trained LogisticRegression model.
    """
    X = data[feature_cols]
    y = data[target_col]
    
    model = LogisticRegression()
    model.fit(X, y)
    
    # Verify convergence and AUC
    if hasattr(model, 'n_iter_') and model.n_iter_ is not None:
        if not np.all(model.n_iter_ > 0):
            raise RuntimeError("Logistic regression model did not converge.")
    
    if len(np.unique(y)) > 1:
        y_pred_prob = model.predict_proba(X)[:, 1]
        auc = roc_auc_score(y, y_pred_prob)
        if auc <= 0.5:
            raise RuntimeError(f"Model AUC ({auc}) is <= 0.5, indicating no predictive power.")
    
    return model

def save_logistic_model(model: LogisticRegression, path: str) -> None:
    """Save a logistic regression model to a pickle file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def load_logistic_model(path: str) -> LogisticRegression:
    """Load a logistic regression model from a pickle file."""
    with open(path, 'rb') as f:
        return pickle.load(f)

def verify_trend_monotonicity(df: pd.DataFrame, strength_col: str = 'dependency_strength', 
                              rate_col: str = 'error_rate') -> Dict[str, Any]:
    """
    Verify monotonic increase of error rates with dependency strength using Spearman correlation.

    Args:
        df: DataFrame with strength and rate columns.
        strength_col: Name of the dependency strength column.
        rate_col: Name of the error rate column.

    Returns:
        Dict with 'spearman_corr', 'p_value', and 'is_monotonic' (True if p < 0.05).
    """
    if df.empty or len(df) < 2:
        return {'spearman_corr': 0.0, 'p_value': 1.0, 'is_monotonic': False}
    
    corr, p_val = stats.spearmanr(df[strength_col], df[rate_col])
    is_monotonic = p_val < 0.05 and corr > 0
    
    return {
        'spearman_corr': corr,
        'p_value': p_val,
        'is_monotonic': is_monotonic
    }

def calculate_power_delta(power_at_r0: float, power_at_r3: float) -> float:
    """
    Calculate the percentage reduction in power between r=0 and r=0.3.
    
    Formula: ((Power(r=0) - Power(r=0.3)) / Power(r=0)) * 100
    
    Args:
        power_at_r0: Observed power at dependency strength r=0.
        power_at_r3: Observed power at dependency strength r=0.3.
    
    Returns:
        Percentage reduction in power. Returns 0.0 if power_at_r0 is 0 to avoid division by zero.
    """
    if power_at_r0 == 0.0:
        return 0.0
    
    reduction = (power_at_r0 - power_at_r3) / power_at_r0 * 100.0
    return reduction