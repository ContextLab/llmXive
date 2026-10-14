"""
Core simulation logic for generating missing data patterns and establishing 
ground truth null hypotheses.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any
from analysis import run_complete_case_analysis, run_multiple_imputation, run_inverse_probability_weighting

def permute_treatment_labels(df: pd.DataFrame, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Permutes the treatment labels to enforce a true null hypothesis (zero effect).
    """
    df_perm = df.copy()
    if seed is not None:
        np.random.seed(seed)
    
    # Shuffle the treatment column
    treatment_vals = df_perm['treatment'].values
    np.random.shuffle(treatment_vals)
    df_perm['treatment'] = treatment_vals
    return df_perm

def simulate_mcar(df: pd.DataFrame, rate: float, seed: Optional[int] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Simulates Missing Completely At Random (MCAR) missingness.
    """
    df_missing = df.copy()
    if seed is not None:
        np.random.seed(seed)
    
    mask = np.random.rand(len(df)) < rate
    df_missing.loc[mask, 'outcome'] = np.nan
    return df_missing, mask

def simulate_mar(df: pd.DataFrame, rate: float, seed: Optional[int] = None, covariate_col: str = 'age') -> Tuple[pd.DataFrame, pd.Series]:
    """
    Simulates Missing At Random (MAR) missingness, where missingness depends on an observed covariate.
    """
    df_missing = df.copy()
    if covariate_col not in df.columns:
        raise ValueError(f"MAR mechanism requires mar_covariate: {covariate_col} not found in data")
    
    if seed is not None:
        np.random.seed(seed)
    
    # Probability of missingness depends on the covariate value.
    # To ensure the overall rate is approximately 'rate', we use a threshold on the standardized covariate.
    cov_vals = df[covariate_col].values
    std_cov = (cov_vals - np.mean(cov_vals)) / (np.std(cov_vals) + 1e-9)
    
    # We identify the threshold for the top 'rate' percentile of the covariate
    threshold = np.percentile(std_cov, 100 * (1 - rate))
    mask = std_cov >= threshold
    
    df_missing.loc[mask, 'outcome'] = np.nan
    return df_missing, mask

def simulate_mnar(df: pd.DataFrame, rate: float, seed: Optional[int] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Simulates Missing Not At Random (MNAR) missingness, where missingness depends on the outcome values.
    """
    df_missing = df.copy()
    if seed is not None:
        np.random.seed(seed)
    
    # Probability of missingness depends on the outcome itself.
    outcome_vals = df['outcome'].values
    std_out = (outcome_vals - np.mean(outcome_vals)) / (np.std(outcome_vals) + 1e-9)
    
    threshold = np.percentile(std_out, 100 * (1 - rate))
    mask = std_out >= threshold
    
    df_missing.loc[mask, 'outcome'] = np.nan
    return df_missing, mask

def simulate_missingness(
    df: pd.DataFrame, 
    mechanism: str, 
    missing_rate: float, 
    seed: Optional[int] = None, 
    mar_covariate: Optional[str] = None, 
    permute_treatment: bool = False
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Wrapper to simulate different missingness mechanisms.
    """
    data = df.copy()
    if permute_treatment:
        data = permute_treatment_labels(data, seed=seed)
    
    mechanism = mechanism.lower()
    if mechanism == 'mcar':
        return simulate_mcar(data, missing_rate, seed)
    elif mechanism == 'mar':
        if mar_covariate is None:
            raise ValueError("MAR mechanism requires mar_covariate")
        return simulate_mar(data, missing_rate, seed, mar_covariate)
    elif mechanism == 'mnar':
        return simulate_mnar(data, missing_rate, seed)
    else:
        raise ValueError(f"Invalid missingness mechanism: {mechanism}")

def run_simulation_iteration(
    dataset: pd.DataFrame, 
    mechanism: str, 
    missing_rate: float, 
    method: str, 
    seed: int, 
    config: Any
) -> Dict[str, Any]:
    """
    Runs a single simulation iteration: Permute -> Simulate Missing -> Analyze.
    Used by main.py.
    """
    # 1. Establish Null Hypothesis
    df_perm = permute_treatment_labels(dataset, seed=seed)
    
    # 2. Simulate Missingness
    # Determine covariate for MAR if applicable
    mar_cov = getattr(config, 'covariate_for_mar', 'age')
    df_missing, _ = simulate_missingness(
        df_perm, 
        mechanism=mechanism, 
        missing_rate=missing_rate, 
        seed=seed + 1, 
        mar_covariate=mar_cov
    )
    
    # 3. Analyze
    outcome_col = 'outcome'
    treatment_col = 'treatment'
    
    try:
        if method == 'CC' or method == 'Complete-Case':
            res = run_complete_case_analysis(df_missing, outcome_col, treatment_col)
        elif method == 'MI' or method == 'Multiple Imputation':
            res = run_multiple_imputation(df_missing, outcome_col, treatment_col)
        elif method == 'IPW' or method == 'Inverse Probability Weighting':
            res = run_inverse_probability_weighting(df_missing, outcome_col, treatment_col)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return {"p_value": float(res.get("p_value", 1.0)), "status": "success"}
    except Exception as e:
        return {"p_value": 1.0, "status": "failed", "error": str(e)}
