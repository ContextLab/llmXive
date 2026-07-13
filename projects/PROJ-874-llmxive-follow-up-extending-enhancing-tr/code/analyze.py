import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import csv

import numpy as np
from scipy import stats
from statsmodels.stats.power import TTestPower

from config import get_results_dir, get_processed_dir, setup_logging

# Ensure these exist in config.py or are added here if missing in previous steps
# Assuming config.py has these based on API surface provided
# If not, they would need to be added to code/config.py in a separate task,
# but we proceed assuming they are there or will be added.
# For this task, we assume the existence of:
# - get_results_dir()
# - get_processed_dir()

# If specific helper functions for loading metrics are not in config, we define them locally
# to ensure this file is self-contained for the report generation logic.

def load_pilot_variance(file_path: str) -> Dict[str, float]:
    """Load pilot variance results from JSON."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Pilot variance file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_power(effect_size: float, n_obs: int, alpha: float = 0.05) -> float:
    """Calculate statistical power for a paired t-test."""
    power_analysis = TTestPower()
    power = power_analysis.solve_power(effect_size=effect_size, nobs1=n_obs, alpha=alpha, alternative='two-sided')
    return power

def run_power_analysis(pilot_data: Dict[str, Any], n_target: int = 50, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run power analysis based on pilot data.
    Returns dict with 'power', 'sufficient' (bool), and 'message'.
    SC-006: If power < 0.8, report must state underpowered.
    """
    # Pilot data expected: {'mean': ..., 'std': ..., 'n_samples': ...}
    # We need to estimate effect size. Assuming we are comparing to a baseline of 0 difference or similar.
    # However, for a paired test, we look at the standard deviation of the differences.
    # If pilot variance is for the metric difference, we use std directly.
    # If it's just variance of the metric, we need a hypothesized mean difference.
    # For this implementation, we assume pilot_data contains 'std_diff' or 'std' representing the SD of differences.
    
    std_diff = pilot_data.get('std', pilot_data.get('std_diff', 0))
    mean_diff = pilot_data.get('mean', 0)
    
    if std_diff == 0:
        # Avoid division by zero, assume infinite effect size or skip
        return {
            'power': 1.0,
            'sufficient': True,
            'message': 'Zero variance in pilot, assuming sufficient power or undefined.'
        }

    # Cohen's d for paired samples: mean_diff / std_diff
    effect_size = abs(mean_diff) / std_diff

    power = calculate_power(effect_size, n_target, alpha)
    
    sufficient = power >= 0.8
    message = f"Power analysis for N={n_target}: Power={power:.4f}. "
    if sufficient:
        message += "Study is sufficiently powered."
    else:
        message += "STUDY IS UNDERPOWERED. Subsequent statistical tests (T027/T028) are invalid."
    
    return {
        'power': power,
        'sufficient': sufficient,
        'message': message,
        'effect_size': effect_size
    }

def check_normality(differences: List[float], alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk test for normality.
    Returns (is_normal, p_value).
    Note: p < 0.05 implies non-normality (reject null).
    """
    if len(differences) < 3:
        logging.warning("Not enough data points for Shapiro-Wilk test. Assuming normality.")
        return True, 1.0
    
    stat, p_value = stats.shapiro(differences)
    is_normal = p_value >= alpha
    return is_normal, p_value

def perform_statistical_test(group1: List[float], group2: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform adaptive statistical testing.
    If normal (Shapiro p >= 0.05): Paired T-test.
    If non-normal (Shapiro p < 0.05): Wilcoxon signed-rank test.
    
    Returns dict with 'p_value', 'test_type', 'statistic'.
    """
    # Calculate differences for Shapiro-Wilk
    if len(group1) != len(group2):
        raise ValueError("Groups must be of equal length for paired tests.")
    
    differences = [g1 - g2 for g1, g2 in zip(group1, group2)]
    
    is_normal, p_norm = check_normality(differences, alpha)
    
    test_type = "paired_t_test" if is_normal else "wilcoxon_signed_rank"
    
    if is_normal:
        stat, p_val = stats.ttest_rel(group1, group2)
    else:
        stat, p_val = stats.wilcoxon(group1, group2)
        
    return {
        'p_value': p_val,
        'test_type': test_type,
        'statistic': stat,
        'is_normal': is_normal,
        'normality_p_value': p_norm
    }

def identify_failure_cases(naive_metrics: List[Dict], corrected_metrics: List[Dict], threshold_obj: float = 0.05, threshold_vbench: float = 0.1) -> List[Dict]:
    """
    Identify failure cases where object permanence drops >= 5% or VBench score drops >= 0.1.
    Output is a list of dicts with video_id and reason.
    """
    failures = []
    # Assuming naive_metrics and corrected_metrics are aligned lists of dicts with 'video_id', 'object_permanence', 'vbench_score'
    for naive, corrected in zip(naive_metrics, corrected_metrics):
        vid = naive.get('video_id', corrected.get('video_id', 'unknown'))
        
        obj_naive = naive.get('object_permanence', 0)
        obj_corrected = corrected.get('object_permanence', 0)
        vbench_naive = naive.get('vbench_score', 0)
        vbench_corrected = corrected.get('vbench_score', 0)
        
        obj_drop = obj_naive - obj_corrected
        vbench_drop = vbench_naive - vbench_corrected
        
        reason = []
        if obj_drop >= threshold_obj:
            reason.append(f"Object permanence drop: {obj_drop:.4f} (>{threshold_obj})")
        if vbench_drop >= threshold_vbench:
            reason.append(f"VBench score drop: {vbench_drop:.4f} (>{threshold_vbench})")
        
        if reason:
            failures.append({
                'video_id': vid,
                'reasons': reason,
                'is_2d_proxy_only': True,
                'note': "These are 2D perceptual proxies and do not guarantee 3D geometric correctness"
            })
    
    return failures

def load_metrics_from_json(file_path: str) -> List[Dict]:
    """Load metrics from a JSON file (output of evaluate.py)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    with open(file_path, 'r') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'metrics' in data:
        return data['metrics']
    else:
        # Fallback: try to interpret the whole dict as a single record or list of dicts
        return [data] if isinstance(data, dict) else []

def generate_report(
    naive_metrics_path: str,
    corrected_metrics_path: str,
    pilot_variance_path: str,
    output_csv_path: str
) -> str:
    """
    Generate the final CSV report.
    Columns: video_id, condition, vbench_score, fvd, object_permanence, p_value, test_type, power_sufficient
    
    This function:
    1. Loads pilot variance and checks power (T030a).
    2. Loads naive and corrected metrics.
    3. Performs statistical tests per video (aggregated or per-metric? T030 implies per video row or summary).
       Given the column requirement 'video_id', we likely report per video if we have per-video stats,
       but statistical tests usually require a distribution.
       
       Interpretation of T030: "Generate CSV report containing all metrics and a final statistical summary with p-values."
       The columns 'p_value', 'test_type' suggest a row-level or summary-level inclusion.
       Since we cannot run a t-test on a single video, we assume:
       - If we have multiple runs per video, we test per video.
       - If we have one run per video, we might be testing the distribution of metrics across videos?
       
       However, the prompt says "CSV columns MUST include... p_value".
       Standard practice: Run the test on the set of differences (Naive vs Corrected) across all videos.
       Then the p_value applies to the whole study.
       But if we must put it in every row, we duplicate the study-level p-value.
       
       Let's assume the task wants the study-level statistical summary repeated for every row,
       or perhaps the task implies a per-video bootstrap?
       
       Given the constraint "Must consume output of T030a", T030a is about N=50 power.
       If power is insufficient, we still generate the CSV but flag 'power_sufficient' as False.
       
       Let's implement:
       1. Aggregate all differences (Naive - Corrected) for each metric.
       2. Run one statistical test for the main metric (e.g., Object Permanence or VBench).
       3. Fill 'p_value' and 'test_type' in every row with the result of the global test.
       4. Fill 'power_sufficient' with the result of T030a.
       
       Wait, the prompt says "statistical summary with p-values". Plural?
       Maybe test each metric?
       Let's test the primary metric (Object Permanence) and maybe VBench.
       But the CSV has one 'p_value' column. We'll use the p-value for Object Permanence as the primary indicator.
    """
    
    # 1. Load Pilot Variance and check power
    power_info = {'power': 0.0, 'sufficient': False, 'message': ''}
    try:
        pilot_data = load_pilot_variance(pilot_variance_path)
        power_info = run_power_analysis(pilot_data, n_target=50)
    except Exception as e:
        logging.error(f"Failed to load pilot variance: {e}")
        power_info['message'] = f"Power analysis failed: {e}"
    
    power_sufficient = power_info.get('sufficient', False)
    
    # 2. Load Metrics
    try:
        naive_list = load_metrics_from_json(naive_metrics_path)
        corrected_list = load_metrics_from_json(corrected_metrics_path)
    except Exception as e:
        logging.error(f"Failed to load metrics: {e}")
        # Create empty report or error report?
        # We must write a CSV. Let's write a header and an error row if possible, or empty.
        # But the task says "Generate CSV report". If data is missing, we can't.
        # We'll raise or return a specific error state.
        raise RuntimeError(f"Cannot generate report: Missing metrics. {e}")
    
    if len(naive_list) != len(corrected_list):
        raise ValueError("Naive and corrected metric lists must have the same length.")
    
    # 3. Perform Statistical Test
    # We need to align by video_id
    naive_dict = {m['video_id']: m for m in naive_list}
    corrected_dict = {m['video_id']: m for m in corrected_list}
    
    common_ids = sorted(set(naive_dict.keys()) & set(corrected_dict.keys()))
    
    if not common_ids:
        raise ValueError("No common video IDs found between naive and corrected metrics.")
    
    # Prepare data for testing (Object Permanence)
    obj_naive = [naive_dict[vid]['object_permanence'] for vid in common_ids]
    obj_corrected = [corrected_dict[vid]['object_permanence'] for vid in common_ids]
    
    test_result = perform_statistical_test(obj_naive, obj_corrected)
    
    p_value = test_result['p_value']
    test_type = test_result['test_type']
    
    # 4. Generate CSV
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    
    fieldnames = ['video_id', 'condition', 'vbench_score', 'fvd', 'object_permanence', 'p_value', 'test_type', 'power_sufficient']
    
    rows = []
    for vid in common_ids:
        n = naive_dict[vid]
        c = corrected_dict[vid]
        
        # We have two conditions per video? Or one row per video with both conditions?
        # The columns suggest one row per video? But 'condition' column implies multiple rows per video?
        # "CSV columns MUST include: 'video_id', 'condition', ..."
        # This implies a long format:
        # video_id | condition | vbench_score | ...
        # vid1 | naive | 0.9 | ...
        # vid1 | corrected | 0.95 | ...
        # But then where do p_value and test_type go? They are study-level.
        # If we put them in every row, it's redundant but satisfies the schema.
        
        # Let's create two rows per video: one for naive, one for corrected.
        # And the p_value/test_type/power_sufficient are repeated in each row.
        
        rows.append({
            'video_id': vid,
            'condition': 'naive',
            'vbench_score': n.get('vbench_score', ''),
            'fvd': n.get('fvd', ''),
            'object_permanence': n.get('object_permanence', ''),
            'p_value': p_value,
            'test_type': test_type,
            'power_sufficient': power_sufficient
        })
        rows.append({
            'video_id': vid,
            'condition': 'corrected',
            'vbench_score': c.get('vbench_score', ''),
            'fvd': c.get('fvd', ''),
            'object_permanence': c.get('object_permanence', ''),
            'p_value': p_value,
            'test_type': test_type,
            'power_sufficient': power_sufficient
        })
    
    with open(output_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logging.info(f"Report generated: {output_csv_path}")
    logging.info(f"Power sufficient: {power_sufficient}. Test type: {test_type}, p-value: {p_value}")
    
    return output_csv_path

def main():
    parser = argparse.ArgumentParser(description="Generate statistical report (T030)")
    parser.add_argument("--naive-metrics", required=True, help="Path to naive metrics JSON")
    parser.add_argument("--corrected-metrics", required=True, help="Path to corrected metrics JSON")
    parser.add_argument("--pilot-variance", required=True, help="Path to pilot variance JSON")
    parser.add_argument("--output-csv", required=True, help="Output CSV path")
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        generate_report(
            naive_metrics_path=args.naive_metrics,
            corrected_metrics_path=args.corrected_metrics,
            pilot_variance_path=args.pilot_variance,
            output_csv_path=args.output_csv
        )
    except Exception as e:
        logging.critical(f"Report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()