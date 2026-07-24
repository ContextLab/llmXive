import math
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from scipy import optimize
from utils.logging import get_logger

logger = get_logger(__name__)

class EstimationResult:
    """
    Container for the results of a meta-analysis estimation.
    Conforms to the EstimationResult schema (T004).
    """
    def __init__(
        self,
        pooled_effect: float,
        se_pooled: float,
        ci_lower: float,
        ci_upper: float,
        tau2: float,
        i2: float,
        q_statistic: float,
        df: int,
        p_value: float,
        n_studies: int,
        convergence_status: str = "success"
    ):
        self.pooled_effect = pooled_effect
        self.se_pooled = se_pooled
        self.ci_lower = ci_lower
        self.ci_upper = ci_upper
        self.tau2 = tau2
        self.i2 = i2
        self.q_statistic = q_statistic
        self.df = df
        self.p_value = p_value
        self.n_studies = n_studies
        self.convergence_status = convergence_status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pooled_effect": self.pooled_effect,
            "se_pooled": self.se_pooled,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "tau2": self.tau2,
            "i2": self.i2,
            "q_statistic": self.q_statistic,
            "df": self.df,
            "p_value": self.p_value,
            "n_studies": self.n_studies,
            "convergence_status": self.convergence_status
        }

def calculate_i_squared(q_statistic: float, df: int) -> float:
    """
    Calculates the I^2 statistic (Higgins & Thompson, 2002).
    
    I^2 = max(0, (Q - df) / Q) * 100
    
    Parameters:
        q_statistic: The Cochran's Q heterogeneity statistic.
        df: Degrees of freedom (k - 1).
        
    Returns:
        I^2 value as a percentage (0.0 to 100.0).
    """
    if q_statistic <= 0 or df <= 0:
        return 0.0
    
    # Formula: max(0, (Q - df) / Q) * 100
    i2_raw = (q_statistic - df) / q_statistic
    i2 = max(0.0, i2_raw) * 100.0
    return i2

def estimate_fixed_effects(
    effect_sizes: List[float], 
    variances: List[float]
) -> EstimationResult:
    """
    Calculates the Fixed-Effects meta-analysis estimate.
    Assumes tau^2 = 0.
    
    Parameters:
        effect_sizes: List of observed effect sizes (y_i).
        variances: List of within-study variances (v_i).
        
    Returns:
        EstimationResult object.
    """
    if len(effect_sizes) != len(variances):
        raise ValueError("Effect sizes and variances must have the same length")
    
    n = len(effect_sizes)
    if n == 0:
        raise ValueError("No studies provided")
    
    # Weights for fixed effects: w_i = 1 / v_i
    weights = [1.0 / v for v in variances]
    sum_w = sum(weights)
    
    if sum_w == 0:
        raise ValueError("Sum of weights is zero (infinite variances)")
    
    # Pooled effect: sum(w_i * y_i) / sum(w_i)
    pooled = sum(w * y for w, y in zip(weights, effect_sizes)) / sum_w
    
    # SE of pooled: sqrt(1 / sum(w_i))
    se_pooled = math.sqrt(1.0 / sum_w)
    
    # 95% CI
    z = 1.96
    ci_lower = pooled - z * se_pooled
    ci_upper = pooled + z * se_pooled
    
    # Cochran's Q for heterogeneity (even though we assume homogeneity)
    # Q = sum(w_i * (y_i - pooled)^2)
    q_statistic = sum(w * (y - pooled)**2 for w, y in zip(weights, effect_sizes))
    df = n - 1
    
    # P-value for Q (Chi-squared distribution)
    from scipy.stats import chi2
    if df > 0:
        p_value = 1.0 - chi2.cdf(q_statistic, df)
    else:
        p_value = 1.0
    
    # Calculate I^2
    i2 = calculate_i_squared(q_statistic, df)
    
    return EstimationResult(
        pooled_effect=pooled,
        se_pooled=se_pooled,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        tau2=0.0,
        i2=i2,
        q_statistic=q_statistic,
        df=df,
        p_value=p_value,
        n_studies=n,
        convergence_status="success"
    )

def estimate_dersimonian_laird(
    effect_sizes: List[float], 
    variances: List[float]
) -> EstimationResult:
    """
    Calculates the DerSimonian-Laird random-effects estimate.
    
    Parameters:
        effect_sizes: List of observed effect sizes (y_i).
        variances: List of within-study variances (v_i).
        
    Returns:
        EstimationResult object.
    """
    if len(effect_sizes) != len(variances):
        raise ValueError("Effect sizes and variances must have the same length")
    
    n = len(effect_sizes)
    if n == 0:
        raise ValueError("No studies provided")
    
    # Step 1: Calculate Fixed Effects weights and Q
    w_fixed = [1.0 / v for v in variances]
    sum_w_fixed = sum(w_fixed)
    
    if sum_w_fixed == 0:
        raise ValueError("Sum of weights is zero")
        
    pooled_fe = sum(w * y for w, y in zip(w_fixed, effect_sizes)) / sum_w_fixed
    q_statistic = sum(w * (y - pooled_fe)**2 for w, y in zip(w_fixed, effect_sizes))
    
    df = n - 1
    if df <= 0:
        # If only 1 study, tau2 is undefined/zero
        return estimate_fixed_effects(effect_sizes, variances)
    
    # Step 2: Calculate tau^2 (DL estimator)
    # tau^2 = max(0, (Q - df) / C)
    # C = sum(w_i) - sum(w_i^2) / sum(w_i)
    sum_w_sq = sum(w**2 for w in w_fixed)
    c_val = sum_w_fixed - (sum_w_sq / sum_w_fixed)
    
    if c_val <= 0:
        tau2 = 0.0
    else:
        tau2_raw = (q_statistic - df) / c_val
        tau2 = max(0.0, tau2_raw)
    
    # Step 3: Calculate Random Effects weights: w*_i = 1 / (v_i + tau^2)
    w_re = [1.0 / (v + tau2) for v in variances]
    sum_w_re = sum(w_re)
    
    if sum_w_re == 0:
        # Fallback to fixed effects if weights collapse
        return estimate_fixed_effects(effect_sizes, variances)
    
    # Pooled effect (RE)
    pooled = sum(w * y for w, y in zip(w_re, effect_sizes)) / sum_w_re
    
    # SE of pooled (RE)
    se_pooled = math.sqrt(1.0 / sum_w_re)
    
    # 95% CI
    z = 1.96
    ci_lower = pooled - z * se_pooled
    ci_upper = pooled + z * se_pooled
    
    # P-value for Q (Chi-squared)
    from scipy.stats import chi2
    p_value = 1.0 - chi2.cdf(q_statistic, df) if df > 0 else 1.0
    
    # Calculate I^2
    i2 = calculate_i_squared(q_statistic, df)
    
    return EstimationResult(
        pooled_effect=pooled,
        se_pooled=se_pooled,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        tau2=tau2,
        i2=i2,
        q_statistic=q_statistic,
        df=df,
        p_value=p_value,
        n_studies=n,
        convergence_status="success"
    )

def estimate_reml(
    effect_sizes: List[float], 
    variances: List[float]
) -> EstimationResult:
    """
    Calculates the Restricted Maximum Likelihood (REML) estimate.
    
    Parameters:
        effect_sizes: List of observed effect sizes (y_i).
        variances: List of within-study variances (v_i).
        
    Returns:
        EstimationResult object.
    """
    n = len(effect_sizes)
    if n == 0:
        raise ValueError("No studies provided")
    if n == 1:
        return estimate_fixed_effects(effect_sizes, variances)
    
    def reml_log_likelihood(tau2: float) -> float:
        """Negative log-likelihood for REML to minimize."""
        if tau2 < 0:
            return float('inf')
        
        # Weights
        w = [1.0 / (v + tau2) for v in variances]
        sum_w = sum(w)
        
        if sum_w <= 0:
            return float('inf')
        
        # Pooled effect for this tau2
        mu = sum(wi * yi for wi, yi in zip(w, effect_sizes)) / sum_w
        
        # Log-likelihood components
        # L = -0.5 * [ sum(log(v_i + tau2)) + log(sum(1/(v_i+tau2))) + sum((y_i - mu)^2 / (v_i + tau2)) ]
        # We return negative L to minimize
        
        term1 = sum(math.log(v + tau2) for v in variances)
        term2 = math.log(sum_w)
        term3 = sum((y - mu)**2 / (v + tau2) for y, v in zip(effect_sizes, variances))
        
        neg_ll = 0.5 * (term1 + term2 + term3)
        return neg_ll
    
    # Optimization
    try:
        res = optimize.minimize_scalar(
            reml_log_likelihood, 
            bounds=(0.0, max(variances) * 10.0), # Reasonable upper bound
            method='bounded',
            options={'xatol': 1e-6}
        )
        
        if not res.success:
            logger.warning(f"REML optimization failed: {res.message}")
            # Fallback to DL if optimization fails
            return estimate_dersimonian_laird(effect_sizes, variances)
        
        tau2 = res.x
        if tau2 < 0:
            tau2 = 0.0
            
    except Exception as e:
        logger.error(f"REML optimization error: {e}")
        return estimate_dersimonian_laird(effect_sizes, variances)
    
    # Calculate final estimates with the optimized tau2
    w_re = [1.0 / (v + tau2) for v in variances]
    sum_w_re = sum(w_re)
    
    if sum_w_re == 0:
        return estimate_fixed_effects(effect_sizes, variances)
    
    pooled = sum(w * y for w, y in zip(w_re, effect_sizes)) / sum_w_re
    se_pooled = math.sqrt(1.0 / sum_w_re)
    
    z = 1.96
    ci_lower = pooled - z * se_pooled
    ci_upper = pooled + z * se_pooled
    
    # Calculate Q for I^2 (using fixed effect weights for Q calculation as per standard practice)
    w_fixed = [1.0 / v for v in variances]
    sum_w_fixed = sum(w_fixed)
    pooled_fe = sum(w * y for w, y in zip(w_fixed, effect_sizes)) / sum_w_fixed
    q_statistic = sum(w * (y - pooled_fe)**2 for w, y in zip(w_fixed, effect_sizes))
    
    df = n - 1
    from scipy.stats import chi2
    p_value = 1.0 - chi2.cdf(q_statistic, df) if df > 0 else 1.0
    
    i2 = calculate_i_squared(q_statistic, df)
    
    return EstimationResult(
        pooled_effect=pooled,
        se_pooled=se_pooled,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        tau2=tau2,
        i2=i2,
        q_statistic=q_statistic,
        df=df,
        p_value=p_value,
        n_studies=n,
        convergence_status="success"
    )

def apply_estimator(
    estimator_name: str,
    effect_sizes: List[float],
    variances: List[float]
) -> EstimationResult:
    """
    Dispatches to the appropriate estimator function.
    
    Parameters:
        estimator_name: One of 'fixed', 'dl', 'reml'.
        effect_sizes: List of observed effect sizes.
        variances: List of within-study variances.
        
    Returns:
        EstimationResult object.
    """
    name = estimator_name.lower()
    if name in ['fixed', 'fixed_effects']:
        return estimate_fixed_effects(effect_sizes, variances)
    elif name in ['dl', 'dersimonian_laird']:
        return estimate_dersimonian_laird(effect_sizes, variances)
    elif name in ['reml', 'restricted_max_likelihood']:
        return estimate_reml(effect_sizes, variances)
    else:
        raise ValueError(f"Unknown estimator: {estimator_name}")