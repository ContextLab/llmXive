import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

# Ensure logging is configured
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_repro_results(file_path: str) -> List[Dict[str, Any]]:
    """Load the aggregated reproducibility results from JSON."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Reproducibility results file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'results' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        logger.warning(f"Unexpected format in {file_path}, treating root as list")
        return [data] if isinstance(data, dict) else []

def extract_metric_values(results: List[Dict[str, Any]], metric_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract reported (reference) and reproduced values for a specific metric.
    Returns (ref_values, reproduced_values) as numpy arrays.
    """
    ref_vals = []
    rep_vals = []
    
    for res in results:
        # Look for metric in various possible locations
        # Common structure: {'reported_metrics': {'MAE': ...}, 'reproduced_metrics': {'MAE': ...}}
        reported = res.get('reported_metrics', {})
        reproduced = res.get('reproduced_metrics', {})
        
        ref = reported.get(metric_name)
        rep = reproduced.get(metric_name)
        
        if ref is not None and rep is not None:
            ref_vals.append(float(ref))
            rep_vals.append(float(rep))
        else:
            logger.debug(f"Skipping result {res.get('paper_id', 'unknown')}: missing {metric_name}")
    
    if len(ref_vals) == 0:
        raise ValueError(f"No valid pairs found for metric {metric_name}")
    
    return np.array(ref_vals), np.array(rep_vals)

def run_paired_ttest(ref: np.ndarray, rep: np.ndarray) -> Dict[str, float]:
    """Run paired t-test and return t-statistic and p-value."""
    t_stat, p_val = stats.ttest_rel(ref, rep)
    return {'t_statistic': float(t_stat), 'p_value': float(p_val)}

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """Apply Bonferroni correction for multiple comparisons."""
    n_tests = len(p_values)
    if n_tests == 0:
        return {'adjusted_p_values': [], 'is_significant': False}
    
    adjusted_p = [min(p * n_tests, 1.0) for p in p_values]
    is_sig = any(p < alpha for p in adjusted_p)
    
    return {
        'adjusted_p_values': adjusted_p,
        'alpha': alpha,
        'is_significant': is_sig
    }

def run_all_paired_ttests(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run paired t-tests for MAE, R2, and Spearman rho."""
    metrics = ['MAE', 'R2', 'Spearman_rho']
    results_dict = {}
    
    p_values = []
    
    for metric in metrics:
        try:
            ref, rep = extract_metric_values(results, metric)
            test_res = run_paired_ttest(ref, rep)
            results_dict[metric] = test_res
            p_values.append(test_res['p_value'])
        except ValueError as e:
            logger.warning(f"Could not run t-test for {metric}: {e}")
            results_dict[metric] = {'error': str(e)}
    
    if p_values:
        correction = apply_bonferroni_correction(p_values)
        results_dict['bonferroni'] = correction
    
    return results_dict

def run_tost(ref: np.ndarray, rep: np.ndarray, delta: float = 0.1) -> Dict[str, Any]:
    """
    Run Two One-Sided Tests (TOST) for equivalence.
    H0: |ref - rep| >= delta vs H1: |ref - rep| < delta
    """
    diff = ref - rep
    n = len(diff)
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    
    if std_diff == 0:
        return {'equivalence': True, 'p_value': 0.0, 'message': 'Zero variance'}
    
    # t-statistic for lower bound (mean_diff - (-delta)) / SE
    t_lower = (mean_diff - (-delta)) / (std_diff / np.sqrt(n))
    # t-statistic for upper bound (mean_diff - delta) / SE
    t_upper = (mean_diff - delta) / (std_diff / np.sqrt(n))
    
    # One-sided p-values
    p_lower = 1 - stats.t.cdf(t_lower, df=n-1)
    p_upper = stats.t.cdf(t_upper, df=n-1)
    
    # Equivalence is established if both p-values are < alpha
    alpha = 0.05
    is_equivalent = (p_lower < alpha) and (p_upper < alpha)
    
    return {
        'is_equivalent': is_equivalent,
        'p_lower': float(p_lower),
        'p_upper': float(p_upper),
        'mean_difference': float(mean_diff),
        'delta': delta
    }

def run_all_tosts(results: List[Dict[str, Any]], delta: float = 0.1) -> Dict[str, Any]:
    """Run TOST for MAE, R2, and Spearman rho."""
    metrics = ['MAE', 'R2', 'Spearman_rho']
    results_dict = {}
    
    for metric in metrics:
        try:
            ref, rep = extract_metric_values(results, metric)
            tost_res = run_tost(ref, rep, delta)
            results_dict[metric] = tost_res
        except ValueError as e:
            logger.warning(f"Could not run TOST for {metric}: {e}")
            results_dict[metric] = {'error': str(e)}
    
    return results_dict

def run_mixed_effects_model(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run Linear Mixed-Effects Model with random intercepts for paper.
    Model: metric ~ 1 + (1 | paper_id)
    We stack all metrics (MAE, R2, Spearman_rho) into a long format.
    """
    # Prepare data for LME
    # We will analyze the difference (reproduced - reported) as the response
    # with paper_id as the random effect grouping variable.
    
    data_rows = []
    
    for res in results:
        paper_id = res.get('paper_id', 'unknown')
        reported = res.get('reported_metrics', {})
        reproduced = res.get('reproduced_metrics', {})
        
        for metric in ['MAE', 'R2', 'Spearman_rho']:
            ref = reported.get(metric)
            rep = reproduced.get(metric)
            
            if ref is not None and rep is not None:
                diff = float(rep) - float(ref)
                data_rows.append({
                    'paper_id': paper_id,
                    'metric': metric,
                    'difference': diff,
                    'reported': float(ref),
                    'reproduced': float(rep)
                })
    
    if len(data_rows) == 0:
        raise ValueError("No data points for mixed-effects model")
    
    df = pd.DataFrame(data_rows)
    
    # Convert to numeric
    df['difference'] = pd.to_numeric(df['difference'], errors='coerce')
    df = df.dropna(subset=['difference'])
    
    if len(df) == 0:
        raise ValueError("No valid data points after dropping NaN")
    
    # Fit LME: difference ~ 1 + (1 | paper_id)
    # We treat 'metric' as a fixed effect if we want to compare across metrics,
    # but for heterogeneity of the overall effect, we might just use intercept.
    # However, to get a pooled effect size for the overall reproducibility,
    # we can include 'metric' as a fixed effect to control for it.
    
    # Let's try: difference ~ C(metric) + (1 | paper_id)
    # This gives us a pooled estimate adjusted for metric type.
    
    try:
        md = smf.mixedlm("difference ~ C(metric)", df, groups=df["paper_id"])
        mdf = md.fit()
        
        # Extract variance components
        var_comp = mdf.cov_re.iloc[0, 0] if hasattr(mdf, 'cov_re') and mdf.cov_re is not None else 0.0
        
        # Fixed effects: the intercept is the pooled effect size (overall mean difference)
        # The coefficient for C(metric) indicates differences between metrics
        fixed_effects = mdf.params.to_dict()
        
        return {
            'pooled_effect_size': float(fixed_effects.get('Intercept', 0.0)),
            'variance_components': {
                'paper_random_intercept': float(var_comp),
                'residual_variance': float(mdf.scale)
            },
            'fixed_effects': fixed_effects,
            'log_likelihood': float(mdf.llf),
            'aic': float(mdf.aic),
            'bic': float(mdf.bic),
            'n_obs': len(df),
            'n_groups': df['paper_id'].nunique()
        }
    except Exception as e:
        logger.error(f"Failed to fit LME model: {e}")
        return {'error': str(e)}

def compute_heterogeneity_and_pooled(lme_results: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute I² heterogeneity and pooled effect size from LME results.
    
    I² = (Q - df) / Q * 100%
    where Q is Cochran's Q statistic and df = k - 1.
    
    For this implementation, we approximate I² using the variance components
    from the LME model:
    I² ≈ σ²_between / (σ²_between + σ²_within)
    
    The pooled effect size is the fixed effect intercept from the LME model.
    """
    if 'error' in lme_results:
        return {'error': lme_results['error'], 'I_squared': None, 'pooled_effect_size': None}
    
    var_between = lme_results.get('variance_components', {}).get('paper_random_intercept', 0.0)
    var_within = lme_results.get('variance_components', {}).get('residual_variance', 1.0)
    
    # Avoid division by zero
    if var_between == 0 and var_within == 0:
        i_squared = 0.0
    else:
        total_var = var_between + var_within
        if total_var == 0:
            i_squared = 0.0
        else:
            i_squared = (var_between / total_var) * 100.0
    
    # Pooled effect size is the intercept from fixed effects
    pooled_effect = lme_results.get('pooled_effect_size', 0.0)
    
    return {
        'I_squared': float(i_squared),
        'pooled_effect_size': float(pooled_effect),
        'variance_between': float(var_between),
        'variance_within': float(var_within),
        'interpretation': get_i2_interpretation(i_squared)
    }

def get_i2_interpretation(i2: float) -> str:
    """Provide a qualitative interpretation of I² value."""
    if i2 < 25:
        return "Low heterogeneity"
    elif i2 < 50:
        return "Moderate heterogeneity"
    elif i2 < 75:
        return "Substantial heterogeneity"
    else:
        return "Considerable heterogeneity"

def generate_bland_altman_plot(results: List[Dict[str, Any]], metric: str, output_path: str) -> None:
    """
    Generate Bland-Altman plot for a specific metric.
    X-axis: Average of (reported, reproduced)
    Y-axis: Difference (reproduced - reported)
    """
    import matplotlib.pyplot as plt
    
    ref, rep = extract_metric_values(results, metric)
    diff = rep - ref
    avg = (ref + rep) / 2.0
    
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    loa_upper = mean_diff + 1.96 * std_diff
    loa_lower = mean_diff - 1.96 * std_diff
    
    plt.figure(figsize=(10, 6))
    plt.scatter(avg, diff, alpha=0.6, edgecolors='k')
    plt.axhline(mean_diff, color='r', linestyle='--', label=f'Mean Diff = {mean_diff:.3f}')
    plt.axhline(loa_upper, color='g', linestyle=':', label=f'LoA Upper = { loa_upper:.3f}')
    plt.axhline(loa_lower, color='g', linestyle=':', label=f'LoA Lower = { loa_lower:.3f}')
    
    plt.xlabel(f'Average of {metric}')
    plt.ylabel(f'Difference ({metric})')
    plt.title(f'Bland-Altman Plot for {metric}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Bland-Altman plot saved to {output_path}")

def generate_stat_summary(results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """
    Generate the comprehensive statistical summary including:
    - Paired t-tests
    - TOST (equivalence)
    - Mixed-effects model
    - Heterogeneity (I²) and pooled effect size
    - Bland-Altman plots
    """
    logger.info("Generating statistical summary...")
    
    # 1. Paired t-tests
    ttest_results = run_all_paired_ttests(results)
    
    # 2. TOST
    tost_results = run_all_tosts(results, delta=0.1)
    
    # 3. Mixed-effects model
    try:
        lme_results = run_mixed_effects_model(results)
        hetero_results = compute_heterogeneity_and_pooled(lme_results, results)
    except Exception as e:
        logger.error(f"LME model failed: {e}")
        lme_results = {'error': str(e)}
        hetero_results = {'error': str(e)}
    
    # 4. Generate Bland-Altman plots
    bland_altman_paths = {}
    for metric in ['MAE', 'R2', 'Spearman_rho']:
        plot_path = f"artifacts/plots/{metric.lower()}_bland_altman.png"
        try:
            generate_bland_altman_plot(results, metric, plot_path)
            bland_altman_paths[metric] = plot_path
        except Exception as e:
            logger.error(f"Failed to generate Bland-Altman for {metric}: {e}")
            bland_altman_paths[metric] = {'error': str(e)}
    
    # Compile final summary
    summary = {
        'paired_t_tests': ttest_results,
        'tost_equivalence': tost_results,
        'mixed_effects_model': lme_results,
        'heterogeneity_and_pooled': hetero_results,
        'bland_altman_plots': bland_altman_paths
    }
    
    # Write to file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Statistical summary saved to {output_path}")
    return summary

def main():
    """Main entry point for the stats module."""
    repro_results_path = "artifacts/reports/repro_results.json"
    stat_summary_path = "artifacts/reports/stat_summary.json"
    
    if not os.path.exists(repro_results_path):
        logger.error(f"Input file not found: {repro_results_path}")
        logger.error("Please run the reproducibility assessment first (code/main.py).")
        sys.exit(1)
    
    try:
        results = load_repro_results(repro_results_path)
        if not results:
            logger.warning("No results found in the input file.")
            sys.exit(0)
        
        summary = generate_stat_summary(results, stat_summary_path)
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        logger.exception(f"Error in stats pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
