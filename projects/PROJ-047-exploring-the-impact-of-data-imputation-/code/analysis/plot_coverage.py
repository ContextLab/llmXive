import os
import sys
import argparse
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Ensure we can import from the project root if needed, though typically run from code/
# The execution environment usually sets PYTHONPATH correctly or runs from code/

def load_and_prepare_data(input_path):
    """Load simulation summary and aggregate coverage by beta."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Filter out failed runs if any status column exists and indicates failure
    if 'status' in df.columns:
        df = df[df['status'] != 'failed']
    
    # Ensure beta is numeric
    df['beta'] = pd.to_numeric(df['beta'], errors='coerce')
    df = df.dropna(subset=['beta'])
    
    # Aggregate mean coverage rate per beta level
    # Coverage rate is expected to be a column, calculate mean per beta
    if 'coverage_rate' not in df.columns:
        # If not pre-calculated, we might need to calculate it, but T029c says it's in the CSV
        # Assuming it's there as per spec
        raise ValueError("Column 'coverage_rate' not found in input data.")
    
    agg = df.groupby('beta')['coverage_rate'].mean().reset_index()
    agg = agg.sort_values('beta')
    
    return agg

def run_regression_test(agg_df):
    """
    Perform linear regression of coverage_rate vs beta.
    Returns slope, intercept, r_value, p_value, std_err.
    We expect a negative slope (coverage decreases as missingness bias beta increases).
    """
    x = agg_df['beta'].values
    y = agg_df['coverage_rate'].values
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_value': r_value,
        'p_value': p_value,
        'std_err': std_err,
        'negative_slope_confirmed': slope < 0,
        'p_value_significant': p_value < 0.05
    }

def plot_coverage_vs_beta(agg_df, output_path, regression_results):
    """
    Plot coverage rate vs beta, annotate with regression stats.
    Saves as PDF.
    """
    plt.figure(figsize=(10, 6))
    
    x = agg_df['beta'].values
    y = agg_df['coverage_rate'].values
    
    plt.scatter(x, y, color='blue', label='Mean Coverage Rate', zorder=3)
    
    # Plot regression line
    slope = regression_results['slope']
    intercept = regression_results['intercept']
    x_line = np.array([min(x), max(x)])
    y_line = slope * x_line + intercept
    plt.plot(x_line, y_line, color='red', linestyle='--', label=f'Regression (slope={slope:.3f})')
    
    plt.xlabel(r'Missingness Mechanism Parameter $\beta$')
    plt.ylabel('Mean Coverage Rate')
    plt.title('Coverage Rate vs Missingness Parameter $\beta$')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1.1) # Coverage is a probability 0-1
    
    # Add text annotation with p-value for the slope test
    # We are testing if slope < 0. The p-value from linregress is for two-tailed.
    # For one-tailed (negative), if r is negative, p_one_tailed = p_two_tailed / 2
    p_val = regression_results['p_value']
    if slope < 0:
        p_one_tailed = p_val / 2
    else:
        p_one_tailed = 1 - (p_val / 2)
    
    annotation_text = (
        f"Slope: {slope:.4f}\n"
        f"p-value (slope): {p_val:.4f}\n"
        f"One-tailed p (negative): {p_one_tailed:.4f}\n"
        f"Negative slope confirmed: {regression_results['negative_slope_confirmed']}"
    )
    
    plt.figtext(0.98, 0.02, annotation_text, ha='right', va='bottom', 
                fontsize=9, bbox=dict(facecolor='white', alpha=0.8, boxstyle='round'))
    
    plt.tight_layout()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, format='pdf')
    plt.close()

def save_regression_results(regression_results, json_path):
    """Save regression test results to JSON."""
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(regression_results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Plot coverage rate vs beta and verify negative slope.')
    parser.add_argument('--input', type=str, required=True, 
                        help='Path to data/results/simulation_summary.csv')
    parser.add_argument('--output', type=str, required=True, 
                        help='Path to output PDF (e.g., docs/paper/coverage_vs_beta.pdf)')
    parser.add_argument('--json-output', type=str, 
                        default='docs/paper/coverage_regression.json',
                        help='Path to output JSON with regression results')
    
    args = parser.parse_args()
    
    print(f"Loading data from {args.input}...")
    agg_df = load_and_prepare_data(args.input)
    
    print(f"Running regression test...")
    regression_results = run_regression_test(agg_df)
    
    print(f"Plotting to {args.output}...")
    plot_coverage_vs_beta(agg_df, args.output, regression_results)
    
    print(f"Saving regression results to {args.json_output}...")
    save_regression_results(regression_results, args.json_output)
    
    print("Done.")

if __name__ == '__main__':
    main()
