import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional, Dict, Any
import seaborn as sns

def load_and_prepare_data(input_path: str) -> pd.DataFrame:
    """Load simulation summary and prepare for distribution plotting."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Filter out failed runs
    if 'status' in df.columns:
        df = df[df['status'] != 'failed']
    
    # Ensure numeric types
    numeric_cols = ['beta', 'bias', 'ate']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def plot_bias_distributions(df: pd.DataFrame, output_path: str):
    """Plot bias distributions across beta levels."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    plt.figure(figsize=(12, 8))
    
    # Filter out NaN bias values
    clean_df = df.dropna(subset=['bias', 'beta'])
    
    if 'method' in clean_df.columns:
        # Create faceted plot by method
        g = sns.FacetGrid(clean_df, col='method', col_wrap=2, height=4, aspect=1.2)
        g.map_dataframe(sns.histplot, x='bias', hue='beta', bins=20, kde=True, alpha=0.6)
        g.set_axis_labels('Bias', 'Count')
        g.set_titles('{col_name}')
        g.add_legend(title='Beta')
        plt.suptitle('Bias Distributions by Method and Beta', y=1.02)
    else:
        # Simple histogram
        sns.histplot(data=clean_df, x='bias', hue='beta', bins=20, kde=True, alpha=0.6)
        plt.xlabel('Bias')
        plt.ylabel('Count')
        plt.title('Bias Distributions by Beta Level')
        plt.legend(title='Beta')
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Plot bias distributions')
    parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    parser.add_argument('--output', type=str, required=True, help='Path to output PNG')
    
    args = parser.parse_args()
    
    # Load data
    df = load_and_prepare_data(args.input)
    
    # Plot
    plot_bias_distributions(df, args.output)
    
    print(f"Bias distribution plot saved to {args.output}")

if __name__ == '__main__':
    main()