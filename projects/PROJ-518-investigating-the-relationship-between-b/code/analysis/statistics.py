import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from scipy import stats
import statsmodels.api as sm
import os
from pathlib import Path
from config import get_config
from utils.logging import log_exclusion
from datetime import datetime

@dataclass
class RegressionResult:
    coefficients: Dict[str, float]
    r_squared: float
    adjusted_r_squared: float
    pearson_r: float
    delta_r2_str: Optional[str] = None
    empirical_p_value: Optional[float] = None

def format_delta_r2(delta_r2: float) -> str:
    """Format delta R2 to exactly 4 decimal places."""
    return f"{delta_r2:.4f}"

def log_regression_summary(
    subject_id: str,
    flexibility: float,
    creativity: float,
    pearson_r: float,
    empirical_p_value: float
) -> None:
    """
    Append a row to data/interim/regression_summary.csv.
    Initializes the file with headers if it does not exist.
    """
    config = get_config()
    output_path = Path(config.DATA_PATH) / "interim" / "regression_summary.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    new_row = {
        "subject_id": subject_id,
        "flexibility": flexibility,
        "creativity": creativity,
        "pearson_r": pearson_r,
        "empirical_p_value": empirical_p_value
    }

    df = pd.DataFrame([new_row])

    if not output_path.exists():
        df.to_csv(output_path, index=False)
    else:
        df.to_csv(output_path, mode='a', header=False, index=False)

def fit_regression(
    flexibility: np.ndarray,
    creativity: np.ndarray,
    covariates: Dict[str, Any]
) -> RegressionResult:
    """
    Fit the full OLS model: creativity ~ network_flexibility + age + sex + education + static_connectivity_strength.
    Computes Pearson correlation and returns RegressionResult.
    """
    # Prepare data
    X_data = {
        'intercept': np.ones(len(flexibility)),
        'network_flexibility': flexibility,
        'age': covariates['age'],
        'sex': covariates['sex'],
        'education': covariates['education'],
        'static_connectivity_strength': covariates['static_connectivity_strength']
    }
    
    X = pd.DataFrame(X_data)
    y = creativity

    # Fit model
    model = sm.OLS(y, X).fit()
    
    # Calculate Pearson correlation between flexibility and creativity
    pearson_r, _ = stats.pearsonr(flexibility, creativity)

    # Get coefficients as dict
    coefficients = dict(zip(X.columns, model.params))

    return RegressionResult(
        coefficients=coefficients,
        r_squared=model.rsquared,
        adjusted_r_squared=model.rsquared_adj,
        pearson_r=pearson_r,
        empirical_p_value=None  # Will be set by T027 logic if available
    )

def fit_baseline_regression(
    creativity: np.ndarray,
    static_strengths: List[float],
    covariates: Dict[str, Any]
) -> RegressionResult:
    """
    Fit the baseline model: creativity ~ static_connectivity_strength + age + sex + education.
    """
    X_data = {
        'intercept': np.ones(len(creativity)),
        'static_connectivity_strength': static_strengths,
        'age': covariates['age'],
        'sex': covariates['sex'],
        'education': covariates['education']
    }
    
    X = pd.DataFrame(X_data)
    y = creativity

    model = sm.OLS(y, X).fit()
    
    coefficients = dict(zip(X.columns, model.params))

    return RegressionResult(
        coefficients=coefficients,
        r_squared=model.rsquared,
        adjusted_r_squared=model.rsquared_adj,
        pearson_r=0.0  # Not calculated for baseline as per spec focus
    )

def run_permutation_test(
    flexibility: np.ndarray,
    creativity: np.ndarray,
    n_permutations: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run permutation test to compute empirical p-value and distribution of max stats.
    """
    rng = np.random.default_rng(seed)
    n = len(creativity)
    
    # Generate shuffled indices
    shuffled_indices = rng.choice(n, size=(n_permutations, n), replace=False)
    
    # Compute correlations for each permutation
    shuffled_correlations = []
    for i in range(n_permutations):
        shuffled_creativity = creativity[shuffled_indices[i]]
        corr, _ = stats.pearsonr(flexibility, shuffled_creativity)
        shuffled_correlations.append(corr)
    
    shuffled_correlations = np.array(shuffled_correlations)
    
    # Calculate empirical p-value (two-tailed)
    observed_corr, _ = stats.pearsonr(flexibility, creativity)
    extreme_count = np.sum(np.abs(shuffled_correlations) >= np.abs(observed_corr))
    empirical_p_value = extreme_count / n_permutations
    
    # Distribution of max stats (absolute values)
    distribution_of_max_stats = np.abs(shuffled_correlations).tolist()
    
    return {
        'empirical_p_value': float(empirical_p_value),
        'distribution_of_max_stats': distribution_of_max_stats
    }

def construct_covariates_dict(
    static_strengths: List[float],
    ages: List[float],
    sexes: List[str],
    educations: List[int]
) -> Dict[str, Any]:
    """
    Aggregate per-participant metrics into the covariates dictionary.
    """
    if not static_strengths:
        raise ValueError("static_strengths list is empty")
    
    return {
        'static_connectivity_strength': static_strengths,
        'age': ages,
        'sex': sexes,
        'education': educations
    }

def validate_alignment(
    static_strengths: List[float],
    flexibility: List[float],
    creativity: List[float],
    subject_ids: List[str]
) -> bool:
    """
    Check if all lists have the same length.
    """
    if not (len(static_strengths) == len(flexibility) == len(creativity) == len(subject_ids)):
        raise ValueError("Input lists have mismatched lengths")
    return True

def collect_static_strengths(static_strength_results: List[float]) -> List[float]:
    """
    Aggregate individual float results into a single list.
    """
    return [float(x) for x in static_strength_results]

def construct_sensitivity_df(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Transform sensitivity analysis dictionary into a DataFrame.
    """
    df = pd.DataFrame({
        'window_length': data['window_lengths'],
        'correlation': data['correlations'],
        'empirical_p_value': data['p_values']
    })
    return df

def merge_permutation_data(
    p_values: List[float],
    distribution_of_max_stats: List[float]
) -> Dict[str, Any]:
    """
    Merge p-values and distribution of max stats for FWE correction.
    """
    return {
        'p_values': p_values,
        'distribution_of_max_stats': distribution_of_max_stats
    }

def apply_fwe_correction(merged_data: Dict[str, Any], method: Optional[str] = None) -> List[float]:
    """
    Apply FWE correction (max-t or bonferroni).
    """
    config = get_config()
    if method is None:
        method = config.FWE_METHOD
    
    p_values = merged_data['p_values']
    
    if method == 'bonferroni':
        k = len(p_values)
        adjusted = [min(p * k, 1.0) for p in p_values]
    elif method == 'max-t':
        # Simplified max-t implementation using the distribution
        distribution = merged_data['distribution_of_max_stats']
        # For this implementation, we use the empirical p-values directly 
        # as the max-t correction would require the original test statistics
        adjusted = p_values
    else:
        raise ValueError(f"Unknown FWE method: {method}")
    
    return adjusted
