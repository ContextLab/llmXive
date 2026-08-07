"""
Plotting script for T042a: Generate bias_vs_beta.png.

Reads aggregated results from data/results/simulation_summary.csv
and produces a publication-quality plot showing the relationship
between the MNAR parameter (beta) and absolute bias.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Ensure the parent directory is in the path so we can import analysis modules
# This is necessary when running as a script from the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analysis.schema_validator import validate_schema

REQUIRED_COLUMNS = {
    'beta',
    'method',
    'estimator',
    'ate',
    'bias',
    'ground_truth_ate',
    'status'
}

def load_and_prepare_data(input_path: str) -> pd.DataFrame:
    """
    Load the simulation summary CSV and prepare it for plotting.
    
    Args:
        input_path: Path to simulation_summary.csv
        
    Returns:
        Cleaned DataFrame ready for aggregation and plotting
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Validate schema
    validate_schema(df, REQUIRED_COLUMNS)
    
    # Filter out failed runs
    df = df[df['status'] == 'success'].copy()
    
    if df.empty:
        raise ValueError("No successful runs found in the input data.")
    
    # Calculate absolute bias if not already present (ensure sign doesn't matter for trend)
    if 'abs_bias' not in df.columns:
        df['abs_bias'] = df['bias'].abs()
    
    return df

def aggregate_bias_by_beta(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate absolute bias by beta level and method.
    
    Args:
        df: Input DataFrame with bias data
        
    Returns:
        Aggregated DataFrame with mean bias per beta/method
    """
    agg_df = df.groupby(['beta', 'method'], as_index=False).agg(
        mean_abs_bias=('abs_bias', 'mean'),
        std_abs_bias=('abs_bias', 'std'),
        count=('abs_bias', 'count')
    )
    
    # Calculate 95% CI for the mean (using t-distribution)
    def calc_ci(group):
        n = len(group['abs_bias'])
        if n < 2:
            return (0, 0)
        mean = group['abs_bias'].mean()
        sem = group['abs_bias'].std() / np.sqrt(n)
        ci = sem * stats.t.ppf(0.975, n-1)
        return (mean - ci, mean + ci)
    
    ci_bounds = df.groupby(['beta', 'method']).apply(calc_ci)
    agg_df['ci_lower'] = ci_bounds.apply(lambda x: x[0])
    agg_df['ci_upper'] = ci_bounds.apply(lambda x: x[1])
    
    return agg_df

def plot_bias_vs_beta(
    agg_df: pd.DataFrame, 
    output_path: str, 
    dpi: int = 300
) -> None:
    """
    Generate and save the bias vs beta plot.
    
    Args:
        agg_df: Aggregated DataFrame with mean bias and CIs
        output_path: Path to save the output PNG
        dpi: Resolution for the output image
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sort beta values to ensure correct plotting order
    agg_df['beta'] = pd.to_numeric(agg_df['beta'])
    agg_df = agg_df.sort_values('beta')
    
    # Plot each method
    methods = agg_df['method'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(methods)))
    
    for i, method in enumerate(methods):
        subset = agg_df[agg_df['method'] == method]
        ax.errorbar(
            subset['beta'],
            subset['mean_abs_bias'],
            yerr=[
                subset['mean_abs_bias'] - subset['ci_lower'],
                subset['ci_upper'] - subset['mean_abs_bias']
            ],
            capsize=5,
            label=method.replace('_', ' ').title(),
            color=colors[i],
            marker='o',
            markersize=8,
            linewidth=2,
            ecolor=colors[i],
            elinewidth=1.5
        )
    
    # Calculate and plot Spearman correlation for the overall trend
    # We'll plot the trend for the "best" performing method or an average
    # For clarity, let's just show the data points and let the legend explain methods
    
    # Set labels and title
    ax.set_xlabel(r'$\beta$ (MNAR Mechanism Parameter)', fontsize=12)
    ax.set_ylabel('Mean Absolute Bias', fontsize=12)
    ax.set_title('Impact of MNAR Parameter on Causal Estimation Bias', fontsize=14, fontweight='bold')
    
    # Add grid for readability
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Add legend
    ax.legend(title='Imputation Method', loc='upper left', framealpha=0.9)
    
    # Add text annotation for Spearman correlation (calculated on Mean Imputation as reference)
    # This demonstrates the monotonic trend verification
    if len(agg_df) > 0:
        # Use Mean Imputation as the reference for the trend annotation
        mean_subset = agg_df[agg_df['method'] == 'mean']
        if len(mean_subset) >= 2:
            rho, p_val = stats.spearmanr(mean_subset['beta'], mean_subset['mean_abs_bias'])
            annotation = f"Spearman ρ = {rho:.3f} (p={p_val:.3g})"
            ax.text(
                0.02, 0.98, annotation,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Plot saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Generate bias vs beta plot from simulation results.'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/results/simulation_summary.csv',
        help='Path to the simulation summary CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='docs/paper/bias_vs_beta.png',
        help='Path to save the output PNG file'
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='Resolution for the output image (default: 300)'
    )
    
    args = parser.parse_args()
    
    try:
        print(f"Loading data from: {args.input}")
        df = load_and_prepare_data(args.input)
        
        print(f"Aggregating data...")
        agg_df = aggregate_bias_by_beta(df)
        
        print(f"Generating plot...")
        plot_bias_vs_beta(agg_df, args.output, args.dpi)
        
        print("Done.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
