"""
Guideline Generator for Code Review Impact Analysis.

This module generates review guideline recommendations based on statistical
analysis results. It identifies metrics with significant differences between
human-written and LLM-generated code and produces actionable recommendations.

Criteria for generating guidelines:
- Adjusted p-value < 0.05 (Benjamini-Hochberg corrected)
- |Cliff's delta| >= 0.1 (small or larger effect size)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import from project modules
from statistical_analysis import get_effect_size_magnitude
from logging_config import setup_logger, get_logger
from state_tracker import update_state_with_artifact, load_state_file, save_state_file

# Constants
SIGNIFICANCE_THRESHOLD = 0.05
EFFECT_SIZE_THRESHOLD = 0.1
RESULTS_DIR = Path("results")
GUIDELINES_FILE = RESULTS_DIR / "guidelines.md"
METRICS_DIR = Path("data/metrics")

def setup_guideline_logger():
    """Setup logger for guideline generation."""
    return setup_logger("guideline_generator", level=logging.INFO)

def load_statistical_results(metrics_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load statistical analysis results from the metrics directory.

    Expected files:
    - mann_whitney_u_results.json: Contains raw p-values
    - cliffs_delta_results.json: Contains effect sizes
    - bh_corrected_results.json: Contains adjusted p-values

    Returns:
        Dict mapping metric names to their statistical results.
    """
    results = {}

    # Load Mann-Whitney U results
    mw_file = metrics_dir / "mann_whitney_u_results.json"
    if mw_file.exists():
        with open(mw_file, 'r') as f:
            mw_data = json.load(f)
            for metric, data in mw_data.items():
                results[metric] = {
                    'raw_p_value': data.get('p_value'),
                    'u_statistic': data.get('u_statistic')
                }

    # Load Cliff's delta results
    cd_file = metrics_dir / "cliffs_delta_results.json"
    if cd_file.exists():
        with open(cd_file, 'r') as f:
            cd_data = json.load(f)
            for metric, data in cd_data.items():
                if metric not in results:
                    results[metric] = {}
                results[metric]['cliffs_delta'] = data.get('cliffs_delta')
                results[metric]['magnitude'] = data.get('magnitude')

    # Load Benjamini-Hochberg corrected results
    bh_file = metrics_dir / "bh_corrected_results.json"
    if bh_file.exists():
        with open(bh_file, 'r') as f:
            bh_data = json.load(f)
            for metric, data in bh_data.items():
                if metric not in results:
                    results[metric] = {}
                results[metric]['adjusted_p_value'] = data.get('adjusted_p_value')

    return results

def determine_recommendation(metric_name: str, cliffs_delta: float, magnitude: str) -> str:
    """
    Generate a specific recommendation based on the metric and effect size.

    Args:
        metric_name: Name of the metric being analyzed.
        cliffs_delta: The Cliff's delta effect size value.
        magnitude: The magnitude label (small, medium, large).

    Returns:
        A recommendation string for code review guidelines.
    """
    direction = "higher" if cliffs_delta > 0 else "lower"
    abs_delta = abs(cliffs_delta)

    # Define recommendations based on metric type and direction
    recommendations = {
        'cyclomatic_complexity': {
            'higher': "LLM-generated code shows significantly higher cyclomatic complexity. "
                      "Recommendation: Implement stricter complexity budgets for generated code. "
                      "Require additional refactoring passes or manual review for functions exceeding "
                      "the baseline threshold by more than 20%.",
            'lower': "LLM-generated code shows lower cyclomatic complexity. "
                     "Recommendation: Verify that simplification hasn't removed necessary error handling. "
                     "Review generated code for potential over-simplification of control flow."
        },
        'maintainability_index': {
            'higher': "LLM-generated code shows higher maintainability index. "
                      "Recommendation: Investigate if this is due to consistent formatting or actual "
                      "improved structure. Consider adopting LLM generation patterns for manual code.",
            'lower': "LLM-generated code shows significantly lower maintainability index. "
                     "Recommendation: Prioritize LLM-generated code for refactoring. "
                     "Consider post-generation cleanup passes focusing on readability and structure."
        },
        'potential_bugs': {
            'higher': "LLM-generated code shows significantly higher potential bug indicators. "
                      "Recommendation: Mandatory security and bug review for all generated code. "
                      "Implement automated bug-detection pre-commit hooks for generated snippets.",
            'lower': "LLM-generated code shows lower potential bug indicators. "
                     "Recommendation: Verify detection sensitivity. Consider if the LLM is avoiding "
                     "patterns that trigger warnings without actually being bug-free."
        },
        'style_issues': {
            'higher': "LLM-generated code shows significantly more style issues. "
                      "Recommendation: Enforce automated formatting (Black, isort) as a mandatory "
                      "post-generation step before code review.",
            'lower': "LLM-generated code shows fewer style issues. "
                     "Recommendation: Investigate if the LLM is adhering to style guidelines better "
                     "than manual coding practices. Consider updating team style guides."
        },
        'loc': {
            'higher': "LLM-generated code is significantly longer. "
                      "Recommendation: Implement length constraints in generation prompts. "
                      "Review for unnecessary verbosity or redundant code patterns.",
            'lower': "LLM-generated code is significantly shorter. "
                     "Recommendation: Check for missing edge cases or error handling. "
                     "Ensure brevity hasn't compromised functionality."
        }
    }

    # Default recommendation if metric not in predefined list
    if metric_name not in recommendations:
        return (f"Significant difference detected in {metric_name} ({direction} in LLM code). "
                f"Effect size: {magnitude} (|Cliff's delta| = {abs_delta:.3f}). "
                f"Recommendation: Manual review of this metric category is required. "
                f"Document findings and consider adjusting generation parameters.")

    return recommendations[metric_name].get(direction, recommendations[metric_name]['higher'])

def generate_guidelines_content(results: Dict[str, Dict[str, Any]]) -> str:
    """
    Generate the full markdown content for the guidelines document.

    Args:
        results: Dictionary of statistical results for each metric.

    Returns:
        Markdown string containing the guidelines.
    """
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("# Code Review Guidelines: LLM-Generated vs Human-Written Code")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")

    # Identify significant metrics
    significant_metrics = []
    for metric, data in results.items():
        adj_p = data.get('adjusted_p_value')
        delta = data.get('cliffs_delta')

        if adj_p is None or delta is None:
            continue

        if adj_p < SIGNIFICANCE_THRESHOLD and abs(delta) >= EFFECT_SIZE_THRESHOLD:
            significant_metrics.append((metric, data))

    if not significant_metrics:
        lines.append("No metrics showed statistically significant differences (adjusted p < 0.05) "
                     "with meaningful effect sizes (|Cliff's delta| >= 0.1).")
        lines.append("")
        lines.append("### General Recommendations")
        lines.append("- Continue monitoring code quality metrics for both human and LLM-generated code.")
        lines.append("- Maintain current review processes for all code submissions.")
        lines.append("- Re-evaluate guidelines when more data becomes available.")
        return "\n".join(lines)

    lines.append(f"Found **{len(significant_metrics)}** metric(s) with statistically significant "
                 f"differences requiring review guideline updates:")
    lines.append("")
    for metric, data in significant_metrics:
        magnitude = data.get('magnitude', 'unknown')
        delta = data.get('cliffs_delta', 0)
        lines.append(f"- **{metric}**: {magnitude} effect size (|Cliff's delta| = {abs(delta):.3f}, "
                     f"adjusted p = {data.get('adjusted_p_value', 'N/A'):.4f})")

    lines.append("")
    lines.append("## Detailed Guidelines")
    lines.append("")

    for metric, data in significant_metrics:
        magnitude = data.get('magnitude', 'unknown')
        delta = data.get('cliffs_delta', 0)
        adj_p = data.get('adjusted_p_value', 0)

        lines.append(f"### {metric.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"**Statistical Evidence:**")
        lines.append(f"- Adjusted p-value: {adj_p:.4f}")
        lines.append(f"- Cliff's delta: {delta:.3f} ({magnitude})")
        lines.append("")

        recommendation = determine_recommendation(metric, delta, magnitude)
        lines.append("**Recommendation:**")
        lines.append(f"{recommendation}")
        lines.append("")

    lines.append("## Implementation Checklist")
    lines.append("")
    lines.append("- [ ] Update code review checklist to include metrics with significant differences")
    lines.append("- [ ] Configure automated tools to flag generated code with outlier metrics")
    lines.append("- [ ] Train reviewers on specific characteristics of LLM-generated code")
    lines.append("- [ ] Schedule follow-up analysis after implementing new guidelines")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append(f"- **Significance Threshold:** Adjusted p-value < {SIGNIFICANCE_THRESHOLD}")
    lines.append(f"- **Effect Size Threshold:** |Cliff's delta| >= {EFFECT_SIZE_THRESHOLD}")
    lines.append("- **Correction Method:** Benjamini-Hochberg for multiple comparisons")
    lines.append("- **Data Source:** CodeSearchNet (human) vs CodeParrot/CodeGen (LLM)")
    lines.append("")
    lines.append("---")
    lines.append("*Generated by the llmXive automated science pipeline*")

    return "\n".join(lines)

def write_guidelines_to_file(content: str, output_path: Path) -> None:
    """Write the guidelines content to the output file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def update_state_with_guidelines(output_path: Path, logger: logging.Logger) -> None:
    """Update the project state file with the generated guidelines artifact."""
    try:
        update_state_with_artifact(
            artifact_path=str(output_path),
            artifact_type="guidelines",
            logger=logger
        )
        logger.info(f"Updated state file with guidelines artifact: {output_path}")
    except Exception as e:
        logger.warning(f"Failed to update state file: {e}")

def run_guideline_generation(metrics_dir: Path = METRICS_DIR,
                             output_path: Path = GUIDELINES_FILE,
                             logger: Optional[logging.Logger] = None) -> Tuple[bool, str]:
    """
    Main entry point for generating review guidelines.

    Args:
        metrics_dir: Directory containing statistical analysis results.
        output_path: Path where the guidelines markdown file will be written.
        logger: Optional logger instance.

    Returns:
        Tuple of (success: bool, message: str)
    """
    if logger is None:
        logger = setup_guideline_logger()

    logger.info("Starting guideline generation process...")

    # Load results
    logger.info(f"Loading statistical results from {metrics_dir}")
    try:
        results = load_statistical_results(metrics_dir)
    except Exception as e:
        msg = f"Failed to load statistical results: {e}"
        logger.error(msg)
        return False, msg

    if not results:
        msg = "No statistical results found. Cannot generate guidelines."
        logger.warning(msg)
        # Generate empty guidelines anyway
        content = generate_guidelines_content({})
    else:
        # Generate content
        logger.info(f"Processing {len(results)} metrics")
        content = generate_guidelines_content(results)

    # Write to file
    try:
        write_guidelines_to_file(content, output_path)
        logger.info(f"Guidelines written to {output_path}")
    except Exception as e:
        msg = f"Failed to write guidelines file: {e}"
        logger.error(msg)
        return False, msg

    # Update state
    update_state_with_guidelines(output_path, logger)

    # Count significant metrics
    significant_count = sum(
        1 for m, d in results.items()
        if d.get('adjusted_p_value', 1) < SIGNIFICANCE_THRESHOLD
        and abs(d.get('cliffs_delta', 0)) >= EFFECT_SIZE_THRESHOLD
    )

    msg = f"Successfully generated guidelines. {significant_count} metric(s) require attention."
    logger.info(msg)
    return True, msg

def main():
    """Command-line entry point."""
    logger = setup_guideline_logger()
    logger.info("=== Guideline Generator ===")

    success, message = run_guideline_generation(logger=logger)

    if not success:
        logger.error(f"Guideline generation failed: {message}")
        sys.exit(1)
    else:
        logger.info(f"Guideline generation completed: {message}")
        sys.exit(0)

if __name__ == "__main__":
    main()
