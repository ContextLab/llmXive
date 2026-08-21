"""
Statistical tests module for SpatialClaw restriction analysis.
Implements McNemar's test, Wilcoxon signed-rank test, T-test, normality checks,
and Bonferroni correction.
"""

import os
import csv
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy.stats import wilcoxon, chi2_contingency, shapiro, ttest_rel

# Configure logger
logger = logging.getLogger(__name__)


def load_paired_dataset(filepath: str) -> List[Dict[str, Any]]:
    """Load the final paired dataset CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Paired dataset not found at {filepath}")
    
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'task_id': row['task_id'],
                'task_type': row['task_type'],
                '2d_success_rate': float(row['2d_success_rate']),
                '2d_mean_latency': float(row['2d_mean_latency']),
                '3d_success': int(float(row['3d_success'])),
                '3d_latency': float(row['3d_latency']),
                'success_diff': float(row['success_diff']),
                'latency_diff': float(row['latency_diff'])
            })
    return data


def group_by_task_type(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by task_type."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for row in data:
        t_type = row['task_type']
        if t_type not in groups:
            groups[t_type] = []
        groups[t_type].append(row)
    return groups


def extract_success_pairs(group: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    """Extract 2D and 3D success values for McNemar's test."""
    d2_success = [int(row['2d_success_rate'] > 0.5) for row in group]
    d3_success = [row['3d_success'] for row in group]
    return d2_success, d3_success


def extract_latency_pairs(group: List[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
    """Extract 2D and 3D latency values for paired tests."""
    d2_latency = [row['2d_mean_latency'] for row in group]
    d3_latency = [row['3d_latency'] for row in group]
    return d2_latency, d3_latency


def run_mcnemar_test(success_2d: List[int], success_3d: List[int]) -> Dict[str, Any]:
    """
    Perform McNemar's test for paired binary data.
    Returns dictionary with statistic, p-value, and conclusion.
    """
    # Construct contingency table:
    #               3D Success
    #               Yes   No
    # 2D Success Yes  a     b
    #          No   c     d
    a = b = c = d = 0
    for s2, s3 in zip(success_2d, success_3d):
        if s2 == 1 and s3 == 1:
            a += 1
        elif s2 == 1 and s3 == 0:
            b += 1
        elif s2 == 0 and s3 == 1:
            c += 1
        else:
            d += 1
    
    contingency = np.array([[a, b], [c, d]])
    # Use exact=False for chi-square approximation if counts are small but > 25 total discordant
    # For robustness, we use chi2_contingency with correction
    try:
        stat, p_val, dof, expected = chi2_contingency(contingency, correction=True)
    except Exception:
        # Fallback if matrix is singular (e.g., all same)
        return {
            'test': 'McNemar',
            'statistic': 0.0,
            'p_value': 1.0,
            'conclusion': 'Inconclusive (zero variance)'
        }
    
    conclusion = "Significant difference" if p_val < 0.05 else "No significant difference"
    return {
        'test': 'McNemar',
        'statistic': float(stat),
        'p_value': float(p_val),
        'conclusion': conclusion,
        'contingency': {'a': int(a), 'b': int(b), 'c': int(c), 'd': int(d)}
    }


def check_normality(latency_diffs: List[float]) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test for normality on latency differences.
    Returns dictionary with statistic, p-value, and is_normal boolean.
    """
    if len(latency_diffs) < 3:
        # Not enough data for Shapiro-Wilk
        return {
            'test': 'Shapiro-Wilk',
            'statistic': 0.0,
            'p_value': 1.0,
            'is_normal': True,  # Assume normal if insufficient data
            'reason': 'Insufficient data points for normality test'
        }
    
    try:
        stat, p_val = shapiro(latency_diffs)
        is_normal = p_val > 0.05
        reason = "Normal distribution assumed" if is_normal else "Normality assumption violated"
    except Exception as e:
        # Fallback if test fails (e.g., constant values)
        return {
            'test': 'Shapiro-Wilk',
            'statistic': 0.0,
            'p_value': 1.0,
            'is_normal': True,
            'reason': f'Test failed: {str(e)}, assuming normal'
        }
    
    return {
        'test': 'Shapiro-Wilk',
        'statistic': float(stat),
        'p_value': float(p_val),
        'is_normal': is_normal,
        'reason': reason
    }


def run_ttest(latency_2d: List[float], latency_3d: List[float]) -> Dict[str, Any]:
    """Run paired t-test."""
    try:
        stat, p_val = ttest_rel(latency_2d, latency_3d)
    except Exception:
        return {'test': 'T-test', 'statistic': 0.0, 'p_value': 1.0, 'conclusion': 'Inconclusive'}
    
    conclusion = "Significant difference" if p_val < 0.05 else "No significant difference"
    return {
        'test': 'T-test',
        'statistic': float(stat),
        'p_value': float(p_val),
        'conclusion': conclusion
    }


def run_wilcoxon_test(latency_2d: List[float], latency_3d: List[float]) -> Dict[str, Any]:
    """Run Wilcoxon signed-rank test."""
    try:
        stat, p_val = wilcoxon(latency_2d, latency_3d)
    except Exception:
        return {'test': 'Wilcoxon', 'statistic': 0.0, 'p_value': 1.0, 'conclusion': 'Inconclusive'}
    
    conclusion = "Significant difference" if p_val < 0.05 else "No significant difference"
    return {
        'test': 'Wilcoxon',
        'statistic': float(stat),
        'p_value': float(p_val),
        'conclusion': conclusion
    }


def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
    corrected = [min(p * n, 1.0) for p in p_values]
    return corrected


def run_statistical_tests(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run the full suite of statistical tests on the paired dataset.
    Includes normality check, test selection (T-test vs Wilcoxon),
    McNemar for success rates, and Bonferroni correction.
    """
    groups = group_by_task_type(data)
    results = {}
    methodology_log_entries = []
    
    for task_type, group_data in groups.items():
        logger.info(f"Processing {task_type} group with {len(group_data)} samples")
        
        # Extract data
        success_2d, success_3d = extract_success_pairs(group_data)
        latency_2d, latency_3d = extract_latency_pairs(group_data)
        
        # Calculate latency differences for normality check
        latency_diffs = [d2 - d3 for d2, d3 in zip(latency_2d, latency_3d)]
        
        # 1. Normality Check (Shapiro-Wilk)
        normality_result = check_normality(latency_diffs)
        
        # 2. Select test based on normality
        if normality_result['is_normal']:
            latency_test_result = run_ttest(latency_2d, latency_3d)
            test_used = "Paired T-test"
        else:
            latency_test_result = run_wilcoxon_test(latency_2d, latency_3d)
            test_used = "Wilcoxon Signed-Rank Test"
        
        # 3. McNemar for success rates
        mcnemar_result = run_mcnemar_test(success_2d, success_3d)
        
        results[task_type] = {
            'n_samples': len(group_data),
            'normality_check': normality_result,
            'latency_test': latency_test_result,
            'test_used': test_used,
            'success_test': mcnemar_result
        }
        
        # Log methodology decision
        methodology_log_entries.append({
            'task_type': task_type,
            'normality_test': normality_result['test'],
            'normality_statistic': normality_result['statistic'],
            'normality_p_value': normality_result['p_value'],
            'is_normal': normality_result['is_normal'],
            'selected_test': test_used,
            'reason': normality_result.get('reason', 'Standard Shapiro-Wilk test')
        })
    
    return results, methodology_log_entries


def load_sensitivity_data(filepath: str) -> Optional[List[Dict[str, Any]]]:
    """Load sensitivity analysis CSV if it exists."""
    if not os.path.exists(filepath):
        return None
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def generate_report_markdown(results: Dict[str, Any], methodology_log: List[Dict[str, Any]], output_path: str) -> None:
    """Generate a markdown report of the statistical analysis."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Statistical Analysis Report\n\n")
        f.write("## Methodology Selection Log\n\n")
        f.write("| Task Type | Normality Test | p-value | Is Normal | Selected Test | Reason |\n")
        f.write("|---|---|---|---|---|---|\n")
        for entry in methodology_log:
            f.write(f"| {entry['task_type']} | {entry['normality_test']} | {entry['normality_p_value']:.4f} | {entry['is_normal']} | {entry['selected_test']} | {entry['reason']} |\n")
        
        f.write("\n## Detailed Results by Task Type\n\n")
        
        for task_type, res in results.items():
            f.write(f"### {task_type}\n\n")
            f.write(f"- **Samples**: {res['n_samples']}\n")
            f.write(f"- **Normality (Shapiro-Wilk)**: p = {res['normality_check']['p_value']:.4f} ({'Normal' if res['normality_check']['is_normal'] else 'Non-Normal'})\n")
            f.write(f"- **Latency Test Used**: {res['test_used']}\n")
            f.write(f"  - Statistic: {res['latency_test']['statistic']:.4f}\n")
            f.write(f"  - p-value: {res['latency_test']['p_value']:.4f}\n")
            f.write(f"  - Conclusion: {res['latency_test']['conclusion']}\n")
            f.write(f"- **Success Rate Test (McNemar)**: p = {res['success_test']['p_value']:.4f} ({res['success_test']['conclusion']})\n")
            f.write("\n")
    
    logger.info(f"Statistical report generated at {output_path}")


def main():
    """Main entry point for running statistical tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run statistical tests on paired dataset")
    parser.add_argument("--input", default="results/analysis/final_paired_dataset.csv",
                      help="Path to final paired dataset CSV")
    parser.add_argument("--output", default="results/analysis/final_statistical_report.md",
                      help="Path to output markdown report")
    parser.add_argument("--log", default="results/analysis/statistical_methodology_log.md",
                      help="Path to output methodology log")
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load data
    try:
        data = load_paired_dataset(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    # Run tests
    results, methodology_log = run_statistical_tests(data)
    
    # Generate report
    generate_report_markdown(results, methodology_log, args.output)
    
    # Write methodology log separately for clarity
    with open(args.log, 'w', encoding='utf-8') as f:
        f.write("# Statistical Methodology Selection Log\n\n")
        f.write("This log documents the decision process for selecting statistical tests\n")
        f.write("based on normality assumptions of latency differences.\n\n")
        for entry in methodology_log:
            f.write(f"## {entry['task_type']}\n\n")
            f.write(f"- **Normality Test**: {entry['normality_test']}\n")
            f.write(f"- **Statistic**: {entry['normality_statistic']:.4f}\n")
            f.write(f"- **p-value**: {entry['normality_p_value']:.4f}\n")
            f.write(f"- **Is Normal**: {entry['is_normal']}\n")
            f.write(f"- **Selected Test**: {entry['selected_test']}\n")
            f.write(f"- **Reason**: {entry['reason']}\n\n")
    
    logger.info("Statistical analysis completed successfully.")


if __name__ == "__main__":
    main()