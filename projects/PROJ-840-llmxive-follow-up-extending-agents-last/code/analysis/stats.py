"""
Statistical analysis module for llmXive.

Implements McNemar's test (primary) and multiple-comparison corrections (Bonferroni, FDR).
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import math

# Conditional import for scipy; fallback to manual calculation if not available
try:
    from scipy.stats import chi2, chi2_contingency, binom_test
    from scipy.stats import fdr_bh as fdr_bh_impl
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    # Fallback implementations
    def chi2_sf(x, df):
        # Survival function for chi-square (approximation for df=1)
        # P(X > x) where X ~ Chi^2(1)
        # Using regularized incomplete beta function approximation or standard normal
        # For df=1, Chi^2 is Z^2. P(Chi^2 > x) = 2 * P(Z > sqrt(x))
        if x < 0:
            return 1.0
        z = math.sqrt(x)
        # Approximation of 1 - Phi(z) using Abramowitz and Stegun
        # 1 - Phi(z) approx t * (a1 + t*(a2 + t*(a3 + t*(a4 + t*a5))))
        # where t = 1 / (1 + p*z), p=0.2316419
        p = 0.2316419
        b1 = 0.319381530
        b2 = -0.356563782
        b3 = 1.781477937
        b4 = -1.821255978
        b5 = 1.330274429
        
        t = 1.0 / (1.0 + p * z)
        poly = t * (b1 + t * (b2 + t * (b3 + t * (b4 + t * b5))))
        # Standard normal PDF
        pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
        return 2 * pdf * poly

    def fdr_bh(p_values):
        """Benjamini-Hochberg FDR correction (manual implementation)."""
        n = len(p_values)
        if n == 0:
            return []
        indexed = sorted(enumerate(p_values), key=lambda x: x[1])
        corrected = [0.0] * n
        min_val = 1.0
        for i in range(n - 1, -1, -1):
            idx, p = indexed[i]
            # Calculate rank (1-based)
            rank = i + 1
            corrected_val = p * n / rank
            if corrected_val < min_val:
                min_val = corrected_val
            else:
                corrected_val = min_val
            corrected[idx] = min(1.0, corrected_val)
        return corrected

def load_json_file(path: str) -> Any:
    """Load a JSON file from the given path."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path: str, data: Any) -> None:
    """Save data to a JSON file at the given path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_pass_rates(baseline_results: List[Dict], intervention_results: List[Dict]) -> Tuple[float, float, int]:
    """
    Calculate pass rates for baseline and intervention.
    
    Returns:
        Tuple of (baseline_pass_rate, intervention_pass_rate, n_pairs)
    """
    if not baseline_results or not intervention_results:
        raise ValueError("Results lists cannot be empty")
    
    if len(baseline_results) != len(intervention_results):
        raise ValueError("Baseline and intervention results must have the same length")
    
    n = len(baseline_results)
    baseline_passes = sum(1 for r in baseline_results if r.get('pass', False))
    intervention_passes = sum(1 for r in intervention_results if r.get('pass', False))
    
    return baseline_passes / n, intervention_passes / n, n

def verify_strict_pairing(baseline_results: List[Dict], intervention_results: List[Dict]) -> bool:
    """
    Verify that baseline and intervention results are strictly paired.
    
    Checks that task_ids match in order and count.
    """
    if len(baseline_results) != len(intervention_results):
        return False
    
    for b, i in zip(baseline_results, intervention_results):
        if b.get('task_id') != i.get('task_id'):
            return False
    
    return True

def mcnemar_test(baseline_results: List[Dict], intervention_results: List[Dict]) -> Dict[str, Any]:
    """
    Perform McNemar's test for paired binary outcomes.
    
    Args:
        baseline_results: List of dicts with 'pass' boolean
        intervention_results: List of dicts with 'pass' boolean
        
    Returns:
        Dict with 'statistic', 'p_value', 'n_pairs', 'contingency_table'
    """
    if not verify_strict_pairing(baseline_results, intervention_results):
        raise ValueError("Results are not strictly paired")
    
    n = len(baseline_results)
    # Contingency table:
    #             Interv: Pass   Interv: Fail
    # Base: Pass      a             b
    # Base: Fail      c             d
    
    a = b = c = d = 0
    for base, inter in zip(baseline_results, intervention_results):
        base_pass = base.get('pass', False)
        inter_pass = inter.get('pass', False)
        
        if base_pass and inter_pass:
            a += 1
        elif base_pass and not inter_pass:
            b += 1
        elif not base_pass and inter_pass:
            c += 1
        else:
            d += 1
    
    contingency = [[a, b], [c, d]]
    
    # McNemar's statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    # Or (b - c)^2 / (b + c) without correction
    # Using continuity correction for small samples
    if (b + c) == 0:
        statistic = 0.0
        p_value = 1.0
    else:
        # Continuity corrected version
        statistic = (abs(b - c) - 1) ** 2 / (b + c)
        if HAS_SCIPY:
            # chi2.sf gives the survival function (1 - cdf)
            p_value = chi2.sf(statistic, 1)
        else:
            p_value = chi2_sf(statistic, 1)
    
    return {
        'statistic': statistic,
        'p_value': p_value,
        'n_pairs': n,
        'contingency_table': {
            'both_pass': a,
            'base_pass_inter_fail': b,
            'base_fail_inter_pass': c,
            'both_fail': d
        }
    }

def mcnemar_asymptotic(baseline_results: List[Dict], intervention_results: List[Dict]) -> Dict[str, Any]:
    """
    Perform McNemar's test without continuity correction (asymptotic).
    
    Returns:
        Dict with 'statistic', 'p_value', 'n_pairs'
    """
    if not verify_strict_pairing(baseline_results, intervention_results):
        raise ValueError("Results are not strictly paired")
    
    n = len(baseline_results)
    b = c = 0
    for base, inter in zip(baseline_results, intervention_results):
        base_pass = base.get('pass', False)
        inter_pass = inter.get('pass', False)
        
        if base_pass and not inter_pass:
            b += 1
        elif not base_pass and inter_pass:
            c += 1
    
    if (b + c) == 0:
        statistic = 0.0
        p_value = 1.0
    else:
        statistic = (b - c) ** 2 / (b + c)
        if HAS_SCIPY:
            p_value = chi2.sf(statistic, 1)
        else:
            p_value = chi2_sf(statistic, 1)
    
    return {
        'statistic': statistic,
        'p_value': p_value,
        'n_pairs': n
    }

def bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of p-values
        
    Returns:
        List of corrected p-values (capped at 1.0)
    """
    n = len(p_values)
    if n == 0:
        return []
    
    corrected = [min(1.0, p * n) for p in p_values]
    return corrected

def fdr_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: List of p-values
        
    Returns:
        List of corrected p-values
    """
    if HAS_SCIPY:
        return fdr_bh_impl(p_values)
    else:
        return fdr_bh(p_values)

def apply_multiple_comparison_correction(p_values: List[float], method: str = 'bonferroni') -> List[float]:
    """
    Apply multiple comparison correction based on the number of hypotheses.
    
    Logic:
    - If only 1 hypothesis (len(p_values) == 1), return original p-values (no correction needed).
    - If > 1 hypothesis, apply the specified correction method.
    
    Args:
        p_values: List of p-values from hypothesis tests
        method: 'bonferroni' or 'fdr'
        
    Returns:
        List of corrected (or original if n=1) p-values
    """
    if len(p_values) <= 1:
        # No correction needed for single hypothesis
        return p_values[:]
    
    if method.lower() == 'bonferroni':
        return bonferroni_correction(p_values)
    elif method.lower() == 'fdr':
        return fdr_correction(p_values)
    else:
        raise ValueError(f"Unknown correction method: {method}")

def calculate_statistical_power(n_pairs: int, effect_size: float = 0.5, alpha: float = 0.05) -> float:
    """
    Estimate statistical power for McNemar's test.
    
    This is a simplified approximation using the normal approximation to the binomial.
    For a more accurate calculation, power analysis for McNemar's test typically
    requires iterative methods or specialized libraries.
    
    Args:
        n_pairs: Number of paired observations
        effect_size: Expected difference in discordant proportions (b - c) / n
        alpha: Significance level
        
    Returns:
        Estimated power (0 to 1)
    """
    # Simplified approximation
    # Under H1, the statistic follows a non-central chi-square distribution
    # Approximating with normal distribution for large n
    if n_pairs < 10:
        return 0.0
    
    # Expected number of discordant pairs under H1
    discordant = n_pairs * abs(effect_size)
    if discordant < 1:
        return 0.0
    
    # Standard error under H0 (for power calculation, we use H1 variance)
    # Approximate power using Z-test logic
    z_alpha = 1.96  # For alpha=0.05 two-tailed
    z_beta = (abs(effect_size) * math.sqrt(n_pairs) - z_alpha) / math.sqrt(1 - effect_size**2) if abs(effect_size) < 1 else 2.0
    
    # Approximate power using standard normal CDF
    # Power = P(Z > z_alpha - effect_size * sqrt(n) / sigma)
    # Simplified:
    power = 0.5 * (1 + math.erf(z_beta / math.sqrt(2)))
    return min(1.0, max(0.0, power))

def run_analysis(baseline_path: str, intervention_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the full statistical analysis pipeline.
    
    1. Load data
    2. Verify pairing
    3. Run McNemar's test
    4. Apply multiple comparison correction (if needed)
    5. Calculate power
    6. Save results
    
    Args:
        baseline_path: Path to baseline results JSON
        intervention_path: Path to intervention results JSON
        output_path: Path to save analysis report
        
    Returns:
        Dict containing the full analysis results
    """
    baseline_results = load_json_file(baseline_path)
    intervention_results = load_json_file(intervention_path)
    
    if not verify_strict_pairing(baseline_results, intervention_results):
        raise ValueError("Strict pairing verification failed")
    
    # Run McNemar's test
    mcnemar_result = mcnemar_test(baseline_results, intervention_results)
    
    # Prepare p-values for correction (here we only have one test, so list has one element)
    # If multiple tests were run (e.g., for different N values), we'd collect them here
    p_values = [mcnemar_result['p_value']]
    
    # Apply multiple comparison correction
    # Since we only have one hypothesis (one McNemar test), correction is skipped
    # but the function handles it gracefully
    corrected_p_values = apply_multiple_comparison_correction(p_values, method='bonferroni')
    mcnemar_result['corrected_p_value'] = corrected_p_values[0]
    mcnemar_result['correction_applied'] = 'none' if len(p_values) == 1 else 'bonferroni'
    
    # Calculate pass rates
    base_rate, inter_rate, n = calculate_pass_rates(baseline_results, intervention_results)
    mcnemar_result['baseline_pass_rate'] = base_rate
    mcnemar_result['intervention_pass_rate'] = inter_rate
    
    # Estimate power
    # Effect size approximation: (b - c) / n
    b = mcnemar_result['contingency_table']['base_pass_inter_fail']
    c = mcnemar_result['contingency_table']['base_fail_inter_pass']
    effect_size = (b - c) / n if n > 0 else 0
    power = calculate_statistical_power(n, effect_size)
    mcnemar_result['estimated_power'] = power
    
    # Prepare final report
    report = {
        'analysis_type': 'McNemar\'s Test with Multiple Comparison Correction',
        'mcnemar_test': mcnemar_result,
        'sample_size': n,
        'pairing_verified': True,
        'methodology_note': 'Spec FR-005 requires McNemar\'s test, overriding Plan.md\'s Mixed-Effects Logistic Regression'
    }
    
    save_json_file(output_path, report)
    return report

def main():
    """CLI entry point for statistical analysis."""
    parser = argparse.ArgumentParser(description="Run statistical analysis on baseline vs intervention results")
    parser.add_argument('--baseline', required=True, help="Path to baseline results JSON")
    parser.add_argument('--intervention', required=True, help="Path to intervention results JSON")
    parser.add_argument('--output', required=True, help="Path to save analysis report JSON")
    parser.add_argument('--correction', default='bonferroni', choices=['bonferroni', 'fdr'], help="Multiple comparison correction method")
    
    args = parser.parse_args()
    
    try:
        report = run_analysis(args.baseline, args.intervention, args.output)
        print(f"Analysis complete. Report saved to {args.output}")
        print(f"McNemar statistic: {report['mcnemar_test']['statistic']:.4f}")
        print(f"Raw p-value: {report['mcnemar_test']['p_value']:.4f}")
        print(f"Corrected p-value: {report['mcnemar_test']['corrected_p_value']:.4f}")
        print(f"Estimated power: {report['mcnemar_test']['estimated_power']:.4f}")
        sys.exit(0)
    except Exception as e:
        print(f"Error running analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()