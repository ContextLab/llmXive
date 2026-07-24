import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy import stats
from scipy.stats import chi2
import json
import os
from pathlib import Path
import math

def load_json_file(path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    with open(path, 'r') as f:
        return json.load(f)

def calculate_pass_rates(baseline_results: List[Dict], intervention_results: List[Dict]) -> Tuple[float, float]:
    """Calculate pass rates for baseline and intervention conditions."""
    if not baseline_results or not intervention_results:
        raise ValueError("Results lists cannot be empty")
    
    baseline_pass = sum(1 for r in baseline_results if r.get('pass', False))
    intervention_pass = sum(1 for r in intervention_results if r.get('pass', False))
    
    return baseline_pass / len(baseline_results), intervention_pass / len(intervention_results)

def verify_strict_pairing(baseline_results: List[Dict], intervention_results: List[Dict]) -> bool:
    """Verify that baseline and intervention results are strictly paired by task_id."""
    baseline_ids = {r['task_id'] for r in baseline_results}
    intervention_ids = {r['task_id'] for r in intervention_results}
    
    if baseline_ids != intervention_ids:
        return False
    
    return True

def mcnemar_test(baseline_results: List[Dict], intervention_results: List[Dict]) -> Tuple[float, float]:
    """
    Perform McNemar's test for paired binary outcomes.
    
    Returns:
        Tuple of (chi2_statistic, p_value)
    """
    # Create 2x2 contingency table
    # a: baseline pass, intervention pass
    # b: baseline pass, intervention fail
    # c: baseline fail, intervention pass
    # d: baseline fail, intervention fail
    
    a = b = c = d = 0
    
    baseline_dict = {r['task_id']: r['pass'] for r in baseline_results}
    intervention_dict = {r['task_id']: r['pass'] for r in intervention_results}
    
    for task_id in baseline_dict:
        baseline_pass = baseline_dict[task_id]
        intervention_pass = intervention_dict[task_id]
        
        if baseline_pass and intervention_pass:
            a += 1
        elif baseline_pass and not intervention_pass:
            b += 1
        elif not baseline_pass and intervention_pass:
            c += 1
        else:
            d += 1
    
    # McNemar's test statistic: (|b - c| - 1)^2 / (b + c)
    # Using continuity correction
    if b + c == 0:
        return 0.0, 1.0
    
    chi2_stat = (abs(b - c) - 1) ** 2 / (b + c)
    p_value = 1 - chi2.cdf(chi2_stat, df=1)
    
    return chi2_stat, p_value

def mcnemar_asymptotic(baseline_results: List[Dict], intervention_results: List[Dict]) -> Tuple[float, float]:
    """
    Perform McNemar's test using the asymptotic distribution (no continuity correction).
    
    Returns:
        Tuple of (chi2_statistic, p_value)
    """
    a = b = c = d = 0
    
    baseline_dict = {r['task_id']: r['pass'] for r in baseline_results}
    intervention_dict = {r['task_id']: r['pass'] for r in intervention_results}
    
    for task_id in baseline_dict:
        baseline_pass = baseline_dict[task_id]
        intervention_pass = intervention_dict[task_id]
        
        if baseline_pass and intervention_pass:
            a += 1
        elif baseline_pass and not intervention_pass:
            b += 1
        elif not baseline_pass and intervention_pass:
            c += 1
        else:
            d += 1
    
    if b + c == 0:
        return 0.0, 1.0
    
    chi2_stat = (b - c) ** 2 / (b + c)
    p_value = 1 - chi2.cdf(chi2_stat, df=1)
    
    return chi2_stat, p_value

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Bonferroni correction to multiple p-values."""
    n = len(p_values)
    if n == 0:
        return []
    
    corrected_p = [min(p * n, 1.0) for p in p_values]
    return corrected_p

def fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction to multiple p-values."""
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and calculate adjusted values
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    adjusted_p = [0.0] * n
    
    for rank, idx in enumerate(sorted_indices):
        adjusted_p[idx] = min(p_values[idx] * n / (rank + 1), 1.0)
    
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])
    
    return adjusted_p

def apply_multiple_comparison_correction(p_values: List[float], method: str = 'bonferroni', alpha: float = 0.05) -> List[float]:
    """Apply multiple comparison correction based on the specified method."""
    if len(p_values) <= 1:
        return p_values
    
    if method == 'bonferroni':
        return bonferroni_correction(p_values, alpha)
    elif method == 'fdr':
        return fdr_correction(p_values, alpha)
    else:
        raise ValueError(f"Unknown correction method: {method}")

def calculate_statistical_power(n: int, effect_size: float = 0.5, alpha: float = 0.05) -> float:
    """
    Calculate the statistical power of McNemar's test given sample size and effect size.
    
    This is an approximation using the normal distribution.
    
    Args:
        n: Sample size (number of paired observations)
        effect_size: Expected effect size (difference in proportions)
        alpha: Significance level (default 0.05)
    
    Returns:
        Statistical power (probability of correctly rejecting null hypothesis)
    """
    if n <= 0:
        return 0.0
    
    # For McNemar's test, we approximate power using the normal approximation
    # The effect size is typically measured as the difference in discordant proportions
    
    # Standard error under null hypothesis
    se_null = np.sqrt(1 / n)
    
    # Critical value for the test
    z_critical = stats.norm.ppf(1 - alpha / 2)
    
    # Non-centrality parameter
    delta = effect_size / se_null
    
    # Power calculation
    power = stats.norm.cdf(delta - z_critical) + stats.norm.cdf(-delta - z_critical)
    
    return max(0.0, min(1.0, power))

def run_analysis(baseline_results: List[Dict], intervention_results: List[Dict], 
                 correction_method: str = 'bonferroni', alpha: float = 0.05,
                 effect_size_estimate: float = 0.5) -> Dict[str, Any]:
    """
    Run the complete statistical analysis including McNemar's test and power calculation.
    
    Args:
        baseline_results: List of baseline execution results
        intervention_results: List of intervention execution results
        correction_method: Method for multiple comparison correction
        alpha: Significance level
        effect_size_estimate: Estimated effect size for power calculation
    
    Returns:
        Dictionary containing analysis results
    """
    # Verify strict pairing
    is_paired = verify_strict_pairing(baseline_results, intervention_results)
    if not is_paired:
        raise ValueError("Results are not strictly paired. Cannot proceed with McNemar's test.")
    
    # Calculate pass rates
    baseline_pass_rate, intervention_pass_rate = calculate_pass_rates(
        baseline_results, intervention_results
    )
    
    # Perform McNemar's test
    chi2_stat, p_value = mcnemar_test(baseline_results, intervention_results)
    
    # Apply multiple comparison correction if needed
    corrected_p_value = p_value
    if len([p_value]) > 1:
        corrected_p_values = apply_multiple_comparison_correction([p_value], correction_method, alpha)
        corrected_p_value = corrected_p_values[0]
    
    # Calculate statistical power
    sample_size = len(baseline_results)
    power = calculate_statistical_power(sample_size, effect_size_estimate, alpha)
    
    return {
        'sample_size': sample_size,
        'baseline_pass_rate': baseline_pass_rate,
        'intervention_pass_rate': intervention_pass_rate,
        'chi2_statistic': chi2_stat,
        'p_value': p_value,
        'corrected_p_value': corrected_p_value,
        'statistical_power': power,
        'power_threshold_met': power >= 0.8,
        'alpha': alpha,
        'effect_size_estimate': effect_size_estimate,
        'correction_method': correction_method,
        'strict_pairing_verified': is_paired
    }

def main():
    """Main entry point for running statistical analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical analysis on baseline and intervention results.')
    parser.add_argument('--baseline', type=str, required=True, help='Path to baseline results JSON')
    parser.add_argument('--intervention', type=str, required=True, help='Path to intervention results JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to output stats report JSON')
    parser.add_argument('--correction', type=str, default='bonferroni', help='Multiple comparison correction method')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--effect-size', type=float, default=0.5, help='Estimated effect size for power calculation')
    
    args = parser.parse_args()
    
    # Load results
    baseline_results = load_json_file(args.baseline)
    intervention_results = load_json_file(args.intervention)
    
    # Run analysis
    results = run_analysis(
        baseline_results, 
        intervention_results,
        correction_method=args.correction,
        alpha=args.alpha,
        effect_size_estimate=args.effect_size
    )
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete. Results written to {args.output}")
    print(f"Sample size: {results['sample_size']}")
    print(f"Baseline pass rate: {results['baseline_pass_rate']:.3f}")
    print(f"Intervention pass rate: {results['intervention_pass_rate']:.3f}")
    print(f"Chi-square statistic: {results['chi2_statistic']:.3f}")
    print(f"P-value: {results['p_value']:.4f}")
    print(f"Statistical power: {results['statistical_power']:.3f}")
    print(f"Power threshold (0.8) met: {results['power_threshold_met']}")

if __name__ == '__main__':
    main()