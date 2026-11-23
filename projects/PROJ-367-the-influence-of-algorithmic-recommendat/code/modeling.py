import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import GLS, WLS
from statsmodels.tools import add_constant
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class RegressionResult:
    """Container for regression analysis results."""
    coefficient: float
    standard_error: float
    p_value: float
    r_squared: float
    vif_values: Dict[str, float]
    n_observations: int
    method: str
    weights_stable: bool = True
    gls_fallback_triggered: bool = False
    n_users: int = 0

def derive_baseline_interest_vector(
    df: pd.DataFrame,
    history_col: str = 'pre_study_history',
    category_list: Optional[List[str]] = None
) -> np.ndarray:
    """
    Derive a baseline interest vector from pre-study history.
    
    Args:
        df: DataFrame containing user history
        history_col: Column name containing historical category interactions
        category_list: List of all possible categories to form the vector space
    
    Returns:
        Normalized vector of interests across categories
    """
    if category_list is None:
        # Infer from data if not provided
        all_cats = set()
        for row in df[history_col]:
            if isinstance(row, list):
                all_cats.update(row)
        category_list = sorted(list(all_cats))
    
    if not category_list:
        logger.warning("No categories found to derive baseline vector")
        return np.array([])
    
    # Count occurrences of each category across all history
    counts = {cat: 0 for cat in category_list}
    total_interactions = 0
    
    for row in df[history_col]:
        if isinstance(row, list):
            for cat in row:
                if cat in counts:
                    counts[cat] += 1
                    total_interactions += 1
    
    # Normalize to create probability vector
    if total_interactions == 0:
        return np.zeros(len(category_list))
    
    vector = np.array([counts[cat] / total_interactions for cat in category_list])
    return vector

def calculate_propensity_scores(
    df: pd.DataFrame,
    treatment_col: str = 'high_diversity_rec',
    covariates: List[str] = ['learner_diversity_score', 'pre_study_interest_variance']
) -> pd.Series:
    """
    Calculate propensity scores using logistic regression.
    
    Args:
        df: DataFrame with treatment and covariates
        treatment_col: Binary treatment indicator column
        covariates: List of covariate column names
    
    Returns:
        Series of propensity scores (probability of treatment)
    """
    # Prepare features
    X = df[covariates].copy()
    X = add_constant(X)
    y = df[treatment_col].values
    
    # Fit logistic regression
    model = sm.Logit(y, X)
    result = model.fit(disp=0)
    
    # Return predicted probabilities
    propensity = result.predict(X)
    # Clip to avoid 0 or 1
    propensity = propensity.clip(0.01, 0.99)
    return propensity

def calculate_stabilized_weights(
    df: pd.DataFrame,
    propensity: pd.Series,
    treatment_col: str = 'high_diversity_rec'
) -> pd.Series:
    """
    Calculate stabilized inverse probability weights.
    
    Args:
        df: DataFrame with treatment indicator
        propensity: Series of propensity scores
        treatment_col: Binary treatment indicator column
    
    Returns:
        Series of stabilized weights
    """
    treatment = df[treatment_col]
    p = propensity.values
    
    # Stabilized weights: P(T) / P(T|X)
    # For treated: P(T=1) / p
    # For control: P(T=0) / (1-p)
    p_treatment = treatment.mean()
    p_control = 1 - p_treatment
    
    weights = np.where(
        treatment == 1,
        p_treatment / p,
        p_control / (1 - p)
    )
    
    return pd.Series(weights, index=df.index)

def check_weight_stability(weights: pd.Series, threshold: float = 10.0) -> Tuple[bool, float]:
    """
    Check for extreme weights that could destabilize estimates.
    
    Args:
        weights: Series of weights
        threshold: Ratio of max weight to median weight threshold
    
    Returns:
        Tuple of (is_stable, max_median_ratio)
    """
    median_weight = weights.median()
    max_weight = weights.max()
    
    if median_weight == 0:
        return False, float('inf')
    
    ratio = max_weight / median_weight
    is_stable = ratio <= threshold
    
    return is_stable, ratio

def check_weight_stability_and_log(
    df: pd.DataFrame,
    weights: pd.Series,
    threshold: float = 10.0
) -> Tuple[bool, float]:
    """
    Check weight stability and log warnings if unstable.
    
    Args:
        df: DataFrame (for context)
        weights: Series of weights
        threshold: Ratio threshold for instability
    
    Returns:
        Tuple of (is_stable, max_median_ratio)
    """
    is_stable, ratio = check_weight_stability(weights, threshold)
    
    if not is_stable:
        logger.warning(
            f"Extreme weights detected: max/median ratio = {ratio:.2f} "
            f"(threshold = {threshold}). Estimates may be unstable."
        )
        # Log specific extreme values
        extreme_mask = weights > (threshold * weights.median())
        if extreme_mask.sum() > 0:
            logger.warning(
                f"Found {extreme_mask.sum()} observations with extreme weights "
                f"(max: {weights[extreme_mask].max():.2f})"
            )
    
    return is_stable, ratio

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for multicollinearity diagnostics.
    
    Args:
        df: DataFrame containing features
        feature_cols: List of column names to check
    
    Returns:
        Dictionary mapping column names to VIF values
    """
    X = df[feature_cols].copy()
    X = add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(feature_cols):
        # VIF for feature j is 1 / (1 - R_j^2)
        # where R_j^2 is from regressing feature j on all other features
        y_j = X[col]
        X_others = X.drop(columns=[col])
        
        try:
            model = sm.OLS(y_j, X_others).fit()
            r_squared = model.rsquared
            vif = 1 / (1 - r_squared) if (1 - r_squared) > 1e-10 else float('inf')
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = float('inf')
    
    return vif_data

def fit_weighted_regression(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    weights: pd.Series,
    covariates: Optional[List[str]] = None
) -> RegressionResult:
    """
    Fit a weighted linear regression model with VIF diagnostics.
    
    Args:
        df: DataFrame with all variables
        outcome_col: Name of outcome variable
        treatment_col: Name of treatment variable
        weights: Series of weights for WLS
        covariates: Optional list of control variables
    
    Returns:
        RegressionResult with coefficient, SE, p-value, VIF, etc.
    """
    # Prepare features
    features = [treatment_col]
    if covariates:
        features.extend(covariates)
    
    # Check for missing values
    mask = df[features + [outcome_col]].notna().all(axis=1)
    df_clean = df[mask].copy()
    weights_clean = weights[mask]
    
    if len(df_clean) == 0:
        raise ValueError("No valid observations after cleaning")
    
    X = df_clean[features]
    X = add_constant(X)
    y = df_clean[outcome_col].values
    
    # Fit weighted least squares
    model = WLS(y, X, weights=weights_clean)
    result = model.fit()
    
    # Extract treatment coefficient (index 1 if constant is 0)
    treatment_idx = features.index(treatment_col) + 1  # +1 for constant
    coef = result.params[treatment_idx]
    se = result.bse[treatment_idx]
    p_val = result.pvalues[treatment_idx]
    r_sq = result.rsquared
    
    # Calculate VIF for feature columns
    vif_values = calculate_vif(df_clean, features)
    
    # Check weight stability
    is_stable, _ = check_weight_stability(weights_clean)
    
    return RegressionResult(
        coefficient=coef,
        standard_error=se,
        p_value=p_val,
        r_squared=r_sq,
        vif_values=vif_values,
        n_observations=len(df_clean),
        method='WLS',
        weights_stable=is_stable
    )

def fit_gls_fallback(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    covariates: Optional[List[str]] = None
) -> RegressionResult:
    """
    Fit GLS fallback model when N < 30 or weights are unstable.
    Uses robust standard errors to handle heteroskedasticity.
    
    Args:
        df: DataFrame with all variables
        outcome_col: Name of outcome variable
        treatment_col: Name of treatment variable
        covariates: Optional list of control variables
    
    Returns:
        RegressionResult with GLS estimates and robust SEs
    """
    features = [treatment_col]
    if covariates:
        features.extend(covariates)
    
    # Check for missing values
    mask = df[features + [outcome_col]].notna().all(axis=1)
    df_clean = df[mask].copy()
    
    if len(df_clean) == 0:
        raise ValueError("No valid observations after cleaning")
    
    X = df_clean[features]
    X = add_constant(X)
    y = df_clean[outcome_col].values
    
    # Fit OLS first to get residuals for GLS
    ols_model = sm.OLS(y, X).fit()
    
    # For GLS fallback, we use a simple structure (identity) but
    # rely on robust standard errors from the OLS fit for inference
    # In practice, we could model the error structure if known
    gls_model = GLS(y, X).fit()
    
    # Use HC1 robust standard errors
    robust_results = ols_model.get_robustcov_results(cov_type='HC1')
    
    # Extract treatment coefficient
    treatment_idx = features.index(treatment_col) + 1
    coef = robust_results.params[treatment_idx]
    se = robust_results.bse[treatment_idx]
    p_val = robust_results.pvalues[treatment_idx]
    r_sq = robust_results.rsquared
    
    # Calculate VIF
    vif_values = calculate_vif(df_clean, features)
    
    return RegressionResult(
        coefficient=coef,
        standard_error=se,
        p_value=p_val,
        r_squared=r_sq,
        vif_values=vif_values,
        n_observations=len(df_clean),
        method='GLS_robust',
        weights_stable=True,
        gls_fallback_triggered=True
    )

def run_ps_analysis(
    df: pd.DataFrame,
    outcome_col: str = 'learning_outcome',
    treatment_col: str = 'high_diversity_rec',
    propensity_col: str = 'propensity_score',
    weights_col: str = 'stabilized_weight',
    covariates: Optional[List[str]] = None,
    n_users: int = 0
) -> RegressionResult:
    """
    Run the full propensity score analysis pipeline:
    1. Calculate propensity scores
    2. Calculate stabilized weights
    3. Check weight stability
    4. Fit weighted regression (or GLS fallback if N < 30)
    
    Args:
        df: DataFrame with all variables
        outcome_col: Outcome variable name
        treatment_col: Treatment indicator name
        propensity_col: Column to store propensity scores
        weights_col: Column to store weights
        covariates: List of covariates for propensity model
        n_users: Number of unique users (for N<30 check)
    
    Returns:
        RegressionResult with full analysis output
    """
    if covariates is None:
        covariates = ['learner_diversity_score', 'pre_study_interest_variance']
    
    # 1. Calculate propensity scores
    logger.info("Calculating propensity scores...")
    propensity = calculate_propensity_scores(df, treatment_col, covariates)
    df[propensity_col] = propensity
    
    # 2. Calculate stabilized weights
    logger.info("Calculating stabilized weights...")
    weights = calculate_stabilized_weights(df, propensity, treatment_col)
    df[weights_col] = weights
    
    # 3. Check weight stability
    is_stable, ratio = check_weight_stability_and_log(df, weights)
    
    # 4. Determine if GLS fallback is needed
    use_gls = False
    if n_users > 0 and n_users < 30:
        logger.warning(f"Small sample size (N={n_users} < 30). Using GLS fallback.")
        use_gls = True
    elif not is_stable:
        logger.warning("Unstable weights detected. Considering GLS fallback.")
        # Decision to fallback on unstable weights depends on severity
        # For now, we proceed with WLS but log the warning
    
    # 5. Fit model
    if use_gls:
        logger.info("Fitting GLS fallback model...")
        result = fit_gls_fallback(df, outcome_col, treatment_col, covariates)
        result.n_users = n_users
    else:
        logger.info("Fitting weighted regression model...")
        result = fit_weighted_regression(df, outcome_col, treatment_col, weights, covariates)
        result.n_users = n_users
        result.weights_stable = is_stable
    
    logger.info(
        f"PS Analysis complete. "
        f"Coefficient: {result.coefficient:.4f}, "
        f"SE: {result.standard_error:.4f}, "
        f"P-value: {result.p_value:.4f}, "
        f"Method: {result.method}"
    )
    
    return result