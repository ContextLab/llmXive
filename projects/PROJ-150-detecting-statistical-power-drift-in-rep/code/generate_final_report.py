import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_safe(path, default=None):
    """Safely load a JSON file, returning a default if not found or invalid."""
    if not os.path.exists(path):
        logger.warning(f"File not found: {path}")
        return default
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON {path}: {e}")
        return default

def format_float(val, decimals=4):
    """Format a float value, handling None."""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"

def generate_final_report():
    """
    Generates results/final_report.md summarizing all findings from:
    - LMM Model (T011c)
    - Permutation Tests (T020, T020b)
    - Sensitivity Analysis (T021b)
    - Cross-Field Aggregation (T025)
    """
    base_dir = Path(__file__).parent.parent
    results_dir = base_dir / "results"
    output_path = results_dir / "final_report.md"

    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating final report...")

    # Load all relevant artifacts
    lmm_summary = load_json_safe(results_dir / "lmm_final_summary.json", {})
    perm_pval = load_json_safe(results_dir / "permutation_pvalue.json", {})
    input_perm = load_json_safe(results_dir / "input_permutation.json", {})
    sensitivity = load_json_safe(results_dir / "sensitivity_report.json", {})
    agg_drift = load_json_safe(results_dir / "aggregated_drift.json", {})

    # --- Report Construction ---
    report_lines = []
    report_lines.append("# Final Report: Detecting Statistical Power Drift in Replicated Studies")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # 1. Executive Summary
    report_lines.append("## 1. Executive Summary")
    report_lines.append("")
    slope = lmm_summary.get('slope_year')
    p_lrt = lmm_summary.get('p_value_lrt')
    drift_direction = "decreasing" if slope and slope < 0 else "increasing" if slope and slope > 0 else "no clear"
    
    report_lines.append(f"The primary analysis indicates a **{drift_direction}** drift in statistical power over time.")
    report_lines.append(f"- **LMM Slope (Year):** {format_float(slope)}")
    report_lines.append(f"- **LMM 95% CI:** [{format_float(lmm_summary.get('ci_lower'))}, {format_float(lmm_summary.get('ci_upper'))}]")
    report_lines.append(f"- **LRT p-value:** {format_float(p_lrt)}")
    report_lines.append("")
    if p_lrt is not None and p_lrt < 0.05:
        report_lines.append("**Conclusion:** The temporal decline in power is statistically significant (p < 0.05).")
    else:
        report_lines.append("**Conclusion:** The evidence for temporal drift is not statistically significant at the 0.05 level.")
    report_lines.append("")

    # 2. Primary LMM Analysis
    report_lines.append("## 2. Primary LMM Analysis")
    report_lines.append("")
    report_lines.append("A Linear Mixed-Effects Model (LMM) was fitted with `power_estimate` as the outcome,")
    report_lines.append("`year` as a fixed effect, and random intercepts for `field` and `original_study_id`.")
    report_lines.append("")
    report_lines.append("| Metric | Value |")
    report_lines.append("| :--- | :--- |")
    report_lines.append(f"| Slope (Year) | {format_float(slope)} |")
    report_lines.append(f"| Standard Error | {format_float(lmm_summary.get('se_year'))} |")
    report_lines.append(f"| 95% CI Lower | {format_float(lmm_summary.get('ci_lower'))} |")
    report_lines.append(f"| 95% CI Upper | {format_float(lmm_summary.get('ci_upper'))} |")
    report_lines.append(f"| LRT Chi-Square | {format_float(lmm_summary.get('chi2_statistic'))} |")
    report_lines.append(f"| LRT p-value | {format_float(p_lrt)} |")
    report_lines.append("")
    report_lines.append("**Methodology Note:** " + lmm_summary.get('methodology_note', 'N/A'))
    report_lines.append("")

    # 3. Robustness: Permutation Tests
    report_lines.append("## 3. Robustness: Permutation Tests")
    report_lines.append("")
    
    report_lines.append("### 3.1 Year Permutation Test")
    report_lines.append("Shuffled `year` labels to generate a null distribution for the slope.")
    report_lines.append(f"- **Observed Slope:** {format_float(perm_pval.get('observed_slope'))}")
    report_lines.append(f"- **Empirical p-value:** {format_float(perm_pval.get('empirical_p_value'))}")
    report_lines.append(f"- **Iterations:** {perm_pval.get('iterations', 0)}")
    if perm_pval.get('fallback_used'):
        report_lines.append("*Note: Fallback to reduced iterations was used due to timeout.*")
    report_lines.append("")

    report_lines.append("### 3.2 Input Permutation Test")
    report_lines.append("Shuffled study rows (preserving joint distribution of effect size and sample size) while keeping year constant.")
    report_lines.append(f"- **Observed Slope:** {format_float(input_perm.get('observed_slope'))}")
    report_lines.append(f"- **Null Distribution Mean:** {format_float(input_perm.get('null_distribution_mean'))}")
    report_lines.append(f"- **Null Distribution Std:** {format_float(input_perm.get('null_distribution_std'))}")
    report_lines.append(f"- **Input Perm p-value:** {format_float(input_perm.get('p_value_input_perm'))}")
    if 'aggregated_slope_p_value' in input_perm:
        report_lines.append(f"- **Aggregated Slope p-value:** {format_float(input_perm.get('aggregated_slope_p_value'))}")
    report_lines.append("")

    # 4. Sensitivity Analysis
    report_lines.append("## 4. Sensitivity Analysis")
    report_lines.append("Significance of the drift effect across different alpha thresholds.")
    report_lines.append("")
    report_lines.append("| Alpha Threshold | Drift Significant? | False Positive Rate |")
    report_lines.append("| :--- | :--- | :--- |")
    
    results_list = sensitivity.get('results', [])
    if not results_list:
        report_lines.append("| *No data available* | - | - |")
    else:
        for res in results_list:
            sig = "Yes" if res.get('drift_significant') else "No"
            fpr = format_float(res.get('false_positive_rate'))
            report_lines.append(f"| {res.get('alpha_value')} | {sig} | {fpr} |")
    report_lines.append("")

    # 5. Cross-Field Aggregation
    report_lines.append("## 5. Cross-Field Aggregation")
    report_lines.append("Adaptively weighted statistic (DerSimonian-Laird) combining evidence across fields.")
    report_lines.append("")
    report_lines.append("| Metric | Value |")
    report_lines.append("| :--- | :--- |")
    report_lines.append(f"| Aggregated Slope | {format_float(agg_drift.get('aggregated_slope'))} |")
    report_lines.append(f"| Aggregated SE | {format_float(agg_drift.get('aggregated_se'))} |")
    report_lines.append(f"| Heterogeneity (Q) | {format_float(agg_drift.get('heterogeneity_q'))} |")
    report_lines.append(f"| Tau-squared (τ²) | {format_float(agg_drift.get('tau_squared'))} |")
    report_lines.append(f"| Aggregated p-value | {format_float(agg_drift.get('aggregated_p_value'))} |")
    report_lines.append("")

    # 6. Conclusion
    report_lines.append("## 6. Conclusion")
    report_lines.append("")
    report_lines.append("This analysis integrated a primary LMM approach with robust permutation tests and")
    report_lines.append("cross-field aggregation to detect statistical power drift. The results suggest that")
    report_lines.append(f"power trends over time are {'consistent' if p_lrt and p_lrt < 0.05 else 'inconclusive'} with a systematic decline.")
    report_lines.append("Further investigation into specific fields showing high heterogeneity is recommended.")
    report_lines.append("")

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Final report generated successfully: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_final_report()