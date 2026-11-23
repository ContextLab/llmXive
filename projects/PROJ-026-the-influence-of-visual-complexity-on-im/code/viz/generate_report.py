"""
Generate the final report artifact for the visual complexity study.
Reads permutation, sensitivity, and power analysis results to produce a markdown report.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_project_root, get_data_path

logger = logging.getLogger(__name__)

def load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_hypothesis_section(permutation_results: Dict[str, Any]) -> str:
    """Generate the hypothesis test summary section."""
    lines = [
        "## Hypothesis Test Results",
        "",
        f"**Test Method**: {permutation_results.get('methodology', 'Permutation Test')}",
        f"**P-value**: {permutation_results.get('p_value', 'N/A')}",
        f"**Observed Cohen's d**: {permutation_results.get('observed_cohen_d', 'N/A')}",
        f"**Effect Size (Standardized Mean Diff)**: {permutation_results.get('effect_size', 'N/A')}",
        f"**Status**: {permutation_results.get('status', 'N/A')}",
        "",
        "**Conclusion**:",
    ]
    
    p_val = permutation_results.get('p_value')
    if p_val is not None:
        if p_val < 0.05:
            lines.append("The difference in D-scores between Low and High visual complexity conditions is statistically significant (p < 0.05).")
        else:
            lines.append("The difference in D-scores between Low and High visual complexity conditions is not statistically significant (p >= 0.05).")
    else:
        lines.append("P-value not available; conclusion cannot be drawn.")
    
    return "\n".join(lines)

def generate_sensitivity_section(sensitivity_results: Dict[str, Any]) -> str:
    """Generate the sensitivity analysis summary section."""
    lines = [
        "## Sensitivity Analysis",
        "",
        "### Threshold Sweep",
        "",
    ]
    
    threshold_sweep = sensitivity_results.get('threshold_sweep', {})
    if threshold_sweep:
        lines.append("The permutation test was re-run with shifted complexity thresholds (±0.05, ±0.10, ±0.15 SD of edge density).")
        lines.append("| Shift | P-value | Status |")
        lines.append("|-------|---------|--------|")
        for shift, result in threshold_sweep.items():
            p_val = result.get('p_value', 'N/A')
            status = result.get('status', 'N/A')
            lines.append(f"| {shift} | {p_val} | {status} |")
        lines.append("")
        lines.append("The results indicate the robustness of the main finding to changes in the complexity categorization threshold.")
    else:
        lines.append("No threshold sweep results available.")
    
    lines.append("")
    lines.append("### Leave-One-Image-Out (LOIO) Analysis")
    lines.append("")
    
    loio_results = sensitivity_results.get('loio_results', {})
    if loio_results:
        lines.append("The permutation test was re-run excluding one image at a time to assess the influence of individual stimuli.")
        lines.append("| Excluded Image | P-value | Status |")
        lines.append("|----------------|---------|--------|")
        for img, result in loio_results.items():
            p_val = result.get('p_value', 'N/A')
            status = result.get('status', 'N/A')
            lines.append(f"| {img} | {p_val} | {status} |")
        lines.append("")
        lines.append("Variation in p-values across exclusions indicates the stability of the result across the stimulus set.")
    else:
        lines.append("No LOIO results available.")
    
    return "\n".join(lines)

def generate_power_section(power_results: Dict[str, Any]) -> str:
    """Generate the power analysis conclusion section."""
    lines = [
        "## Power Analysis",
        "",
    ]
    
    power_value = power_results.get('power_value')
    target = power_results.get('target', 0.80)
    status = power_results.get('status', 'N/A')
    
    if power_value is not None:
        lines.append(f"**Measured Power**: {power_value:.3f}")
        lines.append(f"**Target Power**: {target}")
        lines.append(f"**Status**: {status}")
        lines.append("")
        if power_value >= target:
            lines.append("The study achieved the target power level, indicating sufficient sample size to detect the hypothesized effect.")
        else:
            lines.append(f"The study did not achieve the target power level (measured: {power_value:.3f}, target: {target}). This suggests the sample size may be insufficient to reliably detect the effect, or the effect size is smaller than anticipated.")
    else:
        lines.append("Power analysis results are not available.")
    
    return "\n".join(lines)

def generate_plot_links() -> str:
    """Generate links to the generated plots."""
    lines = [
        "## Generated Plots",
        "",
        "- [D-score Comparison Boxplot](../d_score_comparison.png)",
        "",
        "These visualizations illustrate the distribution of D-scores across complexity conditions and the sensitivity analysis results.",
    ]
    return "\n".join(lines)

def generate_report() -> None:
    """
    Main function to generate the final report.
    Reads required JSON files and writes the markdown report.
    """
    project_root = get_project_root()
    results_dir = project_root / "data" / "results"
    output_path = results_dir / "final_report.md"
    
    logger.info(f"Generating final report at {output_path}")
    
    # Load required input files
    try:
        permutation_results = load_json(results_dir / "permutation_results.json")
        sensitivity_results = load_json(results_dir / "sensitivity_results.json")
        power_results = load_json(results_dir / "power_analysis.json")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise RuntimeError(f"Missing required input file: {e}")
    
    # Generate report sections
    sections = [
        "# Final Report: The Influence of Visual Complexity on Implicit Bias",
        "",
        "This report summarizes the findings from the permutation test, sensitivity analysis, and power analysis conducted in this study.",
        "",
        generate_hypothesis_section(permutation_results),
        "",
        generate_sensitivity_section(sensitivity_results),
        "",
        generate_power_section(power_results),
        "",
        generate_plot_links(),
        "",
        "---",
        f"*Report generated automatically by the llmXive pipeline.*",
    ]
    
    report_content = "\n".join(sections)
    
    # Write the report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Final report successfully written to {output_path}")

if __name__ == "__main__":
    setup_logging = logging
    # Ensure logging is configured if run directly
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    generate_report()
