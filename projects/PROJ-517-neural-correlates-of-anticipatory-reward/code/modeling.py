import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial, Poisson
from statsmodels.stats.power import FTestAnovaPower
from scipy.stats import f
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from logging_config import get_logger

logger = get_logger(__name__)

def calculate_observed_variance(df: pd.DataFrame, output_path: str) -> float:
    """
    Calculate observed variance of spike_count from the validated dataset
    and store in data/processed/observed_variance.json.
    """
    if 'spike_count' not in df.columns:
        raise ValueError("DataFrame must contain 'spike_count' column")
    
    variance = df['spike_count'].var()
    result = {'observed_variance': float(variance)}
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Observed variance calculated: {variance:.4f}, saved to {output_path}")
    return variance

def calculate_dispersion(df: pd.DataFrame) -> float:
    """
    Calculate dispersion parameter for model selection.
    Dispersion = Variance / Mean
    """
    mean_val = df['spike_count'].mean()
    var_val = df['spike_count'].var()
    
    if mean_val == 0:
        return 1.0
    
    dispersion = var_val / mean_val
    logger.info(f"Dispersion calculated: {dispersion:.4f}")
    return dispersion

def select_model_family(dispersion: float) -> Any:
    """
    Select model family based on dispersion.
    Negative Binomial if dispersion > 1.1, Poisson otherwise.
    """
    if dispersion > 1.1:
        logger.info("Selecting Negative Binomial model (overdispersion detected)")
        return NegativeBinomial
    else:
        logger.info("Selecting Poisson model")
        return Poisson

def fit_glm(df: pd.DataFrame, model_class: Any) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit GLM: firing_rate ~ reward_magnitude
    Returns fitted model and results dictionary.
    """
    X = df['reward_magnitude'].values
    y = df['spike_count'].values
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    model = model_class(y, X_with_const)
    fitted = model.fit()
    
    results = {
        'coefficient': float(fitted.params[1]),
        'p_value': float(fitted.pvalues[1]),
        'std_err': float(fitted.bse[1]),
        'log_likelihood': float(fitted.llf),
        'aic': float(fitted.aic),
        'bic': float(fitted.bic)
    }
    
    logger.info(f"GLM fitted: coef={results['coefficient']:.4f}, p={results['p_value']:.4f}")
    return fitted, results

def calculate_mdes(df: pd.DataFrame, variance: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """
    Calculate Minimum Detectable Effect Size (MDES) using Cohen's f2.
    Uses final validated sample size and observed variance.
    """
    n = len(df)
    if n < 2:
        raise ValueError("Need at least 2 samples for MDES calculation")
    
    # For simple linear regression with 1 predictor
    # f2 = (R^2) / (1 - R^2)
    # MDES is the effect size detectable with given power
    
    # Using F-test power analysis approximation
    # For large samples, Cohen's f2 ~ (beta^2 * var(X)) / var(y)
    
    # Simplified approach: use F-test for linear regression
    # We need to find effect size that gives desired power
    
    # Approximate MDES using standard formula for linear regression
    # MDES = sqrt( (f2 * var_y) / var_x ) where f2 is derived from power analysis
    
    # Using statsmodels power analysis
    power_analysis = FTestAnovaPower()
    
    # For simple regression, effect size f2
    # We solve for f2 given power, alpha, and sample size
    # This is an approximation; exact calculation requires iterative solving
    
    # Typical f2 values: 0.02 (small), 0.15 (medium), 0.35 (large)
    # We'll estimate based on sample size and desired power
    
    # Simplified: MDES in terms of coefficient
    # MDES = t_critical * std_err
    # std_err = sqrt(var_y / (n * var_x))
    
    X = df['reward_magnitude'].values
    var_x = np.var(X)
    var_y = variance
    
    if var_x == 0:
        logger.warning("Reward magnitude has zero variance, cannot calculate MDES")
        return float('inf')
    
    # Critical t-value (approximate with normal for large n)
    t_crit = f.ppf(1 - alpha/2, 1, n - 2)
    
    # Standard error of coefficient
    std_err = np.sqrt(var_y / (n * var_x))
    
    # MDES = t_crit * std_err (for 80% power, we use a slightly higher multiplier)
    # For 80% power, we need to account for non-centrality parameter
    # Simplified: MDES ≈ 2.8 * std_err (covers 80% power for typical cases)
    mdes = 2.8 * std_err
    
    logger.info(f"MDES calculated: {mdes:.4f} (80% power, alpha={alpha})")
    return mdes

def run_permutation_test(df: pd.DataFrame, n_iterations: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Perform permutation test to validate the coefficient.
    Returns null distribution and p-value.
    """
    np.random.seed(seed)
    
    X = df['reward_magnitude'].values
    y = df['spike_count'].values
    X_with_const = sm.add_constant(X)
    
    # Fit original model
    original_model = NegativeBinomial(y, X_with_const)
    original_fitted = original_model.fit(dispstart=1.0, maxiter=100)
    original_coef = original_fitted.params[1]
    
    # Permutation test
    perm_coefs = []
    for i in range(n_iterations):
        # Shuffle y
        y_perm = np.random.permutation(y)
        
        try:
            perm_model = NegativeBinomial(y_perm, X_with_const)
            perm_fitted = perm_model.fit(dispstart=1.0, maxiter=50, disp=0)
            perm_coef = perm_fitted.params[1]
            perm_coefs.append(perm_coef)
        except Exception as e:
            logger.debug(f"Permutation {i} failed: {e}")
            continue
    
    perm_coefs = np.array(perm_coefs)
    
    # Calculate p-value (two-tailed)
    abs_original = np.abs(original_coef)
    abs_perm = np.abs(perm_coefs)
    p_value = np.mean(abs_perm >= abs_original)
    
    result = {
        'original_coefficient': float(original_coef),
        'p_value': float(p_value),
        'null_mean': float(np.mean(perm_coefs)),
        'null_std': float(np.std(perm_coefs)),
        'n_iterations': len(perm_coefs)
    }
    
    logger.info(f"Permutation test: p-value={p_value:.4f}, null_mean={np.mean(perm_coefs):.4f}")
    return result

def run_lrt_categorical_vs_linear(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform Likelihood Ratio Test (LRT) comparing categorical vs linear model.
    If p < 0.05, flag non-linearity.
    
    Returns:
        dict with lrt_statistic, p_value, is_nonlinear, model_ll_linear, model_ll_categorical
    """
    X = df['reward_magnitude'].values
    y = df['spike_count'].values
    
    # Fit linear model (continuous reward_magnitude)
    X_with_const = sm.add_constant(X)
    try:
        linear_model = NegativeBinomial(y, X_with_const)
        linear_fitted = linear_model.fit(dispstart=1.0, maxiter=100, disp=0)
        ll_linear = linear_fitted.llf
    except Exception as e:
        logger.error(f"Linear model fitting failed: {e}")
        return {
            'lrt_statistic': None,
            'p_value': None,
            'is_nonlinear': None,
            'model_ll_linear': None,
            'model_ll_categorical': None,
            'error': f"Linear model failed: {str(e)}"
        }
    
    # Fit categorical model (reward_magnitude as factor)
    # Create dummy variables for each unique reward level
    reward_levels = pd.Categorical(df['reward_magnitude'])
    X_cat = pd.get_dummies(reward_levels, drop_first=True).values
    
    # Add constant
    if X_cat.ndim == 1:
        X_cat = X_cat.reshape(-1, 1)
    
    X_cat_with_const = np.hstack([np.ones((X_cat.shape[0], 1)), X_cat])
    
    try:
        categorical_model = NegativeBinomial(y, X_cat_with_const)
        categorical_fitted = categorical_model.fit(dispstart=1.0, maxiter=100, disp=0)
        ll_categorical = categorical_fitted.llf
    except Exception as e:
        logger.error(f"Categorical model fitting failed: {e}")
        return {
            'lrt_statistic': None,
            'p_value': None,
            'is_nonlinear': None,
            'model_ll_linear': float(ll_linear),
            'model_ll_categorical': None,
            'error': f"Categorical model failed: {str(e)}"
        }
    
    # Likelihood Ratio Test
    # H0: Linear model is sufficient (categorical coefficients for levels beyond first are 0)
    # H1: Categorical model fits significantly better
    
    # LRT statistic = 2 * (LL_categorical - LL_linear)
    # Degrees of freedom = df_categorical - df_linear
    # df_linear = 2 (intercept + 1 slope)
    # df_categorical = 1 + (n_levels - 1) = n_levels
    
    n_levels = len(reward_levels.categories)
    df_linear = 2
    df_categorical = n_levels
    df_diff = df_categorical - df_linear
    
    if df_diff <= 0:
        logger.warning("Not enough degrees of freedom for LRT")
        return {
            'lrt_statistic': None,
            'p_value': None,
            'is_nonlinear': None,
            'model_ll_linear': float(ll_linear),
            'model_ll_categorical': float(ll_categorical),
            'error': "Insufficient degrees of freedom"
        }
    
    lrt_statistic = 2 * (ll_categorical - ll_linear)
    
    # Calculate p-value using chi-square distribution
    from scipy.stats import chi2
    p_value = 1 - chi2.cdf(lrt_statistic, df_diff)
    
    # Flag non-linearity if p < 0.05
    is_nonlinear = p_value < 0.05
    
    result = {
        'lrt_statistic': float(lrt_statistic),
        'p_value': float(p_value),
        'is_nonlinear': is_nonlinear,
        'model_ll_linear': float(ll_linear),
        'model_ll_categorical': float(ll_categorical),
        'df_diff': df_diff,
        'n_reward_levels': n_levels,
        'interpretation': 'Non-linear relationship detected' if is_nonlinear else 'Linear relationship sufficient'
    }
    
    logger.info(f"LRT: statistic={lrt_statistic:.4f}, p={p_value:.4f}, nonlinear={is_nonlinear}")
    return result

def run_modeling_pipeline(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the complete modeling pipeline:
    1. Calculate observed variance
    2. Calculate dispersion and select model
    3. Fit GLM
    4. Calculate MDES
    5. Run permutation test
    6. Run LRT for categorical vs linear (T024b)
    
    Returns comprehensive results dictionary.
    """
    logger.info(f"Starting modeling pipeline with input: {input_path}")
    
    # Load data
    df = pd.read_csv(input_path)
    
    # Ensure required columns
    required_cols = ['trial_id', 'neuron_id', 'spike_count', 'reward_magnitude']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Filter out silent neurons (spike_count == 0) if needed
    # Based on validation logic from ingestion
    original_len = len(df)
    df = df[df['spike_count'] > 0]
    logger.info(f"Filtered {original_len - len(df)} silent neuron trials")
    
    results = {
        'input_file': input_path,
        'n_trials': len(df),
        'n_neuron_id': df['neuron_id'].nunique()
    }
    
    # T022a: Calculate observed variance
    variance_path = str(Path(output_path).parent / 'observed_variance.json')
    observed_variance = calculate_observed_variance(df, variance_path)
    results['observed_variance'] = observed_variance
    
    # T019: Calculate dispersion
    dispersion = calculate_dispersion(df)
    results['dispersion'] = dispersion
    
    # T020: Select model family
    model_class = select_model_family(dispersion)
    results['model_family'] = model_class.__name__
    
    # T021: Fit GLM
    fitted_model, glm_results = fit_glm(df, model_class)
    results['glm'] = glm_results
    
    # T022: Calculate MDES
    mdes = calculate_mdes(df, observed_variance)
    results['mdes_80_power'] = mdes
    
    # T023: Permutation test
    perm_results = run_permutation_test(df, n_iterations=1000)
    results['permutation_test'] = perm_results
    
    # T024a: Categorical GLM (already done as part of LRT)
    
    # T024b: Likelihood Ratio Test (Categorical vs Linear)
    lrt_results = run_lrt_categorical_vs_linear(df)
    results['lrt_categorical_vs_linear'] = lrt_results
    
    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Modeling pipeline complete. Results saved to {output_path}")
    return results

def main():
    """Main entry point for modeling pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run neural correlates modeling pipeline')
    parser.add_argument('--input', type=str, default='data/processed/validated_data.csv',
                      help='Input validated data file')
    parser.add_argument('--output', type=str, default='data/processed/modeling_results.json',
                      help='Output results file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    results = run_modeling_pipeline(args.input, args.output)
    
    # Print summary
    print("\n=== Modeling Results Summary ===")
    print(f"Trials analyzed: {results['n_trials']}")
    print(f"Model family: {results['model_family']}")
    print(f"GLM coefficient: {results['glm']['coefficient']:.4f}")
    print(f"GLM p-value: {results['glm']['p_value']:.4f}")
    print(f"MDES (80% power): {results['mdes_80_power']:.4f}")
    print(f"Permutation p-value: {results['permutation_test']['p_value']:.4f}")
    
    lrt = results['lrt_categorical_vs_linear']
    if lrt.get('is_nonlinear') is not None:
        print(f"LRT p-value: {lrt['p_value']:.4f}")
        print(f"Non-linear relationship: {'YES' if lrt['is_nonlinear'] else 'NO'}")
        print(f"Interpretation: {lrt['interpretation']}")
    else:
        print(f"LRT failed: {lrt.get('error', 'Unknown error')}")
    
    print(f"\nFull results saved to: {args.output}")

if __name__ == '__main__':
    main()