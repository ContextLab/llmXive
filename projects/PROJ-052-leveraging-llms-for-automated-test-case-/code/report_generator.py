import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import get_output_dir, get_data_dir

logger = logging.getLogger(__name__)

def generate_markdown_report(analysis_results: Dict[str, Any]) -> str:
    """
    Generates the Markdown content for the final report based on analysis results.
    
    Args:
        analysis_results: Dictionary containing statistical metrics, power analysis, 
                          exclusion rates, and confidence intervals.
    
    Returns:
        A formatted Markdown string representing the final report.
    """
    lines = []
    
    # Header
    lines.append("# Automated Test Case Generation: Statistical Analysis Report\n")
    
    # Warnings (Sample Size & Power)
    if "warnings" in analysis_results:
        lines.append("## Methodological Limitations\n")
        for warning in analysis_results["warnings"]:
            lines.append(f"- {warning}")
        lines.append("\n")
    
    # Exclusion Rate
    if "exclusion_rate" in analysis_results:
        lines.append("## Methodological Constraints\n")
        lines.append(f"**Exclusion Rate**: {analysis_results['exclusion_rate']:.2%}\n")
        lines.append("Samples were excluded based on the 'Strict Pairing' criterion: only bugs with a verified manual baseline test on the buggy version were included in the statistical comparison. High exclusion rates indicate a significant portion of the dataset could not be paired for direct comparison.\n")
        if "exclusion_breakdown" in analysis_results:
            lines.append("**Exclusion Breakdown**:\n")
            for reason, count in analysis_results["exclusion_breakdown"].items():
                lines.append(f"- {reason}: {count}")
            lines.append("\n")
    
    # Descriptive Statistics
    if "descriptive_statistics" in analysis_results:
        lines.append("## Descriptive Statistics\n")
        desc = analysis_results["descriptive_statistics"]
        lines.append(f"- **Generation Success Rate**: {desc.get('generation_success_rate', 'N/A'):.2%}")
        lines.append(f"- **Exclusion Rate (Descriptive)**: {desc.get('exclusion_rate', 'N/A'):.2%}")
        lines.append("\n")
    
    # Statistical Test Results
    lines.append("## Statistical Analysis Results\n")
    if "statistical_test" in analysis_results:
        stats_res = analysis_results["statistical_test"]
        lines.append(f"- **Test Type**: {stats_res.get('test_type', 'N/A')}")
        lines.append(f"- **P-value**: {stats_res.get('p_value', 'N/A'):.4f}")
        lines.append(f"- **Effect Size**: {stats_res.get('effect_size', 'N/A'):.4f} ({stats_res.get('effect_size_type', 'N/A')})")
        lines.append(f"- **Mean Difference**: {stats_res.get('mean_difference', 'N/A'):.4f}")
        lines.append(f"- **Conclusion**: {stats_res.get('conclusion', 'N/A')}\n")
    else:
        lines.append("- *Statistical tests were skipped due to insufficient paired samples.*\n")
        lines.append("\n")
    
    # Confidence Interval Interpretation (T078)
    lines.append("## Confidence Interval Interpretation\n")
    if "confidence_intervals" in analysis_results:
        ci = analysis_results["confidence_intervals"]
        ci_lower = ci.get("lower_bound")
        ci_upper = ci.get("upper_bound")
        includes_null = ci.get("includes_null_hypothesis")
        null_value = ci.get("null_value", 1.0)
        
        lines.append(f"- **95% Confidence Interval**: [{ci_lower:.4f}, {ci_upper:.4f}]")
        lines.append(f"- **Null Hypothesis Point**: {null_value} (No Difference)")
        lines.append(f"- **Includes Null Point**: {'Yes' if includes_null else 'No'}\n")
        
        # Interpretation Logic
        lines.append("**Interpretation**:\n")
        if includes_null:
            if ci_lower <= null_value <= ci_upper:
                lines.append(f"The 95% confidence interval includes the null hypothesis point ({null_value}). ")
                lines.append("This implies that, at the 5% significance level, we cannot reject the null hypothesis. ")
                lines.append("There is insufficient evidence to conclude a statistically significant difference between the LLM-generated tests and the manual baseline tests regarding coverage on changed lines. ")
                lines.append("The observed difference could be due to random chance.\n")
            else:
                # Edge case where logic might say includes but math is weird, fallback
                lines.append("The confidence interval interpretation suggests the null hypothesis cannot be definitively rejected based on the provided bounds.\n")
        else:
            lines.append(f"The 95% confidence interval does **not** include the null hypothesis point ({null_value}). ")
            lines.append("This implies that the observed difference is statistically significant at the 5% level. ")
            if ci_upper < null_value:
                lines.append(f"Since the entire interval is below {null_value}, the LLM-generated tests performed significantly **worse** than the manual baseline.\n")
            elif ci_lower > null_value:
                lines.append(f"Since the entire interval is above {null_value}, the LLM-generated tests performed significantly **better** than the manual baseline.\n")
            else:
                lines.append("The direction of the effect is consistent with the observed mean difference.\n")
    else:
        lines.append("- *Confidence intervals could not be calculated due to insufficient data.*\n")
        lines.append("\n")
    
    # Power Analysis
    if "achieved_power" in analysis_results:
        lines.append("## Power Analysis\n")
        lines.append(f"- **Achieved Power**: {analysis_results['achieved_power']:.4f}")
        if analysis_results.get("power_interpretation"):
            lines.append(f"- **Interpretation**: {analysis_results['power_interpretation']}\n")
        lines.append("\n")
    
    # Assertion Density
    if "assertion_density" in analysis_results:
        lines.append("## Assertion Density Analysis\n")
        ad = analysis_results["assertion_density"]
        lines.append(f"- **Mean Assertion Density**: {ad.get('mean', 'N/A'):.4f}")
        lines.append(f"- **Median Assertion Density**: {ad.get('median', 'N/A'):.4f}\n")
        lines.append("\n")
    
    # Resource Usage
    if "resource_usage" in analysis_results:
        lines.append("## Resource Usage\n")
        res = analysis_results["resource_usage"]
        lines.append(f"- **Peak RAM**: {res.get('peak_ram_gb', 'N/A')} GB")
        lines.append(f"- **CPU Time**: {res.get('cpu_time_sec', 'N/A')} seconds\n")
        lines.append("\n")
    
    # Plot Reference (T076)
    if "power_sensitivity_plot_path" in analysis_results:
        lines.append("## Power Sensitivity Analysis\n")
        lines.append(f"See the sensitivity analysis plot: `{analysis_results['power_sensitivity_plot_path']}`\n")
        lines.append("\n")
    
    return "\n".join(lines)

def generate_final_report() -> None:
    """
    Reads analysis results from data/analysis_results.json, enriches it with 
    confidence interval interpretation logic if missing, and writes the 
    final report to data/final_report.md.
    
    This function implements T078 by explicitly interpreting the 95% CI 
    regarding the null hypothesis point.
    """
    output_dir = get_output_dir()
    data_dir = get_data_dir()
    
    results_path = Path(data_dir) / "analysis_results.json"
    report_path = Path(output_dir) / "final_report.md"
    
    if not results_path.exists():
        logger.error(f"Analysis results file not found: {results_path}")
        return
    
    with open(results_path, 'r') as f:
        analysis_results = json.load(f)
    
    # Ensure Confidence Intervals structure exists if statistical test was run
    if "statistical_test" in analysis_results and "confidence_intervals" not in analysis_results:
        # Fallback logic if T037a didn't run or failed to write, though T037a is marked done.
        # We assume T037a populated it, but we ensure the interpretation key is present.
        logger.warning("Confidence intervals missing in results, skipping interpretation generation.")
    elif "confidence_intervals" in analysis_results:
        # T078 Logic: Ensure 'includes_null_hypothesis' is explicitly calculated and stored
        ci = analysis_results["confidence_intervals"]
        lower = ci.get("lower_bound")
        upper = ci.get("upper_bound")
        null_val = ci.get("null_value", 1.0)
        
        if lower is not None and upper is not None:
            includes_null = lower <= null_val <= upper
            ci["includes_null_hypothesis"] = includes_null
            logger.info(f"T078: CI includes null ({null_val})? {includes_null}")
    
    # Generate Markdown
    markdown_content = generate_markdown_report(analysis_results)
    
    # Write Report
    with open(report_path, 'w') as f:
        f.write(markdown_content)
    
    logger.info(f"Final report generated: {report_path}")
    
    # Update the JSON results file to persist the interpretation flags if we calculated them
    # This ensures the JSON artifact is also complete regarding T078 requirements.
    with open(results_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info("Updated analysis_results.json with T078 interpretation flags.")

if __name__ == "__main__":
    generate_final_report()