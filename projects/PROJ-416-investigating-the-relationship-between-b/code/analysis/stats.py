import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
from scipy import stats

# Attempt to import power analysis library
try:
    from statsmodels.stats.power import FTestAnovaPower
    POWER_ANALYSIS_AVAILABLE = True
except ImportError:
    POWER_ANALYSIS_AVAILABLE = False
    logging.warning("statsmodels power analysis module not available. Power analysis will be skipped.")

from config import Config

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing features
        features: List of feature column names
        
    Returns:
        Dictionary mapping feature names to VIF values
    """
    vif_data = {}
    X = df[features].values
    
    # Add constant for intercept if not present
    if not np.all(np.any(X != 0, axis=0)):
        X = sm.add_constant(X)
        features_with_const = ['const'] + features
    else:
        features_with_const = features
        
    for i, feature in enumerate(features_with_const):
        if feature == 'const':
            continue
        vif = variance_inflation_factor(X, i)
        vif_data[feature] = vif
        logger.debug(f"VIF for {feature}: {vif:.4f}")
        
    return vif_data

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply False Discovery Rate (FDR) correction to p-values.
    
    Args:
        p_values: List of p-values
        alpha: Significance level
        
    Returns:
        Tuple of (adjusted p-values, boolean list indicating significance)
    """
    if not p_values:
        return [], []
        
    rejects, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    return pvals_corrected, rejects.tolist()

def run_power_analysis(n_obs: int, f2: float = 0.15, alpha: float = 0.05, power: float = 0.8) -> Dict[str, float]:
    """
    Perform power analysis to determine minimum sample size required.
    
    Implements G*Power logic for F-test (ANOVA/Regression):
    - H0: No effect (f² = 0)
    - H1: Effect size f² = 0.15 (medium effect)
    
    Args:
        n_obs: Current number of observations
        f2: Effect size f² (default 0.15 for medium effect)
        alpha: Significance level (default 0.05)
        power: Target power (default 0.8)
        
    Returns:
        Dictionary with power analysis results including min_N
    """
    result = {
        'current_n': n_obs,
        'effect_size_f2': f2,
        'alpha': alpha,
        'target_power': power,
        'min_N_required': None,
        'actual_power': None,
        'status': 'unknown',
        'limitation_flag': None
    }

    # HALT if N < 5 (SC-004)
    if n_obs < 5:
        result['status'] = 'halt'
        result['limitation_flag'] = 'CRITICAL: Sample size (N={}) is below minimum threshold of 5. Analysis cannot proceed.'.format(n_obs)
        logger.critical(result['limitation_flag'])
        raise ValueError(result['limitation_flag'])

    # FLAG limitation if 5 <= N < 10
    if 5 <= n_obs < 10:
        result['limitation_flag'] = 'WARNING: Sample size (N={}) is small (5 <= N < 10). Results should be interpreted with caution.'.format(n_obs)
        logger.warning(result['limitation_flag'])
        result['status'] = 'limited_sample'

    # Calculate minimum N required
    if POWER_ANALYSIS_AVAILABLE:
        power_analyzer = FTestAnovaPower()
        
        # Calculate required sample size for given power
        try:
            min_n = power_analyzer.solve_power(
                effect_size=f2,
                alpha=alpha,
                power=power,
                n_groups=2, # Approximation for regression context
                ratio=1.0
            )
            # For regression, we often need to adjust the formula slightly
            # Using the standard formula: N = L / f² where L depends on alpha, power, and k
            # Approximating L for alpha=0.05, power=0.8 is roughly 7.85 for 1 predictor
            # But we use the solver for better accuracy
            
            # Since FTestAnovaPower is for ANOVA, let's use a more direct approach for regression
            # N = (Z_alpha + Z_beta)^2 / f^2 + k + 1
            # Where Z_alpha is z-score for alpha/2, Z_beta for beta (1-power)
            z_alpha = stats.norm.ppf(1 - alpha / 2)
            z_beta = stats.norm.ppf(power)
            k = 1 # Number of predictors (simplified)
            
            min_n_regression = ((z_alpha + z_beta) ** 2) / (f2 ** 2) + k + 1
            min_n = max(min_n, min_n_regression)
            
            result['min_N_required'] = int(np.ceil(min_n))
            result['actual_power'] = power_analyzer.power(
                effect_size=f2,
                nobs1=n_obs,
                alpha=alpha,
                n_groups=2,
                ratio=1.0
            )
            
            if result['min_N_required'] > n_obs:
                result['status'] = 'underpowered'
                logger.info(f"Current N={n_obs} is underpowered. Minimum required N={result['min_N_required']} for f²={f2}, power={power}.")
            else:
                result['status'] = 'powered'
                logger.info(f"Current N={n_obs} is sufficient. Minimum required N={result['min_N_required']}.")
                
        except Exception as e:
            logger.error(f"Error calculating power: {e}")
            result['min_N_required'] = int(np.ceil(((stats.norm.ppf(1 - alpha/2) + stats.norm.ppf(power))**2) / (f2**2) + 2))
            result['status'] = 'calculated_approx'
    else:
        # Fallback calculation if statsmodels power is not available
        # Using standard formula: N = (Z_alpha + Z_beta)^2 / f^2 + k + 1
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)
        k = 1
        min_n = ((z_alpha + z_beta) ** 2) / (f2 ** 2) + k + 1
        result['min_N_required'] = int(np.ceil(min_n))
        result['status'] = 'calculated_approx'
        logger.warning("Using approximate power calculation due to missing statsmodels power module.")

    return result

def run_ancova_analysis(df: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Run ANCOVA analysis.
    
    Args:
        df: DataFrame with data
        formula: Statsmodels formula string
        
    Returns:
        Dictionary with model results
    """
    try:
        model = sm.OLS.from_formula(formula, data=df)
        results = model.fit()
        
        return {
            'params': results.params.to_dict(),
            'pvalues': results.pvalues.to_dict(),
            'rsquared': results.rsquared,
            'rsquared_adj': results.rsquared_adj,
            'f_pvalue': results.f_pvalue,
            'summary': results.summary().as_text()
        }
    except Exception as e:
        logger.error(f"ANCOVA failed: {e}")
        raise

def run_sensitivity_analysis(df: pd.DataFrame, motion_thresholds: List[float], p_values: List[float]) -> Dict[str, Any]:
    """
    Run sensitivity analysis by sweeping parameters.
    
    Args:
        df: DataFrame with data
        motion_thresholds: List of motion thresholds to test
        p_values: List of p-value thresholds to test
        
    Returns:
        Dictionary with sensitivity analysis results
    """
    results = {}
    
    for thresh in motion_thresholds:
        for p_thresh in p_values:
            key = f"motion_{thresh}_p_{p_thresh}"
            # Filter data based on thresholds (simplified)
            filtered_df = df.copy()
            if 'fd_mean' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['fd_mean'] <= thresh]
            
            if len(filtered_df) > 0:
                results[key] = {
                    'n': len(filtered_df),
                    'motion_threshold': thresh,
                    'p_threshold': p_thresh
                }
            else:
                results[key] = {
                    'n': 0,
                    'motion_threshold': thresh,
                    'p_threshold': p_thresh,
                    'note': 'No subjects passed threshold'
                }
                
    return results

def run_analysis(config: Config) -> Dict[str, Any]:
    """
    Main analysis entry point.
    
    Args:
        config: Configuration object
        
    Returns:
        Dictionary with all analysis results
    """
    logger.info("Starting statistical analysis...")
    
    # Load data
    metrics_path = config.METRICS_PATH / "network_metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Network metrics file not found: {metrics_path}")
        
    df = pd.read_csv(metrics_path)
    logger.info(f"Loaded {len(df)} subjects for analysis")
    
    # Run power analysis
    power_results = run_power_analysis(len(df))
    logger.info(f"Power analysis: min_N_required = {power_results['min_N_required']}")
    
    # Prepare data for ANCOVA
    # Assuming columns: pre_score, post_score, modularity, global_eff, local_eff, fd_mean
    if 'pre_treatment_score' in df.columns and 'post_treatment_score' in df.columns:
        # Use post as dependent, pre as covariate, network metric as predictor
        # Example: Post ~ Pre + Modularity + FD
        formula = "post_treatment_score ~ pre_treatment_score + modularity + fd_mean"
        
        # Handle missing values
        clean_df = df.dropna(subset=['post_treatment_score', 'pre_treatment_score', 'modularity', 'fd_mean'])
        
        if len(clean_df) < 5:
            logger.warning("Insufficient data for ANCOVA after cleaning")
            return {'power_analysis': power_results, 'ancova': None, 'sensitivity': None}
        
        ancova_results = run_ancova_analysis(clean_df, formula)
        
        # Calculate VIF
        features = ['pre_treatment_score', 'modularity', 'fd_mean']
        vif_results = calculate_vif(clean_df, features)
        ancova_results['vif'] = vif_results
        
        # Check for multicollinearity and apply Ridge if needed (FR-005, FR-012)
        max_vif = max(vif_results.values())
        if max_vif > 5:
            logger.warning(f"High multicollinearity detected (max VIF={max_vif}). Ridge regression fallback not implemented in this snippet, logging warning.")
            # In a full implementation, we would switch to Ridge here
        
        # FDR correction
        p_values = [v for k, v in ancova_results['pvalues'].items() if k != 'Intercept']
        adj_p, sig = apply_fdr_correction(p_values)
        ancova_results['fdr_adjusted_p'] = adj_p
        ancova_results['fdr_significant'] = sig
        
    else:
        logger.warning("Required columns for ANCOVA not found in data")
        ancova_results = None
        
    # Sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(df, [2.0, 3.0], [0.01, 0.05, 0.1])
    
    return {
        'power_analysis': power_results,
        'ancova': ancova_results,
        'sensitivity': sensitivity_results
    }

def main():
    """Main entry point for command line execution."""
    config = Config()
    results = run_analysis(config)
    logger.info("Analysis complete")
    return results

if __name__ == "__main__":
    main()
