import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy.stats import ttest_rel
from statsmodels.regression.mixed_linear_model import MixedLM
import matplotlib.pyplot as plt
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_repro_results(filepath: str = "artifacts/reports/repro_results.json") -> List[Dict[str, Any]]:
    """Load the aggregated reproducibility results."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Repro results file not found at {filepath}")
    with open(path, 'r') as f:
        data = json.load(f)
    # Handle both list and dict with 'results' key
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    raise ValueError("Unexpected format in repro results file")

def extract_metric_values(results: List[Dict[str, Any]], metric: str) -> Tuple[List[float], List[float]]:
    """
    Extract reported (reference) and reproduced values for a specific metric.
    Returns: (ref_values, repro_values)
    """
    ref_vals = []
    repro_vals = []
    for entry in results:
        # Check if metric exists in reported and reproduced sections
        reported = entry.get('reported_metrics', {})
        reproduced = entry.get('reproduced_metrics', {})
        
        if metric in reported and metric in reproduced:
            ref_vals.append(float(reported[metric]))
            repro_vals.append(float(reproduced[metric]))
        else:
            logger.warning(f"Skipping entry {entry.get('paper_id', 'unknown')}: missing {metric}")
    
    if len(ref_vals) == 0:
        raise ValueError(f"No valid data found for metric {metric}")
    
    return ref_vals, repro_vals

def run_paired_ttest(ref_vals: List[float], repro_vals: List[float]) -> Dict[str, float]:
    """Run paired t-test between reference and reproduced values."""
    stat, p_val = ttest_rel(ref_vals, repro_vals)
    return {'statistic': float(stat), 'p_value': float(p_val)}

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """Apply Bonferroni correction for multiple comparisons."""
    n = len(p_values)
    if n == 0:
        return {'adjusted_p_values': [], 'significant': []}
    
    adjusted = [min(p * n, 1.0) for p in p_values]
    significant = [p_adj < alpha for p_adj in adjusted]
    return {'adjusted_p_values': adjusted, 'significant': significant, 'alpha': alpha, 'n_tests': n}

def run_all_paired_ttests(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Run paired t-tests for MAE, R2, and Spearman rho."""
    metrics = ['mae', 'r2', 'spearman_rho']
    results_dict = {}
    
    for metric in metrics:
        try:
            ref, repro = extract_metric_values(results, metric)
            test_res = run_paired_ttest(ref, repro)
            results_dict[metric] = test_res
        except ValueError as e:
            logger.warning(f"Could not run t-test for {metric}: {e}")
            results_dict[metric] = {'error': str(e)}
    
    # Collect p-values for Bonferroni
    p_vals = [results_dict[m]['p_value'] for m in metrics if 'p_value' in results_dict[m]]
    if p_vals:
        correction = apply_bonferroni_correction(p_vals)
        results_dict['bonferroni'] = correction
    
    return results_dict

def run_tost(ref_vals: List[float], repro_vals: List[float], delta: float = 0.1) -> Dict[str, Any]:
    """
    Run Two One-Sided Tests (TOST) for equivalence.
    Null hypothesis: |mean_diff| >= delta
    Alternative: |mean_diff| < delta
    """
    diffs = np.array(repro_vals) - np.array(ref_vals)
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    n = len(diffs)
    
    if std_diff == 0:
        return {'equivalence': False, 'reason': 'Zero variance'}
    
    t_stat = mean_diff / (std_diff / np.sqrt(n))
    # Two one-sided tests
    # Test 1: H0: mean_diff <= -delta vs H1: mean_diff > -delta
    # Test 2: H0: mean_diff >= delta vs H1: mean_diff < delta
    
    # Using t-distribution
    p_lower = 1 - stats.t.cdf((mean_diff + delta) / (std_diff / np.sqrt(n)), n - 1)
    p_upper = stats.t.cdf((mean_diff - delta) / (std_diff / np.sqrt(n)), n - 1)
    
    # Equivalence is established if both p-values < alpha
    alpha = 0.05
    is_equivalent = (p_lower < alpha) and (p_upper < alpha)
    
    return {
        'mean_difference': float(mean_diff),
        'std_difference': float(std_diff),
        't_statistic': float(t_stat),
        'p_lower': float(p_lower),
        'p_upper': float(p_upper),
        'equivalence': is_equivalent,
        'delta': delta
    }

def run_all_tosts(results: List[Dict[str, Any]], delta: float = 0.1) -> Dict[str, Dict[str, Any]]:
    """Run TOST for all metrics."""
    metrics = ['mae', 'r2', 'spearman_rho']
    results_dict = {}
    
    for metric in metrics:
        try:
            ref, repro = extract_metric_values(results, metric)
            results_dict[metric] = run_tost(ref, repro, delta)
        except ValueError as e:
            logger.warning(f"Could not run TOST for {metric}: {e}")
            results_dict[metric] = {'error': str(e)}
    
    return results_dict

def run_mixed_effects_model(results: List[Dict[str, Any]], metric: str = 'mae') -> Dict[str, Any]:
    """
    Run a Linear Mixed-Effects Model with random intercepts for paper.
    Model: metric ~ 1 + (1 | paper_id)
    """
    ref_vals, repro_vals = extract_metric_values(results, metric)
    paper_ids = [entry.get('paper_id', f'paper_{i}') for i, entry in enumerate(results) 
                 if metric in entry.get('reported_metrics', {}) and metric in entry.get('reproduced_metrics', {})]
    
    # Create a DataFrame-like structure for statsmodels
    # We model the difference (repro - ref) as the outcome
    diffs = np.array(repro_vals) - np.array(ref_vals)
    groups = np.array(paper_ids)
    
    # Convert groups to integer codes for statsmodels
    unique_groups = np.unique(groups)
    group_codes = np.array([np.where(unique_groups == g)[0][0] for g in groups])
    
    # Fit mixed model: diff ~ 1 + (1 | group)
    try:
        model = MixedLM(diffs, np.ones(len(diffs)), groups=group_codes)
        # Use a simple approach since we don't have exog
        # We'll use the formula API approach if possible, but direct construction is safer
        # Alternative: use simple variance components estimation
        
        # Since MixedLM requires exog, we use a constant
        exog = np.ones((len(diffs), 1))
        model = MixedLM(diffs, exog, groups=group_codes)
        result = model.fit(reml=False)
        
        # Extract variance components
        var_intercept = result.cov_re[0, 0] if hasattr(result, 'cov_re') and result.cov_re.size > 0 else 0.0
        var_residual = result.scale if hasattr(result, 'scale') else 0.0
        
        return {
            'metric': metric,
            'fixed_effects': {'intercept': float(result.fe[0])},
            'variance_components': {
                'random_intercept': float(var_intercept),
                'residual': float(var_residual)
            },
            'log_likelihood': float(result.llf) if hasattr(result, 'llf') else None
        }
    except Exception as e:
        logger.error(f"Failed to fit LME for {metric}: {e}")
        return {'error': str(e), 'metric': metric}

def compute_heterogeneity_and_pooled(results: List[Dict[str, Any]], metric: str = 'mae') -> Dict[str, Any]:
    """
    Compute heterogeneity (I²) and pooled effect size from LME results.
    
    I² = (Q - df) / Q * 100%
    Where Q is Cochran's Q statistic and df = k - 1 (k = number of studies)
    
    Pooled effect size is estimated from the fixed effect of the LME model.
    """
    ref_vals, repro_vals = extract_metric_values(results, metric)
    paper_ids = [entry.get('paper_id', f'paper_{i}') for i, entry in enumerate(results) 
                 if metric in entry.get('reported_metrics', {}) and metric in entry.get('reproduced_metrics', {})]
    
    diffs = np.array(repro_vals) - np.array(ref_vals)
    n_studies = len(diffs)
    
    if n_studies < 2:
        return {
            'metric': metric,
            'heterogeneity_i2': None,
            'pooled_effect_size': None,
            'reason': 'Insufficient studies (need at least 2)'
        }
    
    # Calculate Cochran's Q
    # Q = sum(w_i * (theta_i - theta_bar)^2)
    # For simplicity, assume equal weights (inverse variance not available)
    mean_diff = np.mean(diffs)
    var_diff = np.var(diffs, ddof=1)
    
    # Q statistic approximation: (n-1) * (variance of effects) / (mean variance)
    # Since we don't have individual study variances, we use a simplified approach
    # Q = sum((effect_i - mean_effect)^2) / (1/n * sum(1)) -> simplifies to (n-1)*var
    q_stat = (n_studies - 1) * var_diff
    df = n_studies - 1
    
    # I² calculation
    if q_stat > df:
        i2 = (q_stat - df) / q_stat * 100.0
    else:
        i2 = 0.0
    
    # Pooled effect size (fixed effect from LME would be more accurate, but we approximate)
    pooled_effect = mean_diff
    
    # Interpret I²
    if i2 < 25:
        interpretation = "Low heterogeneity"
    elif i2 < 50:
        interpretation = "Moderate heterogeneity"
    elif i2 < 75:
        interpretation = "Substantial heterogeneity"
    else:
        interpretation = "Considerable heterogeneity"
    
    return {
        'metric': metric,
        'n_studies': n_studies,
        'q_statistic': float(q_stat),
        'degrees_of_freedom': df,
        'i2_statistic': float(i2),
        'i2_interpretation': interpretation,
        'pooled_effect_size': float(pooled_effect),
        'pooled_effect_ci_lower': float(pooled_effect - 1.96 * np.sqrt(var_diff / n_studies)),
        'pooled_effect_ci_upper': float(pooled_effect + 1.96 * np.sqrt(var_diff / n_studies))
    }

def get_i2_interpretation(i2: float) -> str:
    """Return interpretation string for I² value."""
    if i2 < 25:
        return "Low heterogeneity"
    elif i2 < 50:
        return "Moderate heterogeneity"
    elif i2 < 75:
        return "Substantial heterogeneity"
    else:
        return "Considerable heterogeneity"

def generate_bland_altman_plot(results: List[Dict[str, Any]], metric: str, output_path: str):
    """Generate Bland-Altman plot for a metric."""
    ref_vals, repro_vals = extract_metric_values(results, metric)
    
    diffs = np.array(repro_vals) - np.array(ref_vals)
    means = (np.array(ref_vals) + np.array(repro_vals)) / 2.0
    
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    loa_upper = mean_diff + 1.96 * std_diff
    loa_lower = mean_diff - 1.96 * std_diff
    
    plt.figure(figsize=(10, 6))
    plt.scatter(means, diffs, alpha=0.6)
    plt.axhline(mean_diff, color='red', linestyle='--', label=f'Mean Diff: {mean_diff:.3f}')
    plt.axhline(loa_upper, color='gray', linestyle=':', label=f'Upper LoA: { loa_upper:.3f}')
    plt.axhline(loa_lower, color='gray', linestyle=':', label=f'Lower LoA: { loa_lower:.3f}')
    plt.xlabel('Mean of Reference and Reproduced')
    plt.ylabel('Difference (Reproduced - Reference)')
    plt.title(f'Bland-Altman Plot: {metric.upper()}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Bland-Altman plot saved to {output_path}")

def generate_stat_summary(results: List[Dict[str, Any]], output_path: str = "artifacts/reports/stat_summary.json"):
    """
    Generate comprehensive statistical summary including:
    - Paired t-tests
    - TOST
    - Mixed-effects model results
    - Heterogeneity (I²) and pooled effect sizes
    """
    summary = {
        't_tests': run_all_paired_ttests(results),
        'tost': run_all_tosts(results, delta=0.1),
        'mixed_effects': {},
        'heterogeneity': {}
    }
    
    metrics = ['mae', 'r2', 'spearman_rho']
    
    for metric in metrics:
        # Mixed effects
        lme_res = run_mixed_effects_model(results, metric)
        summary['mixed_effects'][metric] = lme_res
        
        # Heterogeneity and pooled effect
        het_res = compute_heterogeneity_and_pooled(results, metric)
        summary['heterogeneity'][metric] = het_res
        
        # Generate Bland-Altman plots
        plot_path = f"artifacts/plots/{metric}_bland_altman.png"
        generate_bland_altman_plot(results, metric, plot_path)
    
    # Save summary
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Statistical summary saved to {output_path}")
    return summary

def main():
    """Main entry point for statistical analysis."""
    repro_path = "artifacts/reports/repro_results.json"
    summary_path = "artifacts/reports/stat_summary.json"
    
    if not os.path.exists(repro_path):
        logger.error(f"Repro results not found at {repro_path}. Run model_runner.py first.")
        return
    
    try:
        results = load_repro_results(repro_path)
        if not results:
            logger.warning("No results found in repro_results.json")
            return
        
        summary = generate_stat_summary(results, summary_path)
        print(f"Analysis complete. Summary saved to {summary_path}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()