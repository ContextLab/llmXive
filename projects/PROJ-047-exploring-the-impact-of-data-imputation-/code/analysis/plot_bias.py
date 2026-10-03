import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional, Dict, Any
from scipy import stats

def load_and_prepare_data(input_path: str) -> pd.DataFrame:
    """Load simulation summary and prepare for bias plotting."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Filter out failed runs
    if 'status' in df.columns:
        df = df[df['status'] != 'failed']
    
    # Ensure numeric types
    numeric_cols = ['beta', 'bias', 'rmse', 'ate']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def aggregate_bias_by_beta(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate bias by beta level."""
    if 'method' in df.columns and 'estimator' in df.columns:
        # Group by beta, method, and estimator
        agg_df = df.groupby(['beta', 'method', 'estimator'])['bias'].mean().reset_index()
    else:
        # Group only by beta
        agg_df = df.groupby('beta')['bias'].mean().reset_index()
    
    return agg_df

def plot_bias_vs_beta(agg_df: pd.DataFrame, output_path: str):
    """Plot bias vs beta with error bars."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    
    if 'method' in agg_df.columns and 'estimator' in agg_df.columns:
        # Plot by method and estimator
        methods = agg_df['method'].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(methods)))
        
        for i, method in enumerate(methods):
            method_df = agg_df[agg_df['method'] == method]
            plt.errorbar(
                method_df['beta'], 
                method_df['bias'],
                yerr=method_df.groupby('beta')['bias'].std(),
                label=method,
                marker='o',
                color=colors[i],
                capsize=5
            )
    else:
        # Simple plot
        plt.errorbar(
            agg_df['beta'], 
            agg_df['bias'],
            yerr=agg_df.groupby('beta')['bias'].std(),
            label='Mean Bias',
            marker='o',
            capsize=5
        )
    
    plt.xlabel('Beta (MNAR Intensity)')
    plt.ylabel('Absolute Bias')
    plt.title('Absolute Bias vs MNAR Intensity (Beta)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Plot bias vs beta')
    parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    parser.add_argument('--output', type=str, required=True, help='Path to output PNG')
    
    args = parser.parse_args()
    
    # Load data
    df = load_and_prepare_data(args.input)
    
    # Aggregate
    agg_df = aggregate_bias_by_beta(df)
    
    # Plot
    plot_bias_vs_beta(agg_df, args.output)
    
    print(f"Bias plot saved to {args.output}")

if __name__ == '__main__':
    main()
