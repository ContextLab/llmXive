"""
Report Generator for LLM Robustness Study.

Aggregates pass@1 degradation, statistical significance (McNemar),
mixed-effects variance, and sensitivity metrics into a final research report.
"""
import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from project modules
from config import ensure_directories, get_config_dict
from utils.logging import get_inference_logger

logger = get_inference_logger("report_generator")

# Output paths
REPORT_PATH = Path("docs/research_report.md")
PASS_AT_1_FILE = Path("data/processed/pass_at_1_results.json")
MCNEMAR_FILE = Path("data/processed/mcnemar_results.json")
MIXED_EFFECTS_FILE = Path("data/processed/mixed_effects_results.json")
SENSITIVITY_FILE = Path("data/processed/sensitivity_report.csv")
ERROR_CLASSIFICATION_FILE = Path("data/processed/error_classification_report.json")

def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, otherwise return None."""
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    logger.warning(f"File not found: {path}")
    return None

def load_csv_file(path: Path) -> List[Dict[str, Any]]:
    """Load a CSV file as a list of dictionaries."""
    if path.exists():
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    logger.warning(f"File not found: {path}")
    return []

def calculate_pass_1_degradation(pass_at_1_data: Optional[Dict[str, Any]]) -> str:
    """Calculate and format pass@1 degradation metrics."""
    if not pass_at_1_data:
        return "Pass@1 data not available. Cannot calculate degradation."

    lines = []
    lines.append("### Pass@1 Degradation Analysis")
    lines.append("")
    
    original_rate = pass_at_1_data.get("original_pass_rate", 0.0)
    perturbed_rate = pass_at_1_data.get("perturbed_pass_rate", 0.0)
    
    lines.append(f"- **Original Pass@1**: {original_rate:.2%}")
    lines.append(f"- **Perturbed Pass@1**: {perturbed_rate:.2%}")
    
    if original_rate > 0:
        degradation = (original_rate - perturbed_rate) / original_rate * 100
        lines.append(f"- **Relative Degradation**: {degradation:.2f}%")
    
    lines.append("")
    
    # Per-perturbation type breakdown
    if "by_type" in pass_at_1_data:
        lines.append("**Breakdown by Perturbation Type:**")
        lines.append("")
        for ptype, stats in pass_at_1_data["by_type"].items():
            orig = stats.get("original_rate", 0.0)
            pert = stats.get("perturbed_rate", 0.0)
            lines.append(f"- **{ptype.capitalize()}**: Original={orig:.2%}, Perturbed={pert:.2%}")
        lines.append("")
    
    return "\n".join(lines)

def summarize_mcnemar_results(mcnemar_data: Optional[Dict[str, Any]]) -> str:
    """Summarize McNemar's test results with Bonferroni correction."""
    if not mcnemar_data:
        return "McNemar's test results not available."

    lines = []
    lines.append("### McNemar's Test with Bonferroni Correction")
    lines.append("")
    
    lines.append(f"**Overall Significance (Bonferroni-corrected alpha):** {mcnemar_data.get('bonferroni_alpha', 'N/A')}")
    lines.append("")
    
    if "by_type" in mcnemar_data:
        lines.append("**Results by Perturbation Type:**")
        lines.append("")
        lines.append("| Perturbation Type | McNemar p-value | Significant (α=0.05) | Significant (Corrected) |")
        lines.append("|-------------------|-----------------|----------------------|-------------------------|")
        
        for ptype, stats in mcnemar_data["by_type"].items():
            p_val = stats.get("p_value", "N/A")
            sig_basic = stats.get("significant", False)
            sig_corrected = stats.get("significant_corrected", False)
            lines.append(f"| {ptype.capitalize()} | {p_val} | {'Yes' if sig_basic else 'No'} | {'Yes' if sig_corrected else 'No'} |")
        lines.append("")
    
    return "\n".join(lines)

def summarize_mixed_effects(mixed_effects_data: Optional[Dict[str, Any]]) -> str:
    """Summarize mixed-effects logistic regression results."""
    if not mixed_effects_data:
        return "Mixed-effects model results not available."

    lines = []
    lines.append("### Mixed-Effects Logistic Regression")
    lines.append("")
    
    lines.append("**Model Specification:**")
    lines.append("- Random effect: 'task'")
    lines.append("- Fixed effects: perturbation_type, original_success")
    lines.append("")
    
    variance_component = mixed_effects_data.get("variance_component", 0.0)
    lines.append(f"**Variance Component for 'task'**: {variance_component:.4f}")
    
    if variance_component > 0:
        lines.append("- *Interpretation*: There is significant task-to-task variability in robustness.")
    else:
        lines.append("- *Interpretation*: Task-to-task variability is negligible.")
    lines.append("")
    
    if "fixed_effects" in mixed_effects_data:
        lines.append("**Fixed Effects Coefficients:**")
        lines.append("")
        for effect, coef in mixed_effects_data["fixed_effects"].items():
            lines.append(f"- {effect}: {coef:.4f}")
        lines.append("")
    
    return "\n".join(lines)

def summarize_sensitivity_analysis(sensitivity_data: List[Dict[str, Any]]) -> str:
    """Summarize sensitivity analysis across semantic thresholds."""
    if not sensitivity_data:
        return "Sensitivity analysis results not available."

    lines = []
    lines.append("### Sensitivity Analysis: Semantic Threshold Impact")
    lines.append("")
    lines.append("The following table shows how pass@1 rates and degradation change across different semantic similarity thresholds:")
    lines.append("")
    lines.append("| Threshold | Pass@1 | Delta from Baseline (0.95) |")
    lines.append("|-----------|--------|----------------------------|")
    
    baseline_rate = None
    for row in sensitivity_data:
        threshold = row.get("threshold", "N/A")
        pass_rate = row.get("pass_rate", "N/A")
        delta = row.get("delta_from_baseline", "N/A")
        
        if threshold == "0.95":
            baseline_rate = pass_rate
        
        lines.append(f"| {threshold} | {pass_rate} | {delta} |")
    lines.append("")
    
    lines.append("**Key Findings:**")
    lines.append(f"- The baseline threshold (0.95) yields a pass@1 of {baseline_rate}.")
    lines.append("- Lower thresholds (0.85, 0.90) include more perturbed samples, potentially affecting robustness estimates.")
    lines.append("- Higher thresholds (0.99) are more restrictive, reducing sample size but increasing confidence in semantic preservation.")
    lines.append("")
    
    return "\n".join(lines)

def summarize_error_classification(error_data: Optional[Dict[str, Any]]) -> str:
    """Summarize error classification results."""
    if not error_data:
        return "Error classification results not available."

    lines = []
    lines.append("### Error Classification Analysis")
    lines.append("")
    
    total_errors = error_data.get("total_failures", 0)
    lines.append(f"**Total Failures Analyzed**: {total_errors}")
    lines.append("")
    
    if "by_type" in error_data:
        lines.append("**Failure Distribution by Perturbation Type:**")
        lines.append("")
        for ptype, count in error_data["by_type"].items():
            lines.append(f"- {ptype.capitalize()}: {count} failures")
        lines.append("")
    
    if "by_category" in error_data:
        lines.append("**Failure Distribution by Error Category:**")
        lines.append("")
        for category, count in error_data["by_category"].items():
            percentage = (count / total_errors * 100) if total_errors > 0 else 0
            lines.append(f"- {category.capitalize()}: {count} ({percentage:.1f}%)")
        lines.append("")
    
    return "\n".join(lines)

def generate_report() -> None:
    """Generate the final research report."""
    logger.info("Starting report generation...")
    
    # Ensure docs directory exists
    ensure_directories()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Load all data sources
    pass_at_1_data = load_json_file(PASS_AT_1_FILE)
    mcnemar_data = load_json_file(MCNEMAR_FILE)
    mixed_effects_data = load_json_file(MIXED_EFFECTS_FILE)
    sensitivity_data = load_csv_file(SENSITIVITY_FILE)
    error_data = load_json_file(ERROR_CLASSIFICATION_FILE)
    
    # Build report sections
    report_sections = []
    
    # Title and Metadata
    report_sections.append("# Evaluating the Robustness of LLM-Generated Code to Input Perturbations")
    report_sections.append("")
    report_sections.append("**Research Report**")
    report_sections.append("")
    report_sections.append(f"*Generated: {__import__('datetime').datetime.now().isoformat()}*")
    report_sections.append("")
    report_sections.append("---")
    report_sections.append("")
    
    # Executive Summary
    report_sections.append("## Executive Summary")
    report_sections.append("")
    report_sections.append("This study evaluates how semantic-preserving perturbations to input prompts affect the functional correctness of code generated by large language models.")
    report_sections.append("We measure robustness through pass@1 rates, statistical significance of performance degradation, and task-level variability.")
    report_sections.append("")
    
    # Pass@1 Analysis
    report_sections.append(calculate_pass_1_degradation(pass_at_1_data))
    
    # Statistical Significance
    report_sections.append(summarize_mcnemar_results(mcnemar_data))
    
    # Mixed-Effects Analysis
    report_sections.append(summarize_mixed_effects(mixed_effects_data))
    
    # Sensitivity Analysis
    report_sections.append(summarize_sensitivity_analysis(sensitivity_data))
    
    # Error Classification
    report_sections.append(summarize_error_classification(error_data))
    
    # Conclusion
    report_sections.append("## Conclusion")
    report_sections.append("")
    report_sections.append("The analysis reveals the extent to which LLM-generated code is robust to semantic-preserving input perturbations.")
    report_sections.append("Key metrics include the magnitude of pass@1 degradation, statistical significance of differences (McNemar's test with Bonferroni correction),")
    report_sections.append("and the variance component attributed to task-level differences in the mixed-effects model.")
    report_sections.append("")
    report_sections.append("Future work should explore additional perturbation types, larger model scales, and the impact of different semantic similarity thresholds.")
    report_sections.append("")
    
    # Write report to file
    full_report = "\n".join(report_sections)
    with open(REPORT_PATH, 'w') as f:
        f.write(full_report)
    
    logger.info(f"Report successfully generated at {REPORT_PATH}")

def main():
    """Entry point for the report generator."""
    generate_report()

if __name__ == "__main__":
    main()
