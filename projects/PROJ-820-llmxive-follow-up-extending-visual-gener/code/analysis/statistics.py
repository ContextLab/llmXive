import json
import os
import sys
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats

class StudyInvalidError(Exception):
    """Raised when the study is deemed invalid due to statistical failures."""
    pass

def calculate_effect_size(p1: float, p2: float) -> float:
    """
    Calculate Cohen's h effect size for two proportions.
    
    Args:
        p1: Proportion for group 1.
        p2: Proportion for group 2.
        
    Returns:
        Cohen's h effect size.
    """
    # Fisher's z-transformation
    def phi(p):
        if p <= 0 or p >= 1:
            p = np.clip(p, 0.001, 0.999)
        return 2 * np.arcsin(np.sqrt(p))
    
    return abs(phi(p1) - phi(p2))

def power_analysis_two_proportions(
    p1: float,
    p2: float,
    n1: int,
    n2: int,
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Perform power analysis for two-proportion test.
    
    Args:
        p1: Expected proportion for group 1.
        p2: Expected proportion for group 2.
        n1: Sample size for group 1.
        n2: Sample size for group 2.
        alpha: Significance level.
        
    Returns:
        Dictionary with power and related metrics.
    """
    effect_size = calculate_effect_size(p1, p2)
    n_total = (n1 * n2) / (n1 + n2)  # Harmonic mean approximation for balanced design
    
    # Power calculation using normal approximation
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = effect_size * np.sqrt(n_total) - z_alpha
    power = stats.norm.cdf(z_beta)
    
    return {
        'effect_size': effect_size,
        'power': power,
        'alpha': alpha,
        'n1': n1,
        'n2': n2,
        'p1': p1,
        'p2': p2
    }

def two_proportion_z_test(
    x1: int,
    n1: int,
    x2: int,
    n2: int,
    alternative: str = 'two-sided'
) -> Tuple[float, float]:
    """
    Perform two-proportion z-test.
    
    Args:
        x1: Number of successes in group 1.
        n1: Total trials in group 1.
        x2: Number of successes in group 2.
        n2: Total trials in group 2.
        alternative: Type of test ('two-sided', 'greater', 'less').
        
    Returns:
        Tuple of (z-statistic, p-value).
    """
    p1 = x1 / n1
    p2 = x2 / n2
    p_pooled = (x1 + x2) / (n1 + n2)
    
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    if se == 0:
        return 0.0, 1.0
        
    z_stat = (p1 - p2) / se
    
    if alternative == 'two-sided':
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    elif alternative == 'greater':
        p_value = 1 - stats.norm.cdf(z_stat)
    elif alternative == 'less':
        p_value = stats.norm.cdf(z_stat)
    else:
        raise ValueError("alternative must be 'two-sided', 'greater', or 'less'")
        
    return z_stat, p_value

def fisher_exact_test(
    x1: int,
    n1_minus_x1: int,
    x2: int,
    n2_minus_x2: int,
    alternative: str = 'two-sided'
) -> Tuple[float, float]:
    """
    Perform Fisher's Exact Test.
    
    Args:
        x1: Successes in group 1.
        n1_minus_x1: Failures in group 1.
        x2: Successes in group 2.
        n2_minus_x2: Failures in group 2.
        alternative: Type of test.
        
    Returns:
        Tuple of (odds ratio, p-value).
    """
    contingency = [[x1, n1_minus_x1], [x2, n2_minus_x2]]
    result = stats.fisher_exact(contingency, alternative=alternative)
    return result[0], result[1]

def select_statistical_test(x1: int, n1: int, x2: int, n2: int) -> str:
    """
    Select the appropriate statistical test based on cell counts.
    
    Args:
        x1: Successes in group 1.
        n1: Total in group 1.
        x2: Successes in group 2.
        n2: Total in group 2.
        
    Returns:
        'fisher' or 'z-test'.
    """
    failures_1 = n1 - x1
    failures_2 = n2 - x2
    
    min_cell = min(x1, failures_1, x2, failures_2)
    
    if min_cell < 5:
        return 'fisher'
    return 'z-test'

def load_evaluation_results(results_dir: str) -> List[Dict[str, Any]]:
    """
    Load all evaluation results from the specified directory.
    
    Args:
        results_dir: Path to the evaluation_results directory.
        
    Returns:
        List of evaluation result dictionaries.
    """
    results = []
    results_path = Path(results_dir)
    
    if not results_path.exists():
        return results
        
    for file_path in results_path.glob('*.json'):
        with open(file_path, 'r') as f:
            results.append(json.load(f))
            
    return results

def aggregate_violation_rates(
    results: List[Dict[str, Any]],
    group_field: str = 'group'
) -> Dict[str, Dict[str, int]]:
    """
    Aggregate violation counts by group.
    
    Args:
        results: List of evaluation result dictionaries.
        group_field: Field name containing the group identifier.
        
    Returns:
        Dictionary mapping group names to {'violations': count, 'total': count}.
    """
    aggregates = {}
    
    for result in results:
        group = result.get(group_field, 'unknown')
        is_violation = result.get('is_violation', False)
        
        if group not in aggregates:
            aggregates[group] = {'violations': 0, 'total': 0}
            
        aggregates[group]['total'] += 1
        if is_violation:
            aggregates[group]['violations'] += 1
            
    return aggregates

def calculate_contradiction_rate(log_data: Dict[str, Any], total_scenes: int) -> float:
    """Calculate contradiction rate percentage."""
    if total_scenes <= 0:
        return 0.0
    contradictions = len(log_data.get('contradictions', []))
    return (contradictions / total_scenes) * 100.0

def verify_contradiction_rate(rate: float, threshold: float = 5.0) -> bool:
    """Verify if contradiction rate is within threshold."""
    return rate <= threshold

def run_power_analysis_and_report(
    results: List[Dict[str, Any]],
    p1_expected: float = 0.5,
    p2_expected: float = 0.3,
    alpha: float = 0.05,
    power_target: float = 0.8,
    output_path: str = 'data/processed/power_analysis_report.json'
) -> Dict[str, Any]:
    """
    Run power analysis and save report.
    
    Args:
        results: Evaluation results to analyze.
        p1_expected: Expected proportion for group 1.
        p2_expected: Expected proportion for group 2.
        alpha: Significance level.
        power_target: Target power.
        output_path: Path to save the report.
        
    Returns:
        Power analysis report dictionary.
        
    Raises:
        StudyInvalidError: If achieved power < target.
    """
    aggregates = aggregate_violation_rates(results)
    
    # Assume first two groups are comparison groups
    groups = list(aggregates.keys())
    if len(groups) < 2:
        raise StudyInvalidError("Insufficient groups for power analysis")
        
    g1, g2 = groups[0], groups[1]
    n1 = aggregates[g1]['total']
    n2 = aggregates[g2]['total']
    
    if n1 == 0 or n2 == 0:
        raise StudyInvalidError("Zero sample size in one or more groups")
        
    analysis = power_analysis_two_proportions(p1_expected, p2_expected, n1, n2, alpha)
    
    report = {
        'effect_size': analysis['effect_size'],
        'achieved_power': analysis['power'],
        'target_power': power_target,
        'alpha': alpha,
        'sample_sizes': {'group1': n1, 'group2': n2},
        'expected_proportions': {'group1': p1_expected, 'group2': p2_expected},
        'power_achieved': analysis['power'] >= power_target,
        'groups_analyzed': groups
    }
    
    # Save report
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    if not report['power_achieved']:
        raise StudyInvalidError(
            f"Power analysis failed: achieved power ({analysis['power']:.3f}) "
            f"below target ({power_target})"
        )
        
    return report

def run_statistical_comparison(
    results: List[Dict[str, Any]],
    group1_name: str,
    group2_name: str
) -> Dict[str, Any]:
    """
    Run the appropriate statistical test between two groups.
    
    Args:
        results: Evaluation results.
        group1_name: Name of the first group.
        group2_name: Name of the second group.
        
    Returns:
        Statistical test results.
    """
    aggregates = aggregate_violation_rates(results)
    
    if group1_name not in aggregates or group2_name not in aggregates:
        raise ValueError(f"Groups not found: {group1_name}, {group2_name}")
        
    g1_data = aggregates[group1_name]
    g2_data = aggregates[group2_name]
    
    x1 = g1_data['violations']
    n1 = g1_data['total']
    x2 = g2_data['violations']
    n2 = g2_data['total']
    
    test_type = select_statistical_test(x1, n1, x2, n2)
    
    result = {
        'test_type': test_type,
        'group1': group1_name,
        'group2': group2_name,
        'group1_violations': x1,
        'group1_total': n1,
        'group2_violations': x2,
        'group2_total': n2
    }
    
    if test_type == 'z-test':
        z_stat, p_value = two_proportion_z_test(x1, n1, x2, n2)
        result['z_statistic'] = z_stat
        result['p_value'] = p_value
    else:
        failures_1 = n1 - x1
        failures_2 = n2 - x2
        odds_ratio, p_value = fisher_exact_test(x1, failures_1, x2, failures_2)
        result['odds_ratio'] = odds_ratio
        result['p_value'] = p_value
        
    return result

def generate_final_analysis_csv(
    results: List[Dict[str, Any]],
    output_path: str,
    comparison_groups: Tuple[str, str] = ('Baseline', 'Experimental')
) -> None:
    """
    Generate the final analysis CSV file.
    
    Args:
        results: Evaluation results.
        output_path: Path to save the CSV.
        comparison_groups: Tuple of (group1, group2) names.
    """
    aggregates = aggregate_violation_rates(results)
    stats_result = run_statistical_comparison(results, comparison_groups[0], comparison_groups[1])
    
    # Calculate Prompt Adherence Rate (1 - violation rate)
    rows = []
    for group, data in aggregates.items():
        if data['total'] > 0:
            violation_rate = data['violations'] / data['total']
            adherence_rate = 1.0 - violation_rate
        else:
            adherence_rate = 0.0
            
        rows.append({
            'group': group,
            'total_scenes': data['total'],
            'violations': data['violations'],
            'violation_rate': violation_rate if data['total'] > 0 else 0.0,
            'Prompt Adherence Rate': adherence_rate
        })
        
    # Add comparison stats
    comparison_row = {
        'group': f"{comparison_groups[0]} vs {comparison_groups[1]}",
        'total_scenes': stats_result['group1_total'] + stats_result['group2_total'],
        'violations': stats_result.get('group1_violations', 0) + stats_result.get('group2_violations', 0),
        'violation_rate': 0.0,
        'Prompt Adherence Rate': 0.0,
        'p_value': stats_result.get('p_value', 0.0),
        'test_type': stats_result['test_type']
    }
    rows.append(comparison_row)
    
    # Write CSV
    import csv
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    """Main entry point for the statistics script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical analysis on evaluation results.')
    parser.add_argument('--results-dir', type=str, required=True,
                      help='Path to evaluation_results directory')
    parser.add_argument('--output-csv', type=str, default='data/processed/final_analysis.csv',
                      help='Path to save final analysis CSV')
    parser.add_argument('--group1', type=str, default='Baseline',
                      help='Name of the first comparison group')
    parser.add_argument('--group2', type=str, default='Experimental',
                      help='Name of the second comparison group')
                      
    args = parser.parse_args()
    
    try:
        results = load_evaluation_results(args.results_dir)
        
        if not results:
            print("No evaluation results found.", file=sys.stderr)
            sys.exit(1)
            
        # Generate final analysis
        generate_final_analysis_csv(results, args.output_csv, (args.group1, args.group2))
        print(f"Final analysis saved to {args.output_csv}")
        
        # Run comparison
        stats_result = run_statistical_comparison(results, args.group1, args.group2)
        print(f"Statistical test: {stats_result['test_type']}")
        print(f"P-value: {stats_result['p_value']:.4f}")
        
    except StudyInvalidError as e:
        print(f"Study invalid: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == '__main__':
    main()
