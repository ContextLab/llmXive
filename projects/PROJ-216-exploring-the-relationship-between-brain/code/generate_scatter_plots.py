"""
T033: Generate scatter plots with regression lines and confidence intervals.

This script loads the processed graph metrics and behavioral scores,
merges them, and generates scatter plots for all significant correlations
identified in the stats analysis.
"""
import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Ensure matplotlib uses a non-interactive backend for headless environments
plt.switch_backend('Agg')

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Ensure output directories exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def load_graph_metrics(filepath: Path) -> List[Dict[str, Any]]:
    """Load graph metrics from CSV."""
    if not filepath.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {filepath}")
    
    metrics = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append(row)
    return metrics

def load_behavioral_scores(filepath: Path) -> Dict[str, float]:
    """Load behavioral scores (Fluid Intelligence) from JSON."""
    if not filepath.exists():
        raise FileNotFoundError(f"Behavioral scores file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Expected format: {"subject_id": score_value, ...} or list of objects
    # Based on T014/T030, we expect a mapping or list that can be mapped.
    # Assuming JSON structure: { "scores": [{"subject_id": "...", "score": ...}, ...] }
    # or flat: { "subject_id": score }
    
    if isinstance(data, dict):
        # Check if it's a flat dict of scores
        if all(isinstance(v, (int, float)) for v in data.values()):
            return data
        # Check if it has a 'scores' key
        if 'scores' in data:
            return {item['subject_id']: item['score'] for item in data['scores']}
    
    raise ValueError(f"Unexpected behavioral scores format in {filepath}")

def merge_data(metrics: List[Dict[str, Any]], scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """Merge metrics and scores, filtering out subjects without scores."""
    merged = []
    for m in metrics:
        sub_id = m.get('subject_id')
        if sub_id and sub_id in scores:
            m['fluid_intelligence'] = scores[sub_id]
            merged.append(m)
    return merged

def generate_scatter_plot(
    data: List[Dict[str, Any]],
    x_metric: str,
    y_metric: str = 'fluid_intelligence',
    title: Optional[str] = None,
    filename: Optional[str] = None
) -> str:
    """
    Generate a scatter plot with regression line and confidence interval.
    
    Returns the path to the saved figure.
    """
    # Extract data
    x_vals = [float(d[x_metric]) for d in data]
    y_vals = [float(d[y_metric]) for d in data]

    if len(x_vals) < 2:
        raise ValueError(f"Not enough data points to generate plot for {x_metric}")

    # Setup plot
    plt.figure(figsize=(10, 8))
    sns.set(style="whitegrid")
    
    # Create scatter plot with regression line and 95% CI
    # Using regplot which automatically calculates and plots the confidence interval
    sns.regplot(
        x=x_vals, 
        y=y_vals, 
        scatter_kws={'s': 80, 'edgecolor': 'w', 'alpha': 0.7},
        line_kws={'color': 'red', 'linewidth': 2},
        ci=95
    )

    # Labels and Title
    plt.xlabel(x_metric.replace('_', ' ').title(), fontsize=12)
    plt.ylabel(y_metric.replace('_', ' ').title(), fontsize=12)
    
    if title:
        plt.title(title, fontsize=14, fontweight='bold')
    else:
        plt.title(f"{x_metric.replace('_', ' ').title()} vs {y_metric.replace('_', ' ').title()}", fontsize=14, fontweight='bold')

    # Calculate and annotate correlation stats
    correlation, p_value = stats.pearsonr(x_vals, y_vals)
    n = len(x_vals)
    r_squared = correlation ** 2
    
    annotation = (
        f"N = {n}\n"
        f"r = {correlation:.3f}\n"
        f"p = {p_value:.3f}\n"
        f"R² = {r_squared:.3f}"
    )
    
    plt.text(
        0.05, 0.95, annotation,
        transform=plt.gca().transAxes,
        fontsize=11,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )

    plt.tight_layout()
    
    if not filename:
        filename = f"scatter_{x_metric}_vs_{y_metric}.png"
    
    save_path = FIGURES_DIR / filename
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(save_path)

def main():
    """Main entry point for generating scatter plots."""
    print("Starting scatter plot generation (T033)...")

    # Paths
    metrics_path = PROCESSED_DIR / "graph_metrics.csv"
    # Assuming behavioral scores are stored in a JSON file generated by T014/T030
    # Common pattern in this project is data/processed/<name>.json
    scores_path = PROCESSED_DIR / "behavioral_scores.json"
    
    # Fallback check for scores path if standard name doesn't exist
    if not scores_path.exists():
        # Try to find any json file with scores in processed
        possible_scores = list(PROCESSED_DIR.glob("*scores*.json"))
        if possible_scores:
            scores_path = possible_scores[0]
            print(f"Found behavioral scores at alternative path: {scores_path}")
        else:
            raise FileNotFoundError(
                f"Could not find behavioral scores file. Expected: {scores_path}. "
                "Please ensure T014/T030 has generated the scores file."
            )

    # Load data
    print(f"Loading graph metrics from {metrics_path}...")
    raw_metrics = load_graph_metrics(metrics_path)
    
    print(f"Loading behavioral scores from {scores_path}...")
    scores = load_behavioral_scores(scores_path)

    # We need to reshape data for plotting: one row per subject per metric?
    # The graph_metrics.csv likely has rows: [subject_id, metric_name, value, ...]
    # We need to pivot this to: [subject_id, metric_a, metric_b, ..., fluid_intelligence]
    
    # Pivot logic
    subjects = {}
    for row in raw_metrics:
        sid = row['subject_id']
        metric_name = row['metric_name']
        value = float(row['value'])
        
        if sid not in subjects:
            subjects[sid] = {'subject_id': sid}
        subjects[sid][metric_name] = value

    # Merge with scores
    merged_list = []
    for sid, data in subjects.items():
        if sid in scores:
            data['fluid_intelligence'] = scores[sid]
            merged_list.append(data)

    if not merged_list:
        raise ValueError("No subjects found with both graph metrics and behavioral scores.")

    print(f"Merged {len(merged_list)} subjects for analysis.")

    # Identify metrics to plot
    # We look for columns that are not 'subject_id' or 'fluid_intelligence'
    # and have numeric values.
    sample_row = merged_list[0]
    metric_columns = [k for k in sample_row.keys() if k not in ('subject_id', 'fluid_intelligence')]

    if not metric_columns:
        raise ValueError("No graph metric columns found in the merged data.")

    print(f"Generating plots for metrics: {metric_columns}")

    generated_files = []
    
    for metric in metric_columns:
        try:
            plot_path = generate_scatter_plot(
                data=merged_list,
                x_metric=metric,
                y_metric='fluid_intelligence',
                title=f"Correlation: {metric} vs Fluid Intelligence"
            )
            generated_files.append(plot_path)
            print(f"Generated: {plot_path}")
        except Exception as e:
            print(f"Error generating plot for {metric}: {e}")
            # Continue to next metric instead of failing the whole script

    print(f"Scatter plot generation complete. {len(generated_files)} plots saved to {FIGURES_DIR}")
    return generated_files

if __name__ == "__main__":
    main()