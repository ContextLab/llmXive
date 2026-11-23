"""
Execute Robustness Check (T057b)

Runs the Shapiro-Wilk check implemented in T057a on the final paired dataset
and writes the statistical methodology log.

Output: results/analysis/statistical_methodology_log.md
Dependency: T047c (Final Paired Dataset Execution)
"""
import os
import sys
import csv
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy.stats import shapiro

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats.tests import load_paired_dataset, group_by_task_type, check_normality

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PAIRED_DATASET_PATH = "results/analysis/final_paired_dataset.csv"
OUTPUT_LOG_PATH = "results/analysis/statistical_methodology_log.md"

def load_latencies_by_type(paired_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """
    Extract latency differences (2D - 3D) grouped by task type.
    """
    grouped = group_by_task_type(paired_data)
    latencies = {}
    
    for task_type, tasks in grouped.items():
        diffs = []
        for task in tasks:
            try:
                # Extract latencies, handling potential string/float conversion
                lat_2d = float(task.get('2d_mean_latency', 0))
                lat_3d = float(task.get('3d_latency', 0))
                diff = lat_2d - lat_3d
                diffs.append(diff)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping task {task.get('task_id')} due to latency parsing error: {e}")
                continue
        
        if diffs:
            latencies[task_type] = diffs
        else:
            logger.warning(f"No valid latency differences found for task type: {task_type}")
    
    return latencies

def run_shapiro_wilk_check(latencies: Dict[str, List[float]]) -> Dict[str, Dict[str, Any]]:
    """
    Run Shapiro-Wilk test for normality on each task type's latency differences.
    Returns results including statistic, p-value, and normality conclusion.
    """
    results = {}
    
    for task_type, diffs in latencies.items():
        if len(diffs) < 3:
            results[task_type] = {
                'statistic': None,
                'p_value': None,
                'is_normal': False,
                'reason': 'Insufficient data points (n < 3)',
                'recommendation': 'Use non-parametric test (Wilcoxon) due to low sample size.'
            }
            continue
        
        try:
            statistic, p_value = shapiro(diffs)
            is_normal = p_value > 0.05  # Alpha = 0.05
            
            results[task_type] = {
                'statistic': float(statistic),
                'p_value': float(p_value),
                'is_normal': is_normal,
                'reason': f'p-value ({p_value:.4f}) {"< 0.05" if not is_normal else ">= 0.05"}',
                'recommendation': 'Use t-test (paired)' if is_normal else 'Use non-parametric test (Wilcoxon signed-rank)'
            }
        except Exception as e:
            results[task_type] = {
                'statistic': None,
                'p_value': None,
                'is_normal': False,
                'reason': f'Test execution failed: {str(e)}',
                'recommendation': 'Use non-parametric test (Wilcoxon) due to test failure.'
            }
    
    return results

def generate_methodology_log(results: Dict[str, Dict[str, Any]]) -> str:
    """
    Generate the markdown report documenting the statistical methodology selection.
    """
    lines = [
        "# Statistical Methodology Log",
        "",
        "## Purpose",
        "This report documents the results of the Shapiro-Wilk normality check performed on the latency differences",
        "between the 2D restricted agent and the 3D baseline agent. Based on these results, the appropriate",
        "statistical test (parametric t-test vs. non-parametric Wilcoxon signed-rank) is selected for each task type.",
        "",
        "## Methodology",
        "- **Test**: Shapiro-Wilk Test for Normality",
        "- **Null Hypothesis (H0)**: The distribution of latency differences is normal.",
        "- **Significance Level (α)**: 0.05",
        "- **Decision Rule**: If p-value > 0.05, fail to reject H0 (assume normal); otherwise, reject H0 (non-normal).",
        "",
        "## Results by Task Type",
        ""
    ]
    
    for task_type, res in results.items():
        lines.append(f"### {task_type.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"- **Shapiro-Wilk Statistic**: {res['statistic'] if res['statistic'] is not None else 'N/A'}")
        lines.append(f"- **P-value**: {res['p_value'] if res['p_value'] is not None else 'N/A'}")
        lines.append(f"- **Normality Assumption**: {'✅ Satisfied' if res['is_normal'] else '❌ Violated'}")
        lines.append(f"- **Reason**: {res['reason']}")
        lines.append(f"- **Selected Test**: {res['recommendation']}")
        lines.append("")
    
    lines.append("## Summary & Recommendations")
    lines.append("")
    
    normal_count = sum(1 for r in results.values() if r['is_normal'])
    total_count = len(results)
    
    if normal_count == total_count:
        lines.append("All task types satisfy the normality assumption. **Paired t-tests** will be used for all comparisons.")
    elif normal_count == 0:
        lines.append("No task types satisfy the normality assumption. **Wilcoxon signed-rank tests** will be used for all comparisons.")
    else:
        lines.append("Mixed results detected. Statistical tests will be selected per task type:")
        for task_type, res in results.items():
            test_name = "Paired t-test" if res['is_normal'] else "Wilcoxon signed-rank test"
            lines.append(f"- **{task_type}**: {test_name}")
    
    lines.append("")
    lines.append("---")
    lines.append("*Generated by T057b: Execute Robustness Check*")
    
    return "\n".join(lines)

def main():
    """
    Main entry point for T057b.
    """
    logger.info("Starting Robustness Check (T057b)...")
    
    # Verify input file exists
    if not os.path.exists(PAIRED_DATASET_PATH):
        logger.error(f"Input file not found: {PAIRED_DATASET_PATH}")
        logger.error("Dependency T047c (Final Paired Dataset Execution) must be completed first.")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading paired dataset from {PAIRED_DATASET_PATH}...")
    try:
        paired_data = load_paired_dataset(PAIRED_DATASET_PATH)
        if not paired_data:
            logger.error("Paired dataset is empty. Cannot perform robustness check.")
            sys.exit(1)
        logger.info(f"Loaded {len(paired_data)} task instances.")
    except Exception as e:
        logger.error(f"Failed to load paired dataset: {e}")
        sys.exit(1)
    
    # Extract latencies
    logger.info("Extracting latency differences by task type...")
    latencies = load_latencies_by_type(paired_data)
    if not latencies:
        logger.error("No valid latency data found to analyze.")
        sys.exit(1)
    
    # Run Shapiro-Wilk
    logger.info("Running Shapiro-Wilk normality tests...")
    results = run_shapiro_wilk_check(latencies)
    
    # Generate report
    logger.info(f"Generating methodology log at {OUTPUT_LOG_PATH}...")
    report_content = generate_methodology_log(results)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_LOG_PATH), exist_ok=True)
    
    # Write report
    with open(OUTPUT_LOG_PATH, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info("Robustness check completed successfully.")
    logger.info(f"Report written to: {OUTPUT_LOG_PATH}")
    
    # Print summary to console
    print("\n" + "="*60)
    print("ROBUSTNESS CHECK SUMMARY")
    print("="*60)
    for task_type, res in results.items():
        status = "NORMAL" if res['is_normal'] else "NON-NORMAL"
        print(f"{task_type}: {status} (p={res['p_value']:.4f}) -> {res['recommendation']}")
    print("="*60)

if __name__ == "__main__":
    main()
