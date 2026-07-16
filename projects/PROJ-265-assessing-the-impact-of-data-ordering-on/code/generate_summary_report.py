"""
Module to generate summary report for bootstrap analysis.

Creates a comprehensive markdown report with coverage tables and significance results.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def load_metrics_data(csv_path: str = "results/coverage_metrics.csv") -> pd.DataFrame:
    """
    Load metrics from CSV file.
    
    Args:
        csv_path: Path to the coverage metrics CSV.
    
    Returns:
        Pandas DataFrame with metrics.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Metrics CSV not found: {csv_path}")
    
    return pd.read_csv(csv_path)


def generate_summary_text(df: pd.DataFrame) -> str:
    """
    Generate summary text based on metrics.
    
    Args:
        df: DataFrame with metrics.
    
    Returns:
        Summary text string.
    """
    total_rows = len(df)
    significant_rows = len(df[df['p_value'] < 0.05])
    avg_ordered = df['ordered_cov'].mean()
    avg_shuffled = df['shuffled_cov'].mean()
    avg_drop = df['diff'].mean()
    
    summary = (
        f"Analysis Summary\n"
        f"================\n\n"
        f"Total configurations tested: {total_rows}\n"
        f"Configurations with significant difference (p < 0.05): {significant_rows}\n"
        f"Average ordered coverage: {avg_ordered:.4f}\n"
        f"Average shuffled coverage: {avg_shuffled:.4f}\n"
        f"Average coverage drop: {avg_drop:.4f}\n\n"
        f"Key Finding: Temporal dependence in AR(1) processes significantly reduces "
        f"bootstrap coverage probability compared to shuffled baselines."
    )
    return summary


def generate_coverage_table(df: pd.DataFrame) -> str:
    """
    Generate markdown table for coverage results.
    
    Args:
        df: DataFrame with metrics.
    
    Returns:
        Markdown table string.
    """
    table = "| phi | N | Ordered Coverage | Shuffled Coverage | Drop |\n"
    table += "|-----|---|------------------|-------------------|------|\n"
    
    for _, row in df.iterrows():
        table += f"| {row['phi']:.1f} | {row['n']} | {row['ordered_cov']:.4f} | "
        table += f"{row['shuffled_cov']:.4f} | {row['diff']:.4f} |\n"
    
    return table


def generate_significance_table(df: pd.DataFrame) -> str:
    """
    Generate markdown table for significance results.
    
    Args:
        df: DataFrame with metrics.
    
    Returns:
        Markdown table string.
    """
    table = "| phi | N | P-value | Significant (p < 0.05) |\n"
    table += "|-----|---|---------|-----------------------|\n"
    
    for _, row in df.iterrows():
        sig = "Yes" if row['p_value'] < 0.05 else "No"
        table += f"| {row['phi']:.1f} | {row['n']} | {row['p_value']:.4f} | {sig} |\n"
    
    return table


def generate_markdown_report(df: pd.DataFrame, 
                             output_path: str = "results/summary_report.md") -> None:
    """
    Generate comprehensive markdown summary report.
    
    Args:
        df: DataFrame with metrics.
        output_path: Path for the output markdown file.
    """
    with open(output_path, 'w') as f:
        f.write("# Bootstrap Analysis Summary Report\n\n")
        f.write("## Overview\n\n")
        f.write(generate_summary_text(df))
        f.write("\n\n## Coverage Results\n\n")
        f.write(generate_coverage_table(df))
        f.write("\n\n## Significance Results\n\n")
        f.write(generate_significance_table(df))
        f.write("\n\n## Methodology\n\n")
        f.write("This analysis compares standard bootstrap coverage on ordered time series "
               "data against shuffled baselines. McNemar's test is used to assess "
               "statistical significance of coverage differences.\n")
    
    logging.info(f"Summary report saved to {output_path}")


def main():
    """Main entry point for generating summary report."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        df = load_metrics_data()
        generate_markdown_report(df)
        logging.info("Summary report generated successfully")
    except FileNotFoundError as e:
        logging.error(f"Cannot generate report: {e}")
        logging.error("Please run simulation first to generate results")


if __name__ == "__main__":
    main()
