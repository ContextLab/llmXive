"""
Visualization generator for dependency analysis.
Creates scatter plots of dependency age vs. vulnerability count.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# Use non-interactive backend for server environments
matplotlib.use('Agg')

from src.analysis.correlation import load_dependencies_data


def create_scatter_plot(
    data: pd.DataFrame,
    output_path: Path,
    title: str = "Dependency Age vs Vulnerability Count",
    xlabel: str = "Age in Days (since last release)",
    ylabel: str = "Vulnerability Count",
    figsize: tuple = (10, 6),
    dpi: int = 150,
    alpha: float = 0.6,
    color: str = '#2E86AB'
) -> str:
    """
    Create a scatter plot of dependency age vs vulnerability count.

    Args:
        data: DataFrame containing 'age_in_days' and 'vulnerability_count' columns
        output_path: Path to save the plot (must be .png)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size in inches
        dpi: Resolution
        alpha: Transparency of points
        color: Color of points

    Returns:
        Path to the saved plot as string
    """
    # Validate input data
    if 'age_in_days' not in data.columns or 'vulnerability_count' not in data.columns:
        raise ValueError("DataFrame must contain 'age_in_days' and 'vulnerability_count' columns")

    # Filter out rows where age_in_days is NaN for plotting
    plot_data = data.dropna(subset=['age_in_days'])

    if len(plot_data) == 0:
        raise ValueError("No valid data points to plot after filtering NaN values")

    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Create scatter plot
    ax.scatter(
        plot_data['age_in_days'],
        plot_data['vulnerability_count'],
        alpha=alpha,
        color=color,
        edgecolors='w',
        linewidth=0.5,
        s=20
    )

    # Set labels and title
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)

    # Set axis limits with some padding
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    # Rotate x-axis labels if there are many unique values
    if len(plot_data['age_in_days'].unique()) > 10:
        plt.xticks(rotation=45, ha='right')

    # Tight layout to prevent label cutoff
    plt.tight_layout()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save plot
    plt.savefig(output_path, bbox_inches='tight')
    plt.close(fig)

    return str(output_path)


def create_scatter_plot_with_regression(
    data: pd.DataFrame,
    output_path: Path,
    title: str = "Dependency Age vs Vulnerability Count (with Trend)",
    xlabel: str = "Age in Days (since last release)",
    ylabel: str = "Vulnerability Count",
    figsize: tuple = (10, 6),
    dpi: int = 150,
    alpha: float = 0.6,
    color: str = '#2E86AB',
    trend_color: str = '#E94F37'
) -> str:
    """
    Create a scatter plot with a linear regression trend line.

    Args:
        data: DataFrame containing 'age_in_days' and 'vulnerability_count' columns
        output_path: Path to save the plot
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size
        dpi: Resolution
        alpha: Transparency
        color: Point color
        trend_color: Trend line color

    Returns:
        Path to the saved plot as string
    """
    # Validate input data
    if 'age_in_days' not in data.columns or 'vulnerability_count' not in data.columns:
        raise ValueError("DataFrame must contain 'age_in_days' and 'vulnerability_count' columns")

    # Filter out rows where age_in_days is NaN
    plot_data = data.dropna(subset=['age_in_days'])

    if len(plot_data) == 0:
        raise ValueError("No valid data points to plot after filtering NaN values")

    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Scatter plot
    ax.scatter(
        plot_data['age_in_days'],
        plot_data['vulnerability_count'],
        alpha=alpha,
        color=color,
        edgecolors='w',
        linewidth=0.5,
        s=20,
        label='Data Points'
    )

    # Calculate and plot trend line (linear regression)
    x_vals = plot_data['age_in_days'].values
    y_vals = plot_data['vulnerability_count'].values

    # Fit linear regression
    z = np.polyfit(x_vals, y_vals, 1)
    p = np.poly1d(z)

    # Create line points
    x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
    y_line = p(x_line)

    # Plot trend line
    ax.plot(x_line, y_line, color=trend_color, linewidth=2, linestyle='-', label=f'Trend Line (y={z[0]:.4f}x+{z[1]:.4f})')

    # Set labels and title
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Add legend
    ax.legend(loc='best', fontsize=10)

    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)

    # Set axis limits
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    plt.tight_layout()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save plot
    plt.savefig(output_path, bbox_inches='tight')
    plt.close(fig)

    return str(output_path)


def generate_visualization_report(
    input_csv: str,
    output_dir: str,
    base_filename: str = "age_vs_vulnerability"
) -> Dict[str, Any]:
    """
    Generate visualization report from the processed dependencies data.

    Args:
        input_csv: Path to the input CSV file (dependencies_raw.csv)
        output_dir: Directory to save the output plots
        base_filename: Base name for output files

    Returns:
        Dictionary with paths to generated files and metadata
    """
    input_path = Path(input_csv)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    # Load data
    data = load_dependencies_data(input_path)

    # Generate basic scatter plot
    basic_plot_path = output_path / f"{base_filename}.png"
    basic_plot = create_scatter_plot(
        data,
        basic_plot_path,
        title="Dependency Age vs Vulnerability Count",
        xlabel="Age in Days (since last release)",
        ylabel="Vulnerability Count"
    )

    # Generate scatter plot with trend line
    trend_plot_path = output_path / f"{base_filename}_trend.png"
    trend_plot = create_scatter_plot_with_regression(
        data,
        trend_plot_path,
        title="Dependency Age vs Vulnerability Count (with Regression Trend)",
        xlabel="Age in Days (since last release)",
        ylabel="Vulnerability Count"
    )

    # Create summary metadata
    metadata = {
        "input_file": str(input_path),
        "total_records": len(data),
        "valid_records": len(data.dropna(subset=['age_in_days'])),
        "plots_generated": [
            {
                "type": "scatter",
                "path": basic_plot,
                "filename": basic_plot_path.name
            },
            {
                "type": "scatter_with_trend",
                "path": trend_plot,
                "filename": trend_plot_path.name
            }
        ],
        "statistics": {
            "mean_age": float(data['age_in_days'].mean()) if not data['age_in_days'].isna().all() else None,
            "median_age": float(data['age_in_days'].median()) if not data['age_in_days'].isna().all() else None,
            "mean_vulnerabilities": float(data['vulnerability_count'].mean()),
            "median_vulnerabilities": float(data['vulnerability_count'].median()),
            "max_age": float(data['age_in_days'].max()) if not data['age_in_days'].isna().all() else None,
            "max_vulnerabilities": int(data['vulnerability_count'].max())
        }
    }

    return metadata


def main():
    """
    Main entry point for generating visualizations.
    Reads from data/processed/dependencies_raw.csv and outputs to figures/
    """
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    input_csv = project_root / "data" / "processed" / "dependencies_raw.csv"
    output_dir = project_root / "figures"

    print(f"Starting visualization generation...")
    print(f"Input: {input_csv}")
    print(f"Output: {output_dir}")

    if not input_csv.exists():
        print(f"Error: Input file not found: {input_csv}")
        print("Please ensure data collection (T018) and analysis (T024) have been completed.")
        return 1

    try:
        metadata = generate_visualization_report(
            input_csv=str(input_csv),
            output_dir=str(output_dir),
            base_filename="age_vs_vulnerability"
        )

        print(f"\nVisualization generation complete!")
        print(f"Total records processed: {metadata['total_records']}")
        print(f"Valid records (with age data): {metadata['valid_records']}")
        print(f"\nGenerated files:")
        for plot in metadata['plots_generated']:
            print(f"  - {plot['path']}")

        print(f"\nStatistics:")
        stats = metadata['statistics']
        if stats['mean_age'] is not None:
            print(f"  Mean age: {stats['mean_age']:.1f} days")
            print(f"  Median age: {stats['median_age']:.1f} days")
            print(f"  Max age: {stats['max_age']:.1f} days")
        print(f"  Mean vulnerabilities: {stats['mean_vulnerabilities']:.2f}")
        print(f"  Median vulnerabilities: {stats['median_vulnerabilities']:.2f}")
        print(f"  Max vulnerabilities: {stats['max_vulnerabilities']}")

        return 0

    except Exception as e:
        print(f"Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())