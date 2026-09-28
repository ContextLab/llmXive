import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ensure the docs/paper directory exists
os.makedirs('docs/paper', exist_ok=True)

def load_and_prepare_data(input_path: str) -> pd.DataFrame:
    """Load simulation summary and prepare data for plotting."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Filter out failed runs if any
    if 'status' in df.columns:
        df = df[df['status'] != 'failed']
    
    # Calculate absolute bias if not present
    if 'bias' in df.columns:
        df['abs_bias'] = df['bias'].abs()
    else:
        raise ValueError("Input data must contain 'bias' column")
    
    return df

def plot_bias_distributions(df: pd.DataFrame, output_path: str) -> None:
    """Generate and save the bias distribution plot."""
    plt.figure(figsize=(12, 8))
    
    # Get unique beta values
    betas = sorted(df['beta'].unique())
    
    # Create subplots for each beta level
    n_betas = len(betas)
    cols = min(3, n_betas)
    rows = (n_betas + cols - 1) // cols
    
    for i, beta in enumerate(betas):
        plt.subplot(rows, cols, i+1)
        
        # Filter data for this beta
        beta_data = df[df['beta'] == beta]
        
        # Plot histogram of absolute bias
        plt.hist(beta_data['abs_bias'], bins=20, alpha=0.7, edgecolor='black')
        
        # Add mean line
        mean_bias = beta_data['abs_bias'].mean()
        plt.axvline(mean_bias, color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {mean_bias:.4f}')
        
        plt.xlabel('Absolute Bias')
        plt.ylabel('Frequency')
        plt.title(f'Beta = {beta}')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    plt.suptitle('Distribution of Absolute Bias by Beta Level', fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Plot saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate bias distribution plots from simulation results')
    parser.add_argument('--input', type=str, default='data/results/simulation_summary.csv',
                      help='Path to input CSV file')
    parser.add_argument('--output', type=str, default='docs/paper/bias_distributions.png',
                      help='Path for output PNG file')
    
    args = parser.parse_args()
    
    try:
        # Load and prepare data
        df = load_and_prepare_data(args.input)
        
        # Generate and save plot
        plot_bias_distributions(df, args.output)
        
    except Exception as e:
        print(f"Error generating plot: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
