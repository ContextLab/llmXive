"""
Final Statistical Report Generation (T048)

Executes statistical tests and sensitivity analysis against the final paired dataset
and generates a comprehensive Markdown report.
"""
import os
import csv
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from scipy.stats import wilcoxon, chi2_contingency, shapiro, ttest_rel

# Ensure the stats module is in the path when run as script
import sys
import glob

# Add parent directory to path to resolve imports if run directly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from stats.tests import (
    load_paired_dataset,
    group_by_task_type,
    extract_success_pairs,
    extract_latency_pairs,
    run_mcnemar_test,
    check_normality,
    run_ttest,
    run_wilcoxon_test,
    apply_bonferroni_correction,
    run_statistical_tests
)
from stats.sensitivity import (
    load_comparison_results_for_flat_analysis,
    run_flat_object_sensitivity_analysis,
    write_flat_object_sensitivity_csv
)
from stats.analyze_projection_loss import run_projection_loss_analysis
from utils.verify_baseline_consistency import load_json_file
from utils.budget_report import load_budget_report

logger = logging.getLogger(__name__)

RESULTS_DIR = "results/analysis"
DATA_DIR = "data/raw"

def load_paired_dataset(filepath: str) -> List[Dict[str, Any]]:
    """Load the final paired dataset CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Paired dataset not found at {filepath}")
    
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['2d_success_rate'] = float(row['2d_success_rate'])
            row['2d_mean_latency'] = float(row['2d_mean_latency'])
            row['3d_success'] = int(row['3d_success']) # 0 or 1
            row['3d_latency'] = float(row['3d_latency'])
            row['success_diff'] = float(row['success_diff'])
            row['latency_diff'] = float(row['latency_diff'])
            data.append(row)
    return data

def group_by_task_type(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group data by task_type."""
    groups = {}
    for row in data:
        t_type = row['task_type']
        if t_type not in groups:
            groups[t_type] = []
        groups[t_type].append(row)
    return groups

def extract_success_pairs(group: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    """Extract 2D success rate (as 0/1 for McNemar approximation) and 3D success."""
    # Note: McNemar requires binary outcomes. We use the aggregated success rate 
    # thresholded at 0.5 or use the raw 3D success vs mean 2D success rate.
    # For strict McNemar, we need per-task binary outcomes. 
    # Since we have aggregated rates, we will use a threshold: success_rate >= 0.5 -> 1
    # This is a pragmatic adaptation for the aggregated dataset.
    s_2d = [1 if float(r['2d_success_rate']) >= 0.5 else 0 for r in group]
    s_3d = [int(r['3d_success']) for r in group]
    return s_2d, s_3d

def extract_latency_pairs(group: List[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
    """Extract latency pairs."""
    l_2d = [float(r['2d_mean_latency']) for r in group]
    l_3d = [float(r['3d_latency']) for r in group]
    return l_2d, l_3d

def run_statistical_tests(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run all required statistical tests and return results."""
    groups = group_by_task_type(data)
    results = {
        "test_methodology_log": [],
        "tests": {}
    }

    for task_type, group in groups.items():
        logger.info(f"Running tests for {task_type}")
        
        # 1. Normality Check (Shapiro-Wilk) on latency differences
        l_2d, l_3d = extract_latency_pairs(group)
        diffs = [a - b for a, b in zip(l_2d, l_3d)]
        
        is_normal = True
        test_name = "t-test"
        
        if len(diffs) >= 3: # Shapiro requires at least 3 samples
            stat, p_val = shapiro(diffs)
            log_entry = f"Shapiro-Wilk for {task_type}: W={stat:.4f}, p={p_val:.4f}"
            results["test_methodology_log"].append(log_entry)
            
            if p_val < 0.05:
                is_normal = False
                test_name = "Wilcoxon"
                results["test_methodology_log"].append(f"  -> Normality violated, switching to Wilcoxon")
            else:
                results["test_methodology_log"].append(f"  -> Normality assumed, using t-test")
        else:
            results["test_methodology_log"].append(f"Shapiro-Wilk skipped for {task_type} (N < 3)")

        # 2. Latency Comparison
        if test_name == "t-test":
            stat, p_val = ttest_rel(l_2d, l_3d)
        else:
            stat, p_val = wilcoxon(l_2d, l_3d)
        
        results["tests"][f"{task_type}_latency"] = {
            "test": test_name,
            "statistic": float(stat),
            "p_value_raw": float(p_val),
            "p_value_corrected": 0.0 # Will be corrected later
        }

        # 3. Success Comparison (McNemar approximation using binary threshold)
        s_2d, s_3d = extract_success_pairs(group)
        # Construct contingency table:
        # a: 2D=1, 3D=1
        # b: 2D=1, 3D=0
        # c: 2D=0, 3D=1
        # d: 2D=0, 3D=0
        a = sum(1 for x, y in zip(s_2d, s_3d) if x == 1 and y == 1)
        b = sum(1 for x, y in zip(s_2d, s_3d) if x == 1 and y == 0)
        c = sum(1 for x, y in zip(s_2d, s_3d) if x == 0 and y == 1)
        d = sum(1 for x, y in zip(s_2d, s_3d) if x == 0 and y == 0)
        
        contingency = [[a, b], [c, d]]
        try:
            chi2, p_val_mcnemar, _, _ = chi2_contingency(contingency, correction=True)
            results["tests"][f"{task_type}_success"] = {
                "test": "McNemar (Chi2 approx)",
                "statistic": float(chi2),
                "p_value_raw": float(p_val_mcnemar),
                "p_value_corrected": 0.0,
                "contingency": contingency
            }
        except Exception as e:
            results["tests"][f"{task_type}_success"] = {
                "test": "McNemar",
                "error": str(e),
                "contingency": contingency
            }

    # Apply Bonferroni Correction
    n_tests = len(results["tests"])
    if n_tests > 0:
        alpha = 0.05
        corrected_alpha = alpha / n_tests
        for key in results["tests"]:
            if "p_value_raw" in results["tests"][key]:
                raw_p = results["tests"][key]["p_value_raw"]
                results["tests"][key]["p_value_corrected"] = min(raw_p * n_tests, 1.0)
                results["tests"][key]["corrected_alpha"] = corrected_alpha
                results["tests"][key]["significant"] = results["tests"][key]["p_value_corrected"] < alpha

    return results

def load_sensitivity_data() -> Dict[str, Any]:
    """Load sensitivity analysis results."""
    sensitivity_file = os.path.join(RESULTS_DIR, "flat_object_sensitivity.csv")
    data = []
    if os.path.exists(sensitivity_file):
        with open(sensitivity_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    "epsilon": float(row["epsilon"]),
                    "fpr": float(row["false_positive_rate"]),
                    "fnr": float(row["false_negative_rate"])
                })
    return data

def generate_report_markdown(
    stats_results: Dict[str, Any], 
    sensitivity_data: List[Dict[str, Any]],
    projection_loss_data: Optional[Dict[str, Any]] = None,
    baseline_determinism_report: Optional[str] = None
) -> str:
    """Generate the final Markdown report."""
    lines = []
    lines.append("# Final Statistical Report: SpatialClaw Restriction")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Executive Summary / Conclusion on Loss Ceiling Hypothesis
    lines.append("## 1. Executive Summary & Hypothesis Conclusion")
    lines.append("")
    lines.append("**Hypothesis:** The 2D-restricted agent will exhibit statistically significant performance degradation (higher latency, lower success) compared to the 3D baseline, primarily due to 'projection loss' in occlusion tasks.")
    lines.append("")
    
    significant_latencies = 0
    significant_successes = 0
    total_tests = 0
    
    for key, res in stats_results.get("tests", {}).items():
        if "significant" in res:
            total_tests += 1
            if res["significant"]:
                if "latency" in key:
                    significant_latencies += 1
                elif "success" in key:
                    significant_successes += 1

    lines.append(f"**Statistical Significance (Bonferroni corrected, α=0.05):**")
    lines.append(f"- Latency tests: {significant_latencies}/{total_tests // 2} showed significant difference.")
    lines.append(f"- Success tests: {significant_successes}/{total_tests // 2} showed significant difference.")
    lines.append("")
    
    if significant_latencies > 0 or significant_successes > 0:
        lines.append("✅ **Conclusion:** The data supports the hypothesis. The 2D restriction introduces a measurable 'loss ceiling', resulting in statistically significant performance degradation compared to the 3D baseline.")
    else:
        lines.append("⚠️ **Conclusion:** No statistically significant degradation was detected after correction. The 2D restriction may not impose a significant 'loss ceiling' for the tested tasks, or the sample size was insufficient.")
    lines.append("")

    # Methodology Log
    lines.append("## 2. Statistical Methodology")
    lines.append("")
    lines.append("The following tests were selected based on normality checks (Shapiro-Wilk) on latency differences:")
    lines.append("")
    for log in stats_results.get("test_methodology_log", []):
        lines.append(f"- {log}")
    lines.append("")

    # Detailed Results
    lines.append("## 3. Detailed Statistical Results")
    lines.append("")
    
    for task_type in ["occlusion", "depth", "relative"]:
        if f"{task_type}_latency" in stats_results["tests"]:
            lines.append(f"### {task_type.capitalize()} Tasks")
            lines.append("")
            lines.append("| Metric | Test | Statistic | P-Value (Raw) | P-Value (Bonferroni) | Significant? |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            
            # Latency
            lat_res = stats_results["tests"][f"{task_type}_latency"]
            sig_mark = "Yes" if lat_res.get("significant", False) else "No"
            lines.append(f"| Latency | {lat_res['test']} | {lat_res['statistic']:.4f} | {lat_res['p_value_raw']:.4f} | {lat_res['p_value_corrected']:.4f} | {sig_mark} |")
            
            # Success
            if f"{task_type}_success" in stats_results["tests"]:
                succ_res = stats_results["tests"][f"{task_type}_success"]
                if "error" not in succ_res:
                    sig_mark = "Yes" if succ_res.get("significant", False) else "No"
                    lines.append(f"| Success | {succ_res['test']} | {succ_res['statistic']:.4f} | {succ_res['p_value_raw']:.4f} | {succ_res['p_value_corrected']:.4f} | {sig_mark} |")
                    lines.append(f"  *Contingency Table:* {succ_res['contingency']}")
                else:
                    lines.append(f"| Success | Error | - | - | - | - |")
                    lines.append(f"  *Error:* {succ_res['error']}")
            lines.append("")

    # Sensitivity Analysis
    lines.append("## 4. Sensitivity Analysis (Flat Objects)")
    lines.append("")
    if sensitivity_data:
        lines.append("Effect of varying epsilon (zero-depth variance tolerance) on false positive/negative rates:")
        lines.append("")
        lines.append("| Epsilon | False Positive Rate | False Negative Rate |")
        lines.append("| :--- | :--- | :--- |")
        for row in sensitivity_data:
            lines.append(f"| {row['epsilon']:.4f} | {row['fpr']:.4f} | {row['fnr']:.4f} |")
        lines.append("")
    else:
        lines.append("No sensitivity data available.")
        lines.append("")

    # Projection Loss Breakdown
    lines.append("## 5. Failure Attribution (Projection Loss vs Action Restriction)")
    lines.append("")
    if projection_loss_data:
        total_failures = projection_loss_data.get("total_failures", 0)
        projection_losses = projection_loss_data.get("projection_loss_count", 0)
        action_restrictions = projection_loss_data.get("action_restriction_count", 0)
        
        lines.append(f"- **Total 2D Failures:** {total_failures}")
        lines.append(f"- **Attributed to Projection Loss:** {projection_losses} ({(projection_losses/total_failures*100) if total_failures > 0 else 0:.1f}%)")
        lines.append(f"- **Attributed to Action Restriction:** {action_restrictions} ({(action_restrictions/total_failures*100) if total_failures > 0 else 0:.1f}%)")
        lines.append("")
    else:
        lines.append("No projection loss breakdown available.")
        lines.append("")

    # Baseline Determinism
    lines.append("## 6. Baseline Determinism Verification")
    lines.append("")
    if baseline_determinism_report:
        lines.append(baseline_determinism_report)
    else:
        lines.append("Baseline determinism verification report not found.")
    lines.append("")

    # Budget Compliance
    lines.append("## 7. Budget Compliance")
    lines.append("")
    budget_file = os.path.join(RESULTS_DIR, "budget_compliance_report.json")
    if os.path.exists(budget_file):
        with open(budget_file, 'r') as f:
            budget_data = json.load(f)
            lines.append(f"- **Total Runtime:** {budget_data.get('total_runtime_seconds', 'N/A')}s")
            lines.append(f"- **Budget Limit:** {budget_data.get('budget_limit_seconds', 'N/A')}s")
            lines.append(f"- **Status:** {budget_data.get('status', 'N/A')}")
    else:
        lines.append("Budget compliance report not found.")
    lines.append("")

    return "\n".join(lines)

def main():
    """Main entry point for T048."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    paired_dataset_path = os.path.join(RESULTS_DIR, "final_paired_dataset.csv")
    output_path = os.path.join(RESULTS_DIR, "final_statistical_report.md")

    if not os.path.exists(paired_dataset_path):
        logger.error(f"Paired dataset not found at {paired_dataset_path}. Did T047 run?")
        return 1

    logger.info("Loading paired dataset...")
    data = load_paired_dataset(paired_dataset_path)
    logger.info(f"Loaded {len(data)} task instances.")

    logger.info("Running statistical tests...")
    stats_results = run_statistical_tests(data)

    logger.info("Loading sensitivity data...")
    sensitivity_data = load_sensitivity_data()

    logger.info("Loading projection loss breakdown...")
    projection_loss_data = None
    pl_file = os.path.join(RESULTS_DIR, "projection_loss_breakdown.json")
    if os.path.exists(pl_file):
        with open(pl_file, 'r') as f:
            projection_loss_data = json.load(f)

    logger.info("Loading baseline determinism report...")
    baseline_report = None
    bd_file = os.path.join(RESULTS_DIR, "baseline_determinism_report.md")
    if os.path.exists(bd_file):
        with open(bd_file, 'r') as f:
            baseline_report = f.read()

    logger.info("Generating Markdown report...")
    report = generate_report_markdown(
        stats_results, 
        sensitivity_data, 
        projection_loss_data, 
        baseline_report
    )

    logger.info(f"Writing report to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info("T048 Complete. Report generated.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
