import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy import stats
from scipy.stats import chi2
import json
import os

def mcnemar_test(baseline_results: List[bool], intervention_results: List[bool]) -> Dict[str, Any]:
    """
    Perform McNemar's test on paired binary outcomes.
    
    Args:
        baseline_results: List of boolean outcomes (True=Pass, False=Fail) for baseline.
        intervention_results: List of boolean outcomes (True=Pass, False=Fail) for intervention.
        
    Returns:
        Dictionary containing test statistic, p-value, and contingency counts.
    """
    if len(baseline_results) != len(intervention_results):
        raise ValueError("Baseline and intervention results must have the same length.")
    
    n = len(baseline_results)
    # Contingency table counts
    # n_11: Both pass, n_00: Both fail
    # n_10: Baseline pass, Intervention fail
    # n_01: Baseline fail, Intervention pass
    
    n_11 = sum(1 for b, i in zip(baseline_results, intervention_results) if b and i)
    n_00 = sum(1 for b, i in zip(baseline_results, intervention_results) if not b and not i)
    n_10 = sum(1 for b, i in zip(baseline_results, intervention_results) if b and not i)
    n_01 = sum(1 for b, i in zip(baseline_results, intervention_results) if not b and i)
    
    # McNemar's test statistic (chi-squared with continuity correction)
    # chi2 = (|n_01 - n_10| - 1)^2 / (n_01 + n_10)
    if (n_01 + n_10) == 0:
        statistic = 0.0
        p_value = 1.0
    else:
        statistic = (abs(n_01 - n_10) - 1)**2 / (n_01 + n_10)
        p_value = 1 - chi2.cdf(statistic, 1)
        
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "n_11": n_11,
        "n_00": n_00,
        "n_10": n_10,
        "n_01": n_01,
        "total_pairs": n
    }

def mcnemar_asymptotic(baseline_results: List[bool], intervention_results: List[bool]) -> Dict[str, Any]:
    """
    Perform McNemar's test without continuity correction (asymptotic).
    
    Args:
        baseline_results: List of boolean outcomes.
        intervention_results: List of boolean outcomes.
        
    Returns:
        Dictionary containing test statistic and p-value.
    """
    if len(baseline_results) != len(intervention_results):
        raise ValueError("Baseline and intervention results must have the same length.")
        
    n_10 = sum(1 for b, i in zip(baseline_results, intervention_results) if b and not i)
    n_01 = sum(1 for b, i in zip(baseline_results, intervention_results) if not b and i)
    
    if (n_01 + n_10) == 0:
        statistic = 0.0
        p_value = 1.0
    else:
        # Asymptotic version: chi2 = (n_01 - n_10)^2 / (n_01 + n_10)
        statistic = (n_01 - n_10)**2 / (n_01 + n_10)
        p_value = 1 - chi2.cdf(statistic, 1)
        
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "n_10": n_10,
        "n_01": n_01
    }

def calculate_pass_rates(results: List[bool]) -> Dict[str, float]:
    """
    Calculate the pass rate from a list of boolean outcomes.
    
    Args:
        results: List of boolean outcomes.
        
    Returns:
        Dictionary with 'pass_rate' and 'total_count'.
    """
    if not results:
        return {"pass_rate": 0.0, "total_count": 0}
    
    passes = sum(1 for r in results if r)
    total = len(results)
    return {
        "pass_rate": float(passes) / float(total),
        "total_count": total
    }

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        Dictionary containing corrected p-values and boolean significance flags.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {
            "corrected_p_values": [],
            "significant": [],
            "alpha": alpha,
            "n_tests": 0
        }
        
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]
    significant = [p < alpha for p in corrected_p_values]
    
    return {
        "corrected_p_values": corrected_p_values,
        "significant": significant,
        "alpha": alpha,
        "n_tests": n_tests
    }

def fdr_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg False Discovery Rate (FDR) correction.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        Dictionary containing corrected p-values and boolean significance flags.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {
            "corrected_p_values": [],
            "significant": [],
            "alpha": alpha,
            "n_tests": 0
        }
        
    # Sort p-values and track original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate BH critical values
    # q_i = (i / m) * alpha
    # Corrected p-value = min(p_j * m / j for j >= i)
    
    corrected_sorted = []
    running_min = 1.0
    
    # Iterate backwards to ensure monotonicity
    for i in range(n_tests - 1, -1, -1):
        rank = i + 1
        raw_p = sorted_p_values[i]
        critical_value = (rank / n_tests) * alpha
        
        # BH adjusted p-value calculation
        # p_adj = min(p_j * m / j for j >= i)
        # But we can compute it incrementally backwards
        adj_p = min(running_min, raw_p * n_tests / rank)
        running_min = adj_p
        corrected_sorted.append(adj_p)
        
    corrected_sorted.reverse()
    
    # Map back to original order
    corrected_p_values = [0.0] * n_tests
    for i, idx in enumerate(sorted_indices):
        corrected_p_values[idx] = corrected_sorted[i]
        
    significant = [p < alpha for p in corrected_p_values]
    
    return {
        "corrected_p_values": corrected_p_values,
        "significant": significant,
        "alpha": alpha,
        "n_tests": n_tests
    }

def run_analysis(baseline_file: str, intervention_file: str, output_file: str, 
                 correction_method: str = "bonferroni", alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run full statistical analysis including McNemar's test and multiple comparison correction.
    
    Args:
        baseline_file: Path to JSON file containing baseline results.
        intervention_file: Path to JSON file containing intervention results.
        output_file: Path to write the analysis report.
        correction_method: 'bonferroni' or 'fdr'.
        alpha: Significance level.
        
    Returns:
        Dictionary containing the full analysis results.
    """
    # Load data
    with open(baseline_file, 'r') as f:
        baseline_data = json.load(f)
    with open(intervention_file, 'r') as f:
        intervention_data = json.load(f)
        
    # Extract outcomes (assuming 'outcomes' key with boolean values)
    baseline_outcomes = baseline_data.get('outcomes', [])
    intervention_outcomes = intervention_data.get('outcomes', [])
    
    if len(baseline_outcomes) != len(intervention_outcomes):
        raise ValueError(f"Outcome counts mismatch: {len(baseline_outcomes)} vs {len(intervention_outcomes)}")
    
    # Run McNemar's test
    mcnemar_result = mcnemar_test(baseline_outcomes, intervention_outcomes)
    
    # Calculate pass rates
    baseline_rates = calculate_pass_rates(baseline_outcomes)
    intervention_rates = calculate_pass_rates(intervention_outcomes)
    
    # Prepare p-values for correction (in this case, we have one test, but the structure supports multiple)
    p_values = [mcnemar_result['p_value']]
    
    # Apply correction
    if correction_method.lower() == "bonferroni":
        correction_result = bonferroni_correction(p_values, alpha)
    elif correction_method.lower() == "fdr":
        correction_result = fdr_correction(p_values, alpha)
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    # Compile report
    report = {
        "mcnemar_test": mcnemar_result,
        "baseline_pass_rate": baseline_rates,
        "intervention_pass_rate": intervention_rates,
        "correction_method": correction_method,
        "alpha": alpha,
        "correction_result": correction_result,
        "conclusion": "Significant improvement" if correction_result['significant'][0] else "No significant improvement"
    }
    
    # Write output
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
        
    return report

def main():
    """Main entry point for CLI execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Statistical Analysis for ALE Intervention")
    parser.add_argument("--baseline", type=str, required=True, help="Path to baseline results JSON")
    parser.add_argument("--intervention", type=str, required=True, help="Path to intervention results JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output report JSON")
    parser.add_argument("--method", type=str, default="bonferroni", choices=["bonferroni", "fdr"], 
                        help="Multiple comparison correction method")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    
    args = parser.parse_args()
    
    try:
        result = run_analysis(args.baseline, args.intervention, args.output, args.method, args.alpha)
        print(f"Analysis complete. Report saved to {args.output}")
        print(f"Conclusion: {result['conclusion']} (p={result['mcnemar_test']['p_value']:.4f}, corrected p={result['correction_result']['corrected_p_values'][0]:.4f})")
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()