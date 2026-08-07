"""
Final Statistical Report Generation for SpatialClaw Restriction Study.

This module executes the statistical tests and sensitivity analysis against
the final paired dataset and generates a comprehensive Markdown report.
"""

import os
import csv
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import numpy as np
from scipy import stats as scipy_stats

from stats.tests import run_mcnemar_test, run_wilcoxon_test, apply_bonferroni_correction
from stats.sensitivity import run_sensitivity_analysis, load_comparison_results

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_DATASET_PATH = "results/analysis/final_paired_dataset.csv"
SENSITIVITY_INPUT_PATH = "results/analysis/depth_threshold_sweep.csv"
OUTPUT_REPORT_PATH = "results/analysis/final_statistical_report.md"
OUTPUT_STATS_JSON_PATH = "results/analysis/statistical_test_results.json"

def load_paired_dataset(path: str) -> List[Dict[str, Any]]:
    """Load the final paired dataset from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input dataset not found: {path}")
    
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to float
            numeric_fields = ['2d_success_rate', '2d_mean_latency', '3d_success', '3d_latency', 'success_diff', 'latency_diff']
            processed_row = {}
            for key, value in row.items():
                if key in numeric_fields:
                    try:
                        processed_row[key] = float(value)
                    except ValueError:
                        processed_row[key] = None
                else:
                    processed_row[key] = value
            data.append(processed_row)
    return data

def group_by_task_type(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by task_type for per-type analysis."""
    groups = {}
    for row in data:
        t_type = row.get('task_type', 'unknown')
        if t_type not in groups:
            groups[t_type] = []
        groups[t_type].append(row)
    return groups

def extract_success_pairs(data: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    """Extract binary success pairs for McNemar's test."""
    # We need paired binary outcomes: (2d_success, 3d_success)
    # Since 2d_success_rate is a proportion from multiple runs, we treat >0.5 as success for the test
    # or use the raw boolean if available. Here we assume the aggregated rate implies the majority outcome.
    # For a strict paired test on the *dataset* level, we often look at the mean success rate difference.
    # However, McNemar requires binary counts per pair. 
    # Given the schema has '2d_success_rate' (float) and '3d_success' (float/bool), 
    # we will construct a contingency table based on the aggregated rates per task type.
    
    # Actually, for the report, we perform the test on the *aggregated* counts per task type.
    # We sum the successes and total counts.
    return [], [] # Placeholder, logic moved to group-level aggregation

def calculate_aggregated_counts(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Calculate aggregated success/failure counts per task type."""
    counts = {}
    for row in data:
        t_type = row.get('task_type', 'unknown')
        if t_type not in counts:
            counts[t_type] = {'2d_success': 0, '2d_fail': 0, '3d_success': 0, '3d_fail': 0, 'n': 0}
        
        # Treat 2d_success_rate >= 0.5 as success for binary classification in McNemar
        # Treat 3d_success >= 0.5 as success
        s_2d = 1 if (row.get('2d_success_rate') or 0) >= 0.5 else 0
        s_3d = 1 if (row.get('3d_success') or 0) >= 0.5 else 0
        
        counts[t_type]['n'] += 1
        if s_2d == 1 and s_3d == 1:
            counts[t_type]['both_success'] = counts[t_type].get('both_success', 0) + 1
        elif s_2d == 1 and s_3d == 0:
            counts[t_type]['2d_only'] = counts[t_type].get('2d_only', 0) + 1
        elif s_2d == 0 and s_3d == 1:
            counts[t_type]['3d_only'] = counts[t_type].get('3d_only', 0) + 1
        else:
            counts[t_type]['both_fail'] = counts[t_type].get('both_fail', 0) + 1
    
    return counts

def run_statistical_tests(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run McNemar and Wilcoxon tests on the dataset."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'task_types': {},
        'global_summary': {}
    }
    
    groups = group_by_task_type(data)
    task_types = list(groups.keys())
    
    # Bonferroni correction factor
    alpha = 0.05
    correction_factor = len(task_types) if len(task_types) > 0 else 1
    
    all_p_values = []

    for t_type, rows in groups.items():
        # Prepare data for Wilcoxon (continuous metric: latency difference or success rate diff)
        # We use 'success_diff' (2d - 3d) for Wilcoxon signed-rank test on performance degradation
        diffs = [r.get('success_diff') for r in rows if r.get('success_diff') is not None]
        latencies_2d = [r.get('2d_mean_latency') for r in rows if r.get('2d_mean_latency') is not None]
        latencies_3d = [r.get('3d_latency') for r in rows if r.get('3d_latency') is not None]
        
        # Filter out None values for Wilcoxon
        valid_diffs = [d for d in diffs if d is not None]
        valid_lat_2d = [l for l in latencies_2d if l is not None]
        valid_lat_3d = [l for l in latencies_3d if l is not None]

        # 1. McNemar's Test (Binary Success/Failure)
        counts = calculate_aggregated_counts(rows)
        # We need to re-calculate contingency per task type from the raw rows
        # Re-doing the logic locally for accuracy
        b = 0 # 2d success, 3d fail
        c = 0 # 2d fail, 3d success
        for r in rows:
            s_2d = 1 if (r.get('2d_success_rate') or 0) >= 0.5 else 0
            s_3d = 1 if (r.get('3d_success') or 0) >= 0.5 else 0
            if s_2d == 1 and s_3d == 0:
                b += 1
            elif s_2d == 0 and s_3d == 1:
                c += 1
        
        mcnemar_result = None
        if b + c > 0:
            # Use scipy.stats.chi2_contingency or manual calculation for small samples
            # McNemar statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
            stat = ((abs(b - c) - 1) ** 2) / (b + c)
            p_val = 1 - scipy_stats.chi2.cdf(stat, 1)
            mcnemar_result = {
                'b': b, 'c': c, 'statistic': stat, 'p_value': p_val,
                'significant': p_val < (alpha / correction_factor)
            }
            all_p_values.append(p_val)

        # 2. Wilcoxon Signed-Rank Test (Continuous Latency or Success Diff)
        wilcoxon_result = None
        if len(valid_lat_2d) > 1 and len(valid_lat_3d) > 1:
            try:
                stat, p_val = scipy_stats.wilcoxon(valid_lat_2d, valid_lat_3d)
                wilcoxon_result = {
                    'statistic': stat, 'p_value': p_val,
                    'significant': p_val < (alpha / correction_factor),
                    'metric': 'latency_ms'
                }
                all_p_values.append(p_val)
            except Exception as e:
                logger.warning(f"Wilcoxon failed for {t_type}: {e}")

        # Apply Bonferroni to collected p-values at the end? 
        # Or apply per test? The task asks for Bonferroni corrected p-values.
        # We will store raw and then correct in the summary.
        
        results['task_types'][t_type] = {
            'n_samples': len(rows),
            'mcnemar': mcnemar_result,
            'wilcoxon': wilcoxon_result
        }

    # Global Bonferroni Correction
    corrected_alpha = alpha / max(1, len(all_p_values))
    results['global_summary'] = {
        'alpha': alpha,
        'correction_method': 'Bonferroni',
        'correction_factor': len(all_p_values),
        'corrected_alpha': corrected_alpha,
        'tests_run': len(all_p_values)
    }

    return results

def load_sensitivity_data() -> Optional[List[Dict[str, Any]]]:
    """Load sensitivity analysis data if available."""
    path = SENSITIVITY_INPUT_PATH
    if not os.path.exists(path):
        logger.warning(f"Sensitivity data not found at {path}")
        return None
    
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data.append({
                    'threshold_value': float(row['threshold_value']),
                    'false_positive_rate': float(row['false_positive_rate']),
                    'false_negative_rate': float(row['false_negative_rate'])
                })
            except (ValueError, KeyError):
                continue
    return data

def generate_report_markdown(stats_results: Dict[str, Any], sensitivity_data: Optional[List[Dict[str, Any]]]) -> str:
    """Generate the final Markdown report."""
    lines = []
    lines.append("# Final Statistical Report: SpatialClaw Restriction Study")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    
    # Conclusion on "Loss Ceiling" Hypothesis
    lines.append("### Conclusion on 'Loss Ceiling' Hypothesis")
    lines.append("")
    
    significant_degradation = False
    for t_type, data in stats_results.get('task_types', {}).items():
        mcnemar = data.get('mcnemar')
        if mcnemar and mcnemar.get('significant'):
            if mcnemar.get('c', 0) > mcnemar.get('b', 0):
                significant_degradation = True
                break
    
    if significant_degradation:
        lines.append("**Conclusion**: The null hypothesis is rejected. There is statistically significant evidence")
        lines.append("that the 2D-restricted agent suffers performance degradation (loss ceiling) compared to the 3D baseline")
        lines.append("across specific task types. The restriction to 2D operations imposes a measurable ceiling on agent capability.")
    else:
        lines.append("**Conclusion**: The null hypothesis cannot be rejected with statistical significance at the corrected alpha level.")
        lines.append("While performance differences may exist, they are not statistically significant enough to confirm a strict 'loss ceiling'")
        lines.append("hypothesis across the tested dataset. The 2D agent performs comparably to the 3D baseline within statistical variance.")
    
    lines.append("")
    lines.append(f"**Corrected Alpha (Bonferroni)**: {stats_results['global_summary']['corrected_alpha']:.6f}")
    lines.append("")

    lines.append("## Statistical Test Results")
    lines.append("")
    
    for t_type, data in stats_results.get('task_types', {}).items():
        lines.append(f"### Task Type: {t_type}")
        lines.append("")
        lines.append(f"- **Sample Size**: {data['n_samples']}")
        lines.append("")
        
        # McNemar
        lines.append("#### McNemar's Test (Success/Failure Binary Outcome)")
        lines.append("")
        if data.get('mcnemar'):
            m = data['mcnemar']
            lines.append(f"| Metric | Value |")
            lines.append(f"|---|---|")
            lines.append(f"| Statistic | {m['statistic']:.4f} |")
            lines.append(f"| Raw P-Value | {m['p_value']:.6f} |")
            lines.append(f"| Significant (Bonferroni) | {'Yes' if m['significant'] else 'No'} |")
            lines.append(f"| 2D Success / 3D Fail (b) | {m['b']} |")
            lines.append(f"| 2D Fail / 3D Success (c) | {m['c']} |")
            lines.append("")
        else:
            lines.append("*Not enough data for binary contingency.*")
            lines.append("")

        # Wilcoxon
        lines.append("#### Wilcoxon Signed-Rank Test (Latency/Performance Metric)")
        lines.append("")
        if data.get('wilcoxon'):
            w = data['wilcoxon']
            lines.append(f"| Metric | Value |")
            lines.append(f"|---|---|")
            lines.append(f"| Statistic | {w['statistic']:.4f} |")
            lines.append(f"| Raw P-Value | {w['p_value']:.6f} |")
            lines.append(f"| Significant (Bonferroni) | {'Yes' if w['significant'] else 'No'} |")
            lines.append("")
        else:
            lines.append("*Not enough data for continuous metric.*")
            lines.append("")

    lines.append("## Sensitivity Analysis")
    lines.append("")
    if sensitivity_data:
        lines.append("### Depth Threshold Sensitivity")
        lines.append("")
        lines.append("The following table shows the False Positive Rate (FPR) and False Negative Rate (FNR) for depth estimation errors across different thresholds.")
        lines.append("")
        lines.append("| Threshold | FPR | FNR |")
        lines.append("|---|---|---|")
        for row in sensitivity_data:
            lines.append(f"| {row['threshold_value']:.2f} | {row['false_positive_rate']:.4f} | {row['false_negative_rate']:.4f} |")
        lines.append("")
        
        # Determine optimal threshold if data exists
        if sensitivity_data:
            min_total_error = float('inf')
            best_thresh = None
            for row in sensitivity_data:
                total = row['false_positive_rate'] + row['false_negative_rate']
                if total < min_total_error:
                    min_total_error = total
                    best_thresh = row['threshold_value']
            
            lines.append(f"**Optimal Threshold (Min FPR+FNR)**: {best_thresh:.2f}")
            lines.append("")
    else:
        lines.append("*Sensitivity analysis data not available.*")
        lines.append("")

    lines.append("## Methodology Notes")
    lines.append("")
    lines.append("- **McNemar's Test**: Used for paired binary data (Success/Failure) to determine if the 2D restriction significantly alters success rates.")
    lines.append("- **Wilcoxon Signed-Rank Test**: Used for paired continuous data (Latency) to assess performance degradation.")
    lines.append("- **Bonferroni Correction**: Applied to account for multiple comparisons across task types.")
    lines.append("")
    lines.append("---")
    lines.append("*End of Report*")

    return "\n".join(lines)

def main():
    """Main entry point for report generation."""
    logger.info(f"Starting Final Statistical Report Generation (Task T048)")
    
    try:
        # 1. Load Data
        logger.info(f"Loading paired dataset from {INPUT_DATASET_PATH}")
        data = load_paired_dataset(INPUT_DATASET_PATH)
        if not data:
            raise ValueError("Loaded dataset is empty.")
        logger.info(f"Loaded {len(data)} records.")

        # 2. Run Statistical Tests
        logger.info("Running statistical tests (McNemar, Wilcoxon)...")
        stats_results = run_statistical_tests(data)
        
        # Save raw stats to JSON for reproducibility
        with open(OUTPUT_STATS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(stats_results, f, indent=2)
        logger.info(f"Saved raw stats to {OUTPUT_STATS_JSON_PATH}")

        # 3. Load Sensitivity Data
        logger.info("Loading sensitivity data...")
        sensitivity_data = load_sensitivity_data()

        # 4. Generate Report
        logger.info("Generating Markdown report...")
        report_content = generate_report_markdown(stats_results, sensitivity_data)

        # 5. Write Report
        os.makedirs(os.path.dirname(OUTPUT_REPORT_PATH), exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Report successfully written to {OUTPUT_REPORT_PATH}")
        print(f"SUCCESS: Final Statistical Report generated at {OUTPUT_REPORT_PATH}")
        return 0

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        print(f"FAILED: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
