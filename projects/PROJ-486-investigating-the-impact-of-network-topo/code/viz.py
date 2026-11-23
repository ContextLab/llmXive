import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from typing import Optional, Tuple

# Ensure directory existence
def ensure_dir(path: str) -> None:
    """Ensure the directory for the given path exists."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

# Confidence Interval Calculation
def calculate_confidence_interval(
    x: np.ndarray, y: np.ndarray, confidence: float = 0.95
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate parametric 95% confidence intervals for a linear fit.
    Uses t-distribution on residuals.
    """
    # Fit linear model
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Predictions
    y_pred = slope * x + intercept
    
    # Residuals
    residuals = y - y_pred
    n = len(x)
    dof = n - 2
    
    if dof <= 0:
        # Not enough points for CI
        return y_pred, y_pred
    
    # Standard error of the estimate
    s_res = np.sqrt(np.sum(residuals**2) / dof)
    
    # t-value for confidence interval
    t_val = stats.t.ppf((1 + confidence) / 2, dof)
    
    # Standard error of the prediction
    # SE = s_res * sqrt(1/n + (x - x_mean)^2 / sum((x - x_mean)^2))
    x_mean = np.mean(x)
    ss_x = np.sum((x - x_mean)**2)
    
    if ss_x == 0:
        # All x values are the same
        se_pred = s_res * np.sqrt(1 + 1/n)
    else:
        se_pred = s_res * np.sqrt(1 + 1/n + (x - x_mean)**2 / ss_x)
    
    margin = t_val * se_pred
    
    lower = y_pred - margin
    upper = y_pred + margin
    
    return lower, upper

# Scatter Plot Generation
def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    title: str = "Topology vs Entrainment",
    xlabel: str = "Topology Metric",
    ylabel: str = "Entrainment Metric",
    ci: float = 0.95
) -> None:
    """
    Generate a scatter plot with 95% confidence intervals.
    """
    ensure_dir(output_path)
    
    x = data[x_col].values
    y = data[y_col].values
    
    # Sort by x for smooth CI line
    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    y_sorted = y[sort_idx]
    
    lower, upper = calculate_confidence_interval(x_sorted, y_sorted, confidence=ci)
    
    plt.figure(figsize=(10, 6))
    plt.scatter(x_sorted, y_sorted, alpha=0.6, label='Data Points', edgecolors='k')
    plt.plot(x_sorted, lower, 'r--', linewidth=1.5, label='95% CI')
    plt.plot(x_sorted, upper, 'r--', linewidth=1.5)
    
    # Add regression line
    slope, intercept, _, _, _ = stats.linregress(x_sorted, y_sorted)
    plt.plot(x_sorted, slope * x_sorted + intercept, 'g-', linewidth=2, label='Linear Fit')
    
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

# Sensitivity Bar Chart Generation (T027)
def generate_sensitivity_bar_chart(
    input_path: str,
    output_path: str,
    baseline_atlas: str = "Schaefer"
) -> None:
    """
    Generate a comparative bar chart showing absolute difference in effect sizes
    between the primary Schaefer baseline and alternative atlases (AAL, Power).
    
    Input: data/processed/sensitivity_aggregated.csv
    Output: data/visualizations/sensitivity_comparison.png
    
    Requirements:
    - Exactly two bars: "AAL Diff" and "Power Diff"
    - Numeric values in title: "Sensitivity Analysis: AAL Diff: {val:.3f}, Power Diff: {val:.3f}"
    """
    ensure_dir(output_path)
    
    # Load data
    df = pd.read_csv(input_path)
    
    # Validate columns
    required_cols = ['atlas_type', 'effect_size', 'absolute_diff']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input CSV must contain columns: {required_cols}")
    
    # Filter for non-baseline atlases (AAL and Power)
    # We assume the baseline is the first entry or explicitly named Schaefer
    baseline_mask = df['atlas_type'] == baseline_atlas
    if baseline_mask.sum() == 0:
        raise ValueError(f"Baseline atlas '{baseline_atlas}' not found in data.")
    
    baseline_effect = df.loc[baseline_mask, 'effect_size'].iloc[0]
    
    # Calculate absolute differences if not present (though task T027a says it's calculated)
    # Just in case, we recalculate to be safe based on the spec logic
    df['calculated_diff'] = (df['effect_size'] - baseline_effect).abs()
    
    # Select rows for AAL and Power
    alt_atlases = ["AAL", "Power"]
    alt_df = df[df['atlas_type'].isin(alt_atlases)].copy()
    
    if len(alt_df) != 2:
        # Try to find by partial match if exact names differ slightly
        # Or raise error if data is missing
        raise ValueError(f"Expected 2 alternative atlas rows (AAL, Power), found {len(alt_df)}. Data: {alt_df['atlas_type'].tolist()}")
    
    # Sort by atlas name to ensure consistent order (AAL, then Power)
    alt_df = alt_df.sort_values('atlas_type')
    
    # Extract values
    labels = [f"{row['atlas_type']} Diff" for _, row in alt_df.iterrows()]
    values = [row['absolute_diff'] for _, row in alt_df.iterrows()]
    
    # Format title
    aal_val = values[0] if alt_df.iloc[0]['atlas_type'] == 'AAL' else values[1]
    power_val = values[1] if alt_df.iloc[0]['atlas_type'] == 'AAL' else values[0]
    
    title = f"Sensitivity Analysis: AAL Diff: {aal_val:.3f}, Power Diff: {power_val:.3f}"
    
    # Plot
    plt.figure(figsize=(8, 6))
    bars = plt.bar(labels, values, color=['#4C72B0', '#55A868'], edgecolor='black')
    
    # Add value labels on top of bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{val:.3f}',
                 ha='center', va='bottom', fontsize=12)
    
    plt.title(title, fontsize=14)
    plt.ylabel("Absolute Difference in Effect Size", fontsize=12)
    plt.ylim(bottom=0) # Ensure bars start at 0
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()

def main():
    """
    Main entry point for visualization scripts.
    Parses arguments and generates plots based on task requirements.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate research visualizations.")
    parser.add_argument("--type", type=str, required=True, 
                        choices=["scatter", "sensitivity"],
                        help="Type of plot to generate.")
    parser.add_argument("--input", type=str, required=True,
                        help="Input data file path.")
    parser.add_argument("--output", type=str, required=True,
                        help="Output image file path.")
    parser.add_argument("--x-col", type=str, default=None, help="X column for scatter plot.")
    parser.add_argument("--y-col", type=str, default=None, help="Y column for scatter plot.")
    
    args = parser.parse_args()
    
    if args.type == "scatter":
        if not args.x_col or not args.y_col:
            parser.error("--x-col and --y-col are required for scatter plots.")
        df = pd.read_csv(args.input)
        generate_scatter_plot(df, args.x_col, args.y_col, args.output)
    elif args.type == "sensitivity":
        generate_sensitivity_bar_chart(args.input, args.output)
    
    print(f"Visualization saved to {args.output}")

if __name__ == "__main__":
    main()