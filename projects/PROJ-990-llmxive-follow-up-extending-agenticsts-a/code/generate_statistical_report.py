import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return None

def load_token_reduction_verification(file_path: str) -> Optional[Dict[str, Any]]:
    """Load token reduction verification data."""
    # This file might be part of the baseline comparison or a separate file
    # For now, we assume it's derived from baseline_comparison.csv or similar
    # If it doesn't exist, we'll handle it gracefully
    data = load_json_file(file_path)
    if data:
        return data
    # Fallback: check if we can derive from other files
    baseline_path = "data/processed/baseline_comparison.csv"
    if os.path.exists(baseline_path):
        import pandas as pd
        df = pd.read_csv(baseline_path)
        if 'token_reduction_pct' in df.columns:
            return {
                "token_reduction_pct": float(df['token_reduction_pct'].iloc[0]) if len(df) > 0 else 0.0,
                "threshold_met": bool(df['threshold_met'].iloc[0]) if len(df) > 0 else False
            }
    return None

def load_statistical_results(file_path: str) -> Optional[Dict[str, Any]]:
    """Load aggregated statistical results."""
    return load_json_file(file_path)

def generate_final_report(
    template_path: str,
    agg_stats: Dict[str, Any],
    success_criteria: Dict[str, Any],
    token_verification: Optional[Dict[str, Any]]
) -> str:
    """Generate the final statistical report by filling the template."""
    # Read the template
    with open(template_path, 'r') as f:
        template = f.read()

    # Extract values from aggregated stats
    is_paired = agg_stats.get('paired_status', {}).get('is_paired', False)
    excluded_count = agg_stats.get('paired_status', {}).get('excluded_trajectories_count', 0)
    n_pairs = agg_stats.get('paired_status', {}).get('total_pairs', 0)

    mcnemar = agg_stats.get('mcnemar_results', {})
    ttest = agg_stats.get('ttest_results', {})
    power = agg_stats.get('power_analysis', {})

    dynamic_win_rate = mcnemar.get('dynamic_win_rate', 0.0)
    static_win_rate = mcnemar.get('static_win_rate', 0.0)
    win_rate_diff = dynamic_win_rate - static_win_rate
    mcnemar_stat = mcnemar.get('chi_square', 0.0)
    mcnemar_p = mcnemar.get('p_value', 1.0)
    mcnemar_sig = "Significant" if mcnemar_p < 0.05 else "Not Significant"
    mcnemar_conclusion = "Reject H0: Dynamic policy has different win rate." if mcnemar_p < 0.05 else "Fail to reject H0: No evidence of difference in win rates."

    mean_static = ttest.get('mean_static_tokens', 0.0)
    mean_dynamic = ttest.get('mean_dynamic_tokens', 0.0)
    mean_savings = ttest.get('mean_savings', 0.0)
    std_savings = ttest.get('std_savings', 0.0)
    t_stat = ttest.get('t_statistic', 0.0)
    t_p = ttest.get('p_value_bonferroni', 1.0)
    t_sig = "Significant" if t_p < 0.05 else "Not Significant"
    t_conclusion = "Reject H0: Dynamic policy saves tokens." if t_p < 0.05 else "Fail to reject H0: No evidence of token savings."

    sample_size = agg_stats.get('sample_size', 0)
    power_result = power.get('achieved_power', 0.0)
    power_limitation = power.get('limitation_statement', "Power analysis not performed.")

    homogeneity = agg_stats.get('homogeneity_check', {})
    homogeneity_status = homogeneity.get('status', 'Unknown')
    homogeneity_obs = homogeneity.get('observation', 'No homogeneity issues detected.')

    edge_cases = agg_stats.get('edge_cases', {})
    entropy_count = edge_cases.get('nan_entropy_count', 0)
    divergence_pct = edge_cases.get('divergence_percentage', 0.0)
    pruning_count = edge_cases.get('pruning_count', 0)

    # Success criteria
    sc001_status = success_criteria.get('SC-001', {}).get('status', 'Unknown')
    sc001_evidence = success_criteria.get('SC-001', {}).get('evidence', 'N/A')
    sc002_status = success_criteria.get('SC-002', {}).get('status', 'Unknown')
    sc002_evidence = success_criteria.get('SC-002', {}).get('evidence', 'N/A')
    sc003_status = success_criteria.get('SC-003', {}).get('status', 'Unknown')
    sc003_evidence = success_criteria.get('SC-003', {}).get('evidence', 'N/A')
    sc004_status = success_criteria.get('SC-004', {}).get('status', 'Unknown')
    sc004_evidence = success_criteria.get('SC-004', {}).get('evidence', 'N/A')

    # Token reduction verification
    token_reduction_pct = token_verification.get('token_reduction_pct', 0.0) if token_verification else 0.0

    # Final conclusion
    final_conclusion = []
    if mcnemar_p < 0.05 and t_p < 0.05:
        final_conclusion.append("The dynamic retrieval policy significantly improves win rates and reduces token consumption compared to the static baseline.")
    elif mcnemar_p < 0.05:
        final_conclusion.append("The dynamic retrieval policy significantly improves win rates, but token savings were not statistically significant.")
    elif t_p < 0.05:
        final_conclusion.append("The dynamic retrieval policy significantly reduces token consumption, but win rate differences were not statistically significant.")
    else:
        final_conclusion.append("No statistically significant differences were found between the dynamic and static policies for win rate or token consumption.")

    if sample_size < 300:
        final_conclusion.append(f"However, with a sample size of {sample_size}, statistical power may be marginal. Results should be interpreted with caution.")

    recommendations = [
        "Consider increasing the sample size for future studies to improve statistical power.",
        "Monitor edge cases (NaN entropy, divergence) to ensure data quality in production."
    ]

    # Fill template
    report = template.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
    report = report.replace("{{IS_PAIRED_STATUS}}", str(is_paired))
    report = report.replace("{{EXCLUDED_TRAJECTORIES_COUNT}}", str(excluded_count))
    report = report.replace("{{N_PAIRS}}", str(n_pairs))
    report = report.replace("{{DYNAMIC_WIN_RATE}}", f"{dynamic_win_rate:.4f}")
    report = report.replace("{{STATIC_WIN_RATE}}", f"{static_win_rate:.4f}")
    report = report.replace("{{WIN_RATE_DIFF}}", f"{win_rate_diff:.4f}")
    report = report.replace("{{MCNEMAR_STATISTIC}}", f"{mcnemar_stat:.4f}")
    report = report.replace("{{MCNEMAR_PVALUE}}", f"{mcnemar_p:.6f}")
    report = report.replace("{{MCNEMAR_SIGNIFICANT}}", mcnemar_sig)
    report = report.replace("{{MCNEMAR_CONCLUSION}}", mcnemar_conclusion)
    report = report.replace("{{MEAN_STATIC_TOKENS}}", f"{mean_static:.2f}")
    report = report.replace("{{MEAN_DYNAMIC_TOKENS}}", f"{mean_dynamic:.2f}")
    report = report.replace("{{MEAN_TOKEN_SAVINGS}}", f"{mean_savings:.2f}")
    report = report.replace("{{STD_TOKEN_SAVINGS}}", f"{std_savings:.2f}")
    report = report.replace("{{TTEST_STATISTIC}}", f"{t_stat:.4f}")
    report = report.replace("{{TTEST_PVALUE}}", f"{t_p:.6f}")
    report = report.replace("{{TTEST_SIGNIFICANT}}", t_sig)
    report = report.replace("{{TTEST_CONCLUSION}}", t_conclusion)
    report = report.replace("{{SC001_STATUS}}", sc001_status)
    report = report.replace("{{SC001_EVIDENCE}}", sc001_evidence)
    report = report.replace("{{SC002_STATUS}}", sc002_status)
    report = report.replace("{{SC002_EVIDENCE}}", sc002_evidence)
    report = report.replace("{{SC003_STATUS}}", sc003_status)
    report = report.replace("{{SC003_EVIDENCE}}", sc003_evidence)
    report = report.replace("{{SC004_STATUS}}", sc004_status)
    report = report.replace("{{SC004_EVIDENCE}}", sc004_evidence)
    report = report.replace("{{SAMPLE_SIZE}}", str(sample_size))
    report = report.replace("{{POWER_ANALYSIS_RESULT}}", f"Achieved power: {power_result:.4f}")
    report = report.replace("{{SAMPLE_SIZE_WARNING}}", power_limitation)
    report = report.replace("{{HOMOGENEITY_STATUS}}", homogeneity_status)
    report = report.replace("{{HOMOGENEITY_OBSERVATION}}", homogeneity_obs)
    report = report.replace("{{ENTROPY_EDGE_CASES_COUNT}}", str(entropy_count))
    report = report.replace("{{DIVERGENCE_PERCENTAGE}}", f"{divergence_pct:.2f}")
    report = report.replace("{{PRUNING_COUNT}}", str(pruning_count))
    report = report.replace("{{FINAL_CONCLUSION_TEXT}}", " ".join(final_conclusion))
    report = report.replace("{{RECOMMENDATION_1}}", recommendations[0])
    report = report.replace("{{RECOMMENDATION_2}}", recommendations[1])

    return report

def save_report(report_content: str, output_path: str) -> bool:
    """Save the generated report to a file."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report_content)
        logger.info(f"Report saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        return False

def main():
    """Main entry point for the statistical report generation."""
    # Define paths
    template_path = "data/processed/statistical_analysis_report_template.md"
    agg_stats_path = "data/processed/agg_stats.json"
    success_criteria_path = "data/processed/success_criteria_report.json"
    token_verification_path = "data/processed/token_reduction_verification.json"
    output_path = "data/processed/statistical_analysis_report.md"

    # Check if template exists
    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        sys.exit(1)

    # Load aggregated statistics
    agg_stats = load_statistical_results(agg_stats_path)
    if not agg_stats:
        logger.error(f"Failed to load aggregated statistics from {agg_stats_path}")
        sys.exit(1)

    # Load success criteria
    success_criteria = load_json_file(success_criteria_path)
    if not success_criteria:
        logger.error(f"Failed to load success criteria from {success_criteria_path}")
        sys.exit(1)

    # Load token reduction verification (optional)
    token_verification = load_token_reduction_verification(token_verification_path)

    # Generate report
    report_content = generate_final_report(
        template_path,
        agg_stats,
        success_criteria,
        token_verification
    )

    # Save report
    if save_report(report_content, output_path):
        logger.info("Statistical analysis report generated successfully.")
        sys.exit(0)
    else:
        logger.error("Failed to generate statistical analysis report.")
        sys.exit(1)

if __name__ == "__main__":
    main()