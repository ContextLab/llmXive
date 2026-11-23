"""
Report Generator Module.

Handles loading statistical JSON reports and rendering them into Markdown documentation.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

def load_stats_report(stats_path: Path) -> Dict[str, Any]:
    """
    Loads the statistical report from a JSON file.
    
    Args:
        stats_path: Path to the stats_report.json file.
        
    Returns:
        Dictionary containing the report data.
    """
    if not stats_path.exists():
        return {}
    
    with open(stats_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_report(stats_data: Dict[str, Any], output_path: str) -> None:
    """
    Generates the Markdown report from the stats data.
    
    Args:
        stats_data: The dictionary of statistics to render.
        output_path: The file path where the Markdown will be written.
    """
    output_file = Path(output_path)
    
    # Header
    md_content = [
        "# llmXive Research Results: Graph Memory for LLM Agents",
        "",
        "## Overview",
        "",
        "This report summarizes the statistical analysis of the active reconstruction strategies",
        "tested on the LoCoMo benchmark. It compares the baseline 'Full' traversal against",
        "heuristic approaches ('Lazy' and 'Greedy') to evaluate efficiency and accuracy trade-offs.",
        "",
        "---",
        ""
    ]
    
    # 1. Executive Summary (if available)
    if 'executive_summary' in stats_data:
        md_content.append("## Executive Summary")
        md_content.append("")
        md_content.append(stats_data['executive_summary'])
        md_content.append("")
        md_content.append("---")
        md_content.append("")
    
    # 2. Statistical Significance (Hypothesis Testing)
    if 'statistical_significance' in stats_data:
        md_content.append("## Statistical Significance Analysis")
        md_content.append("")
        stats = stats_data['statistical_significance']
        
        if 'baseline_vs_lazy' in stats:
            md_content.append("### Baseline vs. Lazy Traversal")
            lazy_res = stats['baseline_vs_lazy']
            md_content.append(f"- **Test Type**: {lazy_res.get('test_type', 'N/A')}")
            md_content.append(f"- **Statistic**: {lazy_res.get('statistic', 'N/A')}")
            md_content.append(f"- **P-value**: {lazy_res.get('p_value', 'N/A')}")
            md_content.append(f"- **Conclusion**: {'Significant difference' if lazy_res.get('significant', False) else 'No significant difference'}")
            md_content.append("")
        
        if 'baseline_vs_greedy' in stats:
            md_content.append("### Baseline vs. Greedy Traversal")
            greedy_res = stats['baseline_vs_greedy']
            md_content.append(f"- **Test Type**: {greedy_res.get('test_type', 'N/A')}")
            md_content.append(f"- **Statistic**: {greedy_res.get('statistic', 'N/A')}")
            md_content.append(f"- **P-value**: {greedy_res.get('p_value', 'N/A')}")
            md_content.append(f"- **Conclusion**: {'Significant difference' if greedy_res.get('significant', False) else 'No significant difference'}")
            md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    # 3. Robustness Check (Noisy Data)
    if 'robustness_check' in stats_data:
        md_content.append("## Robustness Check (Noisy Graphs)")
        md_content.append("")
        robust = stats_data['robustness_check']
        
        if 'baseline' in robust:
            md_content.append("### Noisy Baseline Statistics")
            base = robust['baseline']
            md_content.append(f"- **Mean Accuracy**: {base.get('mean_accuracy', 'N/A')}")
            md_content.append(f"- **Std Accuracy**: {base.get('std_accuracy', 'N/A')}")
            md_content.append(f"- **Mean Nodes Visited**: {base.get('mean_nodes_visited', 'N/A')}")
            md_content.append("")
        
        if 'lazy' in robust:
            md_content.append("### Noisy Lazy Statistics")
            lazy = robust['lazy']
            md_content.append(f"- **Mean Accuracy**: {lazy.get('mean_accuracy', 'N/A')}")
            md_content.append(f"- **Std Accuracy**: {lazy.get('std_accuracy', 'N/A')}")
            md_content.append(f"- **Mean Nodes Visited**: {lazy.get('mean_nodes_visited', 'N/A')}")
            md_content.append("")
        
        if 'deltas' in robust:
            md_content.append("### Accuracy Deltas (Heuristic vs Baseline)")
            deltas = robust['deltas']
            if 'lazy_delta' in deltas:
                md_content.append(f"- **Lazy Delta**: {deltas['lazy_delta']}")
            if 'greedy_delta' in deltas:
                md_content.append(f"- **Greedy Delta**: {deltas['greedy_delta']}")
            md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    # 4. Complexity Threshold Analysis
    if 'complexity_threshold' in stats_data:
        md_content.append("## Complexity Threshold Analysis")
        md_content.append("")
        threshold = stats_data['complexity_threshold']
        md_content.append(f"- **Threshold Nodes**: {threshold.get('threshold_nodes', 'N/A')}")
        md_content.append(f"- **Baseline Accuracy**: {threshold.get('baseline_accuracy', 'N/A')}")
        md_content.append(f"- **Drop Threshold**: {threshold.get('drop_threshold', 'N/A')}")
        md_content.append(f"- **Observation**: {threshold.get('observation', 'N/A')}")
        md_content.append("")
        md_content.append("---")
        md_content.append("")
    
    # 5. Correlation Analysis
    if 'correlation_analysis' in stats_data:
        md_content.append("## Correlation Analysis")
        md_content.append("")
        corr = stats_data['correlation_analysis']
        md_content.append(f"- **Correlation Coefficient (Point-Biserial)**: {corr.get('coefficient', 'N/A')}")
        md_content.append(f"- **P-value**: {corr.get('p_value', 'N/A')}")
        md_content.append(f"- **Interpretation**: {corr.get('interpretation', 'N/A')}")
        md_content.append("")
        md_content.append("---")
        md_content.append("")
    
    # 6. Sensitivity Analysis (Lazy Threshold)
    if 'sensitivity_analysis' in stats_data:
        md_content.append("## Sensitivity Analysis: Lazy Heuristic Threshold")
        md_content.append("")
        sens = stats_data['sensitivity_analysis']
        md_content.append("| Threshold | Mean Accuracy | Mean Nodes Visited |")
        md_content.append("| :--- | :--- | :--- |")
        for entry in sens.get('results', []):
            md_content.append(f"| {entry.get('threshold', 'N/A')} | {entry.get('mean_accuracy', 'N/A')} | {entry.get('mean_nodes_visited', 'N/A')} |")
        md_content.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    logger = logging.getLogger(__name__)
    logger.info(f"Report generated successfully at {output_file}")

def main():
    """
    CLI entry point for the report generator.
    Usage: python -m analysis.report_generator
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    stats_file = Path("data/processed/stats_report.json")
    output_file = Path("docs/results.md")
    
    stats_data = load_stats_report(stats_file)
    generate_report(stats_data, str(output_file))

if __name__ == "__main__":
    main()
