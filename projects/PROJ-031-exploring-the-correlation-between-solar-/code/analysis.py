import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
import os
import json
import logging
from typing import Dict, Any, Optional, Tuple, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation and p-value.
    
    Args:
        df: DataFrame containing the data
        x_col: Column name for the independent variable
        y_col: Column name for the dependent variable
        
    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    # Drop rows with NaN in either column
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 3:
        logger.warning(f"Insufficient data for Spearman correlation ({len(valid_data)} rows)")
        return 0.0, 1.0
    
    corr, p_value = stats.spearmanr(valid_data[x_col], valid_data[y_col])
    return corr, p_value

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        df: DataFrame containing the features and target
        features: List of feature column names
        
    Returns:
        Dictionary mapping feature names to VIF values
    """
    X = df[features].dropna()
    if len(X) < len(features) + 1:
        logger.warning(f"Insufficient data for VIF calculation ({len(X)} rows)")
        return {f: float('inf') for f in features}
    
    X = add_constant(X)
    vif_data = {}
    for i, col in enumerate(features):
        vif_data[col] = variance_inflation_factor(X.values, i + 1)  # +1 because of constant
    return vif_data

def linear_regression_r2(df: pd.DataFrame, x_col: str, y_col: str) -> float:
    """
    Calculate R² for a simple linear regression.
    
    Args:
        df: DataFrame containing the data
        x_col: Column name for the independent variable
        y_col: Column name for the dependent variable
        
    Returns:
        R² value
    """
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 3:
        logger.warning(f"Insufficient data for linear regression ({len(valid_data)} rows)")
        return 0.0
    
    X = add_constant(valid_data[x_col])
    y = valid_data[y_col]
    model = OLS(y, X).fit()
    return model.rsquared

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level
        
    Returns:
        Tuple of (corrected p-values, significance flags)
    """
    n = len(p_values)
    if n == 0:
        return [], []
    
    corrected_p = [min(p * n, 1.0) for p in p_values]
    significant = [p < alpha for p in corrected_p]
    return corrected_p, significant

def power_analysis(n: int, effect_size: float = 0.30, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis.
    
    Args:
        n: Sample size
        effect_size: Expected effect size (correlation coefficient)
        alpha: Significance level
        
    Returns:
        Dictionary with power analysis results
    """
    from statsmodels.stats.power import TTestIndPower
    
    # For correlation, we can approximate using t-test power
    # Power = 1 - beta, where beta is Type II error rate
    # Using a simplified approach for correlation power analysis
    if n < 30:
        logger.warning(f"Sample size ({n}) is small (< 30). Power may be low.")
        power_warning = True
    else:
        power_warning = False
    
    # Calculate approximate power for correlation
    # Using the formula for correlation power: t = r * sqrt((n-2)/(1-r^2))
    # Then find the probability of exceeding critical t-value
    if n > 2:
        df = n - 2
        t_critical = stats.t.ppf(1 - alpha/2, df)
        # Non-centrality parameter
        ncp = effect_size * np.sqrt(n - 2) / np.sqrt(1 - effect_size**2)
        # Power is the probability of rejecting null when alternative is true
        # This is approximate; exact calculation requires non-central t-distribution
        power = 1 - stats.t.cdf(t_critical, df, ncp) + stats.t.cdf(-t_critical, df, ncp)
        power = max(0.0, min(1.0, power))
    else:
        power = 0.0
    
    # Calculate minimum detectable effect size for 80% power
    # Solving for r in the power formula
    target_power = 0.80
    if n > 2:
        # Iterative approach to find minimum detectable effect size
        min_effect = 0.01
        for _ in range(100):
            ncp_test = min_effect * np.sqrt(n - 2) / np.sqrt(1 - min_effect**2)
            power_test = 1 - stats.t.cdf(t_critical, df, ncp_test) + stats.t.cdf(-t_critical, df, ncp_test)
            if power_test >= target_power:
                break
            min_effect += 0.001
    else:
        min_effect = 1.0
    
    return {
        'min_detectable_effect_size': round(min_effect, 4),
        'power_warning_flag': power_warning,
        'sample_size': n,
        'assumed_effect_size': effect_size,
        'alpha': alpha
    }

def test_piecewise_model(df: pd.DataFrame, x_col: str, y_col: str, threshold_percentile: float = 50.0) -> Dict[str, Any]:
    """
    Test a piecewise (non-linear) model to see if it improves fit over linear model.
    This is triggered when R² < 0.1 for the linear model.
    
    The piecewise model fits two separate linear regressions on either side of a threshold.
    The threshold is determined by the specified percentile of the independent variable.
    
    Args:
        df: DataFrame containing the data
        x_col: Column name for the independent variable
        y_col: Column name for the dependent variable
        threshold_percentile: Percentile to use as split point (default: 50th = median)
        
    Returns:
        Dictionary with piecewise model results and improvement metrics
    """
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 10:
        logger.warning(f"Insufficient data for piecewise model ({len(valid_data)} rows)")
        return {
            'piecewise_r2': 0.0,
            'linear_r2': 0.0,
            'improvement': 0.0,
            'threshold_value': None,
            'sample_size': len(valid_data),
            'status': 'insufficient_data'
        }
    
    # Calculate linear model R²
    X_linear = add_constant(valid_data[x_col])
    y = valid_data[y_col]
    linear_model = OLS(y, X_linear).fit()
    linear_r2 = linear_model.rsquared
    
    # If linear R² >= 0.1, piecewise model is not needed per task requirements
    if linear_r2 >= 0.1:
        return {
            'piecewise_r2': linear_r2,
            'linear_r2': linear_r2,
            'improvement': 0.0,
            'threshold_value': None,
            'sample_size': len(valid_data),
            'status': 'linear_model_sufficient'
        }
    
    # Find threshold value based on percentile
    threshold_value = np.percentile(valid_data[x_col], threshold_percentile)
    
    # Split data at threshold
    below_threshold = valid_data[valid_data[x_col] <= threshold_value]
    above_threshold = valid_data[valid_data[x_col] > threshold_value]
    
    # Need sufficient data in both segments
    if len(below_threshold) < 3 or len(above_threshold) < 3:
        logger.warning("Insufficient data in either segment for piecewise model")
        return {
            'piecewise_r2': linear_r2,
            'linear_r2': linear_r2,
            'improvement': 0.0,
            'threshold_value': threshold_value,
            'sample_size': len(valid_data),
            'status': 'insufficient_segments'
        }
    
    # Fit piecewise model: two separate linear regressions
    # We'll calculate the weighted R² for the combined model
    # R² for piecewise = 1 - (SS_res_piecewise / SS_tot)
    ss_tot = np.sum((y - np.mean(y))**2)
    
    # Predictions from piecewise model
    y_pred = np.zeros_like(y)
    
    # Fit model for below threshold
    if len(below_threshold) >= 3:
        X_below = add_constant(below_threshold[x_col])
        model_below = OLS(below_threshold[y_col], X_below).fit()
        y_pred[valid_data[x_col] <= threshold_value] = model_below.predict(X_below)
    
    # Fit model for above threshold
    if len(above_threshold) >= 3:
        X_above = add_constant(above_threshold[x_col])
        model_above = OLS(above_threshold[y_col], X_above).fit()
        y_pred[valid_data[x_col] > threshold_value] = model_above.predict(X_above)
    
    # Calculate residual sum of squares for piecewise model
    ss_res_piecewise = np.sum((y - y_pred)**2)
    
    # Calculate R² for piecewise model
    if ss_tot > 0:
        piecewise_r2 = 1 - (ss_res_piecewise / ss_tot)
    else:
        piecewise_r2 = 0.0
    
    # Ensure R² is in valid range
    piecewise_r2 = max(0.0, min(1.0, piecewise_r2))
    
    # Calculate improvement
    improvement = piecewise_r2 - linear_r2
    
    status = 'piecewise_improvement' if improvement > 0 else 'piecewise_no_improvement'
    
    logger.info(f"Piecewise model test: linear R²={linear_r2:.4f}, piecewise R²={piecewise_r2:.4f}, improvement={improvement:.4f}")
    
    return {
        'piecewise_r2': round(piecewise_r2, 6),
        'linear_r2': round(linear_r2, 6),
        'improvement': round(improvement, 6),
        'threshold_value': round(float(threshold_value), 4),
        'sample_size': len(valid_data),
        'status': status
    }

def run_correlation_analysis(df: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline.
    
    Args:
        df: DataFrame with aligned events
        output_path: Path to write metrics.json
        
    Returns:
        Dictionary with all analysis results
    """
    logger.info("Starting correlation analysis...")
    
    results = {}
    
    # 1. Spearman correlations
    # Log10(flare flux) -> Dst
    if 'flare_flux_log10' in df.columns and 'dst' in df.columns:
        corr_flare, p_flare = spearman_correlation(df, 'flare_flux_log10', 'dst')
        results['flare_dst_spearman'] = {
            'correlation': round(corr_flare, 6),
            'p_value': round(p_flare, 6)
        }
    else:
        logger.warning("Missing flare_flux_log10 or dst columns for Spearman correlation")
        results['flare_dst_spearman'] = {'correlation': None, 'p_value': None}
    
    # CME speed -> Dst
    if 'cme_speed' in df.columns and 'dst' in df.columns:
        corr_cme, p_cme = spearman_correlation(df, 'cme_speed', 'dst')
        results['cme_dst_spearman'] = {
            'correlation': round(corr_cme, 6),
            'p_value': round(p_cme, 6)
        }
    else:
        logger.warning("Missing cme_speed or dst columns for Spearman correlation")
        results['cme_dst_spearman'] = {'correlation': None, 'p_value': None}
    
    # 2. VIF calculation
    if 'flare_flux_log10' in df.columns and 'cme_speed' in df.columns:
        vif_features = ['flare_flux_log10', 'cme_speed']
        # Drop rows with NaN in either feature
        valid_for_vif = df[vif_features].dropna()
        if len(valid_for_vif) >= len(vif_features) + 1:
            vif_results = calculate_vif(valid_for_vif, vif_features)
            results['vif'] = {k: round(v, 4) for k, v in vif_results.items()}
            
            # 3. Linear regression and model selection
            max_vif = max(vif_results.values())
            if max_vif > 5:
                logger.info(f"VIF > 5 detected ({max_vif:.2f}). Switching to univariate models.")
                # Select univariate model with higher absolute correlation
                abs_corr_flare = abs(corr_flare) if corr_flare is not None else 0
                abs_corr_cme = abs(corr_cme) if corr_cme is not None else 0
                
                if abs_corr_flare >= abs_corr_cme:
                    selected_model = 'univariate_flare'
                    selected_r2 = linear_regression_r2(df, 'flare_flux_log10', 'dst')
                else:
                    selected_model = 'univariate_cme'
                    selected_r2 = linear_regression_r2(df, 'cme_speed', 'dst')
                
                results['model_selection'] = {
                    'strategy': 'univariate',
                    'selected_model': selected_model,
                    'max_vif': round(max_vif, 4),
                    'selected_model_r2': round(selected_r2, 6)
                }
                results['joint_model_r2'] = None
            else:
                # Joint model
                valid_for_regression = df[['flare_flux_log10', 'cme_speed', 'dst']].dropna()
                if len(valid_for_regression) >= 3:
                    X = add_constant(valid_for_regression[['flare_flux_log10', 'cme_speed']])
                    y = valid_for_regression['dst']
                    model = OLS(y, X).fit()
                    joint_r2 = model.rsquared
                    results['joint_model_r2'] = round(joint_r2, 6)
                    results['model_selection'] = {
                        'strategy': 'joint',
                        'max_vif': round(max_vif, 4),
                        'selected_model_r2': round(joint_r2, 6)
                    }
                else:
                    results['joint_model_r2'] = None
                    results['model_selection'] = {'strategy': 'insufficient_data'}
        else:
            results['vif'] = {'insufficient_data': True}
            results['model_selection'] = {'strategy': 'insufficient_data'}
    else:
        results['vif'] = {'missing_columns': True}
        results['model_selection'] = {'strategy': 'missing_columns'}
    
    # 4. Bonferroni correction
    p_values = []
    if results['flare_dst_spearman']['p_value'] is not None:
        p_values.append(results['flare_dst_spearman']['p_value'])
    if results['cme_dst_spearman']['p_value'] is not None:
        p_values.append(results['cme_dst_spearman']['p_value'])
    
    if p_values:
        corrected_p, significant = bonferroni_correction(p_values)
        results['corrected_p_values'] = {
            'flare_dst': round(corrected_p[0], 6) if len(corrected_p) > 0 else None,
            'cme_dst': round(corrected_p[1], 6) if len(corrected_p) > 1 else None
        }
        results['significance_flags'] = {
            'flare_dst': significant[0] if len(significant) > 0 else None,
            'cme_dst': significant[1] if len(significant) > 1 else None
        }
        results['correction_method'] = 'bonferroni'
    else:
        results['corrected_p_values'] = {}
        results['significance_flags'] = {}
        results['correction_method'] = 'bonferroni'
    
    # 5. Power analysis
    valid_count = df[['dst']].dropna().shape[0]
    power_results = power_analysis(valid_count)
    results['power_analysis'] = power_results
    
    # 6. Piecewise model test (T026)
    # Check if linear model R² < 0.1
    selected_r2_for_piecewise = None
    if 'model_selection' in results and 'selected_model_r2' in results['model_selection']:
        selected_r2_for_piecewise = results['model_selection']['selected_model_r2']
    elif 'joint_model_r2' in results and results['joint_model_r2'] is not None:
        selected_r2_for_piecewise = results['joint_model_r2']
    
    if selected_r2_for_piecewise is not None and selected_r2_for_piecewise < 0.1:
        logger.info(f"Linear R² ({selected_r2_for_piecewise:.4f}) < 0.1. Testing piecewise model...")
        
        # Determine which variable to use for piecewise based on model selection
        if results['model_selection'].get('selected_model') == 'univariate_flare':
            piecewise_x = 'flare_flux_log10'
        elif results['model_selection'].get('selected_model') == 'univariate_cme':
            piecewise_x = 'cme_speed'
        else:
            # Default to flare if joint model or no clear selection
            piecewise_x = 'flare_flux_log10'
        
        if piecewise_x in df.columns and 'dst' in df.columns:
            piecewise_results = test_piecewise_model(df, piecewise_x, 'dst')
            results['piecewise_model'] = piecewise_results
            results['piecewise_r2_improvement'] = piecewise_results['improvement']
            logger.info(f"Piecewise model improvement: {piecewise_results['improvement']:.6f}")
        else:
            results['piecewise_model'] = {'status': 'missing_columns'}
            results['piecewise_r2_improvement'] = 0.0
    else:
        if selected_r2_for_piecewise is not None:
            logger.info(f"Linear R² ({selected_r2_for_piecewise:.4f}) >= 0.1. Skipping piecewise model test.")
        else:
            logger.info("No linear R² available for piecewise model test.")
        results['piecewise_model'] = {'status': 'not_tested'}
        results['piecewise_r2_improvement'] = 0.0
    
    # 7. Write results to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results written to {output_path}")
    return results

def main():
    """Main entry point for the analysis module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run correlation analysis on aligned events')
    parser.add_argument('--input', type=str, default='data/processed/aligned_events.csv',
                      help='Path to aligned events CSV')
    parser.add_argument('--output', type=str, default='results/metrics.json',
                      help='Path to output metrics JSON')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        return
    
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    logger.info(f"Loaded {len(df)} rows")
    results = run_correlation_analysis(df, args.output)
    
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()