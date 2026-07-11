import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from typing import Optional, Tuple

# Ensure we can import from the project root if run as a script
# The execution environment usually sets up the path, but we handle it just in case.
# No external imports beyond standard libs and pinned deps.

def calculate_confidence_interval(
    x: np.ndarray,
    y: np.ndarray,
    confidence: float = 0.95
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculates the 95% confidence interval for the regression line.
    
    Returns:
      x_sorted: Sorted x values
      y_pred: Predicted y values
      ci_lower: Lower bound of CI
      ci_upper: Upper bound of CI
    """
    # Fit linear regression for the line
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Sort x for plotting
    x_sorted = np.sort(x)
    
    # Predicted values
    y_pred = slope * x_sorted + intercept
    
    # Calculate confidence interval
    # Standard error of the estimate
    n = len(x)
    mse = np.sum((y - (slope * x + intercept))**2) / (n - 2)
    
    # Standard error of the prediction
    # SE = sqrt( MSE * (1/n + (x - x_mean)^2 / sum((x - x_mean)^2)) )
    x_mean = np.mean(x)
    ss_x = np.sum((x - x_mean)**2)
    
    # t-statistic for 95% CI
    t_crit = stats.t.ppf((1 + confidence) / 2, df=n - 2)
    
    ci_lower = []
    ci_upper = []
    
    for xi in x_sorted:
        se_pred = np.sqrt(mse * (1/n + (xi - x_mean)**2 / ss_x))
        margin = t_crit * se_pred
        ci_lower.append(y_pred[np.where(x_sorted == xi)[0][0]] - margin)
        ci_upper.append(y_pred[np.where(x_sorted == xi)[0][0]] + margin)
        
    return x_sorted, y_pred, np.array(ci_lower), np.array(ci_upper)

def generate_scatter_plot(
    input_path: str,
    output_path: str,
    x_col: str = 'clustering_coefficient',
    y_col: str = 'entrainment_metric',
    title: str = 'Network Topology vs Entrainment Strength'
) -> None:
    """
    Generates a scatter plot with 95% confidence intervals.
    
    Args:
        input_path: Path to the CSV containing the data.
        output_path: Path to save the PNG.
        x_col: Column name for the topology metric (x-axis).
        y_col: Column name for the entrainment metric (y-axis).
        title: Plot title.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # Filter out NaNs to ensure clean plotting
    df_clean = df[[x_col, y_col]].dropna()
    
    if len(df_clean) < 3:
        raise ValueError(f"Insufficient data points for regression (N={len(df_clean)}).")
        
    x = df_clean[x_col].values
    y = df_clean[y_col].values
    
    # Calculate regression and CI
    x_sorted, y_pred, ci_lower, ci_upper = calculate_confidence_interval(x, y)
    
    # Plotting
    plt.figure(figsize=(10, 8))
    
    # Scatter points
    plt.scatter(x, y, alpha=0.6, color='blue', label='Subjects', edgecolors='black', s=60)
    
    # Regression line
    plt.plot(x_sorted, y_pred, color='red', linewidth=2, label='Regression Line')
    
    # Confidence interval band
    plt.fill_between(x_sorted, ci_lower, ci_upper, color='red', alpha=0.2, label='95% Confidence Interval')
    
    # Labels and Title
    plt.xlabel('Clustering Coefficient', fontsize=12)
    plt.ylabel('Entrainment Strength', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Plot saved to {output_path}")

def generate_sensitivity_bar_chart(
    input_path: str,
    output_path: str,
    baseline_atlas: str = 'Schaefer',
    comparison_atlases: list = None
) -> None:
    """
    Generates a comparative bar chart showing the absolute difference in effect sizes
    between the primary baseline atlas and alternative atlases.
    
    Args:
        input_path: Path to the CSV containing sensitivity analysis results.
        output_path: Path to save the PNG.
        baseline_atlas: Name of the baseline atlas (default: 'Schaefer').
        comparison_atlases: List of atlas names to compare against baseline.
    """
    if comparison_atlases is None:
        comparison_atlases = ['AAL', 'Power 264']
        
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # Expected columns based on T026 output: atlas, effect_size (or r_value)
    # We assume the CSV has columns: 'atlas', 'r_value' (or 'effect_size')
    # Let's check for 'r_value' first, then 'effect_size'
    if 'r_value' in df.columns:
        effect_col = 'r_value'
    elif 'effect_size' in df.columns:
        effect_col = 'effect_size'
    else:
        raise ValueError(f"Input CSV must contain 'r_value' or 'effect_size' column. Found: {df.columns.tolist()}")
        
    # Get baseline effect size
    baseline_row = df[df['atlas'] == baseline_atlas]
    if baseline_row.empty:
        raise ValueError(f"Baseline atlas '{baseline_atlas}' not found in data. Available: {df['atlas'].unique()}")
    baseline_effect = baseline_row[effect_col].values[0]
    
    # Prepare data for plotting
    labels = []
    values = []
    
    for atlas in comparison_atlases:
        atlas_row = df[df['atlas'] == atlas]
        if atlas_row.empty:
            # If an atlas is missing, we can either skip or handle as error.
            # For robustness, we'll skip and log, but the task requires exactly two bars.
            # We'll raise an error if the required atlases are missing to ensure correctness.
            raise ValueError(f"Comparison atlas '{atlas}' not found in data. Available: {df['atlas'].unique()}")
        
        atlas_effect = atlas_row[effect_col].values[0]
        diff = abs(atlas_effect - baseline_effect)
        labels.append(f"{atlas} Diff")
        values.append(diff)
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    # Create bars
    bars = plt.bar(labels, values, color=['steelblue', 'darkorange'], edgecolor='black', linewidth=1.2)
    
    # Add numeric values in the title as per FR-010, SC-002
    # Format: "Sensitivity Analysis: AAL Diff = X.XX, Power Diff = X.XX"
    title_text = f"Sensitivity Analysis: AAL Diff = {values[0]:.4f}, Power Diff = {values[1]:.4f}"
    plt.title(title_text, fontsize=14, pad=20)
    
    # Labels
    plt.xlabel('Atlas Comparison', fontsize=12)
    plt.ylabel('Absolute Difference in Effect Size (|r - r_baseline|)', fontsize=12)
    plt.ylim(0, max(values) * 1.2 if max(values) > 0 else 1.0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Sensitivity comparison plot saved to {output_path}")

def main():
    """
    Main entry point for generating the sensitivity comparison bar chart.
    Reads from data/processed/sensitivity_results.csv and saves to data/visualizations/sensitivity_comparison.png
    """
    # Paths based on project structure
    input_csv = "data/processed/sensitivity_results.csv"
    output_png = "data/visualizations/sensitivity_comparison.png"
    
    try:
        generate_sensitivity_bar_chart(
            input_path=input_csv,
            output_path=output_png,
            baseline_atlas='Schaefer',
            comparison_atlases=['AAL', 'Power 264']
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except ValueError as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()