import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from config import get_output_dir
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def load_metric_data() -> List[Dict[str, Any]]:
    """
    Load aggregated metrics from data/results/metrics_combined.csv.
    Expected columns: repo_name, module_path, gini, bug_density, size_kloc, age_months
    """
    output_dir = get_output_dir()
    metrics_file = Path(output_dir) / "results" / "metrics_combined.csv"
    
    if not metrics_file.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}. Run metrics_calc.py first.")
    
    data = []
    with open(metrics_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data.append({
                    'repo_name': row['repo_name'],
                    'module_path': row['module_path'],
                    'gini': float(row['gini']),
                    'bug_density': float(row['bug_density']),
                    'size_kloc': float(row['size_kloc']),
                    'age_months': float(row['age_months'])
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid row in metrics file: {e}")
                continue
    
    return data

def filter_repos_by_count(data: List[Dict[str, Any]], min_repos: int = 8) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group data by repo_name and filter to only include repos with sufficient data points.
    Returns a dict mapping repo_name to list of module records.
    """
    repo_groups: Dict[str, List[Dict[str, Any]]] = {}
    for record in data:
        repo = record['repo_name']
        if repo not in repo_groups:
            repo_groups[repo] = []
        repo_groups[repo].append(record)
    
    # Filter repos with at least 1 valid module (or adjust threshold if needed)
    # The task asks for plots for >=8 repos. We assume the data has enough.
    valid_repos = {k: v for k, v in repo_groups.items() if len(v) > 0}
    
    if len(valid_repos) < min_repos:
        logger.warning(f"Only {len(valid_repos)} repos found with data. Expected >= {min_repos}.")
    
    return valid_repos

def generate_scatter_plot_with_regression(
    data: List[Dict[str, Any]], 
    repo_name: str, 
    output_path: Path, 
    dpi: int = 300
) -> None:
    """
    Generate a scatter plot of Gini vs Bug Density with a regression line.
    Saves the figure to output_path.
    """
    if not data:
        logger.warning(f"No data for repo {repo_name}, skipping plot.")
        return

    gini_vals = [d['gini'] for d in data]
    bug_vals = [d['bug_density'] for d in data]

    if len(gini_vals) < 2:
        logger.warning(f"Not enough data points for regression in {repo_name}.")
        return

    # Calculate regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(gini_vals, bug_vals)
    
    # Prepare plot
    plt.figure(figsize=(10, 8))
    plt.scatter(gini_vals, bug_vals, alpha=0.6, edgecolors='w', s=50, label='Modules')
    
    # Regression line
    x_line = np.linspace(min(gini_vals), max(gini_vals), 100)
    y_line = slope * x_line + intercept
    plt.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_value:.2f}, p={p_value:.3g})')
    
    plt.xlabel('Gini Coefficient (Ownership Concentration)', fontsize=12)
    plt.ylabel('Bug Density (Bugs/KLOC)', fontsize=12)
    plt.title(f'Code Ownership vs. Bug Density: {repo_name}', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Ensure high DPI
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved plot for {repo_name} to {output_path}")

def generate_all_plots(min_repos: int = 8, dpi: int = 300) -> List[str]:
    """
    Main entry point to generate scatter plots for all valid repos.
    Returns list of generated file paths.
    """
    output_dir = get_output_dir()
    plots_dir = Path(output_dir) / "figures"
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading metric data...")
    data = load_metric_data()
    
    logger.info(f"Grouping data by repository...")
    repo_groups = filter_repos_by_count(data, min_repos)
    
    generated_files = []
    
    for repo_name, records in repo_groups.items():
        # Sanitize filename
        safe_name = repo_name.replace("/", "_").replace("\\", "_").replace(".", "_")
        filename = f"{safe_name}_ownership_bug_density.png"
        output_path = plots_dir / filename
        
        try:
            generate_scatter_plot_with_regression(records, repo_name, output_path, dpi)
            generated_files.append(str(output_path))
        except Exception as e:
            logger.error(f"Failed to generate plot for {repo_name}: {e}")
            continue
    
    logger.info(f"Generated {len(generated_files)} plots.")
    return generated_files

def main():
    """
    Orchestrate the generation of visualization plots.
    """
    logger.info("Starting visualization generation for T034...")
    try:
        files = generate_all_plots(min_repos=8, dpi=300)
        if not files:
            logger.error("No plots were generated. Check data availability.")
            return 1
        logger.info(f"Successfully generated {len(files)} visualization files.")
        return 0
    except Exception as e:
        logger.critical(f"Visualization pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
