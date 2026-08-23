"""
Final Statistical Report Generation (T048).

Executes statistical tests and sensitivity analysis against the final paired dataset
and generates a comprehensive markdown report.
"""
import os
import csv
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from scipy.stats import wilcoxon, chi2_contingency, shapiro, ttest_rel, norm

from stats.tests import (
    load_paired_dataset, 
    group_by_task_type, 
    extract_success_pairs, 
    extract_latency_pairs, 
    run_mcnemar_test, 
    check_normality, 
    run_ttest, 
    run_wilcoxon_test, 
    apply_bonferroni_correction
)
from stats.sensitivity import (
    load_comparison_results_for_flat_analysis,
    run_flat_object_sensitivity_analysis,
    write_flat_object_sensitivity_csv,
    is_flat_object
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('results/logs/final_report_generation.log')
    ]
)
logger = logging.getLogger(__name__)

def load_sensitivity_data_csv(filepath: str) -> List[Dict[str, Any]]:
    """Load sensitivity analysis CSV data."""
    data = []
    if not os.path.exists(filepath):
        logger.warning(f"Sensitivity data file not found: {filepath}")
        return data
    
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def generate_sensitivity_plot_data(data: List[Dict[str, Any]]) -> str:
    """Generate ASCII-based sensitivity plot description for markdown."""
    if not data:
        return "No sensitivity data available."
    
    lines = []
    lines.append("```")
    lines.append("Threshold Sensitivity Analysis (Flat Object Epsilon Sweep)")
    lines.append("")
    
    # Extract columns
    thresholds = [float(row['threshold_value']) for row in data if 'threshold_value' in row]
    fpr = [float(row['false_positive_rate']) for row in data if 'false_positive_rate' in row]
    fnr = [float(row['false_negative_rate']) for row in data if 'false_negative_rate' in row]
    
    if not thresholds or not fpr or not fnr:
        lines.append("Data format mismatch or missing columns.")
        lines.append("```")
        return "\n".join(lines)
    
    # Simple ASCII plot
    max_val = max(max(fpr, default=0), max(fnr, default=0), 1.0)
    scale = 40  # width of plot
    
    lines.append(f"{'Threshold':<10} {'FPR':>8} {'FNR':>8}")
    lines.append("-" * 30)
    
    for t, fp, fn in zip(thresholds, fpr, fnr):
        fp_bar = int((fp / max_val) * scale) if max_val > 0 else 0
        fn_bar = int((fn / max_val) * scale) if max_val > 0 else 0
        fp_str = "#" * fp_bar
        fn_str = "o" * fn_bar
        lines.append(f"{t:<10.4f} {fp:>7.3f} {fn:>7.3f}")
    
    lines.append("")
    lines.append("Legend: # = FPR, o = FNR")
    lines.append("```")
    return "\n".join(lines)

def generate_report_markdown(
    test_results: Dict[str, Any],
    sensitivity_data: List[Dict[str, Any]],
    methodology_log_path: Optional[str] = None
) -> str:
    """Generate the final statistical report in Markdown format."""
    
    report = []
    report.append("# Final Statistical Report: SpatialClaw Restriction Analysis")
    report.append("")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 1. Methodology Section
    report.append("## 1. Methodology")
    report.append("")
    report.append("This report summarizes the statistical analysis comparing the restricted 2D agent")
    report.append("against the 3D baseline on the Synthetic SpatialClaw Proxy dataset.")
    report.append("")
    
    # Check methodology log if available
    if methodology_log_path and os.path.exists(methodology_log_path):
        report.append("### Statistical Test Selection")
        report.append("")
        report.append("The choice of statistical test (T-test vs. Wilcoxon) was determined by a Shapiro-Wilk")
        report.append("normality check on the latency differences, as implemented in T057a.")
        report.append("")
        report.append("```")
        with open(methodology_log_path, 'r') as f:
            report.append(f.read())
        report.append("```")
        report.append("")
    
    # 2. Statistical Test Results
    report.append("## 2. Statistical Test Results")
    report.append("")
    report.append("### 2.1 Success Rate Comparison (McNemar's Test)")
    report.append("")
    report.append("| Task Type | Statistic | P-Value | Bonferroni Corrected P-Value | Significant (α=0.05) |")
    report.append("| :--- | :--- | :--- | :--- | :--- |")
    
    success_results = test_results.get('success_tests', {})
    for task_type, res in success_results.items():
        stat = res.get('statistic', 'N/A')
        p_val = res.get('p_value', 'N/A')
        corrected_p = res.get('bonferroni_p', 'N/A')
        sig = "Yes" if (isinstance(corrected_p, (int, float)) and corrected_p < 0.05) else "No"
        report.append(f"| {task_type} | {stat:.4f} | {p_val:.4e} | {corrected_p:.4e} | {sig} |")
    
    report.append("")
    
    report.append("### 2.2 Latency Comparison (Paired Test)")
    report.append("")
    report.append("| Task Type | Test Used | Statistic | P-Value | Bonferroni Corrected P-Value | Significant (α=0.05) |")
    report.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    latency_results = test_results.get('latency_tests', {})
    for task_type, res in latency_results.items():
        test_name = res.get('test_name', 'N/A')
        stat = res.get('statistic', 'N/A')
        p_val = res.get('p_value', 'N/A')
        corrected_p = res.get('bonferroni_p', 'N/A')
        sig = "Yes" if (isinstance(corrected_p, (int, float)) and corrected_p < 0.05) else "No"
        report.append(f"| {task_type} | {test_name} | {stat:.4f} | {p_val:.4e} | {corrected_p:.4e} | {sig} |")
    
    report.append("")
    
    # 3. Sensitivity Analysis
    report.append("## 3. Sensitivity Analysis: Flat Object Edge Cases")
    report.append("")
    report.append("This section analyzes the sensitivity of the 2D agent's performance to the tolerance")
    report.append("parameter (epsilon) used for identifying 'flat objects' (zero depth variance).")
    report.append("")
    
    if sensitivity_data:
        report.append("### 3.1 Threshold Sweep Results")
        report.append("")
        report.append("| Threshold (ε) | False Positive Rate | False Negative Rate |")
        report.append("| :--- | :--- | :--- |")
        for row in sensitivity_data:
            t = row.get('threshold_value', 'N/A')
            fp = row.get('false_positive_rate', 'N/A')
            fn = row.get('false_negative_rate', 'N/A')
            report.append(f"| {t} | {fp} | {fn} |")
        
        report.append("")
        report.append("### 3.2 Sensitivity Plot")
        report.append("")
        report.append(generate_sensitivity_plot_data(sensitivity_data))
    else:
        report.append("No sensitivity data was generated. Ensure T058a/T058b have been executed.")
    
    report.append("")
    
    # 4. Conclusion
    report.append("## 4. Conclusion: Loss Ceiling Hypothesis")
    report.append("")
    
    # Determine conclusion based on p-values
    # Hypothesis: 2D performance is significantly worse than 3D for occlusion tasks due to projection loss.
    # We look for significant p-values in the 'occlusion' task type for success rate.
    
    occlusion_success = success_results.get('occlusion', {})
    occlusion_sig = False
    if isinstance(occlusion_success.get('bonferroni_p'), (int, float)):
        occlusion_sig = occlusion_success['bonferroni_p'] < 0.05
    
    if occlusion_sig:
        conclusion = (
            "The analysis **supports** the 'Loss Ceiling' hypothesis. "
            "There is a statistically significant difference in success rates between the 2D restricted agent "
            "and the 3D baseline for **occlusion tasks** (Bonferroni-corrected p < 0.05). "
            "This suggests that the information lost during 2D projection is a primary limiting factor "
            "for the restricted agent's performance in these specific scenarios."
        )
    else:
        conclusion = (
            "The analysis **does not strongly support** the 'Loss Ceiling' hypothesis for occlusion tasks "
            "based on the current dataset. The difference in success rates was not statistically significant "
            "after Bonferroni correction. This may indicate that the 2D agent's logic is robust enough to handle "
            "most occlusion scenarios, or that the sample size was insufficient to detect the effect."
        )
    
    report.append(conclusion)
    report.append("")
    report.append("### Summary of Findings")
    report.append("")
    report.append("1. **Success Rate**: Significant degradation observed in [list types] tasks.")
    report.append("2. **Latency**: The 2D agent shows [faster/slower] latency compared to the 3D baseline.")
    report.append("3. **Edge Cases**: Sensitivity analysis indicates the flat object definition is [robust/sensitive] to epsilon variations.")
    report.append("")
    report.append("---")
    report.append("*End of Report*")
    
    return "\n".join(report)

def run_statistical_tests(paired_data_path: str) -> Dict[str, Any]:
    """
    Run all statistical tests on the paired dataset.
    Returns a dictionary of results.
    """
    logger.info(f"Loading paired dataset from {paired_data_path}")
    if not os.path.exists(paired_data_path):
        raise FileNotFoundError(f"Paired dataset not found: {paired_data_path}")
    
    df = load_paired_dataset(paired_data_path)
    if df is None or len(df) == 0:
        raise ValueError("Failed to load or empty paired dataset.")
    
    # Group by task type
    grouped = group_by_task_type(df)
    
    results = {
        'success_tests': {},
        'latency_tests': {},
        'methodology': {}
    }
    
    # Check normality for each task type to decide test
    for task_type, data in grouped.items():
        logger.info(f"Processing task type: {task_type}")
        
        # 1. Success Rate (McNemar)
        success_pairs = extract_success_pairs(data)
        if success_pairs and len(success_pairs[0]) > 1:
            try:
                stat, p_val = run_mcnemar_test(success_pairs[0], success_pairs[1])
                results['success_tests'][task_type] = {
                    'statistic': stat,
                    'p_value': p_val
                }
            except Exception as e:
                logger.warning(f"McNemar test failed for {task_type}: {e}")
                results['success_tests'][task_type] = {'error': str(e)}
        
        # 2. Latency (T-test or Wilcoxon)
        latency_pairs = extract_latency_pairs(data)
        if latency_pairs and len(latency_pairs[0]) > 1:
            try:
                # Check normality
                _, p_normal = check_normality(latency_pairs[0], latency_pairs[1])
                
                if p_normal > 0.05:
                    # Normal distribution -> T-test
                    stat, p_val = run_ttest(latency_pairs[0], latency_pairs[1])
                    test_name = "Paired T-Test"
                else:
                    # Non-normal -> Wilcoxon
                    stat, p_val = run_wilcoxon_test(latency_pairs[0], latency_pairs[1])
                    test_name = "Wilcoxon Signed-Rank"
                
                results['latency_tests'][task_type] = {
                    'test_name': test_name,
                    'statistic': stat,
                    'p_value': p_val
                }
                results['methodology'][task_type] = {
                    'normality_p': p_normal,
                    'test_selected': test_name
                }
            except Exception as e:
                logger.warning(f"Latency test failed for {task_type}: {e}")
                results['latency_tests'][task_type] = {'error': str(e)}
    
    # Apply Bonferroni Correction
    all_p_values = []
    for task_type, res in results['success_tests'].items():
        if 'p_value' in res:
            all_p_values.append(('success', task_type, res['p_value']))
    for task_type, res in results['latency_tests'].items():
        if 'p_value' in res:
            all_p_values.append(('latency', task_type, res['p_value']))
    
    if all_p_values:
        correction_factor = len(all_p_values)
        for metric_type, task_type, p_val in all_p_values:
            corrected = min(p_val * correction_factor, 1.0)
            if metric_type == 'success':
                results['success_tests'][task_type]['bonferroni_p'] = corrected
            else:
                results['latency_tests'][task_type]['bonferroni_p'] = corrected
    
    return results

def load_sensitivity_results(sensitivity_csv_path: str) -> List[Dict[str, Any]]:
    """Load sensitivity analysis results."""
    if not os.path.exists(sensitivity_csv_path):
        logger.warning(f"Sensitivity CSV not found: {sensitivity_csv_path}")
        return []
    
    return load_sensitivity_data_csv(sensitivity_csv_path)

def main():
    """Main entry point for T048."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Final Statistical Report (T048)")
    parser.add_argument(
        "--input-paired",
        default="results/analysis/final_paired_dataset.csv",
        help="Path to the final paired dataset CSV"
    )
    parser.add_argument(
        "--input-sensitivity",
        default="results/analysis/flat_object_sensitivity.csv",
        help="Path to the flat object sensitivity CSV"
    )
    parser.add_argument(
        "--methodology-log",
        default="results/analysis/statistical_methodology_log.md",
        help="Path to the methodology log (T057b output)"
    )
    parser.add_argument(
        "--output-report",
        default="results/analysis/final_statistical_report.md",
        help="Path for the output markdown report"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting Final Statistical Report Generation (T048)")
    
    try:
        # 1. Run Statistical Tests
        test_results = run_statistical_tests(args.input_paired)
        
        # 2. Load Sensitivity Data
        sensitivity_data = load_sensitivity_results(args.input_sensitivity)
        
        # 3. Generate Report
        report_content = generate_report_markdown(
            test_results=test_results,
            sensitivity_data=sensitivity_data,
            methodology_log_path=args.methodology_log
        )
        
        # 4. Write Report
        os.makedirs(os.path.dirname(args.output_report), exist_ok=True)
        with open(args.output_report, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Report generated successfully: {args.output_report}")
        
        # 5. Print summary to console
        print("\n" + "="*50)
        print("FINAL REPORT SUMMARY")
        print("="*50)
        if test_results.get('success_tests'):
            for t, res in test_results['success_tests'].items():
                p = res.get('bonferroni_p', 'N/A')
                sig = "SIGNIFICANT" if isinstance(p, (int,float)) and p < 0.05 else "Not Significant"
                print(f"Success ({t}): p={p:.4e} [{sig}]")
        if test_results.get('latency_tests'):
            for t, res in test_results['latency_tests'].items():
                p = res.get('bonferroni_p', 'N/A')
                sig = "SIGNIFICANT" if isinstance(p, (int,float)) and p < 0.05 else "Not Significant"
                print(f"Latency ({t}): p={p:.4e} [{sig}]")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()