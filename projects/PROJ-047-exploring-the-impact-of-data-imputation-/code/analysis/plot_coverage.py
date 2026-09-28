import os
import sys
import argparse
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

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
    
    return df

def run_regression_test(df: pd.DataFrame) -> Dict[str, float]:
    """
    Run linear regression of coverage rate vs beta.
    
    Returns:
        Dictionary with slope, intercept, r_value, p_value, std_err
    """
    # Aggregate coverage by beta
    agg_df = df.groupby('beta').agg({
        'coverage_rate': 'mean'
    }).reset_index()
    
    if len(agg_df) < 2:
        return {
            'slope': 0.0,
            'intercept': 0.0,
            'r_value': 0.0,
            'p_value': 1.0,
            'std_err': 0.0
        }
    
    x = agg_df['beta'].values
    y = agg_df['coverage_rate'].values
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'r_value': float(r_value),
        'p_value': float(p_value),
        'std_err': float(std_err)
    }

def plot_coverage_vs_beta(df: pd.DataFrame, output_path: str, regression_results: Dict[str, float]) -> None:
    """Generate and save the coverage vs beta plot."""
    # Aggregate coverage by beta
    agg_df = df.groupby('beta').agg({
        'coverage_rate': ['mean', 'std']
    }).reset_index()
    agg_df.columns = ['beta', 'mean_coverage', 'std_coverage']
    
    plt.figure(figsize=(10, 6))
    
    # Plot mean coverage with error bars
    plt.errorbar(
        agg_df['beta'],
        agg_df['mean_coverage'],
        yerr=agg_df['std_coverage'],
        fmt='o-',
        capsize=5,
        label='Mean Coverage Rate',
        color='green',
        linewidth=2,
        markersize=8
    )
    
    # Add trend line
    z = np.polyfit(agg_df['beta'], agg_df['mean_coverage'], 1)
    p = np.poly1d(z)
    plt.plot(
        agg_df['beta'],
        p(agg_df['beta']),
        "--",
        color='red',
        alpha=0.7,
        label=f'Trend (slope={z[0]:.3f}, p={regression_results["p_value"]:.4f})'
    )
    
    plt.xlabel('Beta (MNAR Parameter)', fontsize=12)
    plt.ylabel('Mean Coverage Rate', fontsize=12)
    plt.title('Coverage Rate vs Beta: Impact of MNAR Mechanism Strength', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.ylim(0, 1.1)  # Coverage rate should be between 0 and 1
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Plot saved to: {output_path}")

def save_regression_results(regression_results: Dict[str, float], output_path: str) -> None:
    """Save regression test results to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(regression_results, f, indent=2)
    
    print(f"Regression results saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate coverage vs beta plot from simulation results')
    parser.add_argument('--input', type=str, default='data/results/simulation_summary.csv',
                      help='Path to input CSV file')
    parser.add_argument('--output', type=str, default='docs/paper/coverage_vs_beta.pdf',
                      help='Path for output PDF file')
    parser.add_argument('--regression-output', type=str, default='docs/paper/coverage_regression.json',
                      help='Path for regression results JSON file')
    
    args = parser.parse_args()
    
    try:
        # Load and prepare data
        df = load_and_prepare_data(args.input)
        
        # Run regression test
        regression_results = run_regression_test(df)
        
        # Generate and save plot
        plot_coverage_vs_beta(df, args.output, regression_results)
        
        # Save regression results
        save_regression_results(regression_results, args.regression_output)
        
    except Exception as e:
        print(f"Error generating plot: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
