import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import get_output_dir, get_data_dir

logger = logging.getLogger(__name__)

def generate_markdown_report(
    results: Dict[str, Any],
    descriptive_stats: Optional[Dict[str, Any]] = None,
    exclusion_breakdown: Optional[Dict[str, int]] = None,
) -> str:
    """
    Generate the content of the final markdown report.
    """
    lines = []
    
    # Header
    lines.append("# Automated Test Case Generation: Statistical Analysis Report")
    lines.append("")

    # Warnings / Limitations
    warnings = results.get("warnings", [])
    if warnings:
        lines.append("## Study Limitations")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    # Methodological Constraints & Exclusion Rate
    if exclusion_breakdown:
        lines.append("## Methodological Constraints")
        lines.append(f"**Exclusion Rate**: {results.get('exclusion_rate', 'N/A')}")
        lines.append("Samples were excluded based on the 'Strict Pairing' criteria (missing manual baseline).")
        lines.append("")
        if exclusion_breakdown.get("reasons"):
            lines.append("**Breakdown of Exclusion Reasons:**")
            for reason, count in exclusion_breakdown["reasons"].items():
                lines.append(f"- {reason}: {count}")
            lines.append("")

    # Statistical Results
    lines.append("## Statistical Analysis Results")
    lines.append(f"**Test Used**: {results.get('test_type', 'N/A')}")
    lines.append(f"**P-value**: {results.get('p_value', 'N/A')}")
    lines.append(f"**Effect Size**: {results.get('effect_size', 'N/A')} ({results.get('effect_size_type', 'N/A')})")
    lines.append(f"**95% Confidence Interval**: [{results.get('ci_lower', 'N/A')}, {results.get('ci_upper', 'N/A')}]")
    lines.append(f"**Mean Ratio**: {results.get('mean_ratio', 'N/A')}")
    lines.append("")

    # Confidence Interval Interpretation (T078)
    lines.append("### Confidence Interval Interpretation")
    ci_lower = results.get("ci_lower")
    ci_upper = results.get("ci_upper")
    mean_ratio = results.get("mean_ratio")
    
    if ci_lower is not None and ci_upper is not None:
        includes_null = ci_lower <= 1.0 <= ci_upper
        lines.append(f"The 95% confidence interval for the mean ratio (Generated/Manual) is [{ci_lower:.4f}, {ci_upper:.4f}].")
        lines.append("")
        if includes_null:
            lines.append("**Interpretation**: The interval **includes the 'no difference' point (1.0)**. This implies that we cannot reject the null hypothesis at the 5% significance level. There is insufficient statistical evidence to claim a difference in coverage between the LLM-generated tests and the manual baseline tests.")
        else:
            if mean_ratio is not None and mean_ratio > 1.0:
                lines.append("**Interpretation**: The interval **does not include the 'no difference' point (1.0)** and lies entirely above it. This implies that the LLM-generated tests achieved statistically significantly *higher* coverage than the manual baseline.")
            elif mean_ratio is not None:
                lines.append("**Interpretation**: The interval **does not include the 'no difference' point (1.0)** and lies entirely below it. This implies that the LLM-generated tests achieved statistically significantly *lower* coverage than the manual baseline.")
            else:
                lines.append("**Interpretation**: The interval **does not include the 'no difference' point (1.0)**. This implies a statistically significant difference exists, though the direction depends on the mean ratio.")
        lines.append("")
    else:
        lines.append("Confidence interval data is not available.")
        lines.append("")

    # Power Analysis
    if results.get("achieved_power") is not None:
        lines.append("## Power Analysis")
        lines.append(f"**Achieved Power**: {results['achieved_power']:.4f}")
        if results.get("power_sensitivity_plot"):
            lines.append(f"Refer to `data/{results['power_sensitivity_plot']}` for the sensitivity analysis plot.")
        lines.append("")

    # Descriptive Statistics
    if descriptive_stats:
        lines.append("## Descriptive Statistics")
        lines.append(f"**Generation Success Rate**: {descriptive_stats.get('generation_success_rate', 'N/A')}")
        lines.append(f"**Exclusion Rate (Descriptive)**: {descriptive_stats.get('exclusion_rate', 'N/A')}")
        lines.append("")

    # Assertion Density
    if results.get("assertion_density_stats"):
        lines.append("## Assertion Density Analysis")
        stats = results["assertion_density_stats"]
        lines.append(f"**Mean**: {stats.get('mean', 'N/A')}")
        lines.append(f"**Median**: {stats.get('median', 'N/A')}")
        lines.append("")

    # Conclusion
    lines.append("## Conclusion")
    conclusion = results.get("conclusion", "No conclusion drawn.")
    lines.append(conclusion)
    lines.append("")

    return "\n".join(lines)

def generate_final_report(
    results: Dict[str, Any],
    descriptive_stats: Optional[Dict[str, Any]] = None,
    exclusion_breakdown: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Generates the final report files: data/final_report.md and data/analysis_results.json.
    Enhances the report with Confidence Interval Interpretation (T078).
    """
    output_dir = get_output_dir()
    data_dir = get_data_dir()
    
    # Ensure directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    # Generate Markdown content
    md_content = generate_markdown_report(results, descriptive_stats, exclusion_breakdown)

    # Write Markdown
    report_path = Path(data_dir) / "final_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    logger.info(f"Final report written to {report_path}")

    # Write JSON results
    json_path = Path(data_dir) / "analysis_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis results written to {json_path}")