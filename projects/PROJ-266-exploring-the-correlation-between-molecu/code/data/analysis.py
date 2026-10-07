import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

# --- Logging Setup ---
def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger(__name__)

# --- Data Loading Helpers ---
def load_analysis_data() -> pd.DataFrame:
    """
    Loads the enriched data required for analysis.
    Expects: data/processed/enriched_data.csv
    """
    path = Path("data/processed/enriched_data.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    df = pd.read_csv(path)
    # Ensure necessary columns exist
    required = ['smiles', 'logPapp', 'mw', 'psa', 'logP', 'dihedral_variance', 'complexity_metric']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    # Drop rows with NaN in critical columns
    df = df.dropna(subset=required)
    return df

def load_scaling_results() -> Optional[Dict[str, Any]]:
    """Loads existing scaling analysis results if they exist."""
    path = Path("data/processed/scaling_analysis_results.json")
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return None

# --- Statistical Utilities ---
def calculate_bivariate_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Pearson and Spearman correlations between flexibility descriptors and logPapp.
    Diagnostic only - no confounder control.
    """
    descriptors = ['bond_variance', 'angle_variance', 'dihedral_variance']
    results = []
    for desc in descriptors:
        if desc not in df.columns:
            continue
        # Pearson
        r_p, p_p = stats.pearsonr(df[desc], df['logPapp'])
        # Spearman
        r_s, p_s = stats.spearmanr(df[desc], df['logPapp'])
        results.append({
            'descriptor': desc,
            'correlation_type': 'pearson',
            'r': r_p,
            'p_value': p_p
        })
        results.append({
            'descriptor': desc,
            'correlation_type': 'spearman',
            'r': r_s,
            'p_value': p_s
        })
    return pd.DataFrame(results)

def calculate_controlled_partial_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes partial correlations between dihedral_variance and logPapp,
    controlling for logP, MW, and PSA.
    """
    # Using scipy's partial correlation approach via residuals
    # Y = logPapp, X = dihedral_variance, Z = [logP, MW, PSA]
    Y = df['logPapp'].values
    X = df['dihedral_variance'].values
    Z = df[['logP', 'mw', 'psa']].values

    # Regress Y on Z
    model_Y = sm.OLS(Y, sm.add_constant(Z)).fit()
    res_Y = model_Y.resid

    # Regress X on Z
    model_X = sm.OLS(X, sm.add_constant(Z)).fit()
    res_X = model_X.resid

    # Correlation of residuals
    r_partial, p_val = stats.pearsonr(res_X, res_Y)

    return pd.DataFrame([{
        'predictor': 'dihedral_variance',
        'controlled_for': ['logP', 'mw', 'psa'],
        'partial_r': r_partial,
        'p_value': p_val
    }])

def apply_benjamini_hochberg_fdr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies Benjamini-Hochberg FDR correction to p-values.
    """
    if df.empty:
        return df
    p_values = df['p_value'].values
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    ranks = np.arange(1, n + 1)
    # BH correction
    q_values = (sorted_p * n) / ranks
    q_values = np.minimum.accumulate(q_values[::-1])[::-1] # Ensure monotonicity
    q_values = np.clip(q_values, 0, 1)
    df = df.copy()
    df['q_value'] = 0.0
    df.loc[sorted_indices, 'q_value'] = q_values
    return df

def check_significance(p_value: float, alpha: float = 0.05) -> bool:
    return p_value < alpha

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculates Variance Inflation Factors for given predictors."""
    X = df[predictors].values
    X = sm.add_constant(X)
    vif_data = {}
    for i, col in enumerate(predictors):
        vif = variance_inflation_factor(X, i+1) # +1 because of const
        vif_data[col] = vif
    return vif_data

# --- Model Fitting ---
def run_multivariate_regression(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs multivariate linear regression: logPapp ~ dihedral_variance + logP + MW + PSA
    """
    predictors = ['dihedral_variance', 'logP', 'mw', 'psa']
    X = df[predictors].values
    y = df['logPapp'].values
    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit()
    
    # Cross-validation (simple k-fold for R2)
    from sklearn.model_selection import cross_val_score
    from sklearn.linear_model import LinearRegression
    sklearn_model = LinearRegression()
    cv_scores = cross_val_score(sklearn_model, X[:, 1:], y, cv=5, scoring='r2')
    
    return {
        'coefficients': dict(zip(['const'] + predictors, model.params)),
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'p_values': model.pvalues[1:].to_dict(), # exclude const
        'cv_r2_mean': float(cv_scores.mean()),
        'cv_r2_std': float(cv_scores.std())
    }

def power_law_model(x, a, b, c):
    """
    Power law model: y = a * x^b + c
    """
    return a * np.power(x, b) + c

def fit_power_law_model(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fits the power law model to logPapp vs complexity_metric.
    """
    x = df['complexity_metric'].values
    y = df['logPapp'].values

    # Filter for positive x to allow power law
    mask = x > 0
    x_fit = x[mask]
    y_fit = y[mask]

    if len(x_fit) < 3:
        raise ValueError("Not enough data points with positive complexity_metric to fit power law.")

    # Initial guess [a, b, c]
    p0 = [1.0, -0.5, 0.0]
    
    try:
        popt, pcov = curve_fit(power_law_model, x_fit, y_fit, p0=p0, maxfev=2000)
        a, b, c = popt
        
        # Calculate R2
        y_pred = power_law_model(x_fit, *popt)
        ss_res = np.sum((y_fit - y_pred) ** 2)
        ss_tot = np.sum((y_fit - np.mean(y_fit)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        # Calculate AIC
        n = len(y_fit)
        k = 3 # a, b, c
        rss = ss_res
        aic = n * np.log(rss / n) + 2 * k
        
        return {
            'parameters': {'a': a, 'b': b, 'c': c},
            'r_squared': r_squared,
            'aic': aic,
            'covariance': pcov.tolist()
        }
    except Exception as e:
        logger.error(f"Power law fitting failed: {e}")
        raise

# --- T027: Model Comparison and Hypothesis Testing ---
def compare_models(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compares the linear model (T019a) against the power-law model (T026)
    using AIC/BIC and F-tests.
    
    Returns a dictionary with comparison metrics and a conclusion.
    """
    # 1. Prepare Data
    X_lin = df[['dihedral_variance', 'logP', 'mw', 'psa']].values
    y = df['logPapp'].values
    X_lin = sm.add_constant(X_lin)
    n = len(y)
    k_lin = 4 # 3 predictors + const
    k_pow = 3 # a, b, c (non-linear, but 3 params)

    # 2. Fit Linear Model
    lin_model = sm.OLS(y, X_lin).fit()
    lin_rss = np.sum(lin_model.resid ** 2)
    lin_aic = lin_model.aic
    lin_bic = lin_model.bic
    lin_r2 = lin_model.rsquared

    # 3. Fit Power Law Model
    # Re-use logic from fit_power_law_model but ensure we get RSS for F-test
    x_pow = df['complexity_metric'].values
    mask = x_pow > 0
    x_pow_fit = x_pow[mask]
    y_pow_fit = y[mask]
    
    p0 = [1.0, -0.5, 0.0]
    try:
        popt, _ = curve_fit(power_law_model, x_pow_fit, y_pow_fit, p0=p0, maxfev=5000)
        y_pred_pow = power_law_model(x_pow_fit, *popt)
        pow_rss = np.sum((y_pow_fit - y_pred_pow) ** 2)
        
        # AIC/BIC for power law
        # Note: For non-linear models, AIC = n*ln(RSS/n) + 2k
        n_pow = len(y_pow_fit)
        pow_aic = n_pow * np.log(pow_rss / n_pow) + 2 * k_pow
        pow_bic = n_pow * np.log(pow_rss / n_pow) + k_pow * np.log(n_pow)
        
        # R2 for power law (on the fitted subset)
        ss_tot_pow = np.sum((y_pow_fit - np.mean(y_pow_fit)) ** 2)
        pow_r2 = 1 - (pow_rss / ss_tot_pow)
        
    except Exception as e:
        logger.error(f"Power law fitting failed during comparison: {e}")
        return {
            'status': 'error',
            'message': f"Could not fit power law model: {e}",
            'linear_metrics': {'r2': lin_r2, 'aic': lin_aic, 'bic': lin_bic}
        }

    # 4. F-Test (Nested Model Approximation)
    # Strictly speaking, linear and power-law are non-nested unless specific constraints apply.
    # However, we can compare their fit quality via AIC/BIC primarily.
    # If we treat them as competing models, the one with lower AIC is preferred.
    # For an F-test like statistic, we can compare RSS if we assume the same N, 
    # but here N differs (power law drops non-positive complexity).
    # We will rely on AIC/BIC difference as the primary metric.
    
    delta_aic = lin_aic - pow_aic
    delta_bic = lin_bic - pow_bic
    
    # Conclusion logic
    conclusion = ""
    if delta_aic > 2:
        conclusion = "Power-law model is significantly better (lower AIC)."
    elif delta_aic < -2:
        conclusion = "Linear model is significantly better (lower AIC)."
    else:
        conclusion = "Models are statistically indistinguishable based on AIC."

    if delta_bic > 2:
        conclusion += " (Power-law preferred by BIC)"
    elif delta_bic < -2:
        conclusion += " (Linear preferred by BIC)"
    
    return {
        'status': 'success',
        'linear_model': {
            'r_squared': float(lin_r2),
            'aic': float(lin_aic),
            'bic': float(lin_bic),
            'rss': float(lin_rss),
            'n': n,
            'k': k_lin
        },
        'power_law_model': {
            'r_squared': float(pow_r2),
            'aic': float(pow_aic),
            'bic': float(pow_bic),
            'rss': float(pow_rss),
            'n': int(n_pow),
            'k': k_pow,
            'parameters': {'a': float(popt[0]), 'b': float(popt[1]), 'c': float(popt[2])}
        },
        'comparison': {
            'delta_aic': float(delta_aic),
            'delta_bic': float(delta_bic),
            'conclusion': conclusion
        }
    }

def main():
    """
    Main entry point for T027: Model Comparison and Hypothesis Testing.
    Reads enriched data, fits models, compares them, and saves results.
    """
    logger.info("Starting T027: Model Comparison and Hypothesis Testing")
    
    try:
        # Load data
        df = load_analysis_data()
        logger.info(f"Loaded {len(df)} records for analysis.")
        
        # Perform comparison
        results = compare_models(df)
        
        # Save results
        output_path = Path("data/processed/scaling_analysis_results.json")
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        logger.info(f"Conclusion: {results.get('comparison', {}).get('conclusion', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()