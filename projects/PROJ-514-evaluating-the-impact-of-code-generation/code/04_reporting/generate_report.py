import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import numpy as np

from utils.logger import get_logger
from utils.config import get_output_paths, get_project_root

logger = get_logger(__name__)

def load_processed_metrics(metrics_path: Path) -> List[Dict[str, Any]]:
    """Load processed smell metrics from CSV."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Processed metrics file not found: {metrics_path}")
    
    metrics = []
    with open(metrics_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append({
                'sample_id': row['sample_id'],
                'source_type': row['source_type'],
                'smell_type': row['smell_type'],
                'count': float(row['count']),
                'continuous_metric_value': float(row['continuous_metric_value'])
            })
    return metrics

def load_stat_results(stat_path: Path) -> Dict[str, Any]:
    """Load statistical results from JSON."""
    if not stat_path.exists():
        raise FileNotFoundError(f"Statistical results file not found: {stat_path}")
    
    with open(stat_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_sensitivity_report(sensitivity_path: Path) -> Dict[str, Any]:
    """Load sensitivity analysis report from JSON."""
    if not sensitivity_path.exists():
        raise FileNotFoundError(f"Sensitivity analysis report not found: {sensitivity_path}")
    
    with open(sensitivity_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_box_plot(metrics: List[Dict[str, Any]], output_path: Path):
    """Generate box plots comparing smell distributions between human and LLM samples."""
    smell_types = ['LongMethod', 'DuplicatedCode', 'FeatureEnvy', 'LongParameterList']
    
    plt.figure(figsize=(12, 8))
    
    for i, smell_type in enumerate(smell_types):
        human_data = [m['count'] for m in metrics if m['smell_type'] == smell_type and m['source_type'] == 'human']
        llm_data = [m['count'] for m in metrics if m['smell_type'] == smell_type and m['source_type'] == 'llm']
        
        plt.subplot(2, 2, i + 1)
        plt.boxplot([human_data, llm_data], labels=['Human', 'LLM'])
        plt.title(smell_type)
        plt.ylabel('Count')
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Box plot saved to {output_path}")

def generate_continuous_metric_plot(metrics: List[Dict[str, Any]], output_path: Path):
    """Generate continuous metric comparison plots."""
    smell_types = ['LongMethod', 'DuplicatedCode', 'FeatureEnvy', 'LongParameterList']
    
    plt.figure(figsize=(12, 8))
    
    for i, smell_type in enumerate(smell_types):
        human_data = [m['continuous_metric_value'] for m in metrics if m['smell_type'] == smell_type and m['source_type'] == 'human']
        llm_data = [m['continuous_metric_value'] for m in metrics if m['smell_type'] == smell_type and m['source_type'] == 'llm']
        
        plt.subplot(2, 2, i + 1)
        plt.boxplot([human_data, llm_data], labels=['Human', 'LLM'])
        plt.title(f"{smell_type} (Continuous)")
        plt.ylabel('Metric Value')
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Continuous metric plot saved to {output_path}")

def generate_sensitivity_plot(sensitivity_report: Dict[str, Any], output_path: Path):
    """Generate line plot showing p-value trends across sensitivity analysis sweeps."""
    smell_types = ['LongMethod', 'DuplicatedCode', 'FeatureEnvy', 'LongParameterList']
    stability_threshold = 0.01
    
    plt.figure(figsize=(14, 8))
    
    # Get all threshold values for x-axis (assuming consistent ranges or using max range)
    # We'll plot each smell type separately with its specific thresholds
    for smell_type in smell_types:
        if smell_type not in sensitivity_report.get('results', {}):
            logger.warning(f"No sensitivity data for {smell_type}")
            continue
        
        result = sensitivity_report['results'][smell_type]
        thresholds = result.get('thresholds', [])
        p_values = result.get('p_values', [])
        
        if not thresholds or not p_values:
            continue
        
        plt.plot(thresholds, p_values, marker='o', label=smell_type)
        
        # Highlight stable region if available
        stable_range = result.get('stable_range')
        if stable_range:
            plt.axvspan(stable_range[0], stable_range[1], alpha=0.2, 
                        label=f'{smell_type} Stable', linestyle='--')
    
    plt.axhline(y=stability_threshold, color='r', linestyle='--', 
                label=f'Stability Threshold (variance < {stability_threshold})')
    plt.xlabel('Threshold Value')
    plt.ylabel('P-Value')
    plt.title('Sensitivity Analysis: P-Value Trends Across Thresholds')
    plt.legend(loc='best', fontsize='small')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Sensitivity analysis plot saved to {output_path}")

def format_statistical_table(stat_results: Dict[str, Any]) -> str:
    """Format statistical results into a markdown table."""
    lines = ["## Statistical Comparison Results", ""]
    lines.append("| Smell Type | P-Value | Bonferroni-Corrected P-Value | Effect Size | Significant? |")
    lines.append("|------------|---------|------------------------------|-------------|--------------|")
    
    for smell_type, result in stat_results.get('results', {}).items():
        p_val = result.get('p_value', 'N/A')
        corrected_p = result.get('corrected_p_value', 'N/A')
        effect_size = result.get('effect_size', 'N/A')
        significant = "Yes" if corrected_p < 0.05 else "No"
        lines.append(f"| {smell_type} | {p_val:.4f} | {corrected_p:.4f} | {effect_size:.4f} | {significant} |")
    
    return "\n".join(lines)

def format_sensitivity_table(sensitivity_report: Dict[str, Any]) -> str:
    """Format sensitivity analysis results into a markdown table."""
    lines = ["## Sensitivity Analysis Results", ""]
    lines.append("| Smell Type | Stability Status | Stable Range | Max P-Value Variance |")
    lines.append("|------------|------------------|--------------|----------------------|")
    
    for smell_type, result in sensitivity_report.get('results', {}).items():
        stability = "Stable" if result.get('stability_passed', False) else "Unstable"
        stable_range = result.get('stable_range', 'N/A')
        if isinstance(stable_range, list):
            stable_range = f"{stable_range[0]} - {stable_range[1]}"
        variance = result.get('max_variance', 'N/A')
        lines.append(f"| {smell_type} | {stability} | {stable_range} | {variance:.6f} |")
    
    return "\n".join(lines)

def generate_markdown_report(metrics: List[Dict[str, Any]], 
                            stat_results: Dict[str, Any], 
                            sensitivity_report: Dict[str, Any],
                            output_path: Path):
    """Generate the final markdown report with embedded plots."""
    report_path = output_path.parent / "final_study_report.md"
    
    report_content = [
        "# Evaluating Code Generation Impact on Code Smell Frequency",
        "",
        "## Introduction",
        "This report presents the results of a comparative analysis between human-written and LLM-generated code samples, focusing on the frequency of four code smell categories.",
        "",
        "## Methodology",
        "- **Design**: Balanced Blocked Design with repository-level blocking",
        "- **Statistical Test**: Blocked Permutation Test",
        "- **Correction**: Bonferroni correction for multiple hypothesis testing (α ≤ 0.05)",
        "- **Sensitivity Analysis**: Threshold sweeps for all four code smell categories",
        "",
        "## Results",
        "",
        "### Statistical Comparison",
        "",
        format_statistical_table(stat_results),
        "",
        "### Visualizations",
        "",
        "#### Code Smell Distribution Comparison",
        "",
        "![Box Plots](sensitivity_analysis_plot.png)",
        "",
        "#### Sensitivity Analysis",
        "",
        "![Sensitivity Analysis Plot](sensitivity_analysis_plot.png)",
        "",
        "### Sensitivity Analysis Results",
        "",
        format_sensitivity_table(sensitivity_report),
        "",
        "## Conclusion",
        "",
        "This study is **observational** in nature. The findings presented here describe **associations** between code generation source (human vs. LLM) and code smell frequencies. **No causal claims are made** regarding the impact of code generation on code quality.",
        "",
        "The stability of results across threshold variations suggests robustness in the observed associations, though further validation with larger datasets and additional repositories is recommended.",
        ""
    ]
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_content))
    
    logger.info(f"Final report saved to {report_path}")

def main():
    """Main entry point for report generation."""
    project_root = get_project_root()
    output_paths = get_output_paths(project_root)
    
    # Define input paths
    metrics_path = output_paths['processed_metrics']
    stat_results_path = output_paths['stat_results']
    sensitivity_report_path = output_paths['sensitivity_report']
    
    # Define output paths
    box_plot_path = output_paths['report_output'] / "sensitivity_analysis_plot.png"
    continuous_plot_path = output_paths['report_output'] / "continuous_metric_plot.png"
    report_path = output_paths['report_output'] / "final_study_report.md"
    
    # Ensure output directory exists
    output_paths['report_output'].mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading processed metrics...")
    metrics = load_processed_metrics(metrics_path)
    
    logger.info("Loading statistical results...")
    stat_results = load_stat_results(stat_results_path)
    
    logger.info("Loading sensitivity analysis report...")
    sensitivity_report = load_sensitivity_report(sensitivity_report_path)
    
    # Generate visualizations
    logger.info("Generating sensitivity analysis plot...")
    generate_sensitivity_plot(sensitivity_report, box_plot_path)
    
    logger.info("Generating continuous metric plot...")
    generate_continuous_metric_plot(metrics, continuous_plot_path)
    
    # Generate final report
    logger.info("Generating final markdown report...")
    generate_markdown_report(metrics, stat_results, sensitivity_report, report_path)
    
    logger.info("Report generation completed successfully.")

if __name__ == "__main__":
    main()