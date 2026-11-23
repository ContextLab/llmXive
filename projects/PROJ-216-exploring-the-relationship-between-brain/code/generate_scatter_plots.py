import os
import sys
import csv
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Ensure plots directory exists
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

def load_graph_metrics(csv_path: str = "data/processed/graph_metrics.csv") -> pd.DataFrame:
    """
    Load graph metrics from CSV.
    Expects columns: subject_id, metric_name, value, cohens_d, ci_lower, ci_upper
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Graph metrics file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    return df

def load_behavioral_scores(json_path: str = "data/processed/behavioral_scores.json") -> Dict[str, float]:
    """
    Load behavioral scores (Fluid Intelligence) from JSON.
    Returns dict: {subject_id: score_value}
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Behavioral scores file not found: {json_path}")
    with open(json_path, 'r') as f:
        data = json.load(f)
    # Assuming structure: [{"subject_id": "sub-01", "score_value": 12.5}, ...]
    scores = {}
    for item in data:
        if "subject_id" in item and "score_value" in item:
            scores[item["subject_id"]] = item["score_value"]
    return scores

def merge_data(metrics_df: pd.DataFrame, scores_dict: Dict[str, float], metric_name: str = "global_efficiency") -> pd.DataFrame:
    """
    Merge metrics with behavioral scores for a specific metric.
    """
    # Filter for the specific metric
    metric_df = metrics_df[metrics_df['metric_name'] == metric_name].copy()
    
    # Add scores
    metric_df['fluid_intelligence'] = metric_df['subject_id'].map(scores_dict)
    
    # Drop rows with missing scores
    metric_df = metric_df.dropna(subset=['fluid_intelligence'])
    
    return metric_df

def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    x_label: str,
    y_label: str,
    output_path: str
) -> None:
    """
    Generate and save a scatter plot with regression line.
    """
    plt.figure(figsize=(10, 8))
    sns.set_style("whitegrid")
    
    # Create scatter plot with regression line
    sns.regplot(
        data=data,
        x=x_col,
        y=y_col,
        scatter_kws={'s': 80, 'alpha': 0.7, 'edgecolor': 'black'},
        line_kws={'color': 'red', 'linestyle': '--'}
    )
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    
    # Add grid for better readability
    plt.grid(True, alpha=0.3)
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Scatter plot saved to: {output_path}")

def main():
    """
    Main entry point to generate scatter plots for significant correlations.
    Specifically implements T033b: Save scatter plot to reports/scatter_metric_vs_fluid.png
    """
    # Load data
    print("Loading graph metrics...")
    metrics_df = load_graph_metrics()
    
    print("Loading behavioral scores...")
    scores_dict = load_behavioral_scores()
    
    if metrics_df.empty:
        print("ERROR: No graph metrics found.")
        sys.exit(1)
        
    if not scores_dict:
        print("ERROR: No behavioral scores found.")
        sys.exit(1)

    # Identify significant metrics (we'll plot the first one found or a default)
    # In a full implementation, we would read from stats.py results
    # For T033b, we assume 'global_efficiency' is the primary metric of interest
    # based on typical neuroimaging studies.
    metric_to_plot = "global_efficiency"
    
    if metric_to_plot not in metrics_df['metric_name'].values:
        # Fallback to any available metric if the specific one isn't there
        available_metrics = metrics_df['metric_name'].unique()
        if len(available_metrics) > 0:
            metric_to_plot = available_metrics[0]
            print(f"Note: '{metric_to_plot}' not found. Using '{metric_to_plot}' instead.")
        else:
            print("ERROR: No metrics available to plot.")
            sys.exit(1)

    # Merge data
    print(f"Merging data for metric: {metric_to_plot}")
    merged_df = merge_data(metrics_df, scores_dict, metric_to_plot)
    
    if merged_df.empty:
        print(f"ERROR: No matching data found for metric '{metric_to_plot}' and behavioral scores.")
        sys.exit(1)

    # Generate plot
    output_path = str(REPORTS_DIR / "scatter_metric_vs_fluid.png")
    
    generate_scatter_plot(
        data=merged_df,
        x_col="fluid_intelligence",
        y_col="value",
        title=f"Relationship between {metric_to_plot.replace('_', ' ').title()} and Fluid Intelligence",
        x_label="Fluid Intelligence Score",
        y_label=f"{metric_to_plot.replace('_', ' ').title()}",
        output_path=output_path
    )
    
    print("Task T033b completed successfully.")

if __name__ == "__main__":
    main()