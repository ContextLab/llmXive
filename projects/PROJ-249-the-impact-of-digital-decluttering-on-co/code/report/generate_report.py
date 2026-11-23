"""
Final Report Generator for Digital Decluttering Study.

Generates the comprehensive final report (results/final_report.md) by aggregating:
1. Sensitivity Analysis Report (from T029)
2. Power Simulation Results (from T020)
3. Statistical Summary (from T040)
4. Validation Status (from T043)
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        raise

def load_markdown_file(file_path: Path) -> str:
    """Load a Markdown file and return its contents as a string."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def format_statistical_summary(summary_data: Dict[str, Any]) -> str:
    """Format the statistical summary data into a Markdown section."""
    lines = []
    lines.append("## Statistical Summary")
    lines.append("")
    lines.append("This section presents the primary statistical findings from the study,")
    lines.append("including mean changes, confidence intervals, and corrected p-values.")
    lines.append("")
    
    if 'metrics' in summary_data:
        lines.append("### Key Metrics")
        lines.append("")
        lines.append("| Metric | Mean Change | 95% CI (Lower) | 95% CI (Upper) | Corrected P-value | Effect Size (Cohen's d) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
        
        for metric, stats in summary_data['metrics'].items():
            mean_change = stats.get('mean_change', 'N/A')
            ci_lower = stats.get('ci_lower', 'N/A')
            ci_upper = stats.get('ci_upper', 'N/A')
            p_value = stats.get('holm_bonferroni_p', 'N/A')
            effect_size = stats.get('cohens_d', 'N/A')
            
            # Format numbers for better readability
            if isinstance(mean_change, (int, float)):
                mean_change = f"{mean_change:.3f}"
            if isinstance(ci_lower, (int, float)):
                ci_lower = f"{ci_lower:.3f}"
            if isinstance(ci_upper, (int, float)):
                ci_upper = f"{ci_upper:.3f}"
            if isinstance(p_value, (int, float)):
                p_value = f"{p_value:.4f}"
            if isinstance(effect_size, (int, float)):
                effect_size = f"{effect_size:.3f}"
            
            lines.append(f"| {metric} | {mean_change} | {ci_lower} | {ci_upper} | {p_value} | {effect_size} |")
        
        lines.append("")
    
    if 'methodology' in summary_data:
        lines.append("### Methodology")
        lines.append("")
        lines.append(f"- **Bootstrap Resamples**: {summary_data['methodology'].get('bootstrap_resamples', 'N/A')}")
        lines.append(f"- **Correction Method**: {summary_data['methodology'].get('correction_method', 'N/A')}")
        lines.append(f"- **Fallback Method**: {summary_data['methodology'].get('fallback_method', 'N/A')}")
        lines.append("")
    
    return "\n".join(lines)

def format_power_results(power_data: Dict[str, Any]) -> str:
    """Format the power simulation results into a Markdown section."""
    lines = []
    lines.append("## Power Analysis")
    lines.append("")
    lines.append("This section details the Monte Carlo power simulation results, estimating")
    lines.append("the study's ability to detect an effect size of d=0.5 with Holm-Bonferroni correction.")
    lines.append("")
    
    if 'summary' in power_data:
        summary = power_data['summary']
        lines.append("### Summary")
        lines.append("")
        lines.append(f"- **Simulated Sample Size**: {summary.get('sample_size', 'N/A')}")
        lines.append(f"- **Number of Iterations**: {summary.get('iterations', 'N/A')}")
        lines.append(f"- **Estimated Power**: {summary.get('power', 0):.2%}")
        lines.append(f"- **Target Power**: 80%")
        lines.append(f"- **Effect Size Detected**: {summary.get('effect_size', 'N/A')}")
        lines.append("")
        
        if summary.get('power') >= 0.80:
            lines.append("**Conclusion**: The study design has sufficient power (>80%) to detect the target effect size.")
        else:
            lines.append("**Conclusion**: The study design may be underpowered for the target effect size. Consider increasing sample size.")
        lines.append("")
    
    if 'details' in power_data:
        lines.append("### Detailed Results")
        lines.append("")
        lines.append("The table below shows the proportion of iterations where the null hypothesis was rejected")
        lines.append("after applying Holm-Bonferroni correction.")
        lines.append("")
        
        details = power_data['details']
        lines.append("| Metric | Rejection Rate | Power Estimate |")
        lines.append("| :--- | :---: | :---: |")
        
        for metric, stats in details.items():
            rejection_rate = stats.get('rejection_rate', 0)
            lines.append(f"| {metric} | {rejection_rate:.2%} | {rejection_rate:.2%} |")
        
        lines.append("")
    
    return "\n".join(lines)

def format_validation_status(validation_data: Dict[str, Any]) -> str:
    """Format the validation status into a Markdown section."""
    lines = []
    lines.append("## Validation Status")
    lines.append("")
    lines.append("This section reports the results of the success criteria validation.")
    lines.append("")
    
    if 'overall_status' in validation_data:
        status = validation_data['overall_status']
        status_icon = "✅" if status == "PASS" else "❌"
        lines.append(f"### Overall Status: {status_icon} {status}")
        lines.append("")
    
    if 'criteria_results' in validation_data:
        lines.append("### Individual Criteria")
        lines.append("")
        lines.append("| Criterion | Description | Status | Details |")
        lines.append("| :--- | :--- | :---: | :--- |")
        
        for criterion in validation_data['criteria_results']:
            name = criterion.get('criterion', 'N/A')
            desc = criterion.get('description', 'N/A')
            passed = criterion.get('passed', False)
            details = criterion.get('details', 'N/A')
            
            status_icon = "✅" if passed else "❌"
            lines.append(f"| {name} | {desc} | {status_icon} | {details} |")
        
        lines.append("")
    
    if 'direction_check' in validation_data:
        lines.append("### Direction of Effect Check")
        lines.append("")
        direction_ok = validation_data['direction_check'].get('passed', False)
        direction_icon = "✅" if direction_ok else "❌"
        lines.append(f"Status: {direction_icon} {'All effects are in the expected direction.' if direction_ok else 'Some effects are not in the expected direction.'}")
        lines.append("")
        lines.append(f"Details: {validation_data['direction_check'].get('details', 'N/A')}")
        lines.append("")
    
    return "\n".join(lines)

def generate_report(
    sensitivity_content: str,
    power_data: Dict[str, Any],
    statistical_summary: Dict[str, Any],
    validation_data: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate the final report by combining all input sources.
    
    Args:
        sensitivity_content: Full text of the sensitivity analysis report.
        power_data: Dictionary containing power simulation results.
        statistical_summary: Dictionary containing statistical summary.
        validation_data: Dictionary containing validation status.
        output_path: Path where the final report will be written.
    """
    logger.info(f"Generating final report at {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build report header
    report_lines = []
    report_lines.append("# Final Report: The Impact of Digital Decluttering on Cognitive Performance and Well-being")
    report_lines.append("")
    report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This report presents the comprehensive analysis of the digital decluttering intervention study.")
    report_lines.append("It includes sensitivity analysis, power simulation results, statistical findings, and validation status.")
    report_lines.append("")
    
    # Insert Sensitivity Analysis Report (Full Text)
    report_lines.append("## Sensitivity Analysis")
    report_lines.append("")
    report_lines.append(sensitivity_content)
    report_lines.append("")
    
    # Insert Power Analysis
    report_lines.append(format_power_results(power_data))
    
    # Insert Statistical Summary
    report_lines.append(format_statistical_summary(statistical_summary))
    
    # Insert Validation Status
    report_lines.append(format_validation_status(validation_data))
    
    # Footer
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Appendix")
    report_lines.append("")
    report_lines.append("### Data Sources")
    report_lines.append("- Baseline data: `data/processed/baseline_data.csv`")
    report_lines.append("- Post-intervention data: `data/processed/post_intervention_data.csv`")
    report_lines.append("- Compliance logs: `data/processed/compliance_logs.csv`")
    report_lines.append("")
    report_lines.append("### Generated Artifacts")
    report_lines.append("- Statistical Summary: `results/statistical_summary.json`")
    report_lines.append("- Power Analysis: `results/power_analysis.json`")
    report_lines.append("- Validation Report: `results/validation_report.json`")
    report_lines.append("- Sensitivity Analysis: `results/sensitivity_analysis_report.md`")
    report_lines.append("")
    
    # Write to file
    final_content = "\n".join(report_lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    logger.info(f"Final report successfully generated at {output_path}")

def main():
    """Main entry point for the report generation script."""
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    results_dir = project_root / "results"
    
    # Input files
    sensitivity_report_path = results_dir / "sensitivity_analysis_report.md"
    power_analysis_path = results_dir / "power_analysis.json"
    statistical_summary_path = results_dir / "statistical_summary.json"
    validation_report_path = results_dir / "validation_report.json"
    
    # Output file
    final_report_path = results_dir / "final_report.md"
    
    try:
        # Load all required inputs
        logger.info("Loading sensitivity analysis report...")
        sensitivity_content = load_markdown_file(sensitivity_report_path)
        
        logger.info("Loading power simulation results...")
        power_data = load_json_file(power_analysis_path)
        
        logger.info("Loading statistical summary...")
        statistical_summary = load_json_file(statistical_summary_path)
        
        logger.info("Loading validation status...")
        validation_data = load_json_file(validation_report_path)
        
        # Generate the final report
        generate_report(
            sensitivity_content=sensitivity_content,
            power_data=power_data,
            statistical_summary=statistical_summary,
            validation_data=validation_data,
            output_path=final_report_path
        )
        
        print(f"✅ Final report generated successfully at {final_report_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating final report: {e}")
        raise

if __name__ == "__main__":
    main()
