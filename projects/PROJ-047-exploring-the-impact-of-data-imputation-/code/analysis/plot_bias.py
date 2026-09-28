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

def aggregate_bias_by_beta(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate absolute bias by beta level."""
    agg_df = df.groupby('beta').agg({
        'abs_bias': 'mean',
        'abs_bias': 'std'  # For error bars
    }).reset_index()
    agg_df.columns = ['beta', 'mean_abs_bias', 'std_abs_bias']
    return agg_df

def plot_bias_vs_beta(agg_df: pd.DataFrame, output_path: str) -> None:
    """Generate and save the bias vs beta plot."""
    plt.figure(figsize=(10, 6))
    
    # Plot mean bias with error bars
    plt.errorbar(
        agg_df['beta'],
        agg_df['mean_abs_bias'],
        yerr=agg_df['std_abs_bias'],
        fmt='o-',
        capsize=5,
        label='Mean Absolute Bias',
        color='blue',
        linewidth=2,
        markersize=8
    )
    
    # Add trend line
    z = np.polyfit(agg_df['beta'], agg_df['mean_abs_bias'], 1)
    p = np.poly1d(z)
    plt.plot(
        agg_df['beta'],
        p(agg_df['beta']),
        "--",
        color='red',
        alpha=0.7,
        label=f'Trend (slope={z[0]:.3f})'
    )
    
    plt.xlabel('Beta (MNAR Parameter)', fontsize=12)
    plt.ylabel('Mean Absolute Bias', fontsize=12)
    plt.title('Bias vs Beta: Impact of MNAR Mechanism Strength', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Plot saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate bias vs beta plot from simulation results')
    parser.add_argument('--input', type=str, default='data/results/simulation_summary.csv',
                      help='Path to input CSV file')
    parser.add_argument('--output', type=str, default='docs/paper/bias_vs_beta.png',
                      help='Path for output PNG file')
    
    args = parser.parse_args()
    
    try:
        # Load and prepare data
        df = load_and_prepare_data(args.input)
        
        # Aggregate by beta
        agg_df = aggregate_bias_by_beta(df)
        
        # Generate and save plot
        plot_bias_vs_beta(agg_df, args.output)
        
    except Exception as e:
        print(f"Error generating plot: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
