import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime

from utils import get_logger, ensure_directory

def load_sensitivity_data(filepath: str) -> pd.DataFrame:
    """
    Load the sensitivity analysis data from CSV.
    Expects columns: ['threshold', 'model', 'pass_rate', 'total_galaxies', 'pass_count']
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    if 'threshold' not in df.columns or 'model' not in df.columns or 'pass_rate' not in df.columns:
        raise ValueError("Sensitivity data CSV missing required columns: threshold, model, pass_rate")
    return df

def generate_report(
    data: pd.DataFrame,
    output_path: str,
    title: str = "Sensitivity Analysis Report: MOND vs NFW Goodness-of-Fit"
) -> str:
    """
    Generate a markdown report with visualizations comparing pass rates for thresholds.
    Returns the path to the generated markdown file.
    """
    output_path = Path(output_path)
    ensure_directory(output_path.parent)
    
    # Ensure numeric columns are correct
    data['threshold'] = pd.to_numeric(data['threshold'], errors='coerce')
    data['pass_rate'] = pd.to_numeric(data['pass_rate'], errors='coerce')
    
    # Sort data for plotting
    data = data.sort_values(by=['model', 'threshold'])
    
    # Generate Plot
    plt.figure(figsize=(10, 6))
    
    models = data['model'].unique()
    colors = ['blue', 'green']
    
    for i, model in enumerate(models):
        subset = data[data['model'] == model]
        # Handle potential NaNs in sorting
        subset = subset.dropna(subset=['threshold', 'pass_rate'])
        if not subset.empty:
            plt.plot(
                subset['threshold'], 
                subset['pass_rate'], 
                marker='o', 
                linestyle='-', 
                color=colors[i], 
                label=model
            )
    
    plt.title(title)
    plt.xlabel('Reduced Chi-Squared ($\\chi^2_{red}$) Threshold')
    plt.ylabel('Pass Rate (Fraction of Galaxies)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    
    # Save plot
    plot_path = output_path.parent / "sensitivity_pass_rates.png"
    plt.savefig(plot_path)
    plt.close()
    
    # Generate Summary Text
    # Calculate best threshold for each model based on a balance (e.g., highest pass rate)
    # or simply describe the trend.
    summary_lines = [
        f"# {title}",
        "",
        "## Overview",
        "This report presents the results of the sensitivity analysis performed on the fitted galaxy rotation curves.",
        "The analysis evaluates the robustness of the model comparison (MOND vs. NFW) across a range of reduced chi-squared ($\\chi^2_{red}$) thresholds.",
        "",
        "## Methodology",
        "Galaxies were considered to 'pass' the goodness-of-fit test if their calculated reduced chi-squared value was less than or equal to the specified threshold.",
        "Pass rates were computed as the fraction of the total galaxy sample that passed for each threshold value.",
        "The thresholds analyzed include: 1.0, 1.25, 1.5, and 1.75.",
        "",
        "## Results",
        "",
        "### Visualization",
        f"![Pass Rate Comparison]({plot_path.name})",
        "",
        "### Summary Statistics",
        ""
    ]
    
    # Add specific data points to the report
    summary_lines.append("| Model | Threshold | Pass Rate | Total Galaxies | Pass Count |")
    summary_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    
    for _, row in data.iterrows():
        if not pd.isna(row['threshold']):
            summary_lines.append(
                f"| {row['model']} | {row['threshold']:.2f} | {row['pass_rate']:.2%} | {int(row.get('total_galaxies', 'N/A'))} | {int(row.get('pass_count', 'N/A'))} |"
            )
    
    summary_lines.extend([
        "",
        "## Conclusion",
        "The generated visualization illustrates how the acceptance criteria for model validity change as the threshold for reduced chi-squared is relaxed.",
        "A higher pass rate at lower thresholds indicates a model that fits a larger portion of the galaxy sample with high precision.",
        "Conversely, a steep increase in pass rate as the threshold rises suggests that many galaxies are only marginally well-fit by the model.",
        "Comparing the curves for MOND and NFW allows for an assessment of which model provides a more robust explanation of the rotation curve data across the sample.",
        "",
        f"*Report generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    ])
    
    report_content = "\n".join(summary_lines)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return str(output_path)

def main():
    """
    Main entry point to generate the sensitivity report.
    """
    logger = get_logger(__name__)
    
    # Configuration
    input_file = "results/sensitivity_data.csv"
    output_file = "results/sensitivity_report.md"
    
    logger.info(f"Loading sensitivity data from {input_file}")
    try:
        data = load_sensitivity_data(input_file)
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Ensure T026 (sensitivity analysis) has been run to generate results/sensitivity_data.csv")
        raise
    
    logger.info(f"Generating report with {len(data)} data points")
    
    try:
        report_path = generate_report(data, output_file)
        logger.info(f"Report successfully generated at {report_path}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise

if __name__ == "__main__":
    main()