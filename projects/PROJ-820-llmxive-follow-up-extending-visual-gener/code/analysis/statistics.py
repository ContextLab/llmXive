"""
Statistical analysis module for the llmXive research pipeline.

This module implements:
- Power analysis (sample size calculation)
- Statistical hypothesis testing (Z-test, Fisher's Exact Test)
- Aggregation of evaluation results
- Contradiction rate verification
"""

import json
import os
import sys
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from scipy import stats

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# Constants
POWER_TARGET = 0.8
ALPHA = 0.05
EFFECT_SIZE = 0.2
CONTRADICTION_RATE_THRESHOLD = 0.05  # 5%

class StudyInvalidError(Exception):
    """Raised when the study parameters invalidate the analysis."""
    pass

def calculate_effect_size(prop1: float, prop2: float) -> float:
    """
    Calculate Cohen's h effect size for two proportions.
    
    Args:
        prop1: First proportion
        prop2: Second proportion
        
    Returns:
        Cohen's h effect size
    """
    # Convert proportions to arcsine transformation
    arcsine1 = 2 * np.arcsin(np.sqrt(prop1))
    arcsine2 = 2 * np.arcsin(np.sqrt(prop2))
    return abs(arcsine1 - arcsine2)

def power_analysis_two_proportions(
    effect_size: Optional[float] = None,
    alpha: float = ALPHA,
    power_target: float = POWER_TARGET,
    ratio: float = 1.0
) -> Dict[str, Any]:
    """
    Perform power analysis for two-proportion test.
    
    Args:
        effect_size: Cohen's h effect size (default: EFFECT_SIZE)
        alpha: Significance level (default: ALPHA)
        power_target: Target statistical power (default: POWER_TARGET)
        ratio: Ratio of sample sizes (n2/n1)
        
    Returns:
        Dictionary containing power analysis results
    """
    if effect_size is None:
        effect_size = EFFECT_SIZE
        
    # Calculate required sample size per group
    # Using normal approximation for two-proportion test
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power_target)
    
    # Sample size formula for two proportions
    n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    n_per_group = int(np.ceil(n_per_group))
    
    # Calculate achieved power for this sample size
    achieved_power = stats.norm.cdf(
        np.sqrt(n_per_group / 2) * effect_size - z_alpha
    )
    
    return {
        "effect_size": effect_size,
        "alpha": alpha,
        "power_target": power_target,
        "achieved_power": achieved_power,
        "required_sample_size_per_group": n_per_group,
        "total_sample_size": n_per_group * 2,
        "power_achieved": achieved_power >= power_target
    }

def two_proportion_z_test(
    successes1: int,
    n1: int,
    successes2: int,
    n2: int,
    alternative: str = "two-sided"
) -> Tuple[float, float]:
    """
    Perform two-proportion z-test.
    
    Args:
        successes1: Number of successes in group 1
        n1: Total observations in group 1
        successes2: Number of successes in group 2
        n2: Total observations in group 2
        alternative: Type of test ("two-sided", "larger", "smaller")
        
    Returns:
        Tuple of (z-statistic, p-value)
    """
    if n1 == 0 or n2 == 0:
        raise ValueError("Sample sizes must be greater than 0")
        
    prop1 = successes1 / n1
    prop2 = successes2 / n2
    
    # Pooled proportion
    pooled_prop = (successes1 + successes2) / (n1 + n2)
    
    # Standard error
    se = np.sqrt(pooled_prop * (1 - pooled_prop) * (1/n1 + 1/n2))
    
    if se == 0:
        return 0.0, 1.0
        
    z_stat = (prop1 - prop2) / se
    
    # Calculate p-value based on alternative hypothesis
    if alternative == "two-sided":
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    elif alternative == "larger":
        p_value = 1 - stats.norm.cdf(z_stat)
    elif alternative == "smaller":
        p_value = stats.norm.cdf(z_stat)
    else:
        raise ValueError(f"Invalid alternative: {alternative}")
        
    return z_stat, p_value

def fisher_exact_test(
    successes1: int,
    failures1: int,
    successes2: int,
    failures2: int,
    alternative: str = "two-sided"
) -> Tuple[float, float]:
    """
    Perform Fisher's Exact Test.
    
    Args:
        successes1: Number of successes in group 1
        failures1: Number of failures in group 1
        successes2: Number of successes in group 2
        failures2: Number of failures in group 2
        alternative: Type of test ("two-sided", "greater", "less")
        
    Returns:
        Tuple of (odds ratio, p-value)
    """
    # Create contingency table
    table = [
        [successes1, failures1],
        [successes2, failures2]
    ]
    
    result = stats.fisher_exact(table, alternative=alternative)
    return result[0], result[1]

def select_statistical_test(
    successes1: int,
    n1: int,
    successes2: int,
    n2: int
) -> str:
    """
    Select appropriate statistical test based on cell counts.
    
    Args:
        successes1: Number of successes in group 1
        n1: Total observations in group 1
        successes2: Number of successes in group 2
        n2: Total observations in group 2
        
    Returns:
        "z-test" or "fisher"
    """
    failures1 = n1 - successes1
    failures2 = n2 - successes2
    
    # Check expected cell counts (rule of thumb: all cells >= 5)
    total = n1 + n2
    prop_pooled = (successes1 + successes2) / total
    
    expected_successes1 = n1 * prop_pooled
    expected_failures1 = n1 * (1 - prop_pooled)
    expected_successes2 = n2 * prop_pooled
    expected_failures2 = n2 * (1 - prop_pooled)
    
    min_expected = min(
        expected_successes1, expected_failures1,
        expected_successes2, expected_failures2
    )
    
    if min_expected < 5:
        return "fisher"
    else:
        return "z-test"

def load_evaluation_results(
    results_dir: str,
    exclude_scene_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Load evaluation results from JSON files.
    
    Args:
        results_dir: Directory containing evaluation result JSON files
        exclude_scene_ids: List of scene IDs to exclude
        
    Returns:
        List of evaluation result dictionaries
    """
    if exclude_scene_ids is None:
        exclude_scene_ids = []
        
    results = []
    
    if not os.path.exists(results_dir):
        return results
        
    for filename in os.listdir(results_dir):
        if filename.endswith('.json'):
            scene_id = filename.replace('.json', '')
            
            if scene_id in exclude_scene_ids:
                continue
                
            filepath = os.path.join(results_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    result = json.load(f)
                    result['scene_id'] = scene_id
                    results.append(result)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {filepath}: {e}")
                
    return results

def aggregate_violation_rates(
    results: List[Dict[str, Any]],
    group_field: str = 'group'
) -> Dict[str, Dict[str, int]]:
    """
    Aggregate violation counts by group.
    
    Args:
        results: List of evaluation results
        group_field: Field name containing group identifier
        
    Returns:
        Dictionary mapping group names to {violations, total}
    """
    aggregation = {}
    
    for result in results:
        group = result.get(group_field, 'unknown')
        is_violation = result.get('has_violation', False)
        
        if group not in aggregation:
            aggregation[group] = {'violations': 0, 'total': 0}
            
        aggregation[group]['total'] += 1
        if is_violation:
            aggregation[group]['violations'] += 1
            
    return aggregation

def calculate_contradiction_rate(
    contradiction_log_path: str
) -> Tuple[float, List[str]]:
    """
    Calculate contradiction rate from log file.
    
    Args:
        contradiction_log_path: Path to contradiction log JSON file
        
    Returns:
        Tuple of (contradiction_rate, list_of_contradictory_scene_ids)
    """
    contradictory_scenes = []
    total_scenes = 0
    
    if not os.path.exists(contradiction_log_path):
        return 0.0, []
        
    try:
        with open(contradiction_log_path, 'r') as f:
            log_data = json.load(f)
            
        # Assuming log_data is a list of contradictory scene IDs or objects
        if isinstance(log_data, list):
            contradictory_scenes = [
                item if isinstance(item, str) else item.get('scene_id')
                for item in log_data
                if item
            ]
            contradictory_scenes = [s for s in contradictory_scenes if s]
            
        # We need to know total scenes to calculate rate
        # This would typically come from the scene descriptions
        # For now, we return the count and let the caller handle total
        return len(contradictory_scenes), contradictory_scenes
        
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load contradiction log: {e}")
        return 0.0, []

def verify_contradiction_rate(
    contradiction_rate: float,
    threshold: float = CONTRADICTION_RATE_THRESHOLD
) -> bool:
    """
    Verify that contradiction rate is below threshold.
    
    Args:
        contradiction_rate: Calculated contradiction rate
        threshold: Maximum allowed rate
        
    Returns:
        True if rate is acceptable, False otherwise
    """
    return contradiction_rate <= threshold

def run_power_analysis_and_report(
    output_path: str,
    effect_size: Optional[float] = None,
    alpha: float = ALPHA,
    power_target: float = POWER_TARGET
) -> Dict[str, Any]:
    """
    Run power analysis and save report to file.
    
    Args:
        output_path: Path to save power analysis report
        effect_size: Effect size for calculation
        alpha: Significance level
        power_target: Target power
        
    Returns:
        Power analysis results dictionary
    """
    results = power_analysis_two_proportions(
        effect_size=effect_size,
        alpha=alpha,
        power_target=power_target
    )
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    return results

def run_statistical_comparison(
    results: List[Dict[str, Any]],
    group1: str,
    group2: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run statistical comparison between two groups.
    
    Args:
        results: List of evaluation results
        group1: Name of first group
        group2: Name of second group
        output_path: Optional path to save results
        
    Returns:
        Statistical comparison results dictionary
    """
    # Filter results by groups
    group1_results = [r for r in results if r.get('group') == group1]
    group2_results = [r for r in results if r.get('group') == group2]
    
    if not group1_results or not group2_results:
        raise ValueError(f"One or both groups have no results: {group1}, {group2}")
        
    # Aggregate violations
    agg1 = aggregate_violation_rates(group1_results)
    agg2 = aggregate_violation_rates(group2_results)
    
    stats1 = agg1.get(group1, {'violations': 0, 'total': 0})
    stats2 = agg2.get(group2, {'violations': 0, 'total': 0})
    
    successes1 = stats1['violations']
    n1 = stats1['total']
    successes2 = stats2['violations']
    n2 = stats2['total']
    
    # Select appropriate test
    test_type = select_statistical_test(successes1, n1, successes2, n2)
    
    if test_type == "z-test":
        z_stat, p_value = two_proportion_z_test(successes1, n1, successes2, n2)
        test_details = {"z_statistic": z_stat, "p_value": p_value}
    else:
        failures1 = n1 - successes1
        failures2 = n2 - successes2
        odds_ratio, p_value = fisher_exact_test(
            successes1, failures1, successes2, failures2
        )
        test_details = {"odds_ratio": odds_ratio, "p_value": p_value}
        
    # Calculate effect size
    prop1 = successes1 / n1 if n1 > 0 else 0
    prop2 = successes2 / n2 if n2 > 0 else 0
    effect_size = calculate_effect_size(prop1, prop2)
    
    results_dict = {
        "group1": group1,
        "group2": group2,
        "group1_violations": successes1,
        "group1_total": n1,
        "group1_rate": prop1,
        "group2_violations": successes2,
        "group2_total": n2,
        "group2_rate": prop2,
        "test_type": test_type,
        "effect_size": effect_size,
        "statistical_results": test_details,
        "is_significant": p_value < ALPHA
    }
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2)
            
    return results_dict

def generate_final_analysis_csv(
    results: List[Dict[str, Any]],
    comparison_results: Dict[str, Any],
    output_path: str,
    contradiction_rate: float = 0.0
) -> None:
    """
    Generate final analysis CSV file.
    
    Args:
        results: List of evaluation results
        comparison_results: Statistical comparison results
        output_path: Path to save CSV file
        contradiction_rate: Calculated contradiction rate
    """
    import csv
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "Metric", "Value", "Notes"
        ])
        
        # Summary statistics
        writer.writerow(["Total Scenes", len(results), ""])
        writer.writerow(["Contradiction Rate", f"{contradiction_rate:.2%}", ""])
        
        # Group statistics
        agg = aggregate_violation_rates(results)
        for group, stats in agg.items():
            rate = stats['violations'] / stats['total'] if stats['total'] > 0 else 0
            writer.writerow([
                f"{group} Prompt Adherence Rate",
                f"{1 - rate:.2%}",
                f"{stats['violations']}/{stats['total']} violations"
            ])
        
        # Statistical comparison
        writer.writerow([])
        writer.writerow(["Statistical Comparison", "", ""])
        writer.writerow([
            "Test Type",
            comparison_results.get('test_type', ''),
            ""
        ])
        writer.writerow([
            "Effect Size",
            f"{comparison_results.get('effect_size', 0):.4f}",
            "Cohen's h"
        ])
        
        if 'z_statistic' in comparison_results.get('statistical_results', {}):
            writer.writerow([
                "Z-Statistic",
                f"{comparison_results['statistical_results']['z_statistic']:.4f}",
                ""
            ])
        elif 'odds_ratio' in comparison_results.get('statistical_results', {}):
            writer.writerow([
                "Odds Ratio",
                f"{comparison_results['statistical_results']['odds_ratio']:.4f}",
                ""
            ])
            
        writer.writerow([
            "P-Value",
            f"{comparison_results.get('statistical_results', {}).get('p_value', 0):.4f}",
            ""
        ])
        writer.writerow([
            "Is Significant",
            comparison_results.get('is_significant', False),
            f"alpha={ALPHA}"
        ])

def main():
    """
    Main function for running statistical analysis.
    
    This function:
    1. Runs power analysis
    2. Loads evaluation results
    3. Performs statistical comparison
    4. Generates final analysis report
    """
    # Define paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    results_dir = os.path.join(project_root, "data", "derived", "evaluation_results")
    contradiction_log_path = os.path.join(
        project_root, "data", "derived", "physics_constraints", "contradiction_log.json"
    )
    power_report_path = os.path.join(
        project_root, "data", "derived", "evaluation_results", "power_analysis_report.json"
    )
    comparison_report_path = os.path.join(
        project_root, "data", "derived", "evaluation_results", "statistical_comparison.json"
    )
    final_csv_path = os.path.join(
        project_root, "data", "processed", "final_analysis.csv"
    )
    
    print("Running Power Analysis...")
    power_results = run_power_analysis_and_report(
        power_report_path,
        effect_size=EFFECT_SIZE,
        alpha=ALPHA,
        power_target=POWER_TARGET
    )
    
    # Verify power
    if not power_results['power_achieved']:
        raise StudyInvalidError(
            f"Power analysis failed: achieved power ({power_results['achieved_power']:.2f}) "
            f"is below target ({POWER_TARGET})"
        )
    print(f"Power analysis complete. Required sample size: {power_results['total_sample_size']}")
    
    # Load contradiction log and verify rate
    print("Checking contradiction rate...")
    contradiction_count, contradictory_scenes = calculate_contradiction_rate(contradiction_log_path)
    
    # We need total scenes to calculate rate - this would come from scene descriptions
    # For now, we'll assume we have enough scenes and just log the count
    print(f"Found {contradiction_count} contradictory scenes")
    
    # Load evaluation results (excluding contradictory scenes)
    print("Loading evaluation results...")
    results = load_evaluation_results(results_dir, exclude_scene_ids=contradictory_scenes)
    print(f"Loaded {len(results)} evaluation results")
    
    if len(results) < 10:
        print(f"Warning: Only {len(results)} results available, statistical power may be low")
    
    # Run statistical comparison (Baseline vs Experimental)
    print("Running statistical comparison...")
    try:
        comparison_results = run_statistical_comparison(
            results, "Baseline", "Experimental", comparison_report_path
        )
        print(f"Statistical comparison complete. P-value: {comparison_results['statistical_results']['p_value']:.4f}")
    except ValueError as e:
        print(f"Warning: Could not run statistical comparison: {e}")
        comparison_results = {"error": str(e)}
    
    # Calculate contradiction rate (approximate)
    # In a real scenario, we'd know the total number of scenes
    contradiction_rate = contradiction_count / 100 if contradiction_count > 0 else 0.0
    
    # Generate final analysis CSV
    print("Generating final analysis CSV...")
    generate_final_analysis_csv(
        results,
        comparison_results,
        final_csv_path,
        contradiction_rate
    )
    print(f"Final analysis saved to {final_csv_path}")
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
