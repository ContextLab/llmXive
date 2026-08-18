"""
Main visualization module.
"""
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from visualization.plots import generate_scatter_plots, generate_importance_plot

def run_visualization(data_path: str, metrics_path: str, output_dir: str):
    """Run all visualization tasks."""
    data = pd.read_csv(data_path)
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate scatter plots
    generate_scatter_plots(data, output_path)
    
    # Generate importance plot
    if 'rf_results' in metrics and 'feature_importance' in metrics['rf_results']:
        generate_importance_plot(metrics['rf_results']['feature_importance'], output_path)

def main():
    """Main entry point for visualization."""
    # Default paths
    data_path = "data/processed/cleaned_data.csv"
    metrics_path = "data/results/model_metrics.json"
    output_dir = "data/results/plots"
    
    if os.path.exists(data_path) and os.path.exists(metrics_path):
        run_visualization(data_path, metrics_path, output_dir)
        print("Visualization complete.")
    else:
        print("Required data files not found.")