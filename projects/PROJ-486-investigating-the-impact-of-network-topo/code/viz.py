import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from typing import Optional, Tuple

def ensure_dir(directory: str) -> None:
    """Ensure the directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def calculate_confidence_interval(
    data: np.ndarray, confidence: float = 0.95
) -> Tuple[float, float]:
    """Calculate the confidence interval for a dataset."""
    if len(data) == 0:
        return 0.0, 0.0
    n = len(data)
    mean = np.mean(data)
    std_err = stats.sem(data)
    h = std_err * stats.t.ppf((1 + confidence) / 2.0, n - 1)
    return mean - h, mean + h

def generate_scatter_plot(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    output_path: str,
    title: Optional[str] = None,
) -> None:
    """Generate a scatter plot with 95% confidence intervals."""
    ensure_dir(os.path.dirname(output_path))
    
    plt.figure(figsize=(10, 8))
    
    # Calculate regression line and confidence interval
    if len(x) > 1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        x_line = np.linspace(min(x), max(x), 100)
        y_line = slope * x_line + intercept
        
        # Calculate confidence interval for the regression line
        y_pred = slope * x + intercept
        residuals = y - y_pred
        std_res = np.std(residuals, ddof=2)
        se_line = std_res * np.sqrt(1/len(x) + (x_line - np.mean(x))**2 / np.sum((x - np.mean(x))**2))
        ci_upper = y_line + 1.96 * se_line
        ci_lower = y_line - 1.96 * se_line
        
        plt.plot(x_line, y_line, 'r-', label=f'Regression (r={r_value:.3f})')
        plt.fill_between(x_line, ci_lower, ci_upper, color='red', alpha=0.2, label='95% CI')
    
    plt.scatter(x, y, alpha=0.6, edgecolors='w', linewidth=0.5)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    if title:
        plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

def generate_sensitivity_bar_chart(
    results_path: str,
    output_path: str,
    baseline_atlas: str = "Schaefer",
    comparison_atlases: Optional[list] = None,
) -> None:
    """
    Generate a comparative bar chart showing the absolute difference in effect sizes
    between the primary baseline and alternative atlases.
    
    Args:
        results_path: Path to the CSV containing correlation results for all atlases.
        output_path: Path where the PNG chart will be saved.
        baseline_atlas: The name of the baseline atlas (default: Schaefer).
        comparison_atlases: List of alternative atlas names to compare against.
    """
    if comparison_atlases is None:
        comparison_atlases = ["AAL", "Power 264"]
    
    ensure_dir(os.path.dirname(output_path))
    
    # Load results
    df = pd.read_csv(results_path)
    
    # Ensure we have the necessary columns
    required_cols = ['atlas', 'r_value', 'source']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Filter for valid data (exclude 'Simulated' if we want real comparisons, 
    # but per spec we might need to handle simulated data too)
    # The spec implies we compare effect sizes. If the data is simulated, 
    # we still compare the calculated r-values.
    
    # Calculate absolute differences for each comparison atlas
    diffs = []
    labels = []
    title_values = []
    
    # Find baseline r-value
    baseline_row = df[df['atlas'] == baseline_atlas]
    if baseline_row.empty:
        raise ValueError(f"Baseline atlas '{baseline_atlas}' not found in data.")
    baseline_r = baseline_row['r_value'].iloc[0]
    
    for atlas in comparison_atlases:
        atlas_row = df[df['atlas'] == atlas]
        if atlas_row.empty:
            # If an atlas is missing, we skip it or handle gracefully
            # For this task, we expect exactly two bars: AAL and Power
            continue
        
        atlas_r = atlas_row['r_value'].iloc[0]
        diff = abs(atlas_r - baseline_r)
        diffs.append(diff)
        labels.append(f"{atlas} Diff")
        title_values.append(f"{atlas}: {diff:.4f}")
    
    if len(diffs) == 0:
        raise ValueError("No comparison data found to generate chart.")
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    bars = plt.bar(labels, diffs, color=['#2ecc71', '#3498db'], edgecolor='black')
    
    # Add numeric values on top of bars
    for bar, diff in zip(bars, diffs):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f'{diff:.4f}',
            ha='center',
            va='bottom',
            fontsize=12,
            fontweight='bold'
        )
    
    # Set title with numeric values as requested
    title_str = "Sensitivity Analysis: Absolute Difference in Effect Sizes\n" + ", ".join(title_values)
    plt.title(title_str, fontsize=14, pad=20)
    
    plt.ylabel("Absolute Difference in r (Effect Size)", fontsize=12)
    plt.xlabel("Atlas Comparison", fontsize=12)
    plt.ylim(0, max(diffs) * 1.2 if max(diffs) > 0 else 0.1)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """
    Main entry point for visualization generation.
    Specifically for T027: Generate sensitivity comparison bar chart.
    """
    # Define paths
    results_csv = "data/processed/correlation_results.csv"
    output_png = "data/visualizations/sensitivity_comparison.png"
    
    if not os.path.exists(results_csv):
        print(f"Error: Input file not found: {results_csv}")
        print("Please ensure T026 has been run to generate the correlation results.")
        return
    
    print(f"Generating sensitivity comparison chart from {results_csv}...")
    generate_sensitivity_bar_chart(results_csv, output_png)
    print(f"Chart saved to: {output_png}")

if __name__ == "__main__":
    main()