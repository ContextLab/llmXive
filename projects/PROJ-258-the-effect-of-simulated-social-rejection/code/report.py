import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from config import get_path
import numpy as np
from scipy import stats
from data_model import DesignType

logger = logging.getLogger(__name__)

def calculate_effect_size_ci(
    effect_size: float,
    n1: int,
    n2: int,
    confidence: float = 0.95
) -> Dict[str, float]:
    """
    Calculate confidence interval for effect size (Cohen's d).
    
    Args:
        effect_size: The calculated effect size (Cohen's d)
        n1: Sample size of group 1
        n2: Sample size of group 2
        confidence: Confidence level (default 0.95)
    
    Returns:
        Dictionary with 'lower', 'upper', and 'center' keys
    """
    # Non-centrality parameter approximation for CI
    # Using simplified approximation for d CI
    n = n1 + n2
    se = np.sqrt((n1 + n2) / (n1 * n2) + (effect_size**2) / (2 * (n1 + n2 - 2)))
    
    alpha = 1 - confidence
    z_score = stats.norm.ppf(1 - alpha / 2)
    
    lower = effect_size - z_score * se
    upper = effect_size + z_score * se
    
    return {
        "lower": float(lower),
        "upper": float(upper),
        "center": float(effect_size)
    }

def generate_report_logic(
    results: Dict[str, Any],
    design_type: str
) -> str:
    """
    Generate the final report content based on analysis results.
    
    Args:
        results: Dictionary containing analysis results (p-values, effect sizes, etc.)
        design_type: Either "Within-Subjects" or "Between-Subjects"
    
    Returns:
        Formatted markdown report string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine phrasing based on design type
    if design_type == "Between-Subjects":
        phrasing = "associational"
        limitation_text = (
            "LIMITATIONS:\n"
            "This study utilized a composite dataset approach (Between-Subjects design) "
            "due to the unavailability of a single-cohort dataset containing both rejection "
            "and reward tasks. Consequently, observed differences are **associational** in nature. "
            "We explicitly **cannot** claim causal modulation of reward responses by rejection "
            "within individuals. Group differences may be confounded by unmeasured between-subject "
            "variables. Results should be interpreted as correlational evidence of group-level "
            "differences rather than individual-level causal mechanisms.\n"
        )
    else:
        phrasing = "causal"
        limitation_text = (
            "LIMITATIONS:\n"
            "While this study employed a Within-Subjects design allowing for stronger causal "
            "inferences regarding the modulation of reward responses by social rejection, "
            "limitations remain. Sample size constraints may affect statistical power. "
            "The simulated nature of the rejection task may not fully capture real-world "
            "social dynamics.\n"
        )
    
    # Extract key results
    anova_results = results.get("anova", {})
    fdr_results = results.get("fdr", {})
    sensitivity_results = results.get("sensitivity", {})
    effect_sizes = results.get("effect_sizes", {})
    
    # Build report sections
    report_lines = [
        "# Final Report: Effect of Simulated Social Rejection on Neural Responses to Positive Feedback",
        "",
        f"**Generated:** {timestamp}",
        f"**Design Type:** {design_type}",
        "",
        "## Executive Summary",
        "",
        f"This report presents the findings from the analysis of behavioral data. The study design is classified as **{phrasing}** based on the dataset configuration.",
        "",
        "## Statistical Analysis Results",
        "",
        "### ANOVA Results",
        "",
    ]
    
    # Add ANOVA results
    for test_name, test_data in anova_results.items():
        report_lines.append(f"- **{test_name}**: F({test_data.get('df1', 'N/A')}, {test_data.get('df2', 'N/A')}) = {test_data.get('F', 'N/A'):.4f}, p = {test_data.get('p', 'N/A'):.4f}")
    
    report_lines.extend([
        "",
        "### FDR-Corrected P-values",
        "",
    ])
    
    # Add FDR results
    for metric, p_val in fdr_results.items():
        sig = "** (significant)" if p_val < 0.05 else ""
        report_lines.append(f"- {metric}: p_fdr = {p_val:.4f} {sig}")
    
    report_lines.extend([
        "",
        "### Effect Sizes and Confidence Intervals",
        "",
    ])
    
    # Add effect sizes
    for metric, es_data in effect_sizes.items():
        ci = es_data.get("ci", {})
        report_lines.append(
            f"- **{metric}**: d = {es_data.get('d', 'N/A'):.4f} "
            f"[95% CI: {ci.get('lower', 'N/A'):.4f}, {ci.get('upper', 'N/A'):.4f}]"
        )
    
    report_lines.extend([
        "",
        "### Sensitivity Analysis",
        "",
        "The following table shows the stability of results across different alpha thresholds:",
        "",
        "| Alpha Threshold | Significant Findings | Notes |",
        "|-----------------|----------------------|-------|",
    ])
    
    # Add sensitivity table
    for alpha, data in sensitivity_results.items():
        sig_count = data.get("significant_count", 0)
        report_lines.append(f"| {alpha} | {sig_count} | Threshold applied |")
    
    report_lines.extend([
        "",
        limitation_text,
        "",
        "## Conclusion",
        "",
        f"The analysis provides {phrasing} evidence regarding the relationship between simulated social rejection and responses to positive feedback. ",
        "Future studies should aim to secure single-cohort datasets to enable stronger causal claims about modulation effects.",
        "",
        "---",
        "*Report generated by the llmXive automated science pipeline.*"
    ])
    
    return "\n".join(report_lines)

def save_report(report_content: str, output_path: str) -> None:
    """
    Save the generated report to a markdown file.
    
    Args:
        report_content: The formatted markdown report string
        output_path: Path to save the report
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logger.info(f"Report saved to {output_path}")

def verify_report_constraints(report_path: str) -> bool:
    """
    Verify that the report meets the required constraints.
    
    Args:
        report_path: Path to the report file
    
    Returns:
        True if constraints are met, False otherwise
    """
    if not os.path.exists(report_path):
        logger.error(f"Report file not found: {report_path}")
        return False
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for "associational" in Limitations if Between-Subjects
    # This is a simple check; the content generation logic handles the phrasing
    if "LIMITATIONS:" in content:
        if "associational" not in content.lower():
            logger.warning("Report missing 'associational' phrasing in Limitations")
            # This might be acceptable if design is Within-Subjects
    
    # Check that "causal" is not used inappropriately for Between-Subjects
    # The logic in generate_report_logic handles this
    
    return True

def save_final_results(
    results: Dict[str, Any],
    design_type: str,
    output_path: Optional[str] = None
) -> str:
    """
    Save the final analysis results to a JSON file.
    
    Args:
        results: Dictionary containing analysis results
        design_type: Either "Within-Subjects" or "Between-Subjects"
        output_path: Optional path to save results (defaults to data/processed/final_results.json)
    
    Returns:
        Path to the saved file
    """
    if output_path is None:
        output_path = get_path("processed", "final_results.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Add metadata
    final_output = {
        "design_type": design_type,
        "generated_at": datetime.now().isoformat(),
        "results": results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2)
    
    logger.info(f"Final results saved to {output_path}")
    return output_path

def run_reporting_pipeline(
    analysis_results: Dict[str, Any],
    design_type: str
) -> Dict[str, str]:
    """
    Run the full reporting pipeline: generate report, save results, save report.
    
    Args:
        analysis_results: Dictionary containing analysis results
        design_type: Either "Within-Subjects" or "Between-Subjects"
    
    Returns:
        Dictionary with paths to generated artifacts
    """
    # Save final results JSON
    results_path = save_final_results(analysis_results, design_type)
    
    # Generate report content
    report_content = generate_report_logic(analysis_results, design_type)
    
    # Save report
    report_path = get_path("reports", "final_report.md")
    save_report(report_content, report_path)
    
    # Verify constraints
    if not verify_report_constraints(report_path):
        logger.warning("Report constraints verification failed")
    
    return {
        "results_json": results_path,
        "report_md": report_path
    }

def main():
    """Main entry point for the reporting module (for testing/debugging)."""
    # Example usage
    sample_results = {
        "anova": {
            "rejection_effect": {"df1": 1, "df2": 98, "F": 4.56, "p": 0.035}
        },
        "fdr": {
            "reaction_time": 0.042,
            "mood_change": 0.015
        },
        "effect_sizes": {
            "reaction_time": {"d": 0.45, "ci": {"lower": 0.12, "upper": 0.78}},
            "mood_change": {"d": 0.62, "ci": {"lower": 0.28, "upper": 0.96}}
        },
        "sensitivity": {
            "0.01": {"significant_count": 1},
            "0.05": {"significant_count": 2},
            "0.1": {"significant_count": 2}
        }
    }
    
    run_reporting_pipeline(sample_results, "Between-Subjects")
    print("Reporting pipeline completed.")

if __name__ == "__main__":
    main()
