import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy import stats
from scipy.stats import chi2
import json
import os

def load_json_file(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r') as f:
        return json.load(f)

def calculate_pass_rates(baseline_results: List[Dict[str, Any]], intervention_results: List[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Calculates pass rates for baseline and intervention.
    """
    baseline_pass = sum(1 for r in baseline_results if r.get('pass', False))
    baseline_total = len(baseline_results)
    baseline_rate = baseline_pass / baseline_total if baseline_total > 0 else 0.0
    
    intervention_pass = sum(1 for r in intervention_results if r.get('pass', False))
    intervention_total = len(intervention_results)
    intervention_rate = intervention_pass / intervention_total if intervention_total > 0 else 0.0
    
    return baseline_rate, intervention_rate

def verify_strict_pairing(baseline_results: List[Dict[str, Any]], intervention_results: List[Dict[str, Any]]) -> bool:
    """
    Verifies that baseline and intervention results are strictly paired.
    """
    baseline_ids = set(r['task_id'] for r in baseline_results)
    intervention_ids = set(r['task_id'] for r in intervention_results)
    
    return baseline_ids == intervention_ids

def mcnemar_test(baseline_results: List[Dict[str, Any]], intervention_results: List[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Performs McNemar's test on paired binary outcomes.
    Returns (chi2_statistic, p_value)
    """
    # Create contingency table
    # a: baseline pass, intervention pass
    # b: baseline pass, intervention fail
    # c: baseline fail, intervention pass
    # d: baseline fail, intervention fail
    
    a = b = c = d = 0
    
    baseline_map = {r['task_id']: r['pass'] for r in baseline_results}
    intervention_map = {r['task_id']: r['pass'] for r in intervention_results}
    
    for task_id in baseline_map:
        baseline_pass = baseline_map[task_id]
        intervention_pass = intervention_map[task_id]
        
        if baseline_pass and intervention_pass:
            a += 1
        elif baseline_pass and not intervention_pass:
            b += 1
        elif not baseline_pass and intervention_pass:
            c += 1
        else:
            d += 1
    
    # McNemar's test statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    if b + c == 0:
        return 0.0, 1.0
    
    chi2_stat = (abs(b - c) - 1) ** 2 / (b + c)
    p_value = 1 - chi2.cdf(chi2_stat, 1)
    
    return chi2_stat, p_value

def mcnemar_asymptotic(baseline_results: List[Dict[str, Any]], intervention_results: List[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Asymptotic version of McNemar's test.
    """
    return mcnemar_test(baseline_results, intervention_results)

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Applies Bonferroni correction to p-values.
    """
    n = len(p_values)
    corrected = [min(p * n, 1.0) for p in p_values]
    return corrected

def fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Applies Benjamini-Hochberg FDR correction to p-values.
    """
    n = len(p_values)
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    corrected = [0.0] * n
    
    for i in sorted_indices:
        rank = sorted_indices.index(i) + 1
        corrected[i] = min(p_values[i] * n / rank, 1.0)
    
    return corrected

def apply_multiple_comparison_correction(p_values: List[float], method: str = 'bonferroni', alpha: float = 0.05) -> List[float]:
    """
    Applies multiple comparison correction based on the specified method.
    """
    if method == 'bonferroni':
        return bonferroni_correction(p_values, alpha)
    elif method == 'fdr':
        return fdr_correction(p_values, alpha)
    else:
        return p_values

def run_analysis(baseline_path: str, intervention_path: str, output_path: str) -> Dict[str, Any]:
    """
    Runs the full statistical analysis and generates the report.
    """
    baseline_results = load_json_file(baseline_path)
    intervention_results = load_json_file(intervention_path)
    
    # Verify strict pairing
    if not verify_strict_pairing(baseline_results, intervention_results):
        raise ValueError("Baseline and intervention results are not strictly paired")
    
    baseline_rate, intervention_rate = calculate_pass_rates(baseline_results, intervention_results)
    chi2_stat, p_value = mcnemar_test(baseline_results, intervention_results)
    
    report = {
        "baseline_pass_rate": baseline_rate,
        "intervention_pass_rate": intervention_rate,
        "mcnemar_chi2": chi2_stat,
        "mcnemar_p_value": p_value,
        "significant": p_value < 0.05
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run statistical analysis on baseline and intervention results")
    parser.add_argument("--baseline", type=str, default="data/processed/baseline_results.json", help="Baseline results JSON")
    parser.add_argument("--intervention", type=str, default="data/processed/intervention_results.json", help="Intervention results JSON")
    parser.add_argument("--output", type=str, default="data/processed/stats_report.json", help="Output stats report JSON")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.baseline):
        print(f"Error: Baseline file not found: {args.baseline}")
        sys.exit(1)
    
    if not os.path.exists(args.intervention):
        print(f"Error: Intervention file not found: {args.intervention}")
        sys.exit(1)
    
    report = run_analysis(args.baseline, args.intervention, args.output)
    print(f"Analysis complete. Report saved to {args.output}")
    print(f"Baseline pass rate: {report['baseline_pass_rate']:.4f}")
    print(f"Intervention pass rate: {report['intervention_pass_rate']:.4f}")
    print(f"McNemar p-value: {report['mcnemar_p_value']:.4f}")
    print(f"Significant: {report['significant']}")

if __name__ == "__main__":
    main()
