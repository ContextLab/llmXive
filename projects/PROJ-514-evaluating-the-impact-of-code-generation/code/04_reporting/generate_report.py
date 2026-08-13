import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from utils.logger import get_logger
from utils.config import get_output_paths

logger = get_logger(__name__)

def load_processed_metrics(metrics_path: str) -> pd.DataFrame:
    """Load processed smell metrics from CSV."""
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    return pd.read_csv(metrics_path)

def load_stat_results(results_path: str) -> Dict[str, Any]:
    """Load statistical results from JSON."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Stat results file not found: {results_path}")
    with open(results_path, 'r') as f:
        return json.load(f)

def load_sensitivity_report(report_path: str) -> Dict[str, Any]:
    """Load sensitivity analysis report from JSON."""
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Sensitivity report file not found: {report_path}")
    with open(report_path, 'r') as f:
        return json.load(f)

def generate_box_plot(data: pd.DataFrame, output_path: str, smell_type: str) -> str:
    """Generate a box plot for a specific smell type comparing human vs LLM."""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    human_data = data[(data['source_type'] == 'human') & (data['smell_type'] == smell_type)]['continuous_metric_value']
    llm_data = data[(data['source_type'] == 'llm') & (data['smell_type'] == smell_type)]['continuous_metric_value']
    
    ax.boxplot([human_data.dropna(), llm_data.dropna()], labels=['Human', 'LLM'])
    ax.set_ylabel('Metric Value')
    ax.set_title(f'{smell_type.replace("_", " ")} Distribution')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path

def generate_continuous_metric_plot(data: pd.DataFrame, output_path: str, smell_type: str) -> str:
    """Generate a scatter plot for continuous metric values."""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    human_data = data[(data['source_type'] == 'human') & (data['smell_type'] == smell_type)]
    llm_data = data[(data['source_type'] == 'llm') & (data['smell_type'] == smell_type)]
    
    ax.scatter(human_data['sample_id'], human_data['continuous_metric_value'], 
               alpha=0.6, label='Human', color='blue')
    ax.scatter(llm_data['sample_id'], llm_data['continuous_metric_value'], 
               alpha=0.6, label='LLM', color='red')
    
    ax.set_xlabel('Sample ID')
    ax.set_ylabel('Metric Value')
    ax.set_title(f'{smell_type.replace("_", " ")} Continuous Values')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path

def generate_sensitivity_plot(sensitivity_report: Dict[str, Any], output_path: str) -> str:
    """
    Generate a line plot showing p-value trends across sensitivity analysis sweeps.
    Highlights the stability threshold (p-value variance < 0.01).
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    smell_types = ['Long_Method', 'Duplicated_Code', 'Feature_Envy', 'Long_Parameter_List']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # Stability threshold line
    stability_threshold = 0.01
    ax.axhline(y=stability_threshold, color='gray', linestyle='--', alpha=0.7, 
               label=f'Stability Threshold (variance < {stability_threshold})')
    
    for smell_type, color in zip(smell_types, colors):
        if smell_type in sensitivity_report.get('sweep_results', {}):
            sweep_data = sensitivity_report['sweep_results'][smell_type]
            thresholds = sweep_data.get('thresholds', [])
            p_values = sweep_data.get('p_values', [])
            variances = sweep_data.get('variances', [])
            
            if thresholds and p_values:
                ax.plot(thresholds, p_values, marker='o', color=color, 
                        label=smell_type.replace('_', ' '), linewidth=2)
                
                # Highlight stable region
                stable_indices = [i for i, var in enumerate(variances) if var < stability_threshold]
                if stable_indices:
                    stable_thresholds = [thresholds[i] for i in stable_indices]
                    stable_pvalues = [p_values[i] for i in stable_indices]
                    if stable_thresholds:
                        ax.fill_between(stable_thresholds, 
                                      min(stable_pvalues) - 0.01, 
                                      max(stable_pvalues) + 0.01, 
                                      color=color, alpha=0.1)
    
    ax.set_xlabel('Threshold Value')
    ax.set_ylabel('P-Value')
    ax.set_title('Sensitivity Analysis: P-Value Trends Across Thresholds')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path

def format_statistical_table(stat_results: Dict[str, Any]) -> str:
    """Format statistical results into a markdown table."""
    lines = []
    lines.append("| Smell Type | P-Value (Uncorrected) | P-Value (Bonferroni) | Effect Size | Significant |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")
    
    for smell_type, result in stat_results.get('results', {}).items():
        p_uncorr = result.get('p_value', 0)
        p_corr = result.get('corrected_p_value', 0)
        effect = result.get('effect_size', 0)
        sig = "Yes" if p_corr < 0.05 else "No"
        
        lines.append(f"| {smell_type.replace('_', ' ')} | {p_uncorr:.4f} | {p_corr:.4f} | {effect:.4f} | {sig} |")
    
    return "\n".join(lines)

def format_sensitivity_table(sensitivity_report: Dict[str, Any]) -> str:
    """Format sensitivity analysis results into a markdown table."""
    lines = []
    lines.append("| Smell Type | Stability Status | P-Value Variance | Notes |")
    lines.append("| :--- | :--- | :--- | :--- |")
    
    for smell_type, result in sensitivity_report.get('sweep_results', {}).items():
        stability = result.get('stability_status', 'Unknown')
        variance = result.get('variance', 0)
        notes = result.get('notes', '')
        
        lines.append(f"| {smell_type.replace('_', ' ')} | {stability} | {variance:.6f} | {notes} |")
    
    return "\n".join(lines)

def generate_markdown_report(metrics: pd.DataFrame, stat_results: Dict[str, Any], 
                             sensitivity_report: Dict[str, Any], output_dir: str) -> str:
    """Generate the final markdown report with all sections and plots."""
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, 'final_study_report.md')
    
    # Generate plots
    box_plot_path = os.path.join(output_dir, 'box_plots.png')
    sensitivity_plot_path = os.path.join(output_dir, 'sensitivity_analysis_plot.png')
    
    # Generate box plots for each smell type
    smell_types = ['Long_Method', 'Duplicated_Code', 'Feature_Envy', 'Long_Parameter_List']
    for smell_type in smell_types:
        plot_path = os.path.join(output_dir, f'box_plot_{smell_type}.png')
        generate_box_plot(metrics, plot_path, smell_type)
    
    # Generate sensitivity plot
    generate_sensitivity_plot(sensitivity_report, sensitivity_plot_path)
    
    # Build report content
    report_lines = []
    report_lines.append("# Evaluating Code Generation Impact on Code Smell Frequency")
    report_lines.append("")
    report_lines.append("## Introduction")
    report_lines.append("This study evaluates the association between code generation source (human vs. LLM) and the frequency of code smells.")
    report_lines.append("")
    report_lines.append("## Methodology")
    report_lines.append("We employed a **Blocked Permutation Test** with repository as the blocking variable to control for repository-level variance.")
    report_lines.append("Bonferroni correction was applied to control the family-wise error rate across the four code smell categories.")
    report_lines.append("")
    report_lines.append("## Statistical Results")
    report_lines.append(format_statistical_table(stat_results))
    report_lines.append("")
    report_lines.append("### Distribution Visualizations")
    report_lines.append(f"![Box Plots]({os.path.basename(box_plot_path)})")
    report_lines.append("")
    report_lines.append("## Sensitivity Analysis")
    report_lines.append("We performed a sensitivity analysis by sweeping thresholds for each code smell category.")
    report_lines.append("Stability is defined as a p-value variance < 0.01 across the sweep range.")
    report_lines.append("")
    report_lines.append(format_sensitivity_table(sensitivity_report))
    report_lines.append("")
    report_lines.append("### Sensitivity Plot")
    report_lines.append(f"![Sensitivity Analysis]({os.path.basename(sensitivity_plot_path)})")
    report_lines.append("")
    report_lines.append("## Conclusion")
    report_lines.append("**This study is observational.** The results indicate an **association** between the code generation source and code smell frequency.")
    report_lines.append("We explicitly avoid causal claims. The observed differences may be influenced by unmeasured confounding variables.")
    report_lines.append("")
    report_lines.append("## Deviations from Original Plan")
    report_lines.append("Refer to the Deviation Log in `spec.md` (Section 4.3) for details on sample size adjustments.")
    
    with open(report_path, 'w') as f:
        f.write("\n".join(report_lines))
    
    return report_path

def main():
    """Main entry point for report generation."""
    paths = get_output_paths()
    
    metrics_path = paths.get('processed_metrics', 'data/processed/smell_metrics.csv')
    stat_results_path = paths.get('stat_results', 'data/intermediate/stat_results.json')
    sensitivity_report_path = paths.get('sensitivity_report', 'data/intermediate/sensitivity_analysis_report.json')
    output_dir = paths.get('reports', 'reports')
    
    logger.info("Loading processed metrics...")
    metrics = load_processed_metrics(metrics_path)
    
    logger.info("Loading statistical results...")
    stat_results = load_stat_results(stat_results_path)
    
    logger.info("Loading sensitivity report...")
    sensitivity_report = load_sensitivity_report(sensitivity_report_path)
    
    logger.info("Generating final report...")
    report_path = generate_markdown_report(metrics, stat_results, sensitivity_report, output_dir)
    
    logger.info(f"Report generated successfully: {report_path}")
    return report_path

if __name__ == "__main__":
    main()