"""
Visualization module for generating plots.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Import configuration
from config import RANDOM_SEED
from logging_config import log_pipeline_start, log_pipeline_end, log_operation

np.random.seed(RANDOM_SEED)

def generate_scatter_plot(df, x_col, y_col, output_path):
    """
    Generate a scatter plot.
    
    Args:
        df: DataFrame
        x_col: X-axis column name
        y_col: Y-axis column name
        output_path: Path to save the plot
    """
    plt.figure(figsize=(10, 6))
    
    # Create scatter plot
    sns.scatterplot(data=df, x=x_col, y=y_col, alpha=0.6)
    
    # Add labels and title
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f'{x_col} vs {y_col}')
    
    # Add regression line
    sns.regplot(data=df, x=x_col, y=y_col, scatter=False, color='red')
    
    # Save plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    log_operation("generate_scatter_plot", output=str(output_path))

def generate_histogram_plot(df, col, output_path):
    """
    Generate a histogram plot.
    
    Args:
        df: DataFrame
        col: Column name
        output_path: Path to save the plot
    """
    plt.figure(figsize=(10, 6))
    
    # Create histogram
    sns.histplot(data=df, x=col, kde=True)
    
    # Add labels and title
    plt.xlabel(col)
    plt.ylabel('Frequency')
    plt.title(f'Distribution of {col}')
    
    # Save plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    log_operation("generate_histogram_plot", output=str(output_path))

def run_visualization_pipeline():
    """Run the visualization pipeline."""
    log_pipeline_start("visualization_pipeline")
    
    try:
        # Load data
        df = pd.read_csv("data/processed/cleaned_data.csv")
        
        # Create output directory
        output_dir = Path("data/processed/plots")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate scatter plot
        if 'shannon_index' in df.columns and 'fluid_intelligence_score' in df.columns:
            scatter_path = output_dir / "scatter_shannon_fi.png"
            generate_scatter_plot(df, 'shannon_index', 'fluid_intelligence_score', scatter_path)
        
        # Generate histograms
        for col in ['shannon_index', 'fluid_intelligence_score']:
            if col in df.columns:
                hist_path = output_dir / f"histogram_{col}.png"
                generate_histogram_plot(df, col, hist_path)
        
        log_pipeline_end("visualization_pipeline", status="success")
        
    except Exception as e:
        log_pipeline_end("visualization_pipeline", status="failed", error=str(e))
        raise

def main():
    """Main entry point for visualization."""
    run_visualization_pipeline()

if __name__ == "__main__":
    main()
