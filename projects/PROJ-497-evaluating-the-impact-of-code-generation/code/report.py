"""
Report generation module for llmXive project.

This module generates summary reports from processed analysis data.
It strictly adheres to the Single Source of Truth principle by reading
exclusively from data/processed directory.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from config import get_paths

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_csv_file(file_path: Path) -> pd.DataFrame:
    """Load a CSV file and return it as a pandas DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    return pd.read_csv(file_path)


def extract_key_stats(aggregated_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract key statistics from the aggregated analysis dataset.
    
    Args:
        aggregated_df: DataFrame containing aggregated analysis results.
        
    Returns:
        Dictionary containing key statistics.
    """
    stats = {}
    
    # Overall statistics
    stats['total_samples'] = len(aggregated_df)
    stats['mean_vuln_count'] = aggregated_df['mean_vulnerability_count'].mean()
    stats['std_vuln_count'] = aggregated_df['mean_vulnerability_count'].std()
    
    # By source type
    source_stats = aggregated_df.groupby('source_type')['mean_vulnerability_count'].agg(['mean', 'std', 'count'])
    stats['by_source'] = {
        source: {
            'mean': float(row['mean']),
            'std': float(row['std']),
            'count': int(row['count'])
        }
        for source, row in source_stats.iterrows()
    }
    
    # By benchmark
    benchmark_stats = aggregated_df.groupby('benchmark')['mean_vulnerability_count'].agg(['mean', 'std', 'count'])
    stats['by_benchmark'] = {
        bench: {
            'mean': float(row['mean']),
            'std': float(row['std']),
            'count': int(row['count'])
        }
        for bench, row in benchmark_stats.iterrows()
    }
    
    return stats


def extract_fpr_metrics(fpr_file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract FPR metrics from the FPR metrics file.
    
    Args:
        fpr_file_path: Path to the FPR metrics JSON file.
        
    Returns:
        Dictionary containing FPR metrics, or None if file doesn't exist.
    """
    if not fpr_file_path.exists():
        logger.warning(f"FPR metrics file not found: {fpr_file_path}")
        return None
    
    try:
        return load_json_file(fpr_file_path)
    except Exception as e:
        logger.error(f"Error loading FPR metrics: {e}")
        return None


def extract_zinb_results(zinb_file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract ZINB regression results from the ZINB results file.
    
    Args:
        zinb_file_path: Path to the ZINB results JSON file.
        
    Returns:
        Dictionary containing ZINB results, or None if file doesn't exist.
    """
    if not zinb_file_path.exists():
        logger.warning(f"ZINB results file not found: {zinb_file_path}")
        return None
    
    try:
        return load_json_file(zinb_file_path)
    except Exception as e:
        logger.error(f"Error loading ZINB results: {e}")
        return None


def generate_summary_markdown(
    key_stats: Dict[str, Any],
    zinb_results: Optional[Dict[str, Any]],
    fpr_metrics: Optional[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generate a summary report in Markdown format.
    
    Args:
        key_stats: Dictionary containing key statistics.
        zinb_results: Dictionary containing ZINB regression results.
        fpr_metrics: Dictionary containing FPR metrics.
        output_path: Path where the Markdown report will be saved.
    """
    lines = []
    lines.append("# Vulnerability Density Analysis Report")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"This report summarizes the vulnerability density analysis comparing ")
    lines.append(f"LLM-generated code against human-written code.")
    lines.append("")
    
    # Key Statistics
    lines.append("## Key Statistics")
    lines.append("")
    lines.append(f"- **Total Samples Analyzed**: {key_stats['total_samples']}")
    lines.append(f"- **Overall Mean Vulnerability Count**: {key_stats['mean_vuln_count']:.2f}")
    lines.append(f"- **Overall Std Dev**: {key_stats['std_vuln_count']:.2f}")
    lines.append("")
    
    # By Source Type
    lines.append("### By Source Type")
    lines.append("")
    lines.append("| Source Type | Mean Vuln Count | Std Dev | Sample Count |")
    lines.append("|-------------|-----------------|---------|--------------|")
    for source, stats in key_stats['by_source'].items():
        lines.append(f"| {source} | {stats['mean']:.2f} | {stats['std']:.2f} | {stats['count']} |")
    lines.append("")
    
    # By Benchmark
    lines.append("### By Benchmark")
    lines.append("")
    lines.append("| Benchmark | Mean Vuln Count | Std Dev | Sample Count |")
    lines.append("|-----------|-----------------|---------|--------------|")
    for bench, stats in key_stats['by_benchmark'].items():
        lines.append(f"| {bench} | {stats['mean']:.2f} | {stats['std']:.2f} | {stats['count']} |")
    lines.append("")
    
    # Statistical Analysis Results
    if zinb_results:
        lines.append("## Statistical Analysis Results")
        lines.append("")
        lines.append("### ZINB Regression Results")
        lines.append("")
        
        if 'coefficients' in zinb_results:
            lines.append("| Variable | Coefficient | Std Error | Z-value | P-value |")
            lines.append("|----------|-------------|-----------|---------|---------|")
            for var, coef in zinb_results['coefficients'].items():
                lines.append(f"| {var} | {coef['coef']:.4f} | {coef['std_err']:.4f} | {coef['z']:.4f} | {coef['p_value']:.4f} |")
            lines.append("")
        
        if 'model_fit' in zinb_results:
            lines.append(f"**Model Log-Likelihood**: {zinb_results['model_fit']['log_likelihood']:.4f}")
            lines.append(f"**AIC**: {zinb_results['model_fit']['aic']:.4f}")
            lines.append(f"**BIC**: {zinb_results['model_fit']['bic']:.4f}")
            lines.append("")
    
    # FPR Metrics
    if fpr_metrics:
        lines.append("## False Positive Rate Analysis")
        lines.append("")
        lines.append("| CWE ID | Group Size | False Positive Rate |")
        lines.append("|--------|------------|---------------------|")
        for cwe, metrics in fpr_metrics.get('cwe_metrics', {}).items():
            lines.append(f"| {cwe} | {metrics['group_size']} | {metrics['fpr']:.4f} |")
        lines.append("")
    
    # Visualization Paths
    lines.append("## Generated Visualizations")
    lines.append("")
    lines.append("The following visualizations have been generated:")
    lines.append("")
    lines.append("1. **Vulnerability Distribution Boxplot**: `results/boxplot_vulnerability_distribution.png`")
    lines.append("2. **Top Vulnerability Types Bar Chart**: `results/top_vulnerability_types.png`")
    lines.append("")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Summary report generated: {output_path}")


def main():
    """Main function to generate the summary report."""
    paths = get_paths()
    
    # Define input paths (all from data/processed - Single Source of Truth)
    aggregated_data_path = paths['data_processed'] / 'aggregated_analysis_dataset.csv'
    zinb_results_path = paths['data_processed'] / 'zinb_results.json'
    fpr_metrics_path = paths['data_processed'] / 'fpr_metrics.json'
    
    # Define output path
    output_path = paths['results'] / 'summary.md'
    
    # Ensure results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting report generation...")
    logger.info(f"Reading aggregated data from: {aggregated_data_path}")
    
    # Load aggregated data
    try:
        aggregated_df = load_csv_file(aggregated_data_path)
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        raise
    
    # Extract key statistics
    logger.info("Extracting key statistics...")
    key_stats = extract_key_stats(aggregated_df)
    
    # Extract ZINB results
    logger.info("Extracting ZINB results...")
    zinb_results = extract_zinb_results(zinb_results_path)
    
    # Extract FPR metrics
    logger.info("Extracting FPR metrics...")
    fpr_metrics = extract_fpr_metrics(fpr_metrics_path)
    
    # Generate summary markdown
    logger.info("Generating summary markdown report...")
    generate_summary_markdown(key_stats, zinb_results, fpr_metrics, output_path)
    
    logger.info("Report generation completed successfully.")
    return output_path


if __name__ == '__main__':
    main()